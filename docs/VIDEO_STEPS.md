# Assignment II - demo video steps (about 6-8 minutes)

## Before you record

1. In the lab, make sure the app is running. In the lab terminal:

       export PATH=~/bin:$PATH
       cd /home/cloud/Documents/market-ops-ai
       curl -s localhost:8000/health

   If you don't see {"status":"ok",...}, run `bash scripts/lab_run.sh serve` and wait 1-2 minutes.

2. In lab Firefox, open two tabs:
   - Tab 1: http://localhost:8000/docs
   - Tab 2: http://localhost:8501
   Close the "Refresh Firefox" banner (X). Zoom 67% is fine.

3. In the lab terminal, run `clear`, then `bash scripts/lab_run.sh curl` once, so the API calls are on screen.

4. On your PC: maximise the Chrome window with the lab, and close other windows and notifications
   (Windows: Settings > System > Notifications > Do not disturb ON).

5. Do not show the Chrome address bar for long (the lab URL contains a session token). If possible,
   press F11 in Chrome for full screen; this hides the address bar.

## Start recording (Windows Snipping Tool)

1. Press Win + Shift + R (or open Snipping Tool > Record icon > New).
2. Drag a box around the lab window (or the whole screen).
3. Optional: turn the microphone on (mic icon) to narrate.
4. Click Start. A 3-second countdown follows.
5. To finish: click the Stop (red square) button in the bar at the top.
6. The recording opens in Snipping Tool: click Save (floppy icon) > save as
   AIMLZG549_Group31_Demo.mp4 in Downloads.

(Alternative: Microsoft Teams / Clipchamp / OBS, any MP4 recorder is fine.)

## What to show and say (script)

| Time      | Show                                                            | Say (roughly)                                                                                         |
|-----------|-----------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| 0:00-0:30 | Lab desktop                                                     | "we are Group 31. Our app is a Market Operations Ticket Copilot: an NLP assistant for electricity-market help desks, running in the BITS lab on CPU." |
| 0:30-1:15 | Lab terminal: scroll up to the fine-tuning results              | "Part II: we fine-tuned DistilBERT on 8 ticket categories. On unseen ticket templates it reaches 75.75% accuracy versus 55.5% for a TF-IDF baseline." |
| 1:15-1:45 | Lab terminal: the index and eval output                         | "Part III: the four PJM market manuals were split into 2,589 chunks in a FAISS index. The correct manual is retrieved for 12 of 12 test questions." |
| 1:45-2:15 | Firefox tab 1: /docs                                            | "The FastAPI service exposes each sub-task as a REST endpoint: health, classify, summarize, extract, rag/ask and triage." |
| 2:15-2:45 | Lab terminal: the curl output                                   | "Calling the API directly: HTTP 200 for valid requests, and HTTP 422 when the ticket text is empty." |
| 2:45-4:30 | Firefox tab 2: End-to-end triage > Run triage (takes ~1.5 min)  | While it runs: "Triage chains all sub-tasks: classify, summarise, extract fields, retrieve rules, draft a reply." When done, scroll slowly: category + confidence, summary, extracted fields, draft reply, manual sections used. |
| 4:30-5:00 | Classify tab > Classify                                         | "Sub-task 1: the fine-tuned classifier routes the ticket to the Credit Risk queue with 98% confidence." |
| 5:00-5:30 | Summarise tab > Summarise                                       | "Sub-task 2: a long email thread summarised into two sentences." |
| 5:30-6:00 | Extract tab > Extract                                           | "Sub-task 3: dates, hour-ending, amounts, MWh, invoice and ticket IDs, and pricing nodes extracted." |
| 6:00-7:15 | Manuals chatbot tab: type "What is the deadline for submitting a billing dispute?" > Enter (30-60 s) > click Sources | "Part III: the RAG chatbot answers from the manuals and shows which manual pages it used. Retrieval is accurate; the small CPU model sometimes mixes passages, which is why we recommend enforced citations." |
| 7:15-7:30 | Any screen                                                      | "Thank you." Stop the recording. |

Tip: if a step is slow, keep talking about what it does, or pause the recording (pause button) and resume when the result appears.

## Upload to Google Drive

1. Open https://drive.google.com on your PC (signed in with your BITS / Google account).
2. New > File upload > choose AIMLZG549_Group31_Demo.mp4. Wait for the upload to finish.
3. Right-click the video > Share > Share.
4. Under "General access" choose "Anyone with the link" (Viewer). Click Copy link > Done.
5. Open the link in a private/incognito window to check it plays without signing in.
6. Send the link to Claude so it can be added to the report.

## After recording

In the lab terminal: `bash scripts/lab_run.sh stop`
