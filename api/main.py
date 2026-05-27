"""FastAPI backend for TelAnalysis.

Wraps the existing pure-Python analysis (`analysis/*`) as JSON endpoints — the
endpoint set mirrors the old Streamlit cache wrappers in `ui/cache.py`. The
React SPA (frontend/) talks to these locally; the export file is read from a
local path and never leaves the machine (privacy preserved).

Caching mirrors Streamlit's `@st.cache_data`: keyed by (path, mtime, chat,
from, to) via functools.lru_cache. The heavy sentiment model (if installed)
loads lazily on first use, once per process.

Run:
    .venv/bin/uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from analysis import anniversaries as anniversaries_mod
from analysis import emoji_stats as emoji_mod
from analysis import highlights as highlights_mod
from analysis import latency as latency_mod
from analysis import loader, overview
from analysis import media as media_mod
from analysis import render as render_mod
from analysis import timing as timing_mod

app = FastAPI(title="TelAnalysis API", version="0.1.0")

# Dev: Vite dev server (5173) calls the API on 8000. In prod the SPA is served
# same-origin by this app, so CORS is a no-op there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

COMBINE = "__combine__"


# --- resolution + caching (mirrors the old cache_key = path::mtime::chat::from::to) ---


def _mtime(path: str) -> float:
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return os.path.getmtime(path)


@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> dict:
    return loader.load_export(path)


@lru_cache(maxsize=4)
def _chats(path: str, mtime: float) -> tuple:
    return tuple(loader.list_chats(_load(path, mtime)))


def _pick_chat(path: str, mtime: float, chat_id: str | None):
    chats = _chats(path, mtime)
    if chat_id == COMBINE:
        return loader.combined_chat(list(chats))
    if chat_id:
        for c in chats:
            if str(c.id) == str(chat_id):
                return c
        raise HTTPException(status_code=404, detail="Chat not found")
    return chats[0]


@lru_cache(maxsize=16)
def _messages(path: str, mtime: float, chat_id: str | None, from_d: str | None, to_d: str | None):
    """Filtered message list for (chat, date range) — cached like Streamlit."""
    chat = _pick_chat(path, mtime, chat_id)
    msgs = chat.messages
    if from_d and to_d:
        msgs = overview.filter_by_date(msgs, from_d, to_d)
    return chat, msgs


def _resolve(path: str, chat: str | None, from_: str | None, to: str | None):
    mtime = _mtime(path)
    return _messages(path, mtime, chat, from_, to)


def to_jsonable(obj: Any) -> Any:
    """Dataclass → dict (recursive); everything else passes through to JSON."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    return obj


# common query params
_P = Query(..., description="Absolute path to result.json / export folder")
_C = Query(None, description="Chat id, or '__combine__' for the whole archive")
_F = Query(None, alias="from")
_T = Query(None, alias="to")


# --- endpoints ---


@app.get("/api/chats")
def chats(path: str = _P):
    mtime = _mtime(path)
    data = _load(path, mtime)
    cs = _chats(path, mtime)
    return {
        "source": data.get("_source", "json"),
        "chats": [
            {"id": str(c.id), "name": c.name, "type": c.type, "count": len(c.messages)}
            for c in cs
        ],
    }


@app.get("/api/bounds")
def bounds(path: str = _P, chat: str | None = _C):
    _, msgs = _resolve(path, chat, None, None)
    b = overview.date_bounds(msgs)
    return {"bounds": list(b) if b else None}


@app.get("/api/kpis")
def kpis(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(overview.compute_kpis(msgs))


@app.get("/api/per-day")
def per_day(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return {"per_day": overview.messages_per_day(msgs)}


@app.get("/api/hour-weekday")
def hour_weekday(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return {"grid": overview.hour_weekday_heatmap(msgs)}


@app.get("/api/participants")
def participants(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return {"participants": overview.participants_table(msgs)}


@app.get("/api/media")
def media(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(media_mod.analyze(msgs))


@app.get("/api/emojis")
def emojis(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(emoji_mod.analyze(msgs))


@app.get("/api/latency")
def latency(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(latency_mod.compute(msgs))


@app.get("/api/hero")
def hero(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    chat_obj, msgs = _resolve(path, chat, from_, to)
    k = overview.compute_kpis(msgs)
    pd = overview.messages_per_day(msgs)
    grid = overview.hour_weekday_heatmap(msgs)
    streaks = timing_mod.streaks_and_silences(msgs)
    h = highlights_mod.build_hero(chat_name=chat_obj.name, kpis=k, per_day=pd, grid=grid, streaks=streaks)
    return {**to_jsonable(h), "chat_type": chat_obj.type, "chat_id": str(chat_obj.id)}


@app.get("/api/highlights")
def highlights(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    k = overview.compute_kpis(msgs)
    pd = overview.messages_per_day(msgs)
    grid = overview.hour_weekday_heatmap(msgs)
    streaks = timing_mod.streaks_and_silences(msgs)
    items = highlights_mod.top_highlights(kpis=k, per_day=pd, grid=grid, streaks=streaks)
    return {"highlights": [to_jsonable(h) for h in items]}


@app.get("/api/anniversaries")
def anniversaries(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    k = overview.compute_kpis(msgs)
    pd = overview.messages_per_day(msgs)
    a = anniversaries_mod.compute(
        first_date=k.first_date, total_messages=k.total_messages, per_day=pd
    )
    return to_jsonable(a)


@app.get("/api/wordcloud")
def wordcloud(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    from analysis import words as words_mod

    _, msgs = _resolve(path, chat, from_, to)
    res = words_mod.analyze(msgs, most_com=200)
    png = render_mod.wordcloud_png(res.chat_top_words)
    if not png:
        raise HTTPException(status_code=404, detail="Not enough text for a wordcloud")
    return Response(content=png, media_type="image/png")


@app.get("/api/health")
def health():
    return {"ok": True}
