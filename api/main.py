"""FastAPI backend for TelAnalysis.

Wraps the pure-Python analysis (`analysis/*`) as JSON endpoints. The React SPA
(frontend/) talks to these locally; the export file is read from a local path
and never leaves the machine (privacy preserved).

Results are cached with `functools.lru_cache` keyed by (path, mtime, chat,
from, to), so re-querying the same file/range is instant. The heavy sentiment
model (if installed) loads lazily on first use, once per process.

Run:
    .venv/bin/uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, is_dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import i18n
from analysis import anniversaries as anniversaries_mod
from analysis import chains as chains_mod
from analysis import channel as channel_mod
from analysis import emoji_stats as emoji_mod
from analysis import forwards as forwards_mod
from analysis import graph as graph_mod
from analysis import highlights as highlights_mod
from analysis import latency as latency_mod
from analysis import loader, overview, theme
from analysis import mat as mat_mod
from analysis import media as media_mod
from analysis import monologues as monologues_mod
from analysis import phrases as phrases_mod
from analysis import reciprocity as reciprocity_mod
from analysis import render as render_mod
from analysis import sessions as sessions_mod
from analysis import speaking as speaking_mod
from analysis import stickers as stickers_mod
from analysis import timing as timing_mod
from analysis import words as words_mod


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


# resolution + caching (mirrors the old cache_key = path::mtime::chat::from::to)


def _mtime(path: str) -> float:
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return os.path.getmtime(path)


@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> dict:
    # A malformed / non-export file (e.g. a random text file) makes the loader
    # raise — turn that into a clean 400 instead of a 500 with a traceback.
    # lru_cache never caches a raised exception, so a fixed file still loads.
    try:
        return loader.load_export(path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse export: {exc}") from exc


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
    """Filtered message list for (chat, date range) — cached by (path, mtime, …)."""
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


def _only_user(msgs: list, user: str | None) -> list:
    """Filter to one sender's messages (by from_id). Compared as strings since
    query params arrive as strings while raw from_id may be int."""
    if not user:
        return msgs
    return [m for m in msgs if isinstance(m, dict) and str(m.get("from_id")) == str(user)]


@lru_cache(maxsize=8)
def _words_result(path: str, mtime: float, chat: str | None, from_d: str | None, to_d: str | None, most_com: int):
    """Cached WordsResult — sentiment inference is expensive, so /words,
    /sentiment and /distinguishing share one computation per (chat, period)."""
    _, msgs = _messages(path, mtime, chat, from_d, to_d)
    return words_mod.analyze(msgs, most_com=most_com)


# common query params
_P = Query(..., description="Absolute path to result.json / export folder")
_C = Query(None, description="Chat id, or '__combine__' for the whole archive")
_F = Query(None, alias="from")
_T = Query(None, alias="to")


# endpoints


# Chat-type ordering for the picker: personal → groups → channels → bots →
# saved → unknown.
_TYPE_RANK = {
    "personal_chat": 0,
    "private_group": 1,
    "private_supergroup": 1,
    "public_supergroup": 1,
    "private_channel": 2,
    "public_channel": 2,
    "bot_chat": 3,
    "saved_messages": 4,
}


@app.get("/api/chats")
def chats(path: str = _P):
    mtime = _mtime(path)
    data = _load(path, mtime)
    cs = _chats(path, mtime)
    # Sort by (type rank, name) — the rank groups personals together, then
    # groups, channels, bots; alphabetical within each cluster keeps the list
    # predictable while search still matches by name.
    ordered = sorted(cs, key=lambda c: (_TYPE_RANK.get(c.type, 9), c.name.lower()))
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
            for c in ordered
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
def per_day(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    user: str | None = Query(None),
):
    _, msgs = _resolve(path, chat, from_, to)
    return {"per_day": overview.messages_per_day(_only_user(msgs, user))}


@app.get("/api/hour-weekday")
def hour_weekday(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    user: str | None = Query(None),
):
    _, msgs = _resolve(path, chat, from_, to)
    return {"grid": overview.hour_weekday_heatmap(_only_user(msgs, user))}


@app.get("/api/hour-by-user")
def hour_by_user(path: str = _P, chat: str | None = _C, from_: str | None = _F, to: str | None = _T):
    """Per-user hour-of-day distribution (24-int list). Used by the 2-user
    "when do we overlap" chart in Overview — one shot instead of N hour-weekday
    calls."""
    _, msgs = _resolve(path, chat, from_, to)
    dist = overview.hour_distribution_per_user(msgs)
    return {
        "users": [
            {"user_id": str(uid), "name": name, "hours": hours}
            for uid, (name, hours) in dist.items()
        ]
    }


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
        "communities": graph_mod.detect_communities(g),
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
    top_n: int = Query(12),
):
    _, msgs = _resolve(path, chat, from_, to)
    return {uid: to_jsonable(s) for uid, s in stickers_mod.analyze(msgs, top_n=top_n).per_user.items()}


_STICKER_EXTS = {".webp", ".webm", ".jpg", ".jpeg", ".png", ".tgs"}
_STICKER_MIME = {
    ".webp": "image/webp",
    ".webm": "video/webm",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tgs": "application/octet-stream",
}


@app.get("/api/sticker-file")
def sticker_file(
    path: str = _P,
    rel: str = Query(..., description="Media path relative to the export root"),
):
    """Serve a sticker / thumbnail image straight from the export folder.

    `path` is the loaded result.json; its parent directory is the export root.
    `rel` is the media path stored in the JSON (e.g.
    `chats/chat_009/stickers/sticker (1).webp`). We only resolve files that stay
    inside the export root, live under `chats/`, and carry a known image/video
    extension — so a crafted `?rel=../../etc/passwd` can't escape. Returns 404
    when the media isn't on disk (e.g. a session loaded from an uploaded copy of
    result.json, which has no media alongside it)."""
    rel_norm = rel.replace("\\", "/")
    parts = rel_norm.split("/")
    if ".." in parts or rel_norm.startswith("/") or not rel_norm.startswith("chats/"):
        raise HTTPException(status_code=404, detail="Not found")
    ext = Path(rel_norm).suffix.lower()
    if ext not in _STICKER_EXTS:
        raise HTTPException(status_code=404, detail="Not found")
    root = Path(path).resolve().parent
    target = (root / rel_norm).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(target, media_type=_STICKER_MIME.get(ext, "application/octet-stream"))


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
    res = _words_result(path, _mtime(path), chat, from_, to, top)
    return _words_summary(res)


@app.get("/api/sentiment")
def sentiment(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    top: int = Query(10),
    user: str | None = Query(None),
):
    """Sentiment over time / by hour / by weekday + extreme messages.
    Reuses the cached WordsResult (the sentiment model runs there).
    With ?user=, the extreme messages are restricted to that participant."""
    res = _words_result(path, _mtime(path), chat, from_, to, 30)
    if not res.sentiment_available:
        return {"available": False}
    extremes: list[tuple[str, float, str]] = []
    for u in res.users.values():
        if user and str(u.user_id) != str(user):
            continue
        for txt, s in u.messages:
            if isinstance(s, float) and txt and abs(s) > 0.05:
                extremes.append((txt, s, u.name))
    pos = sorted(extremes, key=lambda r: -r[1])[:top]
    neg = sorted(extremes, key=lambda r: r[1])[:top]
    return {
        "available": True,
        "avg": res.chat_avg_sentiment,
        "sarcasm_marked": res.sarcasm_marked,
        "weekly": words_mod.sentiment_period_series(res.dated_scores, "week"),
        "per_user_weekly": words_mod.sentiment_period_series(res.dated_scores, "week", per_user=True),
        "by_hour": words_mod.sentiment_by_hour(res.dated_scores),
        "by_weekday": words_mod.sentiment_by_weekday(res.dated_scores),
        "user_names": {u.user_id: u.name for u in res.users.values()},
        "positive": pos,
        "negative": neg,
    }


@app.get("/api/distinguishing")
def distinguishing(
    path: str = _P,
    chat: str | None = _C,
    from_: str | None = _F,
    to: str | None = _T,
    top: int = Query(15),
):
    """Log-odds distinctive words for a 2-person chat (each side's lexicon)."""
    res = _words_result(path, _mtime(path), chat, from_, to, 30)
    users = list(res.users.values())
    if len(users) != 2:
        return {"available": False}
    a, b = users
    a_words, b_words = words_mod.distinguishing_words(a._tokens, b._tokens, top_n=top)
    return {
        "available": True,
        "a_name": a.name,
        "b_name": b.name,
        "a": a_words,
        "b": b_words,
    }


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


_UPLOAD_DIR = Path(tempfile.gettempdir()) / "telanalysis_uploads"


def _prune_uploads(max_age_seconds: int = 86_400) -> None:
    """Drop upload copies older than max_age so the temp dir doesn't grow
    without bound across sessions. Best-effort: ignores files we can't remove."""
    if not _UPLOAD_DIR.is_dir():
        return
    cutoff = time.time() - max_age_seconds
    for f in _UPLOAD_DIR.iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """Accept a result.json (or messages.html) upload and return its local path.

    The browser File API hides the original filesystem path for privacy, so we
    save a copy under the OS temp dir and hand back that absolute path — the
    same path-based endpoints (/chats, /kpis, …) take it from there. The bytes
    stay on the user's machine: uvicorn binds to 127.0.0.1.
    """
    raw = file.filename or "result.json"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(raw)).strip("_") or "result.json"
    if not safe.lower().endswith((".json", ".html")):
        safe += ".json"
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _prune_uploads()
    # Prefix with a timestamp so re-uploads of "result.json" don't collide.
    target = _UPLOAD_DIR / f"{int(time.time() * 1000)}-{safe}"
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"path": str(target.resolve()), "size": target.stat().st_size}


