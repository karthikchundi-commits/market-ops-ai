# Lab run checklist (Assignment II)

Run the commands in the lab VM terminal. Save each screenshot into `docs/screenshots/lab/` with the name shown. The report builder uses a lab screenshot whenever one exists.
Crop the browser address bar out of screenshots, because the lab URL contains a session token.

| # | Command / page | Screenshot file |
|---|----------------|-----------------|
| 1 | `git clone <repo> && cd market-ops-ai && bash scripts/lab_run.sh setup` | (no screenshot) |
| 2 | `bash scripts/lab_run.sh env`: user, host, CPU, RAM, Python and torch versions | `L1_env.png` |
| 3 | `bash scripts/lab_run.sh data`: dataset sizes | `L2_data.png` |
| 4 | `bash scripts/lab_run.sh train` (about 10-25 min on CPU): baseline versus fine-tuned accuracy and the classification report | `L3_train.png` |
| 5 | `bash scripts/lab_run.sh index`: manuals downloaded, "indexed N chunks" | `L4_index.png` |
| 6 | `bash scripts/lab_run.sh eval`: retrieval hit@k, extraction, latency | `L5_eval.png` |
| 7 | `bash scripts/lab_run.sh serve`, then open http://localhost:8000/docs | `01_api_docs.png` |
| 8 | `bash scripts/lab_run.sh curl`: HTTP 200 and 422 responses | `02_api_calls.png` |
| 9 | http://localhost:8501, **End-to-end triage** tab, click *Run triage* (about 1.5 min) | `03_ui_triage.png` |
| 10 | **Classify** tab, click *Classify* | `04_ui_classify.png` |
| 11 | **Summarise** tab, click *Summarise* | `05_ui_summarise.png` |
| 12 | **Extract** tab, click *Extract* | `06_ui_extract.png` |
| 13 | **Manuals chatbot** tab: ask "What is the deadline for submitting a billing dispute?", then open *Sources* | `07_ui_rag_chat.png` |
| 14 | `bash scripts/lab_run.sh stop` | (no screenshot) |

Copy `reports/classifier_metrics.json`, `reports/evaluation.json` and `reports/confusion_matrix.png` back from the lab, so the report numbers match the lab run.
