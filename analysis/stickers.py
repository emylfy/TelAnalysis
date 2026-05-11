"""Sticker-emoji preferences per user.

Telegram desktop export anonymises sticker filenames (`chats/chat_NNN/
stickers/sticker.webp`) so the original sticker pack is unrecoverable from
the JSON. The `sticker_emoji` field, however, IS preserved per message and
captures the emotional tone each sticker carries — which is what people
actually mean when they say "your favorite stickers".

So we group stickers by their assigned emoji, per user. "Use stickers
mostly tagged 🤡" is still a strong personal-style signal.

Pure functions; no UI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class UserStickers:
    user_id: str
    name: str
    total_stickers: int = 0
    top_emojis: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class StickerStats:
    per_user: dict[str, UserStickers] = field(default_factory=dict)
    chat_total: int = 0


def analyze(messages: list[dict], top_n: int = 10) -> StickerStats:
    per_user_counter: dict[str, Counter] = {}
    names: dict[str, str] = {}
    chat_total = 0

    for m in messages:
        if not isinstance(m, dict):
            continue
        if m.get("media_type") != "sticker":
            continue
        uid = m.get("from_id")
        if not uid:
            continue
        uid = str(uid).replace(" ", "")
        names.setdefault(uid, m.get("from") or uid)
        emoji = m.get("sticker_emoji") or "?"
        per_user_counter.setdefault(uid, Counter())[emoji] += 1
        chat_total += 1

    per_user: dict[str, UserStickers] = {}
    for uid, counter in per_user_counter.items():
        per_user[uid] = UserStickers(
            user_id=uid,
            name=names.get(uid, uid),
            total_stickers=sum(counter.values()),
            top_emojis=counter.most_common(top_n),
        )
    return StickerStats(per_user=per_user, chat_total=chat_total)
