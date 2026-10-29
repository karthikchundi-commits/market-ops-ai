"""Streamlit front end. Talks to the FastAPI service over HTTP.

Run:  streamlit run app/ui.py     (API must be running on API_URL)
"""
import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import samples  # noqa: E402

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Market Ops Ticket Copilot", page_icon="⚡", layout="wide")


def call(path, payload=None):
    try:
        r = requests.post(f"{API}{path}", json=payload, timeout=600) if payload is not None \
            else requests.get(f"{API}{path}", timeout=10)
    except requests.ConnectionError:
        st.error(f"Cannot reach the API at {API}. Start it with: uvicorn app.api:app --port 8000")
        st.stop()
    if r.status_code != 200:
        st.error(f"HTTP {r.status_code}: {r.text}")
        st.stop()
    return r.json()


def show_sources(sources):
    st.dataframe(pd.DataFrame(sources), hide_index=True, use_container_width=True)


health = call("/health")
with st.sidebar:
    st.header("⚡ Market Ops Copilot")
    st.caption("Electricity market-operations help desk assistant")
    st.markdown(f"**API:** `{API}`  \n**Status:** {health['status']}  \n"
                f"**LLM backend:** {health['llm_backend']}  \n**LLM:** `{health['llm_model']}`")
    st.divider()
    st.markdown("**Models**\n- Classifier: DistilBERT (fine-tuned)\n- Summariser: DistilBART-CNN\n"
                "- NER: BERT-base-NER + market rules\n- Retriever: MiniLM-L6 + FAISS\n"
                "- Generator: " + health["llm_model"])

st.title("Market Operations Ticket Copilot")
tab_triage, tab_cls, tab_sum, tab_ext, tab_chat = st.tabs(
    ["🧭 End-to-end triage", "🏷️ Classify", "📝 Summarise", "🔎 Extract", "💬 Manuals chatbot (RAG)"])

with tab_triage:
    st.subheader("Triage an incoming ticket")
    st.caption("Routes the ticket, summarises it, extracts key fields, retrieves the governing "
               "manual sections and drafts a first reply.")
    choice = st.selectbox("Load a sample", ["Settlement dispute thread", "Meter correction thread"]
                          + samples.SHORT_TICKETS, key="tri_sample")
    default = {"Settlement dispute thread": samples.THREAD_SETTLEMENT,
               "Meter correction thread": samples.THREAD_METER}.get(choice, choice)
    text = st.text_area("Ticket text", default, height=260, key="tri_text")
    if st.button("Run triage", type="primary"):
        with st.spinner("Running classifier → summariser → extractor → retriever → LLM ..."):
            res = call("/triage", {"text": text})
        c = res["classification"]
        m1, m2 = st.columns([3, 1])
        m1.metric("Category", c["label"])
        m2.metric("Confidence", f"{c['confidence']:.1%}")
        st.markdown(f"**Route to queue:** {c['queue']}")
        st.markdown("**Summary**")
        st.info(res["summary"]["summary"])
        st.markdown("**Extracted fields**")
        st.json(res["extraction"]["fields"])
        st.markdown("**Draft reply** (for analyst review)")
        st.success(res["draft_reply"])
        st.markdown("**Manual sections used**")
        show_sources(res["sources"])
        st.caption(f"End-to-end latency: {res['latency_ms']:,} ms · generator: {res['model']}")

with tab_cls:
    st.subheader("Ticket classification (fine-tuned DistilBERT)")
    t = st.text_area("Ticket", samples.SHORT_TICKETS[0], height=120, key="cls_text")
    if st.button("Classify"):
        res = call("/classify", {"text": t})
        st.metric(res["queue"], res["label"], f"{res['confidence']:.1%} confidence")
        st.bar_chart(pd.Series(res["scores"], name="probability"))
        st.caption(f"{res['latency_ms']} ms")

with tab_sum:
    st.subheader("Thread summarisation (DistilBART-CNN)")
    t = st.text_area("Email thread", samples.THREAD_METER, height=260, key="sum_text")
    if st.button("Summarise"):
        res = call("/summarize", {"text": t})
        st.info(res["summary"])
        st.caption(f"{res['input_words']} words in · {res['latency_ms']} ms")

with tab_ext:
    st.subheader("Entity & field extraction (BERT-NER + market rules)")
    t = st.text_area("Text", samples.THREAD_SETTLEMENT, height=260, key="ext_text")
    if st.button("Extract"):
        res = call("/extract", {"text": t})
        c1, c2 = st.columns(2)
        c1.markdown("**Market fields**")
        c1.json(res["fields"])
        c2.markdown("**Named entities**")
        c2.dataframe(pd.DataFrame(res["entities"]), hide_index=True, use_container_width=True)
        st.caption(f"{res['latency_ms']} ms")

with tab_chat:
    st.subheader("Ask the PJM manuals")
    st.caption("Retrieval-augmented answers from Manuals 11, 18, 28 and 29, with citations.")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    with st.expander("Example questions"):
        for q in samples.RAG_QUESTIONS:
            st.markdown(f"- {q}")
    for turn in st.session_state.chat:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn.get("sources"):
                with st.expander("Sources"):
                    show_sources(turn["sources"])
    if q := st.chat_input("Ask about settlements, billing, capacity, market rules ..."):
        with st.chat_message("user"):
            st.markdown(q)
        history = [{"role": t["role"], "content": t["content"]} for t in st.session_state.chat]
        with st.chat_message("assistant"):
            with st.spinner("Retrieving and generating ..."):
                res = call("/rag/ask", {"question": q, "history": history})
            st.markdown(res["answer"])
            with st.expander("Sources"):
                show_sources(res["sources"])
            st.caption(f"{res['latency_ms']:,} ms · {res['model']}")
        st.session_state.chat += [{"role": "user", "content": q},
                                  {"role": "assistant", "content": res["answer"], "sources": res["sources"]}]
