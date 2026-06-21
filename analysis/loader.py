"""Telegram export loader.

Two JSON shapes are supported:
- Single-chat export: top-level dict with `name`, `type`, `messages`.
- Full archive export: top-level `chats.list[*]` of chats.

HTML exports (Telegram Desktop "Export chat history" → HTML) are also accepted
via `analysis.html_loader`; `load_export` dispatches on path/extension. HTML is
lossier than JSON (see html_loader docstring) — the resulting dict carries a
`_source` marker so the UI can warn.

Loaders return a list of `Chat` records normalised to single-chat shape so
the rest of the pipeline doesn't care which export it came from.
"""

from __future__ import annotations

import glob
import json
import os
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
    with open(path, encoding="utf-8", errors="replace") as f:
        return json.load(f)


def load_export(path: str) -> dict:
    """Load a Telegram export (JSON or HTML) into single-export dict shape.

    Dispatch:
    - directory → prefer `result.json`, else fall back to `messages*.html`;
    - `.html`/`.htm` file → HTML loader;
    - anything else → JSON loader.

    HTML results carry `_source == "html"`; JSON results have no `_source`.
    """
    # Imported lazily so the JSON path doesn't pull in the HTML parser.
    from analysis import html_loader

    if os.path.isdir(path):
        json_in_dir = os.path.join(path, "result.json")
        if os.path.exists(json_in_dir):
            return load_json(json_in_dir)
        if glob.glob(os.path.join(path, "messages*.html")):
            return html_loader.parse_html_export(path)
        raise FileNotFoundError(f"no result.json or messages*.html in {path}")

    if os.path.splitext(path)[1].lower() in (".html", ".htm"):
        return html_loader.parse_html_export(path)
    return load_json(path)


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


def combined_chat(chats: list[Chat]) -> Chat:
    """Synthesize a virtual chat from concatenated messages of all input chats.
    Used for the 'Analyse all chats' aggregate view in full-archive exports."""
    all_msgs: list = []
    for c in chats:
        all_msgs.extend(c.messages)
    return Chat(
        id="all",
        name=f"All chats (combined, {len(chats)})",
        type="multichat",
        messages=all_msgs,
    )


# Telegram chat type → which dashboard sections make sense.
# Keep this conservative: missing keys default to "show everything".
_DASHBOARD_BY_TYPE = {
    # 1-on-1 chat: the reply graph is always 2 nodes / 1 edge (meaningless),
    # and reply reciprocity already lives in the per-user tab — so no "graph".
    "personal_chat": {"overview", "words", "perusers", "highlights"},
    "private_group": {"overview", "graph", "words", "perusers", "highlights"},
    "private_supergroup": {"overview", "graph", "words", "perusers", "highlights"},
    "public_supergroup": {"overview", "graph", "words", "perusers", "highlights"},
    "private_channel": {"overview", "channel", "highlights"},
    "public_channel": {"overview", "channel", "highlights"},
    "saved_messages": {"overview", "words", "highlights"},
    "bot_chat": {"overview", "words", "perusers", "highlights"},
    # Synthetic combined-archive view: graph and perusers don't make sense
    # because participants come from disjoint chats.
    "multichat": {"overview", "words", "highlights"},
}


def sections_for_type(chat_type: str) -> set[str]:
    """Which dashboard tabs apply to this chat type."""
    return _DASHBOARD_BY_TYPE.get(
        chat_type,
        {"overview", "graph", "words", "channel", "perusers", "highlights"},
    )
