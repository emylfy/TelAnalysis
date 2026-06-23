#!/usr/bin/env python3
"""Regenerate the README screenshots in ``docs/screenshots/``.

Drives the built single-page app with Playwright against a running (or
auto-started) server, loading the two bundled demo exports. Each shot seeds
``localStorage["tla.path"]`` — the key the app reads for the export path (see
``frontend/src/App.tsx``) — and opens ``?tab=<id>&lang=en`` so the onboarding
screen is skipped and the dashboard renders straight away.

Usage
-----
    python tools/screenshots.py                 # regenerate all 5
    python tools/screenshots.py --only group-02-network personal-01-sentiment
    python tools/screenshots.py --base-url http://127.0.0.1:9000
    python tools/screenshots.py --headed        # watch it run

Requirements (dev-only — intentionally not in requirements.txt)
---------------------------------------------------------------
    pip install playwright
    python -m playwright install chromium

The server must serve a built frontend (``frontend/dist`` — run ``./run.sh`` or
``./run.sh --rebuild`` once). If ``--base-url`` is unreachable, this script
starts ``uvicorn api.main:app`` itself and shuts it down on exit.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "screenshots"
GROUP = ROOT / "demo" / "group_demo.json"
PERSONAL = ROOT / "demo" / "personal_demo.json"

# Logical viewport; doubled on disk via device_scale_factor for crisp output.
VIEWPORT = {"width": 1380, "height": 900}
SCALE = 2

# One entry per README image. `kind`:
#   "viewport"  — capture the visible viewport from the top of the page.
#   "sentiment" — element-shot of the Sentiment section (the "relationship arc").
TARGETS = [
    {"name": "group-01-overview", "demo": GROUP, "tab": "overview", "kind": "viewport", "settle": 1800},
    {"name": "group-02-network", "demo": GROUP, "tab": "network", "kind": "viewport", "settle": 3800},
    {"name": "group-03-words", "demo": GROUP, "tab": "words", "kind": "viewport", "settle": 1600, "wordcloud": True},
    {"name": "group-04-per-user", "demo": GROUP, "tab": "peruser", "kind": "viewport", "settle": 2200},
    {"name": "personal-01-sentiment", "demo": PERSONAL, "tab": "words", "kind": "sentiment", "settle": 1500},
]


def _server_up(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/api/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _start_server(base_url: str) -> subprocess.Popen:
    if not (ROOT / "frontend" / "dist" / "index.html").is_file():
        sys.exit("frontend/dist not built — run `./run.sh --rebuild` first, then re-run.")
    parsed = urlparse(base_url)
    host, port = parsed.hostname or "127.0.0.1", parsed.port or 8000
    print(f"==> starting uvicorn on {host}:{port} …")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", host, "--port", str(port)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        if _server_up(base_url):
            return proc
        if proc.poll() is not None:
            sys.exit("uvicorn exited before becoming healthy.")
        time.sleep(0.5)
    proc.terminate()
    sys.exit("server did not become healthy within 30s.")


def _capture(browser, base_url: str, tgt: dict) -> Path | None:
    ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=SCALE)
    # Seed the export path *before* app JS runs, so onboarding is skipped.
    ctx.add_init_script(f"window.localStorage.setItem('tla.path', {json.dumps(str(tgt['demo']))})")
    page = ctx.new_page()
    out = OUT_DIR / f"{tgt['name']}.png"
    try:
        page.goto(f"{base_url.rstrip('/')}/?tab={tgt['tab']}&lang=en", wait_until="domcontentloaded", timeout=60_000)
        # Hero card renders an <h1> only once chat metadata + KPIs have loaded.
        page.wait_for_selector("main h1", timeout=90_000)

        if tgt["kind"] == "sentiment":
            # Either the real block (an <h2> "Sentiment") or the "install
            # requirements-sentiment" off-card appears. The model loads lazily and
            # scores ~18k messages on CPU on first call, so the heading can take a
            # while; the off-card shows immediately. Wait for whichever comes.
            page.wait_for_selector(
                "main h2:has-text('Sentiment'), main pre:has-text('requirements-sentiment')",
                timeout=300_000,
            )
            if page.locator("main pre:has-text('requirements-sentiment')").count():
                print("    skipped — sentiment model not installed "
                      "(pip install -r requirements-sentiment.txt)")
                return None
            # The sticky top bar (position: sticky) otherwise composites itself
            # into the middle of a tall stitched element screenshot as Playwright
            # scrolls. Drop it to normal flow for the shot — no layout reflow,
            # since sticky already reserves its space.
            page.add_style_tag(content="header { position: static !important; }")
            section = page.get_by_role("heading", name="Sentiment", exact=True).locator("xpath=ancestor::section[1]")
            section.scroll_into_view_if_needed()
            page.wait_for_timeout(tgt["settle"])
            section.screenshot(path=str(out))
        else:
            if tgt.get("wordcloud"):
                page.wait_for_function(
                    "() => { const i = document.querySelector('img[src*=\"/api/wordcloud\"]');"
                    " return i && i.complete && i.naturalWidth > 0; }",
                    timeout=90_000,
                )
            # ECharts renders to <canvas>; wait for the first chart of the tab.
            page.wait_for_selector("main canvas", timeout=90_000)
            page.wait_for_timeout(tgt["settle"])
            page.evaluate("() => window.scrollTo(0, 0)")
            page.screenshot(path=str(out), full_page=False)
    finally:
        ctx.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenerate docs/screenshots/*.png")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--only", nargs="*", metavar="NAME", help="subset of shot names")
    ap.add_argument("--headed", action="store_true", help="run a visible browser")
    args = ap.parse_args()

    for demo in (GROUP, PERSONAL):
        if not demo.is_file():
            sys.exit(f"missing {demo.relative_to(ROOT)} — run `python tools/gen_demo_data.py` first.")

    targets = TARGETS
    if args.only:
        wanted = set(args.only)
        targets = [t for t in TARGETS if t["name"] in wanted]
        if not targets:
            sys.exit(f"--only matched nothing; valid names: {', '.join(t['name'] for t in TARGETS)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    proc = None
    if not _server_up(args.base_url):
        proc = _start_server(args.base_url)
    else:
        print(f"==> using server at {args.base_url}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed — run: pip install playwright && python -m playwright install chromium")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not args.headed)
            for tgt in targets:
                print(f"--> {tgt['name']} ({tgt['tab']}) …")
                out = _capture(browser, args.base_url, tgt)
                if out is not None:
                    print(f"    wrote {out.relative_to(ROOT)}")
            browser.close()
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    print("done.")


if __name__ == "__main__":
    main()
