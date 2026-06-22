"""Tests for the backup manager (analysis.backup + /api/backup/*).

Builds a real on-disk full export (result.json + chats/chat_XXX media folders)
in a tmp dir, so the folder-derivation, size, trash and atomic-rewrite paths are
exercised against the filesystem — not mocks. Destructive ops run only on the
tmp copy.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis import backup


def _msg(i: int, date: str, media: str | None = None) -> dict:
    m = {"id": i, "type": "message", "date": date, "from": "A", "from_id": "u1", "text": "hi"}
    if media:
        m["photo"] = media
    return m


@pytest.fixture
def export_dir(tmp_path: Path) -> Path:
    """A full export: chat 111 has a media folder (photos+video), chat 222 has
    no media, left chat 333 is text-only."""
    photos = tmp_path / "chats" / "chat_002" / "photos"
    photos.mkdir(parents=True)
    (photos / "a.jpg").write_bytes(b"x" * 1000)
    videos = tmp_path / "chats" / "chat_002" / "video_files"
    videos.mkdir()
    (videos / "v.mp4").write_bytes(b"y" * 5000)

    data = {
        "chats": {
            "list": [
                {
                    "id": 111, "name": "Alice", "type": "personal_chat",
                    "messages": [
                        _msg(1, "2024-01-01T10:00:00"),
                        _msg(2, "2024-01-05T10:00:00", "chats/chat_002/photos/a.jpg"),
                    ],
                },
                {
                    "id": 222, "name": "Bob", "type": "personal_chat",
                    "messages": [_msg(1, "2024-02-01T10:00:00")],
                },
            ]
        },
        "left_chats": {
            "list": [
                {"id": 333, "name": "OldGroup", "type": "private_group",
                 "messages": [_msg(1, "2023-01-01T00:00:00")]},
            ]
        },
    }
    (tmp_path / "result.json").write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def _result(root: Path) -> dict:
    return json.loads((root / "result.json").read_text(encoding="utf-8"))


def test_chat_folder_derivation():
    msgs = [{"id": 1, "text": "x"}, {"id": 2, "photo": "chats/chat_009/photos/p.jpg"}]
    assert backup.chat_folder(msgs) == "chat_009"
    assert backup.chat_folder([{"id": 1, "text": "no media"}]) is None


def _chats_html(pairs: list[tuple[str, str]]) -> str:
    """Minimal lists/chats.html with one <a> entry per (folder, name)."""
    blocks = "".join(
        f'<a class="entry block_link clearfix" href="../chats/{folder}/messages.html#allow_back">'
        f'<div class="body"><div class="pull_right info details">private</div>'
        f'<div class="name bold">\n{name}\n</div></div></a>'
        for folder, name in pairs
    )
    return f"<html><body>{blocks}</body></html>"


def test_folder_map_prefers_authoritative_html(tmp_path: Path):
    """A chat that forwards heavily from another (its first/most media path
    points at the OTHER chat's folder) must still map to its OWN folder via
    lists/chats.html — the bug that double-counted disk size."""
    (tmp_path / "chats" / "chat_003").mkdir(parents=True)
    (tmp_path / "chats" / "chat_031").mkdir()
    (tmp_path / "lists").mkdir()
    (tmp_path / "lists" / "chats.html").write_text(
        _chats_html([("chat_003", "Egor"), ("chat_031", "Forwarder")]), encoding="utf-8"
    )
    data = {
        "chats": {"list": [
            {"id": 1, "name": "Egor", "type": "personal_chat",
             "messages": [_msg(1, "2024-01-01T00:00:00", "chats/chat_003/photos/a.jpg")] * 3},
            # Forwarder's only media are forwards from Egor → point at chat_003
            {"id": 2, "name": "Forwarder", "type": "personal_chat",
             "messages": [_msg(1, "2024-01-01T00:00:00", "chats/chat_003/photos/a.jpg")]},
        ]}
    }
    fmap = backup.folder_map(tmp_path, data)
    assert fmap["1"] == "chat_003"
    assert fmap["2"] == "chat_031"  # NOT chat_003, despite its media pointing there


def test_media_owner_fallback_is_bijection(tmp_path: Path):
    """With no chats.html, a folder goes to the chat referencing it MOST; the
    light forwarder gets nothing rather than stealing the owner's folder."""
    data = {
        "chats": {"list": [
            {"id": 1, "name": "Owner", "type": "personal_chat",
             "messages": [_msg(i, "2024-01-01T00:00:00", "chats/chat_003/p.jpg") for i in range(50)]},
            {"id": 2, "name": "Forwarder", "type": "personal_chat",
             "messages": [_msg(1, "2024-01-01T00:00:00", "chats/chat_003/p.jpg")]},
        ]}
    }
    fmap = backup.folder_map(tmp_path, data)  # tmp_path has no lists/chats.html
    assert fmap.get("1") == "chat_003"
    assert "2" not in fmap


def test_can_manage(export_dir: Path):
    assert backup.can_manage(str(export_dir / "result.json")) is True
    # a lone result.json with no adjacent chats/ folder is not manageable
    lone = export_dir / "copy"
    lone.mkdir()
    (lone / "result.json").write_text("{}", encoding="utf-8")
    assert backup.can_manage(str(lone / "result.json")) is False


def test_safe_under_root_rejects_escape(export_dir: Path):
    root = backup.export_root(str(export_dir / "result.json"))
    assert backup.safe_under_root(root, "chats/chat_002").is_relative_to(root)
    for bad in ("../../etc/passwd", "/etc/passwd", "chats/../../x"):
        with pytest.raises(ValueError):
            backup.safe_under_root(root, bad)


def test_chat_rows(export_dir: Path):
    p = str(export_dir / "result.json")
    rows = backup.chat_rows(backup.loader.load_json(p), backup.export_root(p))
    by_id = {r["id"]: r for r in rows}
    assert by_id["111"]["folder"] == "chats/chat_002"
    assert by_id["111"]["disk_bytes"] == 6000
    assert by_id["111"]["media"] == {"photos": 1000, "video_files": 5000}
    assert by_id["111"]["first_date"] == "2024-01-01T10:00:00"
    assert by_id["222"]["folder"] is None and by_id["222"]["disk_bytes"] == 0
    assert by_id["333"]["is_left"] is True


def test_delete_trash_restore_roundtrip(export_dir: Path):
    p = str(export_dir / "result.json")
    res = backup.delete_chats(p, ["111"])
    assert res["removed_chats"] == 1
    assert res["removed_messages"] == 2
    assert res["bytes"] == 6000
    # folder moved out, JSON entry gone, trash populated
    assert not (export_dir / "chats" / "chat_002").exists()
    assert [c["id"] for c in _result(export_dir)["chats"]["list"]] == [222]
    entries = backup.trash_entries(export_dir)
    assert len(entries) == 1 and entries[0]["bytes"] == 6000

    backup.restore(p, res["trash_id"])
    assert (export_dir / "chats" / "chat_002" / "photos" / "a.jpg").exists()
    assert sorted(str(c["id"]) for c in _result(export_dir)["chats"]["list"]) == ["111", "222"]
    assert backup.trash_entries(export_dir) == []


def test_delete_left_chat_no_folder(export_dir: Path):
    p = str(export_dir / "result.json")
    res = backup.delete_chats(p, ["333"])
    assert res["removed_chats"] == 1 and res["bytes"] == 0
    assert _result(export_dir)["left_chats"]["list"] == []


def test_slim_and_empty_trash(export_dir: Path):
    p = str(export_dir / "result.json")
    res = backup.slim_chat(p, "111", ["video_files"])
    assert res["bytes"] == 5000
    assert not (export_dir / "chats" / "chat_002" / "video_files").exists()
    # text + the other media survive; JSON entry untouched
    assert (export_dir / "chats" / "chat_002" / "photos" / "a.jpg").exists()
    assert any(c["id"] == 111 for c in _result(export_dir)["chats"]["list"])

    freed = backup.empty_trash(p)["freed_bytes"]
    assert freed >= 5000
    assert not (export_dir / backup.TRASH_DIR).exists()


def test_atomic_rewrite_preserves_other_sections(export_dir: Path):
    # add a sibling top-level section; deleting a chat must not drop it
    data = _result(export_dir)
    data["personal_information"] = {"first_name": "Tim"}
    (export_dir / "result.json").write_text(json.dumps(data), encoding="utf-8")
    backup.delete_chats(str(export_dir / "result.json"), ["222"])
    after = _result(export_dir)
    assert after["personal_information"] == {"first_name": "Tim"}
    assert [c["id"] for c in after["chats"]["list"]] == [111]


# HTML tail cleanup


def _entry(kind: str, name: str, folder: str | None) -> str:
    body = (
        '<div class="body"><div class="pull_right info details">channel</div>'
        f'<div class="name bold">\n{name}\n</div></div>'
    )
    if kind == "link":
        return (
            f'<a class="entry block_link clearfix" href="../chats/{folder}/messages.html#allow_back">'
            f"{body}</a>"
        )
    return f'<div class="entry clearfix">{body}</div>'


def _two_container_html(active: list, left: list) -> str:
    """A chats.html with the real two-section layout: active chats, then left."""
    a = "\n\n     ".join(_entry(*e) for e in active)
    l = "\n\n     ".join(_entry(*e) for e in left)
    return (
        "<html><body>\n   <div class=\"page_body list_page\">\n"
        '    <div class="page_about details">This page lists all chats.</div>\n'
        f'    <div class="entry_list">\n\n     {a}\n\n    </div>\n'
        '    <div class="page_about details">Left chats — you can rejoin later.</div>\n'
        f'    <div class="entry_list">\n\n     {l}\n\n    </div>\n'
        "   </div>\n  </body></html>\n"
    )


def _results_html(count: int) -> str:
    return (
        '<html><body><a class="section block_link chats" href="lists/chats.html#allow_back">'
        f'<div class="counter details">\n{count}\n</div><div class="label bold">Chats</div></a>'
        "</body></html>"
    )


def _names(html: str) -> list[str]:
    import re

    return [re.sub(r"\s+", " ", m).strip() for m in re.findall(r'<div class="name bold">\s*(.*?)\s*</div>', html, re.S)]


def _counter(html: str) -> int:
    return int(backup._RESULTS_COUNT_RE.search(html).group(2))


@pytest.fixture
def tail_export(tmp_path: Path) -> Path:
    """Export whose HTML tails mirror result.json: 2 active (Alice linked +
    CurrentGroup bare), 3 left (two same-named 'OldChannel' tombstones + a
    text-only 'SavedStuff')."""
    (tmp_path / "chats" / "chat_002" / "photos").mkdir(parents=True)
    (tmp_path / "chats" / "chat_002" / "photos" / "a.jpg").write_bytes(b"x" * 1000)
    (tmp_path / "lists").mkdir()
    data = {
        "chats": {"list": [
            {"id": 111, "name": "Alice", "type": "personal_chat",
             "messages": [_msg(1, "2024-01-01T00:00:00", "chats/chat_002/photos/a.jpg")]},
            {"id": 444, "name": "CurrentGroup", "type": "private_group", "messages": []},
        ]},
        "left_chats": {"list": [
            {"id": 333, "name": "OldChannel", "type": "public_channel", "messages": []},
            {"id": 555, "name": "OldChannel", "type": "public_channel", "messages": []},
            {"id": 666, "name": "SavedStuff", "type": "private_channel",
             "messages": [_msg(1, "2023-01-01T00:00:00")]},
        ]},
    }
    (tmp_path / "result.json").write_text(json.dumps(data), encoding="utf-8")
    (tmp_path / "lists" / "chats.html").write_text(
        _two_container_html(
            active=[("link", "Alice", "chat_002"), ("bare", "CurrentGroup", None)],
            left=[("bare", "OldChannel", None), ("bare", "OldChannel", None), ("bare", "SavedStuff", None)],
        ),
        encoding="utf-8",
    )
    (tmp_path / "export_results.html").write_text(_results_html(5), encoding="utf-8")
    return tmp_path


def test_delete_tombstones_cleans_html_tails(tail_export: Path):
    """Deleting the two same-named left tombstones removes exactly their rows
    (multiset) from the LEFT container, leaves active chats + SavedStuff intact,
    and decrements the export_results counter."""
    p = str(tail_export / "result.json")
    backup.delete_chats(p, ["333", "555"])

    html = (tail_export / "lists" / "chats.html").read_text(encoding="utf-8")
    assert _names(html) == ["Alice", "CurrentGroup", "SavedStuff"]  # both OldChannel gone, others kept
    assert html.count('class="entry block_link clearfix"') == 1  # Alice's link untouched
    assert _counter((tail_export / "export_results.html").read_text(encoding="utf-8")) == 3


def test_delete_active_cleans_linked_row(tail_export: Path):
    """Deleting an active chat strips its linked row from the active container
    (matched by folder) and decrements the counter."""
    p = str(tail_export / "result.json")
    backup.delete_chats(p, ["111"])
    html = (tail_export / "lists" / "chats.html").read_text(encoding="utf-8")
    assert "Alice" not in _names(html)
    assert _names(html) == ["CurrentGroup", "OldChannel", "OldChannel", "SavedStuff"]
    assert _counter((tail_export / "export_results.html").read_text(encoding="utf-8")) == 4


def test_html_tails_restore_roundtrip(tail_export: Path):
    """Restore returns removed rows (to their own container) and the counter."""
    p = str(tail_export / "result.json")
    before_names = sorted(_names((tail_export / "lists" / "chats.html").read_text(encoding="utf-8")))
    res = backup.delete_chats(p, ["333", "555"])
    backup.restore(p, res["trash_id"])

    html = (tail_export / "lists" / "chats.html").read_text(encoding="utf-8")
    assert sorted(_names(html)) == before_names
    assert _counter((tail_export / "export_results.html").read_text(encoding="utf-8")) == 5
    # restored rows land back in the left container (after its opener)
    left_seg = html[backup._container_opens(html)[1]:]
    assert left_seg.count("OldChannel") == 2


def test_html_tails_noop_without_html(export_dir: Path):
    """A JSON-only export (no chats.html / export_results.html) deletes cleanly,
    storing no HTML manifest data."""
    p = str(export_dir / "result.json")
    res = backup.delete_chats(p, ["333"])
    entry = next(e for e in backup._load_manifest(export_dir)["entries"] if e["id"] == res["trash_id"])
    assert entry["html"] == {}


# API layer

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)


