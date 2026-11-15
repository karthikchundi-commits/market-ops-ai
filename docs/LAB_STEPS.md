# Assignment II - lab steps (BITS Prayogshala Linux VM)

Plan for about 1.5-2 hours in the lab; most of it is waiting (setup ~15 min, training ~20 min).
Take screenshots on your own PC with Win + Shift + S. Leave out the browser address bar (the lab URL has a session token).
Save them with the exact names below, e.g. in Downloads\lab_shots\.

## A. Set up (no screenshots)

1. Log in to Prayogshala, start the Linux VM, open a Terminal.
2. Make sure Python 3.12 is active (the lab's default python3 is 3.9, which is too old):

       conda env list                       # reuse an existing 3.12 env if there is one
       conda create -n mops python=3.12 -y  # otherwise create one (2-3 min)
       conda activate mops
       python3 --version                    # must show 3.12.x

   In every new terminal run `conda activate mops` before any lab_run.sh step.
   If setup was already run with 3.9, delete it first: `rm -rf .venv`

3. Download the project:

       cd ~
       git clone https://github.com/karthikchundi-commits/market-ops-ai.git
       cd market-ops-ai

4. Install everything (10-15 min):

       bash scripts/lab_run.sh setup

   It ends with a line like "torch 2.x.x+cpu | transformers 5.x | streamlit 1.x".

## B. Run each stage and screenshot it

Run the command, wait until the $ prompt comes back, then take the screenshot.

| Step | Command                          | Wait       | What you see                                          | Save as       |
|------|----------------------------------|------------|-------------------------------------------------------|---------------|
| 5    | bash scripts/lab_run.sh env      | 5 sec      | user, host, CPUs, memory, Python/torch, CUDA False    | L1_env.png    |
| 6    | bash scripts/lab_run.sh data     | 5 sec      | train 1836, val 324, test 400                         | L2_data.png   |
| 7    | bash scripts/lab_run.sh train    | 10-25 min  | baseline ~55%, fine-tuned ~75%, per-category table    | L3_train.png  |
| 8    | bash scripts/lab_run.sh index    | 2-5 min    | 4 manuals downloaded, "indexed ~2589 chunks"          | L4_index.png  |
| 9    | bash scripts/lab_run.sh eval     | 5-10 min   | retrieval hit@1/hit@4, extraction scores, latency     | L5_eval.png   |

If the output is longer than the screen, take two shots (L3_train_a.png, L3_train_b.png).

## C. Start the app and screenshot it

10. Start the API and the web UI:

        bash scripts/lab_run.sh serve

    Wait until it prints {"status":"ok",...} and the two web addresses.

11. In the browser inside the lab VM open http://localhost:8000/docs
    -> save as 01_api_docs.png

12. Back in the terminal:

        bash scripts/lab_run.sh curl

    Several responses end with HTTP 200, the last one with HTTP 422 (deliberate empty-text error).
    -> save as 02_api_calls.png

13. In the lab browser open http://localhost:8501

| Step | Do this                                                                 | Wait        | Save as             |
|------|-------------------------------------------------------------------------|-------------|---------------------|
| 13a  | End-to-end triage tab -> click Run triage                               | 1.5-3 min   | 03_ui_triage.png    |
| 13b  | Classify tab -> click Classify                                          | few sec     | 04_ui_classify.png  |
| 13c  | Summarise tab -> click Summarise                                        | ~5 sec      | 05_ui_summarise.png |
| 13d  | Extract tab -> click Extract                                            | few sec     | 06_ui_extract.png   |
| 13e  | Manuals chatbot (RAG) tab -> ask "What is the deadline for submitting a billing dispute?" -> Enter -> click Sources | 30-60 sec | 07_ui_rag_chat.png |

## D. Record the video (5-8 min), app still running

1. Introduce yourself and the problem (~30 sec): Market Ops Ticket Copilot for electricity market help-desk tickets.
2. Show the training output: baseline vs fine-tuned accuracy.
3. Show the API docs page and the curl output.
4. Walk through the UI tabs: triage, classify, summarise, extract.
5. Ask the chatbot 1-2 questions and open Sources.
6. Upload to Google Drive, share as "Anyone with the link", copy the link.

## E. Bring the result files back

    ~/market-ops-ai/reports/classifier_metrics.json
    ~/market-ops-ai/reports/evaluation.json
    ~/market-ops-ai/reports/confusion_matrix.png

Easiest: upload them to Google Drive from the lab browser, then download on your PC.
Or run `cat reports/classifier_metrics.json` and `cat reports/evaluation.json` and screenshot the output.

## F. Finish

14. Stop the app:

        bash scripts/lab_run.sh stop

15. Send Claude the screenshots (L1-L5, 01-07), the three files and the video link.

## If something goes wrong

- Out of memory / "Killed" during eval or the chatbot:
  `export LOCAL_LLM=Qwen/Qwen2.5-0.5B-Instruct`, then repeat that step and serve.
- A manual download fails in index: run `bash scripts/lab_run.sh index` again.
- localhost:8501 does not load: wait 30 sec and refresh; else `tail -20 logs/ui.log` and screenshot it.
- Any other error: screenshot the terminal and send it to Claude.
