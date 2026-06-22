"""Emoji usage analytics. Pure functions over message lists."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

import emoji as _emoji
import jmespath

from .utils import display_name


@dataclass
class EmojiStats:
    chat_top: list[tuple[str, int]]  # [(emoji, count)] desc
    per_user: dict[str, list[tuple[str, int]]]  # user_id -> top emojis
    user_names: dict[str, str]
    total_emojis: int
    messages_with_emoji: int


def _emojis_in(text: str) -> list[str]:
    """Extract emoji characters from a text string. Returns a list (order preserved,
    duplicates allowed)."""
    if not isinstance(text, str) or not text:
        return []
    try:
        return [d["emoji"] for d in _emoji.emoji_list(text)]
    except Exception:
        return []


def _walk_text(message) -> list[str]:
    """Pull text fragments out of a message, including text_entities and caption."""
    out: list[str] = []
    if isinstance(message, dict):
        t = message.get("text")
        if isinstance(t, str):
            out.append(t)
        elif isinstance(t, list):
            for item in t:
                if isinstance(item, str):
                    out.append(item)
                elif isinstance(item, dict) and "text" in item:
                    out.append(item.get("text") or "")
        c = message.get("caption")
        if isinstance(c, str):
            out.append(c)
        ents = jmespath.search("text_entities[*].text", message)
        if ents:
            out.extend(e for e in ents if isinstance(e, str))
    return out


def analyze(messages: list[dict], top_per_user: int = 20) -> EmojiStats:
    chat_counter: Counter[str] = Counter()
    per_user_counter: dict[str, Counter[str]] = defaultdict(Counter)
    user_names: dict[str, str] = {}
    total = 0
    msgs_with = 0

    for m in messages:
        if not isinstance(m, dict):
            continue
        user = m.get("from_id") or m.get("actor_id")
        if user is None:
            continue
        user = str(user)
        if user not in user_names:
            user_names[user] = display_name(m.get("from"), user)

        found_in_msg = False
        for fragment in _walk_text(m):
            for e in _emojis_in(fragment):
                chat_counter[e] += 1
                per_user_counter[user][e] += 1
                total += 1
                found_in_msg = True
        if found_in_msg:
            msgs_with += 1

    per_user = {uid: c.most_common(top_per_user) for uid, c in per_user_counter.items()}
    return EmojiStats(
        chat_top=chat_counter.most_common(top_per_user * 2),
        per_user=per_user,
        user_names=user_names,
        total_emojis=total,
        messages_with_emoji=msgs_with,
    )
