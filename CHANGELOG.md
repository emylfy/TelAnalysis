# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-21

First public release as a standalone project: a React SPA served same-origin
by a FastAPI backend over a modular, pure-Python analysis engine. Everything
runs locally — no telemetry, no remote API calls.

### Added
- **React + FastAPI app** — single local server (`./run.sh`) builds the SPA and
  serves it with the analysis API on `127.0.0.1:8000`.
- **Dockerfile + docker-compose** for one-command self-hosting.
- **Reply graph** with Louvain community colouring exposed via `/api/graph`
  (`communities` map) and rendered in the ECharts force-directed graph.
- Analysis engine: Overview KPIs & heatmaps, reply latency (with Q&A split),
  per-user speaking-style radar, reply-chain depth, conversation sessions,
  longest monologues, sticker-emoji preferences, forwards ratio, streaks,
  anniversaries, "Spotify Wrapped" highlights.
- Text analytics: wordcloud, top words, n-gram phrases, russian-profanity
  tracker, MTLD lexical diversity, email/phone extraction.
- Optional Russian/English sentiment via `rubert-tiny2-russian-sentiment`.
- HTML + JSON export support, full-archive (multi-chat) handling, RU/EN UI.
- Tests (pytest) and CI across Python 3.11–3.14 plus a frontend typecheck/build.

### Changed
- **Relicensed to MIT.** TelAnalysis is an independent rewrite inspired by
  [krakodjaba/TelAnalysis](https://github.com/krakodjaba/TelAnalysis); it shares
  no UI or architecture with the original and does not inherit its terms.
- Consolidated all Python dependencies into a single `requirements.txt`.

### Removed
- **Classic Streamlit UI** (`app.py` and the Streamlit-specific `ui/` helpers).
  The React SPA is now the only frontend, dropping the `streamlit`, `plotly`,
  `pyvis` and `pandas` dependencies.
