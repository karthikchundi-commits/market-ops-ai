// Builds docs/AIMLZG549_Assignment2_Group31.docx from screenshots, metrics and evaluation results.
// Usage: NODE_PATH=<dir with docx + image-size> node scripts/build_report_docx.js
const fs = require("fs");
const path = require("path");
const sizeOf = require("image-size");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, LevelFormat, PageBreak, Footer, PageNumber,
  TableOfContents,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const SHOTS = `${ROOT}/docs/screenshots`;
const REPORTS = `${ROOT}/reports`;
const OUT = `${ROOT}/docs/AIMLZG549_Assignment2_Group31.docx`;

const metrics = JSON.parse(fs.readFileSync(`${REPORTS}/classifier_metrics.json`));
const evalr = JSON.parse(fs.readFileSync(`${REPORTS}/evaluation.json`));
const pct = (x) => `${(x * 100).toFixed(1)}%`;
const sec = (ms) => `${(ms / 1000).toFixed(1)} s`;

const CONTENT_W = 9026; // A4 width 11906 - 2 x 1440 margins (DXA)
const MAX_PX = 600;
const FONT = "Calibri";
const border = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" };
const ACCENT = "1F4E79";

const p = (text, opts = {}) => new Paragraph({ spacing: { after: 120 }, ...opts, children: runs(text) });
// **bold** and `code` inline markup
function runs(text) {
  const out = [];
  for (const part of text.split(/(\*\*[^*]+\*\*|`[^`]+`)/)) {
    if (!part) continue;
    if (part.startsWith("**")) out.push(new TextRun({ text: part.slice(2, -2), bold: true }));
    else if (part.startsWith("`")) out.push(new TextRun({ text: part.slice(1, -1), font: "Consolas", size: 20 }));
    else out.push(new TextRun(part));
  }
  return out;
}
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: runs(t) });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const quote = (t) => new Paragraph({
  spacing: { before: 60, after: 160 }, indent: { left: 400 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: "2E75B6", space: 8 } },
  children: [new TextRun({ text: t, italics: true, size: 20, color: "333333" })],
});

// Prefer screenshots captured in the lab (docs/screenshots/lab/<name>) over local ones.
const LAB = `${SHOTS}/lab`;
const shotPath = (name) => (fs.existsSync(`${LAB}/${name}`) ? `${LAB}/${name}` : `${SHOTS}/${name}`);
function labFigure(name, caption) {
  if (fs.existsSync(`${LAB}/${name}`)) return figure(`${LAB}/${name}`, caption, 560);
  return [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 240 },
    border: { top: border, bottom: border, left: border, right: border },
    children: [new TextRun({ text: `[Lab screenshot ${name} — ${caption}]`, italics: true, color: "C00000" })] })];
}

let figNo = 0;
function figure(file, caption, maxPx = MAX_PX) {
  const buf = fs.readFileSync(file);
  const { width, height } = sizeOf(buf);
  let w = Math.min(maxPx, width);
  let h = Math.round((height * w) / width);
  if (h > 820) { w = Math.round((w * 820) / h); h = 820; } // keep tall captures on one page
  figNo += 1;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: w, height: h },
        altText: { title: caption, description: caption, name: path.basename(file) } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 240 },
      children: [new TextRun({ text: `Figure ${figNo}: `, bold: true, italics: true, size: 20, color: "555555" }),
                 new TextRun({ text: caption, italics: true, size: 20, color: "555555" })],
    }),
  ];
}

const borders = { top: border, bottom: border, left: border, right: border };
function table(header, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, isHead, w) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: isHead ? { fill: ACCENT, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: isHead
      ? [new TextRun({ text, bold: true, color: "FFFFFF", size: 20 })]
      : runs(String(text)) })],
  });
  return [new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, true, widths[i])) }),
      ...rows.map((r) => new TableRow({ children: r.map((t, i) => cell(t, false, widths[i])) })),
    ],
  }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}

const base = metrics.baseline_tfidf_lr, ft = metrics.finetuned_distilbert;
const lat = evalr.latency_ms;
const ret = evalr.retrieval;
const perClass = Object.entries(metrics.per_class).map(([k, v]) =>
  [k, v.precision.toFixed(2), v.recall.toFixed(2), v["f1-score"].toFixed(2)]);
