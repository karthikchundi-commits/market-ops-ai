"""The four NLP sub-tasks of the Market Operations Ticket Copilot.

1. classify()   - ticket routing, fine-tuned DistilBERT (Part II)
2. summarize()  - abstractive summary of long ticket threads, DistilBART-CNN
3. extract()    - named entities (BERT-NER) + market fields (regex rules)
4. ask()        - RAG question answering over PJM manuals (Part III)
triage() chains all four into one workflow: route, summarise, extract, retrieve
the governing rules and draft a reply for the analyst.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from app import llm

ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER_DIR = ROOT / "models" / "ticket-classifier"
INDEX_DIR = ROOT / "rag" / "index"
SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"
NER_MODEL = "dslim/bert-base-NER"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

QUEUES = {
    "settlement_dispute": "Settlements - Disputes",
    "meter_data_correction": "Settlements - Meter Data",
    "bid_offer_submission": "Market Operations - Day-Ahead / Real-Time",
    "billing_invoice": "Billing",
    "credit_collateral": "Credit Risk",
    "capacity_market": "Capacity Market Operations",
    "system_access": "Market Systems Access / IT",
    "outage_reporting": "Outage Coordination",
}


# ---------- 1. classification ----------
@lru_cache(maxsize=1)
def _classifier():
    from transformers import pipeline
    return pipeline("text-classification", model=str(CLASSIFIER_DIR), top_k=None)


def classify(text: str) -> dict:
    scores = _classifier()(text, truncation=True, max_length=128)[0]
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)
    top = scores[0]
    return {"label": top["label"], "confidence": round(top["score"], 4),
            "queue": QUEUES.get(top["label"], "Market Operations"),
            "scores": {s["label"]: round(s["score"], 4) for s in scores[:3]}}


# ---------- 2. summarization ----------
@lru_cache(maxsize=1)
def _summarizer():
    # transformers 5 removed the "summarization" pipeline, so drive the seq2seq model directly
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    return AutoTokenizer.from_pretrained(SUMMARY_MODEL), AutoModelForSeq2SeqLM.from_pretrained(SUMMARY_MODEL)


def summarize(text: str) -> dict:
    import torch
    words = len(text.split())
    if words < 40:
        return {"summary": text.strip(), "input_words": words, "note": "too short to summarise"}
    tok, model = _summarizer()
    max_len = min(130, max(30, words // 2))
    inputs = tok(text, return_tensors="pt", truncation=True, max_length=1024)
    with torch.no_grad():
        ids = model.generate(**inputs, max_length=max_len, min_length=min(25, max_len - 5),
                             num_beams=4, no_repeat_ngram_size=3, early_stopping=True)
    summary = re.sub(r"\s+([.,])", r"\1", tok.decode(ids[0], skip_special_tokens=True)).strip()
    return {"summary": summary, "input_words": words}


# ---------- 3. information extraction ----------
@lru_cache(maxsize=1)
def _ner():
    from transformers import pipeline
    return pipeline("token-classification", model=NER_MODEL, aggregation_strategy="simple")


FIELD_PATTERNS = {
    "dates": r"\b20\d{2}-\d{2}-\d{2}\b",
    "hour_ending": r"\bHE ?\d{1,2}\b",
    "amounts_usd": r"\$\s?[\d,]+(?:\.\d{2})?(?:/MWh)?",
    "quantities": r"\b[\d,]+(?:\.\d+)? ?(?:MWh|MW)\b",
    "invoice_ids": r"\bINV-\d{6}\b",
    "ticket_ids": r"\bMO-\d{5}\b",
    "pricing_nodes": r"\b[A-Z][A-Z ]{2,}(?:\d{2,3}KV(?: [A-Z0-9]+)?|ZONE|HUB)\b",
}


def extract(text: str) -> dict:
    entities = [{"text": e["word"], "type": e["entity_group"], "score": round(float(e["score"]), 3)}
                for e in _ner()(text) if e["score"] > 0.6]
    fields = {k: sorted(set(m.strip() for m in re.findall(p, text))) for k, p in FIELD_PATTERNS.items()}
    return {"entities": entities, "fields": {k: v for k, v in fields.items() if v}}


# ---------- 4. RAG ----------
@lru_cache(maxsize=1)
def _index():
    import faiss
    from sentence_transformers import SentenceTransformer
    index = faiss.read_index(str(INDEX_DIR / "faiss.index"))
    chunks = json.loads((INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
    return index, chunks, SentenceTransformer(EMBED_MODEL)


def retrieve(query: str, k: int = 4) -> list[dict]:
    index, chunks, embedder = _index()
    q = embedder.encode([query], normalize_embeddings=True)
    scores, ids = index.search(q, k)
    return [{**chunks[i], "score": round(float(s), 4)} for s, i in zip(scores[0], ids[0])]


RAG_SYSTEM = (
    "You are a market-operations assistant for an electricity ISO/RTO. Answer the "
    "question using only the numbered context passages from the PJM manuals. Cite "
    "passages inline like [1] or [2]. If the context does not contain the answer, say "
    "you could not find it in the manuals. Be concise (under 150 words)."
)


def _context_block(passages):
    return "\n\n".join(f"[{n}] ({p['source']}, p.{p['page']}) {p['text']}"
                       for n, p in enumerate(passages, 1))


def ask(question: str, history: list[dict] | None = None, k: int = 4) -> dict:
    passages = retrieve(question, k)
    prompt = f"Context:\n{_context_block(passages)}\n\nQuestion: {question}"
    messages = (history or [])[-4:] + [{"role": "user", "content": prompt}]
    answer = llm.generate(RAG_SYSTEM, messages)
    return {"answer": answer, "backend": llm.backend(), "model": llm.model_name(),
            "sources": [{"source": p["source"], "page": p["page"], "score": p["score"],
                         "excerpt": p["text"][:300]} for p in passages]}


# ---------- unified workflow ----------
DRAFT_SYSTEM = (
    "You are an analyst on an electricity market-operations help desk. Write a short, "
    "professional first reply (under 120 words) to the market participant. Acknowledge "
    "the issue, state which team owns it, reference the relevant manual rule from the "
    "context with a citation like [1], and list any information still needed."
)


def triage(text: str) -> dict:
    cls = classify(text)
    summ = summarize(text)
    ext = extract(text)
    query = f"{cls['label'].replace('_', ' ')}: {summ['summary']}"
    passages = retrieve(query, k=3)
    prompt = (f"Ticket category: {cls['queue']}\nTicket summary: {summ['summary']}\n"
              f"Key fields: {json.dumps(ext['fields'])}\n\nContext:\n{_context_block(passages)}")
    draft = llm.generate(DRAFT_SYSTEM, [{"role": "user", "content": prompt}])
    return {"classification": cls, "summary": summ, "extraction": ext, "draft_reply": draft,
            "backend": llm.backend(), "model": llm.model_name(),
            "sources": [{"source": p["source"], "page": p["page"], "score": p["score"]}
                        for p in passages]}
