"""Sticker preferences per user — as images, not just emoji tags.

Telegram desktop export keeps the actual sticker FILE per message (`file` and
`thumbnail`, relative to the export root) even though the original pack name is
anonymised. So a user's *favourite stickers* are recoverable as pictures: the
same sticker reuses the same `file`, so we group sends by file path, count them,
and carry the thumbnail for the UI to render. (The image only resolves when the
chat was loaded from the export folder — an uploaded copy of `result.json` alone
has no media; the API serves the file separately, see /api/sticker-file.)

We also keep the per-emoji rollup (`sticker_emoji`) as a lightweight fallback
signal for when the files aren't available.

Pure functions; no UI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class StickerRef:
    file: str       # relative path from export root, e.g. chats/chat_009/stickers/sticker (1).webp
    thumbnail: str  # relative path to the .jpg preview (universal render target)
    emoji: str      # the emoji Telegram tagged this sticker with
    count: int      # how many times this exact sticker was sent


@dataclass
class UserStickers:
    user_id: str
    name: str
    total_stickers: int = 0
    top_emojis: list[tuple[str, int]] = field(default_factory=list)
    top_stickers: list[StickerRef] = field(default_factory=list)


@dataclass
class StickerStats:
    per_user: dict[str, UserStickers] = field(default_factory=dict)
    chat_total: int = 0
    chat_top_stickers: list[StickerRef] = field(default_factory=list)


def analyze(messages: list[dict], top_n: int = 12) -> StickerStats:
    per_user_emoji: dict[str, Counter] = {}
    per_user_file: dict[str, Counter] = {}
    chat_file: Counter = Counter()
    # one representative (thumbnail, emoji) per file path — same file ⇒ same sticker
    file_meta: dict[str, tuple[str, str]] = {}
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
        per_user_emoji.setdefault(uid, Counter())[emoji] += 1
        chat_total += 1

        f = m.get("file")
        if isinstance(f, str) and f:
            per_user_file.setdefault(uid, Counter())[f] += 1
            chat_file[f] += 1
            if f not in file_meta:
                thumb = m.get("thumbnail")
                file_meta[f] = (thumb if isinstance(thumb, str) else "", emoji)

    def refs(counter: Counter, n: int) -> list[StickerRef]:
        out: list[StickerRef] = []
        for f, c in counter.most_common(n):
            thumb, emoji = file_meta.get(f, ("", "?"))
            out.append(StickerRef(file=f, thumbnail=thumb, emoji=emoji, count=c))
        return out

    per_user: dict[str, UserStickers] = {}
    for uid, ec in per_user_emoji.items():
        per_user[uid] = UserStickers(
            user_id=uid,
            name=names.get(uid, uid),
            total_stickers=sum(ec.values()),
            top_emojis=ec.most_common(top_n),
            top_stickers=refs(per_user_file.get(uid, Counter()), top_n),
        )
    return StickerStats(
        per_user=per_user,
        chat_total=chat_total,
        chat_top_stickers=refs(chat_file, top_n),
    )
