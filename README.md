<div align="right">

**English** · [Русский](README.ru.md)

</div>

# TelAnalysis

[![CI](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml/badge.svg)](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml)
![Python 3.11–3.14](https://img.shields.io/badge/python-3.11--3.14-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Built with React + FastAPI](https://img.shields.io/badge/built%20with-React%20%2B%20FastAPI-61DAFB.svg)

> Drop in a Telegram chat export and explore it as an interactive dashboard: activity heatmaps, a reply-network graph, word clouds, per-user breakdowns, and optional sentiment. Runs locally in your browser — no upload, no account.

<p align="center">
  <img src="docs/screenshots/group-01-overview.png" alt="Overview tab — KPIs, hero, daily timeline, peak hours" width="900">
</p>

## What it does

Reads a Telegram Desktop export (single chat or full archive) and renders an interactive dashboard. The tabs adapt to the chat type: channels get broadcast stats, groups get the network graph and per-user breakdown, 1-on-1 chats get paired analytics.

> **JSON is recommended** — in the export dialog switch the format from the default *HTML* to *Machine-readable JSON*. **HTML exports also work** (drop in the export folder or `messages.html`), but they're lossier: Telegram's HTML has no participant IDs, so the Network and Per-User tabs are less accurate for groups (the app warns on load). Either way, exporting is a Telegram Desktop feature — mobile and the native macOS client can't export chat history.

Both export shapes are supported:
- **Single chat** — `Settings → Export Chat History`
- **Full archive** — `Settings → Advanced → Export Telegram Data` → a chat picker appears once the export is loaded, plus a [chat manager](#manage-the-archive-reclaim-disk-space) for pruning the export down to size

UI ships in **EN / RU** (toggle in the header). Chat content is left untouched — wordclouds and message previews show whatever language the messages are in.

## Highlights

A few things you won't find in a plain message counter:

- **Who answers whom faster** — for 1-on-1 chats, reply stats *per direction*: median and 90th-percentile response time, plus the share answered within 5 / 30 / 60 minutes.
- **How long you actually talked** — messages are grouped into conversation sessions, so you get real wall-clock time spent talking, not just a message count.
- **Who opens and who closes** — per-person share of conversations started, and of having the last word before a silence.
- **A reply network with auto-detected communities** — for groups: Louvain clusters plus a "chat portrait" that calls out hubs, bridges, and reply-magnets.
- **Favourite stickers as actual images** — recovered from the export and shown as pictures, not just emoji tags.
- **The words that give you away** — log-odds distinctive words that set each person apart in a 1-on-1.
- **Anniversary milestones** — 100 / 365 / 1000 days, 10k / 100k messages: when each was crossed and which one is next.
- **A Russian-mat leaderboard** — hits per 100 messages with morphological root matching (a community favourite; English-only chats just won't trigger it).

## Features

The Overview opens with a **"Wrapped"-style recap**: a short summary, an activity sparkline, headline numbers (messages, participants, days active, media, voice time), anniversary milestones, and highlight cards (peak hour, busiest day, top emoji, longest streak).

| Tab | What you get |
| --- | --- |
| **Overview** | Daily-activity chart and a multi-year calendar heatmap, an hour×weekday heatmap with peak-hour and night-owl callouts, and an hour-overlap chart for 1-on-1s. Conversation sessions, media and voice breakdown, top link domains and emojis, reply latency (question→answer), and longest monologues. |
| **Network** | An interactive force-directed graph (drag, zoom, hover) where edges track reply count and direction and node colour is the Louvain community, plus a "chat portrait" of hubs, bridges and magnets, a per-user role table, and reply-chain depth. Small chats fall back to a bar chart; nodes and edges export to CSV for Gephi. |
| **Words** | Wordcloud (whole chat or per user), a top-words chart and table, common phrases (bigrams and trigrams), per-participant vocabulary richness (MTLD), and extracted emails and phone numbers. |
| **Channel** | Wordcloud and word-frequency analysis for broadcast channels. |
| **Per-user** | A page per participant — persona card, headline tiles (messages, last-word share, words per message, question share, reply speed), a tone radar, timelines and heatmaps, and a lot more (full list below). |

<details>
<summary>Everything on a per-user page</summary>

- Persona card with trait chips (night owl / early bird, terse / verbose, initiator / responder, fast / slow)
- Headline tiles: messages, last-word share, words per message, question share, reply share
- Tone radar vs. the chat average (questions, exclamations, CAPS, replies)
- Daily timeline and an hour×weekday heatmap
- Time-of-day and message-length distributions
- Reply speed and reciprocity (directional in 1-on-1s)
- Activity streaks and longest silences
- How often they start conversations, and their forwards share
- Characteristic phrases; top words, emojis, and stickers
- Log-odds distinctive words (what sets them apart in a 1-on-1)
- Russian-mat leaderboard (`hits / 100 msgs`)
</details>

Optional **sentiment analysis** (`rubert-tiny2-russian-sentiment`, Russian/English — [a separate install](#optional-sentiment-analysis)) adds a sentiment-over-time arc, per-participant tone lines, an hour/weekday breakdown, and the most positive and negative messages, on the **Words** and **Per-user** tabs.

<p align="center"><b>Network</b> — a force-directed reply graph with auto-detected communities</p>

<p align="center">
  <img src="docs/screenshots/group-02-network.png" alt="Network tab — force-directed graph with communities" width="900">
</p>

<p align="center"><b>Words</b> — wordcloud, top words and common phrases</p>

<p align="center">
  <img src="docs/screenshots/group-03-words.png" alt="Words tab — wordcloud and top phrases" width="900">
</p>

<p align="center"><b>Per-user</b> — a page per participant: persona, tone radar, timelines</p>

<p align="center">
  <img src="docs/screenshots/group-04-per-user.png" alt="Per-User tab — speaking style radar and timeline" width="900">
</p>

<p align="center"><b>Sentiment</b> — the relationship arc over time (optional model)</p>

<p align="center">
  <img src="docs/screenshots/personal-01-sentiment.png" alt="Sentiment over time — relationship arc in a 1-on-1 chat" width="900">
</p>

## Manage the archive (reclaim disk space)

A full Telegram archive can be tens of gigabytes of media you'll never open. For writable JSON full archives, a **Manage chats** button ranks every chat by disk size (with a media breakdown) and lets you delete or *slim* them — dropping heavy media while keeping the text. Deletions move to a reversible `.telanalysis_trash/` and aren't freed until you **Empty trash**. Edits happen in place, so point it at a copy to keep the original untouched.

## Privacy

Everything runs on your machine — no account, no upload, no telemetry. The only thing that touches the network is a one-time download on first run: NLTK's `stopwords` + `punkt_tab` corpora (~10 MB), plus the sentiment model **only if** you opted into it (see [Optional: sentiment analysis](#optional-sentiment-analysis)). After that it works fully offline.

## Install

Requires **Python 3.11+**. Tested in CI on 3.11, 3.12, 3.13 and 3.14. The frontend build needs **Node.js 20+** (one-time, see [Run](#run)).

The core install is the same on every OS:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Per-platform notes (system packages, Apple Silicon, Windows PowerShell):

<details>
<summary><b>macOS</b></summary>

```bash
# 1. Python 3.11+ via Homebrew (if not already installed)
brew install python@3.12

# 2. venv + dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Apple Silicon (M1/M2/M3) works out of the box — `torch`, `wordcloud` and friends all ship arm64 wheels, nothing to compile.
</details>

<details>
<summary><b>Linux (Ubuntu / Debian)</b></summary>

```bash
# 1. System packages — Python 3.11+, venv, build-essential for the occasional source build
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential

# If your distro ships Python <3.11 (Ubuntu 22.04 and older):
#   sudo add-apt-repository ppa:deadsnakes/ppa
#   sudo apt install -y python3.12 python3.12-venv

# 2. venv + dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
</details>

<details>
<summary><b>Linux (Fedora / RHEL)</b></summary>

```bash
sudo dnf install -y python3 python3-pip python3-virtualenv gcc gcc-c++ make
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
</details>

<details>
<summary><b>Linux (Arch)</b></summary>

```bash
sudo pacman -S --needed python python-pip base-devel
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
</details>

<details>
<summary><b>Windows (10 / 11)</b></summary>

```powershell
# 1. Python 3.11+ — pick ONE
winget install -e --id Python.Python.3.12
# or the installer from https://www.python.org/downloads/
#   ✓ tick "Add python.exe to PATH" on the first screen

# 2. venv + dependencies (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell refuses to run `Activate.ps1` (`running scripts is disabled`), allow user-scope scripts once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

In Command Prompt instead: `.\.venv\Scripts\activate.bat`. The Microsoft Store build of Python also works, but the python.org / winget installers are easier to find on `PATH`.
</details>

## Run

A single local server (FastAPI + uvicorn) serves the React SPA and the
analysis API on the same origin. The launcher builds the frontend on first
run, which needs **Node.js 20+**:

```bash
source .venv/bin/activate   # Python deps from Install above
./run.sh                    # builds the SPA on first launch, then serves it
```

Open <http://127.0.0.1:8000>. On the landing screen paste a path to your
`result.json` (or open a bundled demo). Pass a port (`./run.sh 9000`) or force
a fresh frontend build (`./run.sh --rebuild`).

<details>
<summary><b>Docker</b></summary>

`docker compose up --build` (or `docker-compose up --build` if you have only the standalone binary, e.g. `brew install docker` without the Compose plugin), then open <http://127.0.0.1:8000>. The image bundles the SPA and the two demos, so the **Try demo** buttons work out of the box.

To analyse your own export, mount its folder and paste a path *inside the container* — uncomment the `volumes:` block in `docker-compose.yml` (e.g. `- /path/to/export:/data:ro`), then enter `/data/result.json` in the UI.

Russian sentiment (torch + transformers, ~1 GB) is off by default — bake it in with `docker build --build-arg WITH_SENTIMENT=1 .` (or uncomment `args:` in the compose file).
</details>

For frontend work with hot-reload, run the two dev servers separately — Vite
proxies `/api` to the backend:

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000   # terminal 1 — API
cd frontend && npm install && npm run dev             # terminal 2 — http://localhost:5173
```

NLTK data (`stopwords`, `punkt_tab`) downloads automatically on the first word-analysis run. If `nltk.download()` errors out on macOS with an SSL cert problem, run `/Applications/Python\ 3.x/Install\ Certificates.command` once — applies only to the python.org installer, not the Homebrew build.

### Try it without your own data

Two synthetic exports ship with the repo, so the landing screen's **Try demo** buttons work right after cloning — nothing to download or generate (they're bundled into the Docker image too):

```
demo/group_demo.json       # 7-person studio chat, ~70k messages
demo/personal_demo.json    # 1-on-1, ~18k messages
```

To regenerate them (or tweak the participant profiles), run the generator:

```bash
python3 tools/gen_demo_data.py   # rewrites demo/group_demo.json + demo/personal_demo.json
```

Content is sampled from vocab pools with a fixed RNG seed; no real conversations are referenced.

## Optional: sentiment analysis

Russian / English sentiment via `rubert-tiny2-russian-sentiment`. The `torch` + `transformers` dependencies are ~1 GB on disk; the model weights themselves are ~50 MB, downloaded on first use:

```bash
pip install -r requirements-sentiment.txt
```

Restart the app after install. The model doesn't understand slang or jokes, and while the app dampens scores on obvious sarcasm markers (🤡 🙄, a trailing `/s`), it stays a rough heuristic — read the numbers with healthy scepticism.

**Use a different model.** The default is Russian-first. To score another language, set `TLA_SENTIMENT_MODEL` to any HuggingFace sequence-classification model whose labels include *positive* / *negative*, then restart:

```bash
# multilingual (English, Spanish, …)
TLA_SENTIMENT_MODEL=cardiffnlp/twitter-xlm-roberta-base-sentiment ./run.sh
# English-only
TLA_SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english ./run.sh
```

## Screenshots

The dashboard images in this README are generated, not hand-captured — re-run the script after a UI change to refresh them:

```bash
pip install playwright            # dev-only, intentionally not in requirements.txt
python -m playwright install chromium
python tools/screenshots.py       # writes the 5 PNGs in docs/screenshots/
```

`tools/screenshots.py` drives headless Chromium against the two bundled demos and overwrites `docs/screenshots/*.png`. It starts a server automatically if one isn't already running; pass `--only <name>` to refresh a single shot or `--base-url` to target another port. The sentiment shot needs the optional model (see above) — without it that one is skipped.

## Tests & lint

```bash
pip install ruff pytest
ruff check .
pytest
```

CI runs the same on every push and PR (`.github/workflows/ci.yml`).

## Credits

Inspired by [**TelAnalysis** by Eduard Isaev](https://github.com/krakodjaba/TelAnalysis) ([@e_isaevsan](https://t.me/stdinio)) — thanks for the original idea and for showing how to parse the Telegram export format. This version is an independent rewrite with its own UI and architecture (React SPA + FastAPI here, server-rendered templates there) and a different, broader set of analytics.

## License

MIT — see [`LICENSE`](LICENSE). TelAnalysis is an independent work; the upstream project that inspired it does not ship an OSI-approved license, so this project does not derive its terms from it.