const ragRows = evalr.rag_answers.map((a) => [a.question, a.answer.replace(/\s+/g, " ").slice(0, 330) + (a.answer.length > 330 ? " …" : ""), a.sources.slice(0, 2).join("; ")]);
const triage = evalr.triage_example;

const children = [
  // ---------- Cover ----------
  new Paragraph({ spacing: { before: 2000 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "AIMLZG 549 — API-driven Cloud Native Solutions", size: 32, color: ACCENT, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 },
    children: [new TextRun({ text: "Assignment II", size: 44, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 500 },
    children: [new TextRun({ text: "Market Operations Ticket Copilot — an API-based NLP assistant for electricity-market support desks", size: 28 })] }),
  ...table(["Field", "Value"], [
    ["Group No", "31"],
    ["Domain", "Energy — wholesale electricity market operations (ISO/RTO participant support)"],
    ["Category", "Natural Language Processing (NLP)"],
    ["Sub-tasks", "Text classification · Summarisation · Named-entity / field extraction · Retrieval-augmented question answering"],
    ["Platform", "Hugging Face Transformers + Sentence-Transformers + FAISS; FastAPI service; Streamlit UI"],
    ["Code", "`market-ops-ai/` (README.md has setup and run steps)"],
  ], [2400, 6626]),
  h2("Group Member Names with Contribution"),
  ...table(["Sl. No", "BITS ID", "Name", "Contribution (Qualitative)", "% (Quantitative)"], [
    ["1", "2025ae05338", "Chodavarapu Venkata Hemalatha", "<fill in>", "<x>"],
    ["2", "2025ae05356", "Siva Ganesh K", "<fill in>", "<x>"],
    ["3", "2025ae05851", "C V R Karthik", "<fill in>", "<x>"],
  ], [800, 1500, 2700, 2900, 1126]),
  pageBreak(),
  new Paragraph({ spacing: { after: 180 }, children: [new TextRun({ text: "Contents", size: 32, bold: true, color: ACCENT })] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  pageBreak(),

  // ---------- Lab execution ----------
  h1("Lab Execution"),
  p("The whole project was executed in the BITS virtual lab (Linux VM, CPU only) from the public repository with one script, `scripts/lab_run.sh`. Each step below was run in the lab terminal; the application screenshots in Parts I–III were also captured in the lab."),
  ...table(["Step", "Command", "Purpose"], [
    ["1", "`git clone https://github.com/karthikchundi-commits/market-ops-ai.git`", "Get the code"],
    ["2", "`bash scripts/lab_run.sh setup`", "Create virtualenv, install CPU PyTorch, Transformers, FAISS, FastAPI, Streamlit"],
    ["3", "`bash scripts/lab_run.sh env`", "Record the lab environment"],
    ["4", "`bash scripts/lab_run.sh data` / `train`", "Generate the dataset and fine-tune DistilBERT (Part II)"],
    ["5", "`bash scripts/lab_run.sh index`", "Download the PJM manuals and build the FAISS index (Part III)"],
    ["6", "`bash scripts/lab_run.sh eval`", "Evaluation used in Part IV"],
    ["7", "`bash scripts/lab_run.sh serve` / `curl`", "Start the API and UI; call the REST endpoints"],
  ], [700, 4626, 3700]),
  ...labFigure("L1_env.png", "Lab environment: user, host, CPU, memory, Python and PyTorch versions"),
  ...labFigure("L2_data.png", "Synthetic ticket dataset generated in the lab"),
  ...labFigure("L3_train.png", "Fine-tuning run in the lab: baseline versus fine-tuned accuracy and classification report"),
  ...labFigure("L4_index.png", "RAG index built in the lab from the PJM manuals"),
  ...labFigure("L5_eval.png", "Evaluation run in the lab: retrieval hit@k, extraction scores and latency"),
  pageBreak(),

  // ---------- Part I ----------
  h1("I. API-based AI Application (4 marks)"),
  h2("1. Domain and real-world problem"),
  p("Wholesale electricity markets are run by Independent System Operators / Regional Transmission Organisations (ISOs/RTOs) such as PJM. Hundreds of market participants — generators, utilities, traders, storage and demand-response providers — raise support tickets every day about settlements, meter data, day-ahead and real-time offers, invoices, credit and collateral, capacity obligations, system access and outages. Each ticket must be routed to the right team, read (often as a long email thread), and answered by referring to hundreds of pages of market manuals. Today this is manual and slow, and answer quality depends on the individual analyst's familiarity with the rules."),
  p("**Unified objective:** reduce the time an analyst needs to route, understand and research a participant ticket, and give them a cited first-draft reply."),
  h2("2–3. Category and sub-tasks"),
  p("Category: **Natural Language Processing**. Four NLP sub-tasks are combined into one triage workflow:"),
  ...table(["#", "Sub-task", "Role in the workflow", "Model"], [
    ["1", "Text classification", "Routes the ticket to one of 8 queues (settlement disputes, meter data, offers, billing, credit, capacity, system access, outages)", "`distilbert-base-uncased` **fine-tuned** (Part II)"],
    ["2", "Abstractive summarisation", "Condenses long email threads into 2–3 sentences for the analyst", "`sshleifer/distilbart-cnn-12-6`"],
    ["3", "Named-entity & field extraction", "Pulls out participant, people, dates, hour-ending, $ amounts, MW/MWh, invoice/ticket IDs, pricing nodes", "`dslim/bert-base-NER` + market-specific rules"],
    ["4", "Retrieval-augmented QA", "Finds the governing manual sections and answers questions / drafts the reply with citations", "`all-MiniLM-L6-v2` + FAISS → `Qwen2.5-1.5B-Instruct`"],
  ], [500, 2000, 4026, 2500]),
  h2("4. Model selection rationale"),
  bullet("**Small Language Models (SLMs) for the deterministic tasks.** DistilBERT (66M params), DistilBART (306M) and BERT-NER (108M) run on a laptop CPU in milliseconds to a few seconds, which matters for a help desk that processes every incoming ticket."),
  bullet("**Fine-tuning instead of zero-shot for routing.** Queue names are organisation-specific, so a model trained on labelled tickets beats generic zero-shot classification and a TF-IDF baseline (Part II)."),
  bullet("**Small instruction-tuned LLM for generation.** `Qwen2.5-1.5B-Instruct` runs fully offline on CPU, so confidential ticket text never leaves the machine."),
  bullet("**Compact embedding model for retrieval.** MiniLM-L6 (384-dimensional vectors) indexes about 2,600 manual chunks in under two minutes on CPU; retrieval takes about 20 ms per query."),
  h2("5. Cohesive design"),
  p("All sub-tasks are chained by the `POST /triage` endpoint: **classify → summarise → extract → retrieve → generate**. The predicted category and the summary form the retrieval query, the extracted fields are passed to the generator, and the generator writes a draft reply that cites the retrieved manual pages. Each sub-task is also exposed as its own endpoint so it can be reused by other systems (e.g. a ticketing tool that only needs routing)."),
  ...table(["Endpoint", "Method", "Purpose"], [
    ["`/health`", "GET", "Service status and active LLM backend"],
    ["`/classify`", "POST", "Ticket category, target queue, confidence, top-3 scores"],
    ["`/summarize`", "POST", "Abstractive summary of a ticket thread"],
    ["`/extract`", "POST", "Named entities and market fields"],
    ["`/rag/ask`", "POST", "Chatbot answer with cited manual passages (supports chat history)"],
    ["`/triage`", "POST", "End-to-end workflow combining all of the above"],
  ], [1800, 1000, 6226]),
  h2("6–7. Application and demonstration"),
  p("The application has two layers: a **FastAPI** REST service (`app/api.py`) with OpenAPI/Swagger documentation and request validation, and a **Streamlit** web interface (`app/ui.py`) that calls the API over HTTP. Run `uvicorn app.api:app --port 8000` and `streamlit run app/ui.py`."),
  ...figure(shotPath("01_api_docs.png"), "FastAPI service — auto-generated OpenAPI documentation of all endpoints", 560),
  ...figure(shotPath("02_api_calls.png"), "Calling the REST API directly — HTTP 200 responses for /health, /classify, /extract and HTTP 422 validation error for an empty ticket", 560),
  ...figure(shotPath("03_ui_triage.png"), "End-to-end triage of a settlement-dispute thread — category, queue, summary, extracted fields, draft reply and the manual pages used"),
  ...figure(shotPath("04_ui_classify.png"), "Sub-task 1 — classification with the fine-tuned DistilBERT model (top-3 probabilities)"),
  ...figure(shotPath("05_ui_summarise.png"), "Sub-task 2 — summarising a meter-correction email thread"),
  ...figure(shotPath("06_ui_extract.png"), "Sub-task 3 — market fields (rules) and named entities (BERT-NER)"),

  // ---------- Part II ----------
  pageBreak(),
  h1("II. Fine-Tuning (2 marks)"),
  h2("Dataset"),
  p("Real participant tickets are confidential, so we built a **synthetic, anonymised dataset** that mirrors an ISO help desk (`data/generate_tickets.py`). It covers 8 categories with 8 templates each, plus randomised participants, pricing nodes, units, dates, hour-endings, $ amounts, MW/MWh values, invoice IDs, greetings and sign-offs."),
  bullet(`**Train / validation:** ${metrics.n_train} / ${metrics.n_val} tickets from 6 templates per category.`),
  bullet(`**Test:** ${metrics.n_test} tickets from the **2 held-out templates per category** that the model never saw. This measures generalisation to new phrasings rather than memorisation.`),
  h2("Training setup"),
  ...table(["Setting", "Value"], [
    ["Base model", "`distilbert-base-uncased` (66M parameters) + new 8-way classification head"],
    ["Method", "Full fine-tuning with Hugging Face `Trainer`, cross-entropy loss"],
    ["Hyper-parameters", "3 epochs · batch 16 · learning rate 5e-5 · weight decay 0.01 · 10% warm-up · max length 128"],
    ["Model selection", "Best macro-F1 on the validation set (`load_best_model_at_end`)"],
    ["Hardware / time", "12-core laptop CPU, no GPU · about 11 minutes"],
    ["Script", "`training/finetune_classifier.py` → `models/ticket-classifier/`"],
  ], [2400, 6626]),
  h2("Results"),
  ...table(["Model (test set — unseen templates)", "Accuracy", "Macro-F1"], [
    ["Baseline: TF-IDF (1–2-grams) + logistic regression", pct(base.accuracy), pct(base.macro_f1)],
    ["**Fine-tuned DistilBERT**", `**${pct(ft.accuracy)}**`, `**${pct(ft.macro_f1)}**`],
  ], [5626, 1700, 1700]),
  p(`Fine-tuning improves accuracy by **${((ft.accuracy - base.accuracy) * 100).toFixed(1)} percentage points** over the baseline, because contextual embeddings generalise to unseen wording (e.g. "my login is locked" vs "token and role assignment") where n-gram overlap fails. Validation accuracy reached 100% from epoch 1, because validation tickets share templates with training; this is why the held-out-template test set is the honest measure.`),
  ...table(["Class", "Precision", "Recall", "F1"], perClass, [3626, 1800, 1800, 1800]),
  p("The weakest class is `capacity_market`: its two held-out templates (a non-performance charge dispute and a must-offer exception for a deactivating unit) share vocabulary with settlement disputes and outages, and were misrouted. This is the kind of gap that real, diverse labelled tickets would close (see Part IV)."),
  ...figure(`${REPORTS}/confusion_matrix.png`, "Confusion matrix of the fine-tuned classifier on the held-out test set", 500),

  // ---------- Part III ----------
  pageBreak(),
  h1("III. RAG Model (4 marks)"),
  h2("Knowledge base"),
  p("We used the public **PJM market manuals** — the same rulebooks a market-operations analyst consults when answering a participant:"),
  ...table(["Manual", "Topic"], [
    ["Manual 11", "Energy & Ancillary Services Market Operations (offers, day-ahead / real-time markets, virtual bids)"],
    ["Manual 18", "PJM Capacity Market (RPM auctions, capacity performance, non-performance charges)"],
    ["Manual 28", "Operating Agreement Accounting (settlement calculations, operating reserves, meter corrections)"],
    ["Manual 29", "Billing (invoices, payment, billing disputes)"],
  ], [2000, 7026]),
  h2("Pipeline"),
  bullet("**Ingestion** (`rag/build_index.py`): download PDFs → extract text per page with `pypdf` → normalise whitespace → split into 1,000-character chunks with 200-character overlap, keeping manual name and page number as metadata. Result: **2,589 chunks**."),
  bullet("**Embedding & index:** `all-MiniLM-L6-v2` sentence embeddings (normalised) stored in a FAISS `IndexFlatIP` (cosine similarity)."),
  bullet("**Retrieval:** top-k (default 4) passages for the question."),
  bullet("**Generation:** the passages are numbered and inserted into the prompt with an instruction to answer only from the context, cite passages, and say so when the answer is not present. The last two chat turns are included so follow-up questions work."),
  bullet("**Chatbot interface:** Streamlit chat tab with conversation history and an expandable list of sources (manual, page, similarity score) under each answer."),
  ...figure(shotPath("07_ui_rag_chat.png"), "RAG chatbot answering questions from the PJM manuals, with the retrieved sources shown"),
  h2("Retrieval quality"),
  p(`On ${ret.n} hand-written analyst questions with a known governing manual, the correct manual was the top passage for **${pct(ret["hit@1"])}** of questions (hit@1) and appeared in the top 4 for **${pct(ret["hit@4"])}** (hit@4).`),
  ...table(["Question", "Expected", "Top-4 retrieved (manual, page)"],
    ret.detail.map((d) => [d.question, d.expected.join(", "), d.retrieved.join(", ")]), [4426, 1100, 3500]),
  h2("Sample chatbot answers (local Qwen2.5-1.5B generator)"),
  ...table(["Question", "Answer (truncated)", "Top sources"], ragRows, [2400, 4826, 1800]),

  // ---------- Part IV ----------
  pageBreak(),
  h1("IV. Situated Learning – Workplace Application (5 marks)"),
  p("**Individual section — C V R Karthik (2025ae05851).** Other group members replace this section with their own workplace application."),
  h2("1. Anchor – Workplace problem"),
  p("**Organisational context.** I work as a Staff Software Engineer in **Electric Market Systems at GE Vernova**, as an Oracle database designer and developer. The group builds the software that ISOs/RTOs use to run wholesale electricity markets: bidding, market clearing, settlements and billing."),
  p("**Current workflow.** When an ISO customer's market-operations or settlements team sees a result they believe is wrong (for example, a missing operating reserve credit, a meter correction that did not flow into reconciliation, or an invoice line item that cannot be traced), they raise an issue. Engineers then: (1) read a long email or ticket thread, (2) decide which component and team owns it (settlements, meter data, market clearing, billing, credit, capacity, access), (3) collect identifiers such as operating day, interval, pricing node, unit and amount in order to query the database, and (4) look up the governing market rule in the customer's tariff and manuals to decide whether the system behaviour is a defect or follows the rules."),
  p("**Limitations.** Steps 1–4 are manual and depend on individual knowledge of hundreds of pages of market rules. Tickets are often misrouted at first, identifiers are re-typed by hand into SQL, and research into the rules is repeated for similar issues. Junior engineers need a long time to become productive."),
  p("**Expected benefit.** Automatic routing, a short summary, auto-extracted query parameters and a cited pointer to the relevant rule cut the time from ticket arrival to root-cause investigation, make answers more consistent, and help new team members ramp up."),
  p("**Workplace artefact used.** Customer tickets and the product's internal documentation are confidential, so I used a close analogue: **synthetic, anonymised tickets** with the same structure, and the **public PJM manuals** as the market-rules knowledge base. These are the same kind of rules our ISO customers' tariffs encode."),
  h2("2. Apply – Adapting the solution to the workplace"),
  ...table(["Workplace need", "Data source / system", "Copilot component"], [
    ["Route the issue to the owning team", "Ticketing system (e.g. ServiceNow / Jira) — ticket text", "Fine-tuned DistilBERT classifier → queue"],
    ["Understand a long customer thread quickly", "Email / ticket thread", "DistilBART summariser"],
    ["Turn the ticket into database query parameters", "Ticket text → Oracle settlement and meter tables (operating day, HE interval, pnode, unit, invoice)", "BERT-NER + market field rules → structured JSON"],
    ["Find the governing rule", "ISO tariff / business practice manuals; product design documents", "FAISS retriever + LLM with citations"],
    ["Respond to the customer", "Ticket reply", "Draft reply for engineer review"],
  ], [2600, 3426, 3000]),
  p("**Representative input → output.** For the settlement-dispute thread below, the copilot produced the following (full screenshot in Figure 3):"),
  quote("Input (excerpt): \"We are formally disputing the balancing operating reserve credit for our Westfall combustion turbine (Unit 2) for operating day 2026-08-14. The unit was dispatched … from HE15 to HE19 … the operating reserve credit on the settlement statement is zero. Our shadow settlement calculates a credit of approximately $48,350.00 … WESTFALL 230KV GEN1 … invoice INV-604118 …\""),
  ...table(["Output", "Value"], [
    ["Category / queue", `${triage.classification.label} → ${triage.classification.queue} (confidence ${pct(triage.classification.confidence)})`],
    ["Summary", triage.summary.summary],
    ["Extracted query parameters", Object.entries(triage.extraction.fields).map(([k, v]) => `${k}: ${v.join(", ")}`).join(" · ")],
    ["Rules retrieved", triage.sources.map((s) => `${s.source}, p.${s.page}`).join("; ")],
    ["Draft reply (excerpt)", triage.draft_reply.replace(/\s+/g, " ").slice(0, 420) + " …"],
  ], [2400, 6626]),
  p("The extracted fields map directly to the WHERE clause an engineer would write against the settlement tables (operating day = 2026-08-14, hours 15–19, pnode = WESTFALL 230KV GEN1, invoice INV-604118). The next integration step would be a read-only SQL tool that pulls the matching settlement determinants automatically."),
  h2("3. Analyse – Evaluation against workplace needs"),
  ...table(["Need", "Measure", "Result", "Assessment"], [
    ["Correct routing", "Accuracy on unseen phrasings", `${pct(ft.accuracy)} (baseline ${pct(base.accuracy)})`, "Useful as a suggestion; not reliable enough for automatic assignment — capacity tickets misrouted"],
    ["Finding the right rule", "Retrieval hit@1 / hit@4 (12 questions)", `${pct(ret["hit@1"])} / ${pct(ret["hit@4"])}`, "Strong — the right manual is almost always retrieved"],
    ["Accurate query parameters", "Field recall / precision (2 threads)", `${pct(evalr.extraction.THREAD_SETTLEMENT.recall)} / ${pct(evalr.extraction.THREAD_SETTLEMENT.precision)}`, "Strong for well-formatted identifiers; NER splits some names (\"J\", \". Patel\")"],
    ["Answer quality", "Manual review of 5 RAG answers", "Mostly grounded, but no inline citations and some unsupported statements", "Weakest link — must be verified by an engineer"],
    ["Efficiency", "Median latency on CPU", `classify ${lat.classify.median} ms · extract ${lat.extract.median} ms · retrieve ${lat.retrieve.median} ms · summarise ${sec(lat.summarize.median)} · RAG answer ${sec(lat.rag_answer.median)} · full triage ${sec(lat.triage_end_to_end.median)}`, "Fast except generation, which is CPU-bound"],
    ["Scalability", "Architecture", "Stateless FastAPI; models loaded once per process", "Scales horizontally behind a load balancer; generation needs GPU or a managed LLM"],
  ], [1600, 2100, 2600, 2726]),
  p("**Gap between the prototype and what the organisation needs:**"),
  bullet("**Data:** trained on synthetic tickets; production needs thousands of real, labelled historical tickets, the customer-specific category taxonomy, and periodic retraining. The held-out-template result (75.8%) shows that phrasing outside the training distribution hurts routing."),
  bullet("**Knowledge base:** public PJM manuals stand in for each customer's own tariff, business practice manuals, product design documents and past resolved tickets. These need versioning, because rules change, and per-customer access control."),
  bullet("**Answer reliability:** the 1.5B CPU model ignores the citation instruction and sometimes invents details (in the draft reply it named a \"Reserves Team\" that does not exist). A production system needs enforced citations, abstention and human approval."),
  bullet("**Integration:** the prototype is stand-alone. Production needs connectors to the ticketing system, SSO, audit logging, and read-only database access for the extracted parameters."),
  bullet("**Operations:** monitoring of drift, latency and accuracy; an evaluation set that is rerun on every model or index change."),
  h2("4. Reflect – Deployment constraints and the most important improvement"),
  ...table(["Constraint", "Implication for deployment"], [
    ["Data privacy & confidentiality", "Ticket text contains customer financial positions and market-sensitive data; it must not go to an unapproved external service. Use self-hosted models or an LLM endpoint inside the company's cloud tenancy with no data retention."],
    ["Security", "SSO/RBAC per customer (one ISO must never see another's data), encryption in transit and at rest, prompt-injection filtering on ticket text, audit trail of every generated answer."],
    ["Regulation & compliance", "Market rules are FERC-regulated tariffs; customer-facing statements about settlements must be accurate and traceable. Requires a human in the loop and NERC CIP-aware handling if any operational data is touched."],
    ["Infrastructure & cost", "Classification, extraction and retrieval run cheaply on CPU. Generation needs a GPU or a pay-per-token managed LLM. At about 100 tickets/day a managed API costs little compared with engineer hours."],
    ["Integration", "ServiceNow/Jira webhooks for incoming tickets, Oracle read-only views for settlement determinants, document management system for manuals, and a feedback loop where engineers correct the predicted category."],
  ], [2400, 6626]),
  p("**Single most important improvement: grounded, verifiable answer generation.** Replace the CPU-hosted 1.5B generator with an enterprise-approved LLM running inside the company's own cloud environment (for example Claude through Amazon Bedrock or a private endpoint), and enforce citations: every sentence of a reply must cite a retrieved passage, uncited sentences are removed or flagged, and the model must answer \"not found in the rules\" when retrieval confidence is low."),
  p("**Justification.** The evaluation shows that retrieval (hit@4 = 100%) and field extraction (100% recall) are already good enough, and routing errors are cheap because an engineer simply re-assigns the ticket. The generated answer is the only component that (a) failed to cite its sources, (b) introduced unsupported statements, and (c) dominates latency (about 33 seconds per answer). It is also the output that reaches customers, so in a regulated market an incorrect statement about settlement rules carries financial and compliance risk. Fixing generation removes the biggest risk and the biggest latency cost in one step."),

  // ---------- Contribution ----------
  pageBreak(),
  h1("Contribution of Each Group Member"),
  ...table(["Member (Name / BITS ID)", "Activities owned", "Key files / artefacts", "Contribution"], [
    ["Chodavarapu Venkata Hemalatha / 2025ae05338", "<fill in>", "<fill in>", "<x>%"],
    ["Siva Ganesh K / 2025ae05356", "<fill in>", "<fill in>", "<x>%"],
    ["C V R Karthik / 2025ae05851", "<fill in>", "<fill in>", "<x>%"],
  ], [2600, 2600, 2726, 1100]),

  h1("Appendix — How to Reproduce"),
  bullet("Install: `pip install -r requirements.txt`"),
  bullet("Dataset: `python data/generate_tickets.py`"),
  bullet("Fine-tune: `python training/finetune_classifier.py --epochs 3`"),
  bullet("RAG index: `python rag/build_index.py`"),
  bullet("Run API: `uvicorn app.api:app --port 8000`; run UI: `streamlit run app/ui.py`"),
  bullet("Evaluation: `python scripts/evaluate.py` → `reports/evaluation.json`"),
];

const doc = new Document({
  creator: "AIMLZG549 Group 31",
  title: "AIMLZG549 Assignment II — Market Operations Ticket Copilot",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: ACCENT, font: FONT },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: "2E75B6", font: FONT },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "AIMLZG549 Assignment II — Group 31 — Page ", size: 18, color: "808080" }),
                 new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT, buf.length, "bytes"); });
