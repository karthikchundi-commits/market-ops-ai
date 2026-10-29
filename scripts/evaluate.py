"""Part IV (Analyse) - measure the copilot against workplace needs.

* Retrieval: hit@k - does a passage from the manual that governs the topic appear in the top k?
* Extraction: recall of hand-labelled market fields on the sample threads.
* Latency: wall-clock per sub-task on CPU.
* RAG answers: generated answers + whether they cite a passage (saved for manual review).

Usage:  python scripts/evaluate.py [--no-generate]
Output: reports/evaluation.json
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import llm, samples, tasks  # noqa: E402

# question -> manual(s) that govern the topic
RETRIEVAL_SET = [
    ("How is balancing operating reserve credit calculated for a generator dispatched in real time?", {"m28"}),
    ("What is the deadline for submitting a billing dispute?", {"m29"}),
    ("How are meter data corrections handled in the reconciliation process?", {"m28"}),
    ("What happens if a capacity resource does not perform during a performance assessment interval?", {"m18"}),
    ("When is the day-ahead energy market offer submission deadline?", {"m11"}),
    ("How are day-ahead and real-time spot market energy charges calculated?", {"m28"}),
    ("How often are invoices issued to market participants and when is payment due?", {"m29"}),
    ("What is the Base Residual Auction and when is it held?", {"m18"}),
    ("How are virtual bids such as increment offers and decrement bids cleared in the day-ahead market?", {"m11"}),
    ("How is regulation market performance score used in settlement credits?", {"m28", "m11"}),
    ("How are congestion charges and transmission losses charges calculated?", {"m28"}),
    ("What are the requirements for capacity resources to submit offers in the energy market (must offer)?", {"m18", "m11"}),
]

EXTRACTION_GOLD = {
    "THREAD_SETTLEMENT": {"dates": {"2026-08-14"}, "hour_ending": {"HE15", "HE19"},
                          "amounts_usd": {"$48,350.00"}, "quantities": {"210 MW", "1,050 MWh"},
                          "invoice_ids": {"INV-604118"}, "ticket_ids": {"MO-48213"},
                          "pricing_nodes": {"WESTFALL 230KV GEN1"}},
    "THREAD_METER": {"dates": {"2026-07-09", "2026-07-12"}, "quantities": {"4,320 MWh"},
                     "pricing_nodes": {"SUNBURY 500KV"}},
}


def timed(fn, *a):
    t = time.perf_counter()
    out = fn(*a)
    return out, (time.perf_counter() - t) * 1000


def main(generate):
    results = {"llm_backend": llm.backend(), "llm_model": llm.model_name()}

    # warm-up so latencies exclude model loading
    tasks.classify("warm up"); tasks.summarize(samples.THREAD_METER); tasks.extract("warm up"); tasks.retrieve("x")

    rows, hits1, hits4 = [], 0, 0
    for q, gold in RETRIEVAL_SET:
        got = tasks.retrieve(q, k=4)
        codes = [p["code"] for p in got]
        h1, h4 = codes[0] in gold, bool(set(codes) & gold)
        hits1 += h1; hits4 += h4
        rows.append({"question": q, "expected": sorted(gold), "retrieved": [f"{p['code']} p.{p['page']}" for p in got],
                     "hit@1": h1, "hit@4": h4})
    results["retrieval"] = {"n": len(RETRIEVAL_SET), "hit@1": hits1 / len(RETRIEVAL_SET),
                            "hit@4": hits4 / len(RETRIEVAL_SET), "detail": rows}
    print(f"retrieval hit@1={hits1}/{len(rows)} hit@4={hits4}/{len(rows)}")

    ext = {}
    for name, gold in EXTRACTION_GOLD.items():
        got = tasks.extract(getattr(samples, name))["fields"]
        g = {(k, v) for k, vs in gold.items() for v in vs}
        p = {(k, v) for k, vs in got.items() for v in vs}
        ext[name] = {"recall": len(g & p) / len(g), "precision": len(g & p) / max(1, len(p)),
                     "missed": sorted(map(list, g - p)), "extra": sorted(map(list, p - g))}
    results["extraction"] = ext
    print("extraction", {k: round(v["recall"], 2) for k, v in ext.items()})

    lat = {"classify": [], "summarize": [], "extract": [], "retrieve": []}
    for t in samples.SHORT_TICKETS + [samples.THREAD_SETTLEMENT, samples.THREAD_METER]:
        lat["classify"].append(timed(tasks.classify, t)[1])
        lat["extract"].append(timed(tasks.extract, t)[1])
        lat["retrieve"].append(timed(tasks.retrieve, t)[1])
    for t in [samples.THREAD_SETTLEMENT, samples.THREAD_METER]:
        lat["summarize"].append(timed(tasks.summarize, t)[1])
    results["short_ticket_routing"] = [{"ticket": t[:80], **tasks.classify(t)} for t in samples.SHORT_TICKETS]

    if generate:
        answers, gen_ms = [], []
        for q in samples.RAG_QUESTIONS:
            out, ms = timed(tasks.ask, q)
            gen_ms.append(ms)
            answers.append({"question": q, "answer": out["answer"], "cited": "[" in out["answer"],
                            "sources": [f"{s['source']} p.{s['page']}" for s in out["sources"]]})
            print(f"  RAG {ms / 1000:.1f}s  {q[:60]}")
        lat["rag_answer"] = gen_ms
        results["rag_answers"] = answers
        out, ms = timed(tasks.triage, samples.THREAD_SETTLEMENT)
        lat["triage_end_to_end"] = [ms]
        results["triage_example"] = out

    results["latency_ms"] = {k: {"median": round(statistics.median(v)), "max": round(max(v))}
                             for k, v in lat.items() if v}
    print("latency", results["latency_ms"])
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "evaluation.json").write_text(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-generate", action="store_true")
    main(not ap.parse_args().no_generate)
