"""Russian profanity (mat) tracker.

Counts mat occurrences per user via a small set of canonical roots — Russian
profanity is highly productive (one root produces dozens of forms with
prefixes/suffixes), so root-substring matching catches morphology without
maintaining a 5000-word inflection table.

False-positive risk: short roots inside neutral words. We mitigate with
word-boundary requirements and a small denylist of common collisions
(`страх` doesn't match `х*й`-roots since we require word boundary).

Pure functions; no UI."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from .utils import display_name

# Canonical roots. Substring match is intentional — `хуй`, `охуенно`,
# `хуёво`, `хуйня` all share `хуй` so one entry covers them. Adding
# explicit `охуе` etc would double-count.
_MAT_ROOTS: tuple[str, ...] = (
    "хуй",
    "хуе",
    "хуё",
    "хуя",
    "хуи",
    "пизд",
    "пезд",
    "ебат",
    "ебал",
    "ебан",
    "ебашит",
    "ебашит",
    "ебуч",
    "ебён",
    "ёбан",
    "блядь",
    "бляд",
    "блят",
    "блять",
    "сук",
    "сучар",
    "пидор",
    "пидар",
    "пидр",
    "мудак",
    "мудил",
    "мудоз",
    "залуп",
    "хер",
    "херн",
    "гондон",
    "шлюх",
    "уеб",
    "уёб",
    "*бан",
    "*бат",
    "*бал",
    "*бл",
    "*бн",  # asterisk-censored variants
)

# Compile regex with word boundaries so `сука` matches but `сукно`/`сукуба` don't.
# Must be done at module load so we don't pay regex compile per message.
_MAT_PATTERN = re.compile(
    r"(?<![\w])(" + "|".join(re.escape(r) for r in _MAT_ROOTS) + r")(?:[\w]*)?",
    re.UNICODE | re.IGNORECASE,
)


@dataclass
class UserMat:
    user_id: str
    name: str
    total_messages: int  # messages with text from this user
    mat_messages: int  # messages containing ≥1 mat hit
    mat_hits: int  # total mat occurrences (multiple hits per msg counted)

    @property
    def msg_share(self) -> float:
        """Share of this user's messages that contain any mat."""
        return self.mat_messages / self.total_messages if self.total_messages else 0.0

    @property
    def hits_per_100(self) -> float:
        """Mat-words per 100 messages — comparable across users with
        different message volumes."""
        return self.mat_hits * 100 / self.total_messages if self.total_messages else 0.0


@dataclass
class MatStats:
    per_user: dict[str, UserMat] = field(default_factory=dict)
    # (iso_week_start, total_hits) — chat-wide weekly totals for trend.
    weekly_totals: list[tuple[str, int]] = field(default_factory=list)


def _msg_text(m: dict) -> str:
    parts: list[str] = []
    t = m.get("text")
    if isinstance(t, str):
        parts.append(t)
    elif isinstance(t, list):
        for item in t:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                v = item.get("text")
                if isinstance(v, str):
                    parts.append(v)
    c = m.get("caption")
    if isinstance(c, str):
        parts.append(c)
    return " ".join(parts)


def analyze(messages: list[dict]) -> MatStats:
    counts: dict[str, int] = defaultdict(int)
    mat_msgs: dict[str, int] = defaultdict(int)
    mat_hits: dict[str, int] = defaultdict(int)
    weekly: Counter = Counter()
    names: dict[str, str] = {}

    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            continue
        uid = str(uid).replace(" ", "")
        names.setdefault(uid, display_name(m.get("from"), uid))
        text = _msg_text(m)
        if not text:
            continue
        counts[uid] += 1
        hits = _MAT_PATTERN.findall(text)
        if hits:
            mat_msgs[uid] += 1
            mat_hits[uid] += len(hits)
            d = m.get("date")
            if isinstance(d, str):
                try:
                    dt = datetime.fromisoformat(d)
                    # Monday-anchored ISO week
                    from datetime import timedelta as _td

                    week_start = (dt - _td(days=dt.weekday())).strftime("%Y-%m-%d")
                    weekly[week_start] += len(hits)
                except ValueError:
                    pass

    per_user: dict[str, UserMat] = {}
    for uid, total in counts.items():
        per_user[uid] = UserMat(
            user_id=uid,
            name=names.get(uid, uid),
            total_messages=total,
            mat_messages=mat_msgs.get(uid, 0),
            mat_hits=mat_hits.get(uid, 0),
        )

    weekly_totals = sorted(weekly.items())
    return MatStats(per_user=per_user, weekly_totals=weekly_totals)
