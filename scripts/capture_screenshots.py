"""Capture report screenshots of the running app (API on :8000, Streamlit on :8501).

Usage:  python scripts/capture_screenshots.py      (needs `playwright` + installed Chrome)
Output: docs/screenshots/*.png
"""
import html
import json
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

API, UI = "http://localhost:8000", "http://localhost:8501"
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
LONG = 900_000  # LLM generation on CPU can take minutes


def post(path, body):
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return r.status, json.loads(r.read())


def terminal(page, name, blocks):
    body = "".join(
        f'<div class="cmd">$ {html.escape(cmd)}</div><pre>{html.escape(out)}</pre>' for cmd, out in blocks)
    page.set_content(
        "<html><body style='margin:0;background:#1e1e1e;color:#d4d4d4;font:13px Consolas,monospace;padding:18px'>"
        "<style>.cmd{color:#4ec9b0;margin-top:10px}pre{margin:4px 0 0;white-space:pre-wrap}</style>"
        f"{body}</body></html>")
    page.screenshot(path=OUT / name, full_page=True)
    print("saved", name)


def shot(page, name):
    """Streamlit scrolls inside its own container, so grow the viewport to the content height."""
    h = page.evaluate("document.querySelector('[data-testid=stMainBlockContainer]').scrollHeight")
    page.set_viewport_size({"width": 1440, "height": max(1000, h + 120)})
    page.wait_for_timeout(1200)
    page.screenshot(path=OUT / name, full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1000})
    print("saved", name)


def tab(page, label):
    page.get_by_role("tab", name=label).click()
    page.wait_for_timeout(800)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        # 1. API docs
        page.goto(f"{API}/docs")
        page.wait_for_selector("text=Market Ops Ticket Copilot API")
        page.wait_for_timeout(1500)
        page.screenshot(path=OUT / "01_api_docs.png", full_page=True)
        print("saved 01_api_docs.png")

        # 2. raw API calls with HTTP status codes
        t = "Invoice INV-551902 for September shows administrative charges 18% higher than August; please provide a breakdown."
        blocks = []
        with urllib.request.urlopen(f"{API}/health") as r:
            blocks.append((f"curl {API}/health", f"HTTP {r.status}\n" + json.dumps(json.loads(r.read()), indent=2)))
        for path in ["/classify", "/extract"]:
            s, body = post(path, {"text": t})
            blocks.append((f"curl -X POST {API}{path} -d '{{\"text\": \"{t[:60]}...\"}}'",
                           f"HTTP {s}\n" + json.dumps(body, indent=2)))
        try:
            post("/classify", {"text": ""})
        except urllib.error.HTTPError as e:
            blocks.append((f"curl -X POST {API}/classify -d '{{\"text\": \"\"}}'",
                           f"HTTP {e.code}\n" + json.dumps(json.loads(e.read()), indent=2)[:600]))
        terminal(page, "02_api_calls.png", blocks)

        # 3-7. Streamlit UI
        page.goto(UI)
        page.wait_for_selector("text=Market Operations Ticket Copilot", timeout=120_000)
        page.wait_for_timeout(2500)

        page.get_by_role("button", name="Run triage").click()
        page.wait_for_selector("text=Draft reply", timeout=LONG)
        page.wait_for_timeout(1500)
        shot(page, "03_ui_triage.png")

        tab(page, "🏷️ Classify")
        page.get_by_role("button", name="Classify", exact=True).click()
        page.wait_for_selector("text=confidence", timeout=120_000)
        page.wait_for_timeout(1500)
        shot(page, "04_ui_classify.png")

        tab(page, "📝 Summarise")
        page.get_by_role("button", name="Summarise", exact=True).click()
        page.wait_for_selector("text=words in", timeout=300_000)
        page.wait_for_timeout(1000)
        shot(page, "05_ui_summarise.png")

        tab(page, "🔎 Extract")
        page.get_by_role("button", name="Extract", exact=True).click()
        page.wait_for_selector("text=Named entities", timeout=120_000)
        page.wait_for_timeout(1500)
        shot(page, "06_ui_extract.png")

        tab(page, "💬 Manuals chatbot (RAG)")
        for q in ["What is the deadline for submitting a billing dispute?",
                  "How is balancing operating reserve credit calculated for a generator dispatched in real time?"]:
            n = page.locator("[data-testid='stChatMessage']").count()
            box = page.get_by_placeholder("Ask about settlements")
            box.fill(q)
            box.press("Enter")
            page.wait_for_function(
                f"document.querySelectorAll('[data-testid=\"stChatMessage\"]').length >= {n + 2} && "
                "!document.body.innerText.includes('Retrieving and generating')", timeout=LONG)
            page.wait_for_timeout(1500)
        page.locator("[data-testid='stExpander']").last.click()
        page.wait_for_timeout(1000)
        shot(page, "07_ui_rag_chat.png")
        browser.close()


if __name__ == "__main__":
    main()
