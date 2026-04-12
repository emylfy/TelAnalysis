"""Telegram export JSON loader.

Two shapes are supported:
- Single-chat export: top-level dict with `name`, `type`, `messages`.
- Full archive export: top-level `chats.list[*]` of chats.

Loaders return a list of `Chat` records normalised to single-chat shape so
the rest of the pipeline doesn't care which export it came from.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class Chat:
    id: Any
    name: str
    type: str
    messages: list


def is_full_export(data: dict) -> bool:
    return (
        isinstance(data, dict)
        and isinstance(data.get("chats"), dict)
        and isinstance(data["chats"].get("list"), list)
    )


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def list_chats(data: dict) -> list[Chat]:
    """Return all chats in the export as a flat list of Chat records.

    Single-chat export → 1-element list.
    Full export → all chats from `chats.list`.
    """
    if is_full_export(data):
        out = []
        for ch in data["chats"]["list"]:
            out.append(
                Chat(
                    id=ch.get("id"),
                    name=ch.get("name") or "Saved Messages",
                    type=ch.get("type") or "?",
                    messages=ch.get("messages") or [],
                )
            )
        return out
    return [
        Chat(
            id=data.get("id"),
            name=data.get("name") or "Chat",
            type=data.get("type") or "?",
            messages=data.get("messages") or [],
        )
    ]


def chat_label(chat: Chat) -> str:
    return f"{chat.name} [{chat.type}] · {len(chat.messages):,} msgs"


# Telegram chat type → which dashboard sections make sense.
# Keep this conservative: missing keys default to "show everything".
_DASHBOARD_BY_TYPE = {
    "personal_chat": {"overview", "graph", "words", "perusers"},
    "private_group": {"overview", "graph", "words", "perusers"},
    "private_supergroup": {"overview", "graph", "words", "perusers"},
    "public_supergroup": {"overview", "graph", "words", "perusers"},
    "private_channel": {"overview", "channel"},
    "public_channel": {"overview", "channel"},
    "saved_messages": {"overview", "words"},
    "bot_chat": {"overview", "words", "perusers"},
}


def sections_for_type(chat_type: str) -> set[str]:
    """Which dashboard tabs apply to this chat type."""
    return _DASHBOARD_BY_TYPE.get(
        chat_type, {"overview", "graph", "words", "channel", "perusers"}
    )
