"""Smoke tests for the FastAPI layer (api.main).

Covers status codes, response shape, ?lang= i18n switching, and the
malformed-file → 400 guard. Uses an in-memory export written to a tmp file so
the suite runs in CI without the (git-untracked) demo data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Skip the whole module if the backend deps aren't installed (the analysis-only
# test runs don't need FastAPI). CI installs api/requirements.txt + httpx.
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture
def export_path(tmp_path: Path) -> str:
    """A minimal but valid personal_chat export: two users, a week of dated
    messages with enough text for the words/wordcloud endpoints."""
    msgs = []
    for i in range(40):
        day = 1 + (i % 7)
        uid, name = ("user1", "Alice") if i % 2 == 0 else ("user2", "Bob")
        msgs.append(
            {
                "id": i + 1,
                "type": "message",
                "date": f"2023-01-0{day}T{10 + i % 12:02d}:{i % 60:02d}:00",
                "from": name,
                "from_id": uid,
                "text": "hello world " * (1 + i % 3),
            }
        )
    export = {"name": "Alice", "type": "personal_chat", "id": 12345, "messages": msgs}
    p = tmp_path / "result.json"
    p.write_text(json.dumps(export), encoding="utf-8")
    return str(p)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_chats_shape(export_path: str):
    r = client.get("/api/chats", params={"path": export_path})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "json"
    assert len(body["chats"]) == 1
    c = body["chats"][0]
    assert c["id"] == "12345"
    assert c["type"] == "personal_chat"
    assert c["count"] == 40
    # sections drive which tabs the SPA shows — must be a non-empty list
    assert isinstance(c["sections"], list) and c["sections"]


def test_kpis(export_path: str):
    r = client.get("/api/kpis", params={"path": export_path})
    assert r.status_code == 200
    k = r.json()
    assert k["total_messages"] == 40
    assert k["unique_users"] == 2


def test_bounds(export_path: str):
    r = client.get("/api/bounds", params={"path": export_path})
    assert r.status_code == 200
    bounds = r.json()["bounds"]
    assert bounds is not None and len(bounds) == 2


def test_words_endpoint(export_path: str):
    # sentiment_available depends on optional torch/transformers; the endpoint
    # must still succeed (and report the flag) when they're absent.
    r = client.get("/api/words", params={"path": export_path})
    assert r.status_code == 200
    w = r.json()
    assert "chat_top_words" in w
    assert isinstance(w["sentiment_available"], bool)
    assert len(w["users"]) == 2


def test_missing_file_404():
    r = client.get("/api/kpis", params={"path": "/no/such/file.json"})
    assert r.status_code == 404


def test_malformed_file_400(tmp_path: Path):
    # A non-export file used to surface as a 500 with a traceback; the loader
    # guard now turns it into a clean 400.
    bad = tmp_path / "garbage.json"
    bad.write_text("this is not json at all {", encoding="utf-8")
    r = client.get("/api/chats", params={"path": str(bad)})
    assert r.status_code == 400


def test_lang_switches_localized_output(export_path: str):
    """The ?lang= dependency drives per-request i18n: the hero prose is
    composed server-side, so RU and EN must differ."""
    ru = client.get("/api/hero", params={"path": export_path, "lang": "ru"}).json()
    en = client.get("/api/hero", params={"path": export_path, "lang": "en"}).json()
    assert ru["prose_html"] != en["prose_html"]


def test_chat_not_found_404(export_path: str):
    r = client.get("/api/kpis", params={"path": export_path, "chat": "999999"})
    assert r.status_code == 404
