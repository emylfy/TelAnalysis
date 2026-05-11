"""Forwards-vs-original ratio per user.

Telegram exports tag re-shared messages with `forwarded_from`. Surfacing
this separates "I share other people's takes" from "I post my own thoughts" —
a useful behavioural signal that the raw text analyses miss.

Pure functions; no UI."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field


@dataclass
class UserForwards:
    user_id: str
    name: str
    total_messages: int
    forwarded_count: int
    top_sources: list[tuple[str, int]] = field(default_factory=list)

    @property
    def forwarded_ratio(self) -> float:
        return self.forwarded_count / self.total_messages if self.total_messages else 0.0


@dataclass
class ForwardsStats:
    per_user: dict[str, UserForwards] = field(default_factory=dict)
    chat_total_messages: int = 0
    chat_forwarded_count: int = 0

    @property
    def chat_ratio(self) -> float:
        if not self.chat_total_messages:
            return 0.0
        return self.chat_forwarded_count / self.chat_total_messages


def analyze(messages: list[dict], top_sources: int = 5) -> ForwardsStats:
    counts: dict[str, int] = defaultdict(int)
    forwards: dict[str, int] = defaultdict(int)
    sources: dict[str, Counter] = defaultdict(Counter)
    names: dict[str, str] = {}

    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            continue
        uid = str(uid).replace(" ", "")
        names.setdefault(uid, m.get("from") or uid)
        counts[uid] += 1
        src = m.get("forwarded_from")
        if isinstance(src, str) and src.strip():
            forwards[uid] += 1
            sources[uid][src.strip()] += 1

    per_user: dict[str, UserForwards] = {}
    for uid, total in counts.items():
        per_user[uid] = UserForwards(
            user_id=uid,
            name=names.get(uid, uid),
            total_messages=total,
            forwarded_count=forwards.get(uid, 0),
            top_sources=sources[uid].most_common(top_sources),
        )

    return ForwardsStats(
        per_user=per_user,
        chat_total_messages=sum(counts.values()),
        chat_forwarded_count=sum(forwards.values()),
    )