def test_api_backup_chats(export_dir: Path):
    r = client.get("/api/backup/chats", params={"path": str(export_dir / "result.json")})
    assert r.status_code == 200
    body = r.json()
    assert body["can_manage"] is True and body["is_full"] is True
    assert len(body["chats"]) == 3


def test_api_delete_restore(export_dir: Path):
    p = str(export_dir / "result.json")
    r = client.post("/api/backup/delete", json={"path": p, "chat_ids": ["111"]})
    assert r.status_code == 200 and r.json()["bytes"] == 6000
    assert len(client.get("/api/backup/chats", params={"path": p}).json()["chats"]) == 2
    tid = client.get("/api/backup/trash", params={"path": p}).json()["entries"][0]["id"]
    assert client.post("/api/backup/restore", json={"path": p, "trash_id": tid}).status_code == 200
    assert len(client.get("/api/backup/chats", params={"path": p}).json()["chats"]) == 3


def test_api_delete_blocked_for_lone_json(tmp_path: Path):
    lone = tmp_path / "result.json"
    lone.write_text(json.dumps({"chats": {"list": []}}), encoding="utf-8")
    r = client.post("/api/backup/delete", json={"path": str(lone), "chat_ids": ["1"]})
    assert r.status_code == 400
    assert r.json()["detail"] == "not-manageable"
