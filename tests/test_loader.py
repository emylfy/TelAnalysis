"""Tests for analysis.loader: export-shape detection and chat enumeration."""

from __future__ import annotations

import json
from pathlib import Path

from analysis import loader

SINGLE_CHAT = {
    "name": "Alice",
    "type": "personal_chat",
    "id": 12345,
    "messages": [
        {"id": 1, "type": "message", "from": "Bob", "text": "hi"},
        {"id": 2, "type": "message", "from": "Alice", "text": "hello"},
    ],
}

FULL_EXPORT = {
    "about": "telegram archive",
    "chats": {
        "list": [
            {
                "name": "Alice",
                "type": "personal_chat",
                "id": 1,
                "messages": [{"id": 1, "type": "message", "text": "x"}],
            },
            {
                "name": None,
                "type": "saved_messages",
                "id": 2,
                "messages": [],
            },
            {
                "name": "Group",
                "type": "private_supergroup",
                "id": 3,
                "messages": [{"id": 1}, {"id": 2}, {"id": 3}],
            },
        ]
    },
}


def test_is_full_export_true():
    assert loader.is_full_export(FULL_EXPORT) is True


def test_is_full_export_false_on_single():
    assert loader.is_full_export(SINGLE_CHAT) is False


def test_is_full_export_false_on_garbage():
    assert loader.is_full_export({}) is False
    assert loader.is_full_export({"chats": []}) is False
    assert loader.is_full_export({"chats": {"list": "nope"}}) is False


def test_list_chats_single_returns_one():
    chats = loader.list_chats(SINGLE_CHAT)
    assert len(chats) == 1
    assert chats[0].name == "Alice"
    assert chats[0].type == "personal_chat"
    assert len(chats[0].messages) == 2


def test_list_chats_full_returns_all():
    chats = loader.list_chats(FULL_EXPORT)
    assert len(chats) == 3
    # Saved Messages fallback name when name is null
    assert chats[1].name == "Saved Messages"
    assert chats[2].type == "private_supergroup"


def test_combined_chat_concatenates_messages():
    chats = loader.list_chats(FULL_EXPORT)
    combined = loader.combined_chat(chats)
    assert combined.id == "all"
    assert combined.type == "multichat"
    assert len(combined.messages) == 1 + 0 + 3


def test_sections_for_personal_chat():
    sections = loader.sections_for_type("personal_chat")
    # 1-on-1: no network graph (trivial 2-node), but core tabs stay.
    assert "graph" not in sections
    assert "channel" not in sections
    assert {"overview", "words", "perusers", "highlights"} <= sections


def test_sections_for_channel():
    sections = loader.sections_for_type("public_channel")
    assert "channel" in sections
    assert "graph" not in sections
    assert "perusers" not in sections


def test_sections_for_unknown_type_returns_all():
    """Unknown chat types should default to showing every section."""
    sections = loader.sections_for_type("some_future_type")
    assert {"overview", "graph", "words", "channel", "perusers", "highlights"} <= sections


def test_chat_label_format():
    chat = loader.Chat(id=1, name="Alice", type="personal_chat", messages=[{}, {}])
    label = loader.chat_label(chat)
    assert "Alice" in label
    assert "personal_chat" in label
    assert "2" in label


def test_load_json_roundtrip(tmp_path: Path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps(SINGLE_CHAT), encoding="utf-8")
    data = loader.load_json(str(p))
    assert data["name"] == "Alice"
    assert len(data["messages"]) == 2
