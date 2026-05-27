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

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from analysis import anniversaries as anniversaries_mod
from analysis import chains as chains_mod
from analysis import channel as channel_mod
from analysis import emoji_stats as emoji_mod
from analysis import forwards as forwards_mod
from analysis import graph as graph_mod
from analysis import highlights as highlights_mod
from analysis import latency as latency_mod
from analysis import loader, overview
from analysis import mat as mat_mod
from analysis import media as media_mod
from analysis import monologues as monologues_mod
from analysis import phrases as phrases_mod
from analysis import reciprocity as reciprocity_mod
from analysis import render as render_mod
from analysis import sessions as sessions_mod
from analysis import speaking as speaking_mod
from analysis import stickers as stickers_mod
from analysis import theme
from analysis import timing as timing_mod
from analysis import words as words_mod
from ui import i18n


async def _set_lang(lang: str = Query("ru")) -> str:
    """Global dependency: drive the i18n override from ?lang= for the request.

    Must be async: it runs in the request task's context, so the contextvar it
    sets is copied into the threadpool that runs the (sync) endpoint. A sync
    dependency would set it in a throwaway worker-thread context instead.
    """
    i18n.set_lang(lang)
    return lang


app = FastAPI(
    title="TelAnalysis API",
    version="0.1.0",
    dependencies=[Depends(_set_lang)],
)

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
            {
                "id": str(c.id),
                "name": c.name,
                "type": c.type,
                "count": len(c.messages),
                "sections": sorted(loader.sections_for_type(c.type)),
            }
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
    png = render_mod.wordcloud_png(res.chat_top_words, colors=theme.COLORWAY)
    if not png:
        raise HTTPException(status_code=404, detail="Not enough text for a wordcloud")
    return Response(content=png, media_type="image/png")


@app.get("/api/graph")
def graph(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    g = graph_mod.build(msgs)
    return {
        "nodes": g.nodes,
        "edges": g.edges,
        "summary": graph_mod.interaction_summary(msgs),
    }


@app.get("/api/chains")
def chains(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(chains_mod.analyze(msgs))


@app.get("/api/sessions")
def sessions(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    gap_minutes: int = Query(30),
):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(sessions_mod.stats(sessions_mod.split_into_sessions(msgs, gap_minutes=gap_minutes)))


@app.get("/api/streaks")
def streaks(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    user: str | None = Query(None),
):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(timing_mod.streaks_and_silences(msgs, filter_uid=user))


@app.get("/api/initiators")
def initiators(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    gap_hours: int = Query(4),
):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(timing_mod.conversation_initiators(msgs, gap_hours=gap_hours))


@app.get("/api/reciprocity")
def reciprocity(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(reciprocity_mod.compute(msgs))


@app.get("/api/speaking")
def speaking(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return {uid: to_jsonable(s) for uid, s in speaking_mod.analyze(msgs).items()}


@app.get("/api/phrases")
def phrases(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    n: int = Query(2),
    top: int = Query(30),
):
    _, msgs = _resolve(path, chat, from_, to)
    return {"phrases": phrases_mod.top_phrases(msgs, n=n, top=top)}


@app.get("/api/per-user-phrases")
def per_user_phrases(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    n: int = Query(2),
    top: int = Query(15),
):
    _, msgs = _resolve(path, chat, from_, to)
    return phrases_mod.per_user_phrases(msgs, n=n, top=top)


@app.get("/api/forwards")
def forwards(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(forwards_mod.analyze(msgs, top_sources=5))


@app.get("/api/mat")
def mat(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(mat_mod.analyze(msgs))


@app.get("/api/monologues")
def monologues(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    top_n: int = Query(10),
    min_run: int = Query(3),
):
    _, msgs = _resolve(path, chat, from_, to)
    return to_jsonable(monologues_mod.analyze(msgs, top_n=top_n, min_run=min_run))


@app.get("/api/stickers")
def stickers(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    top_n: int = Query(10),
):
    _, msgs = _resolve(path, chat, from_, to)
    return {uid: to_jsonable(s) for uid, s in stickers_mod.analyze(msgs, top_n=top_n).per_user.items()}


def _words_summary(res) -> dict:
    """Curated WordsResult — drops per-user message lists (~30k tuples) and the
    private _tokens; heavy per-user drilldowns get dedicated endpoints later."""
    return {
        "chat_top_words": res.chat_top_words,
        "chat_avg_sentiment": res.chat_avg_sentiment,
        "sentiment_available": res.sentiment_available,
        "sarcasm_marked": getattr(res, "sarcasm_marked", 0),
        "emails": res.emails,
        "phones": res.phones,
        "users": [
            {
                "user_id": u.user_id,
                "name": u.name,
                "msg_count": len(u.messages),
                "avg_sentiment": u.avg_sentiment,
                "top_words": u.top_words,
                "total_tokens": u.total_tokens,
                "unique_tokens": u.unique_tokens,
                "mtld": getattr(u, "mtld", 0.0),
                "ttr": getattr(u, "ttr", 0.0),
            }
            for u in sorted(res.users.values(), key=lambda x: -len(x.messages))
        ],
    }


@app.get("/api/words")
def words(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    top: int = Query(30),
):
    _, msgs = _resolve(path, chat, from_, to)
    return _words_summary(words_mod.analyze(msgs, most_com=top))


@app.get("/api/channel")
def channel(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    top: int = Query(30),
):
    _, msgs = _resolve(path, chat, from_, to)
    res = channel_mod.analyze(msgs, most_com=top)
    return {
        "top_words": res.top_words,
        "token_count": res.token_count,
        "has_wordcloud": res.wordcloud_png is not None,
    }


@app.get("/api/channel/wordcloud")
def channel_wordcloud(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
):
    _, msgs = _resolve(path, chat, from_, to)
    res = channel_mod.analyze(msgs, most_com=200)
    png = render_mod.wordcloud_png(res.top_words, colors=theme.COLORWAY)
    if not png:
        raise HTTPException(status_code=404, detail="Not enough text for a wordcloud")
    return Response(content=png, media_type="image/png")


@app.get("/api/health")
def health():
    return {"ok": True}
