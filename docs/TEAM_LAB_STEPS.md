# Assignment II (Group 31): lab steps for each member

The repository is public, so anyone can clone it without a GitHub login:

    https://github.com/karthikchundi-commits/market-ops-ai.git

Each member runs in their **own** BITS Prayogshala Linux VM session (Rocky Linux, CPU only).
Screenshots: take them on your own PC with Win + Shift + S, and **leave out the browser address bar** (the lab URL contains a session token).
Name each screenshot with your initials first, e.g. `HEMA_01_api_docs.png`.

---------------------------------------------------------------------------------------------------

## Part A: everyone (about 20 minutes, mostly waiting)

Open a Terminal in the lab VM and run these lines one by one:

    # 1. The lab's default python3 is 3.9 (too old). Point python3 at the installed 3.11:
    mkdir -p ~/bin
    ln -sf /usr/bin/python3.11 ~/bin/python3
    export PATH=~/bin:$PATH
    python3 --version                 # must show Python 3.11.x

    # 2. Get the code
    cd ~
    git clone https://github.com/karthikchundi-commits/market-ops-ai.git
    cd market-ops-ai

    # 3. Install everything (10-15 min). It ends with "torch ... | transformers ... | streamlit ..."
    bash scripts/lab_run.sh setup

    # 4. Record the environment  -> screenshot  <INITIALS>_L1_env.png
    bash scripts/lab_run.sh env

**IMPORTANT:** in every new terminal, first run:

    export PATH=~/bin:$PATH
    cd ~/market-ops-ai

If the lab VM was reset and `~/market-ops-ai` is gone, repeat Part A.

---------------------------------------------------------------------------------------------------

## Part B: Hemalatha: Part I (dataset, REST API, web UI). About 40 minutes

    bash scripts/lab_run.sh data                    # -> HEMA_L2_data.png  (train 1836 / val 324 / test 400)
    EPOCHS=1 bash scripts/lab_run.sh train          # ~20 min; the app needs the trained classifier
    bash scripts/lab_run.sh index                   # ~5 min; needed for triage
    bash scripts/lab_run.sh serve                   # wait for {"status":"ok",...}
    bash scripts/lab_run.sh curl                    # -> HEMA_02_api_calls.png (HTTP 200s, last one HTTP 422)

(EPOCHS=1 saves time. The report quotes the 3-epoch accuracy from the main run, so a slightly lower number here is expected.)

In the lab Firefox:

| Open / do                                                     | Screenshot                 |
|---------------------------------------------------------------|----------------------------|
| http://localhost:8000/docs                                    | HEMA_01_api_docs.png       |
| http://localhost:8501 > Classify tab > Classify              | HEMA_04_ui_classify.png    |
| Summarise tab > Summarise                                    | HEMA_05_ui_summarise.png   |
| Extract tab > Extract                                        | HEMA_06_ui_extract.png     |
| End-to-end triage tab > Run triage (1.5-3 min)               | HEMA_03_ui_triage.png      |

Finish: `bash scripts/lab_run.sh stop`

---------------------------------------------------------------------------------------------------

## Part C: Siva Ganesh K: Part III (RAG index and chatbot). About 25 minutes, no training needed

    bash scripts/lab_run.sh index                   # -> SIVA_L4_index.png  (4 manuals, ~2589 chunks)
    bash scripts/lab_run.sh serve                   # wait for {"status":"ok",...}

Ask the chatbot through the API (first answer can take 1-2 min while the model loads):

    curl -s -X POST localhost:8000/rag/ask -H 'Content-Type: application/json' \
         -d '{"question":"What is the deadline for submitting a billing dispute?"}'
                                                    # -> SIVA_08_rag_api.png

In the lab Firefox open http://localhost:8501 > **Manuals chatbot (RAG)** tab:

| Ask (press Enter, wait 30-90 s, then click Sources)                         | Screenshot             |
|-----------------------------------------------------------------------------|------------------------|
| What is the deadline for submitting a billing dispute?                      | SIVA_07_rag_chat_1.png |
| How are balancing operating reserve credits calculated?                     | SIVA_07_rag_chat_2.png |

(Do not use the Classify or Triage tabs: they need the trained classifier, which this part skips.)

Finish: `bash scripts/lab_run.sh stop`

---------------------------------------------------------------------------------------------------

## Part D: Vadapalli Rohini: evaluation and testing. About 50 minutes

    bash scripts/lab_run.sh data
    EPOCHS=1 bash scripts/lab_run.sh train          # ~20 min; evaluation needs the classifier
    bash scripts/lab_run.sh index                   # ~5 min
    bash scripts/lab_run.sh eval                    # 10-15 min -> ROHINI_L5_eval.png
                                                    #   (retrieval hit@1 / hit@4, extraction scores, latency)
    cat reports/evaluation.json | head -60          # -> ROHINI_eval_json.png

API testing (valid and invalid requests):

    bash scripts/lab_run.sh serve
    bash scripts/lab_run.sh curl                    # -> ROHINI_02_api_calls.png (HTTP 200s + HTTP 422)

Finish: `bash scripts/lab_run.sh stop`

---------------------------------------------------------------------------------------------------

## Part E: C V R Karthik: DONE

Setup, full 3-epoch training, index, eval, app, screenshots and the demo video were completed on 2026-11-02.

---------------------------------------------------------------------------------------------------

## If something goes wrong

- `python3 --version` still shows 3.9: run `export PATH=~/bin:$PATH` again in this terminal.
- "Killed" / out of memory: `export LOCAL_LLM=Qwen/Qwen2.5-0.5B-Instruct`, then repeat the step (this is already the default on VMs with less than 14 GB of RAM).
- A manual download fails in `index`: run `bash scripts/lab_run.sh index` again.
- http://localhost:8501 does not load: wait 30 s and refresh; otherwise run `tail -20 logs/ui.log` and screenshot it.
- Send all screenshots to Karthik for the report.
