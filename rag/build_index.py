"""Part III - download public PJM market manuals and build a FAISS vector index.

The manuals are the same rulebooks a market-operations analyst consults when
answering participant tickets (settlements, billing, capacity, market rules).

Usage:  python rag/build_index.py
Output: rag/docs/*.pdf, rag/index/faiss.index, rag/index/chunks.json
"""
import json
import re
from pathlib import Path

import faiss
import requests
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "rag" / "docs"
INDEX = ROOT / "rag" / "index"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

MANUALS = {
    "PJM Manual 11 - Energy & Ancillary Services Market Operations": "m11",
    "PJM Manual 18 - Capacity Market": "m18",
    "PJM Manual 28 - Operating Agreement Accounting": "m28",
    "PJM Manual 29 - Billing": "m29",
}
URL = "https://www.pjm.com/-/media/documents/manuals/{}.ashx"
CHUNK_CHARS, OVERLAP = 1000, 200


def download():
    DOCS.mkdir(parents=True, exist_ok=True)
    for title, code in MANUALS.items():
        path = DOCS / f"{code}.pdf"
        if path.exists():
            continue
        r = requests.get(URL.format(code), headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
        r.raise_for_status()
        path.write_bytes(r.content)
        print(f"downloaded {title} ({len(r.content) / 1e6:.1f} MB)")


def chunk_pages():
    chunks = []
    for title, code in MANUALS.items():
        reader = PdfReader(DOCS / f"{code}.pdf")
        for page_no, page in enumerate(reader.pages, start=1):
            text = re.sub(r"\s+", " ", page.extract_text() or "").strip()
            if len(text) < 200:  # skip blank / TOC-fragment pages
                continue
            for start in range(0, len(text), CHUNK_CHARS - OVERLAP):
                piece = text[start:start + CHUNK_CHARS]
                if len(piece) < 150:
                    break
                chunks.append({"source": title, "code": code, "page": page_no, "text": piece})
        print(f"{code}: {len(reader.pages)} pages")
    return chunks


def main():
    download()
    chunks = chunk_pages()
    model = SentenceTransformer(EMBED_MODEL)
    emb = model.encode([c["text"] for c in chunks], batch_size=64, show_progress_bar=True,
                       normalize_embeddings=True)
    index = faiss.IndexFlatIP(emb.shape[1])  # cosine similarity on normalised vectors
    index.add(emb)
    INDEX.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX / "faiss.index"))
    (INDEX / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    print(f"indexed {len(chunks)} chunks, dim={emb.shape[1]}")


if __name__ == "__main__":
    main()
