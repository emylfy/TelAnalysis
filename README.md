<div align="right">

**English** · [Русский](README.ru.md)

</div>

# TelAnalysis

[![CI](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml/badge.svg)](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml)
![Python 3.11–3.14](https://img.shields.io/badge/python-3.11--3.14-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Built with React + FastAPI](https://img.shields.io/badge/built%20with-React%20%2B%20FastAPI-61DAFB.svg)

> Local web app for analysing Telegram chat exports — runs entirely on your machine. Drop in `result.json`, get heatmaps, network graphs, word clouds, reply latency, sentiment arcs, and per-user breakdowns. A React SPA served same-origin by a FastAPI backend; your data never leaves your device.

<p align="center">
  <img src="docs/screenshots/group-01-overview.png" alt="Overview tab — KPIs, hero, daily timeline, peak hours" width="900">
</p>

## What it does

Reads a Telegram Desktop export (single chat or full archive) and renders an interactive dashboard. Tabs adapt to chat type — channels get broadcast-style stats, groups get the network graph and per-user breakdown, 1-on-1 chats get matched-pair analytics.

> **JSON is recommended** — in the export dialog switch the format from the default *HTML* to *Machine-readable JSON*. **HTML exports also work** (drop in the export folder or `messages.html`), but they're lossier: Telegram's HTML has no participant IDs, so the Network and Per-User tabs are less accurate for groups (the app warns on load). Either way, exporting is a Telegram Desktop feature — mobile and the native macOS client can't export chat history.

Both export shapes are supported:
- **Single chat** — `Settings → Export Chat History`
- **Full archive** — `Settings → Advanced → Export Telegram Data` → a chat picker appears once the export is loaded

UI ships in **EN / RU** (toggle in the header). Chat content is left untouched — wordclouds and message previews show whatever language the messages are in.

## Features

| Tab | What you get |
| --- | --- |
| **Overview** | KPI cards (messages, participants, days active, media, voice time), area chart of daily activity, calendar heatmap (year × week × day, with binary "did we talk today" toggle), hour × weekday heatmap, top emojis, reply latency distribution, Q&A latency split |
| **Network** | Interactive force-directed graph (drag / zoom / hover, edge thickness by interaction count, node colour by Louvain community), reply-chain depth metrics, "who replies to whom" matrix. Falls back to a bar chart for small chats. Edges/nodes export to CSV for Gephi |
| **Words** | Wordcloud + top words bar chart + virtualised table, n-gram phrase extraction (bigrams/trigrams), russian-profanity tracker per user (`hits / 100 msgs`), unique-vocabulary index, email + phone extraction |
| **Channel** | Broadcast-style wordcloud and frequency analysis for channels |
| **Per-user** | Per-user daily timeline, hour × weekday heatmap, top emojis, sticker-emoji preferences, reply latency, top words with wordcloud, speaking-style radar (avg message length, question rate, emoji rate, reply rate), longest monologues, forwards source breakdown |
| **Highlights** | Auto-generated "Spotify Wrapped" cards, anniversary milestones, conversation-length distribution, top-10 longest sessions |

Optional Russian/English **sentiment analysis** powered by `rubert-tiny2-russian-sentiment` — adds a per-user sentiment score, sentiment-over-time line, and sentiment by hour-of-day / weekday.

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/group-02-network.png" alt="Network tab — force-directed graph with communities"></td>
    <td width="50%"><img src="docs/screenshots/group-03-words.png" alt="Words tab — wordcloud and top phrases"></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshots/group-04-per-user.png" alt="Per-User tab — speaking style radar and timeline"></td>
    <td width="50%"><img src="docs/screenshots/personal-01-sentiment.png" alt="Sentiment over time — relationship arc in a 1-on-1 chat"></td>
  </tr>
</table>

## Privacy

Everything runs locally. The dashboard does not send your chat data anywhere — no analytics, no telemetry, no remote API calls. The only network activity is on first run:

- NLTK downloads its `stopwords` + `punkt_tab` corpora (~10 MB).
- *Optional only:* if you install `requirements-sentiment.txt`, HuggingFace downloads the `rubert-tiny2-russian-sentiment` model (~50 MB) the first time you open a tab that needs it.

After that first launch the app works fully offline. There is no telemetry, no analytics, and no remote API calls.

## Install

Requires **Python 3.11+**. Tested in CI on 3.11, 3.12, 3.13 and 3.14. The frontend build needs **Node.js 20+** (one-time, see [Run](#run)).

### macOS

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

### Linux (Ubuntu / Debian)

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

### Linux (Fedora / RHEL)

```bash
sudo dnf install -y python3 python3-pip python3-virtualenv gcc gcc-c++ make
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Linux (Arch)

```bash
sudo pacman -S --needed python python-pip base-devel
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows (10 / 11)

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

## Run

A single local server (FastAPI + uvicorn) serves the React SPA and the
analysis API same-origin — your export is read locally and never leaves the
machine. The launcher builds the frontend on first run, which needs
**Node.js 20+**:

```bash
source .venv/bin/activate   # Python deps from Install above
./run.sh                    # builds the SPA on first launch, then serves it
```

Open <http://127.0.0.1:8000>. On the landing screen paste a path to your
`result.json` (or open a bundled demo). Pass a port (`./run.sh 9000`) or force
a fresh frontend build (`./run.sh --rebuild`).

> **Docker:** `docker compose up --build` (or `docker-compose up --build` if you
> have only the standalone binary, e.g. `brew install docker` without the Compose
> plugin), then open <http://127.0.0.1:8000>.
> The image bundles the SPA and the two demos, so the **Try demo** buttons work
> out of the box. To analyse your own export, mount its folder and paste a path
> *inside the container* — uncomment the `volumes:` block in `docker-compose.yml`
> (e.g. `- /path/to/export:/data:ro`), then enter `/data/result.json` in the UI.
> Russian sentiment (torch + transformers, ~1GB) is off by default — bake it in
> with `docker build --build-arg WITH_SENTIMENT=1 .` (or uncomment `args:` in the
> compose file).

For frontend work with hot-reload, run the two dev servers separately — Vite
proxies `/api` to the backend:

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000   # terminal 1 — API
cd frontend && npm install && npm run dev             # terminal 2 — http://localhost:5173
```

NLTK data (`stopwords`, `punkt_tab`) downloads automatically on the first word-analysis run. If `nltk.download()` errors out on macOS with an SSL cert problem, run `/Applications/Python\ 3.x/Install\ Certificates.command` once — applies only to the python.org installer, not the Homebrew build.

### Try it without your own data

There's a generator for two synthetic exports — a 7-person studio chat and a 1-on-1 — purely for previewing the app:

```bash
python3 tools/gen_demo_data.py   # writes demo/group_demo.json + demo/personal_demo.json
./run.sh
```

On the landing screen choose a bundled demo, or paste a path:
```
demo/group_demo.json       # 7-person studio chat, ~70k messages
demo/personal_demo.json    # 1-on-1, ~18k messages
```

Content is sampled from vocab pools with a fixed RNG seed; no real conversations are referenced. Files are gitignored — regenerate any time.

## Optional: sentiment analysis

Russian / English sentiment via `rubert-tiny2-russian-sentiment` (~1 GB on disk, 50 MB model on first call):

```bash
pip install -r requirements-sentiment.txt
```

Restart the app after install. The model is not sarcasm-aware and does not understand slang or jokes — read the numbers with healthy scepticism.

## Tests & lint

```bash
pip install ruff pytest
ruff check .
pytest
```

CI runs the same on every push and PR (`.github/workflows/ci.yml`).

## Credits

Inspired by [**TelAnalysis** by Eduard Isaev](https://github.com/krakodjaba/TelAnalysis) ([@e_isaevsan](https://t.me/stdinio)) — thanks for the original idea and for showing how to parse the Telegram export format. This project is an independent rewrite: it shares no UI or architecture with the original (React SPA + FastAPI here vs. server-rendered templates there) and goes well beyond it in analytics.

Highlights of what this version adds:
- A React SPA served same-origin by a FastAPI backend, over a modular pure-Python analysis engine
- Interactive force-directed reply graph with Louvain community colouring; activity heatmaps (hour × weekday, calendar)
- Per-user tab (speaking-style radar, reply latency, monologues, sticker-emoji preferences, forwards ratio)
- Russian/English sentiment (`rubert-tiny2`), MTLD lexical diversity, n-gram phrases, russian-profanity tracker
- Reply-chain depth, conversation sessions, Q&A latency split, streaks, anniversaries, "Spotify Wrapped" highlights
- HTML + JSON export support, full-archive (multi-chat) handling, EN/RU UI, tests and CI

## License

MIT — see [`LICENSE`](LICENSE). TelAnalysis is an independent work; the upstream project that inspired it does not ship an OSI-approved license, so this project does not derive its terms from it.