@app.post("/api/browse")
def browse(prompt: str = Query("Choose your Telegram export result.json")):
    """Open a NATIVE macOS file picker and return the chosen absolute path.

    The server runs locally in the user's GUI session, so unlike /api/upload it
    hands back the REAL path — the adjacent media (chats/…) stays resolvable, so
    stickers/photos load. This is a sync `def`, so FastAPI runs it in a thread
    pool: the blocking dialog never stalls the async event loop.

    Returns {"path", "size"} on pick, {"cancelled": True} if the user cancels,
    or 501 on non-macOS (the frontend then falls back to the manual path field).
    """
    if sys.platform != "darwin":
        raise HTTPException(status_code=501, detail="native-picker-unavailable")
    # Escape for an AppleScript string literal — only \ and ". NOT json.dumps:
    # it emits \uXXXX for non-ASCII, which AppleScript can't parse (syntax error
    # -2741). osascript reads UTF-8, so a raw Cyrillic prompt is fine.
    esc = prompt.replace("\\", "\\\\").replace('"', '\\"')
    script = f'POSIX path of (choose file with prompt "{esc}")'
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, encoding="utf-8", timeout=600,
        )
    except Exception as exc:  # osascript missing / timeout
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        if "-128" in err or "cancel" in err.lower():  # user hit Cancel
            return {"cancelled": True}
        raise HTTPException(status_code=500, detail=err or "picker failed")
    path = proc.stdout.strip()
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=400, detail="no file chosen")
    if not path.lower().endswith((".json", ".html")):
        raise HTTPException(status_code=400, detail="not-json")
    return {"path": path, "size": os.path.getsize(path)}


@app.get("/api/health")
def health():
    return {"ok": True}


# serve the built SPA (prod)
# When `frontend/dist` exists, mount it at root so a single `uvicorn` serves
# both the API (/api/*, registered above) and the React app same-origin. In
# dev this directory is absent; the Vite dev server proxies /api → :8000.
_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="spa")
