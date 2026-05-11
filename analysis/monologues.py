"""Longest monologue runs — N+ consecutive messages from one user with no
reply from anyone else in between.

Distinguishes "storytelling / venting" episodes (one person dumps a long
chain) from balanced back-and-forth. Walks the message list in chronological
order and groups by `from_id`-runs.

Pure functions; no UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Monologue:
    user_id: str
    name: str
    msg_count: int
    start: datetime
    end: datetime

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds()


@dataclass
class MonologueStats:
    longest: list[Monologue] = field(default_factory=list)
    per_user_longest: dict[str, Monologue] = field(default_factory=dict)


def _parse(s) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def analyze(
    messages: list[dict],
    top_n: int = 10,
    min_run: int = 3,
) -> MonologueStats:
    """Walk messages in time order; close a run whenever from_id changes.

    Only runs of `min_run` messages or more qualify. Returns the top_n
    longest runs across all users plus the per-user record-holder run.
    """
    rows: list[tuple[datetime, str, str, dict]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            continue
        ts = _parse(m.get("date"))
        if ts is None:
            continue
        rows.append((ts, str(uid), m.get("from") or str(uid), m))
    rows.sort(key=lambda r: r[0])

    if not rows:
        return MonologueStats()

    runs: list[Monologue] = []
    cur_uid = rows[0][1]
    cur_name = rows[0][2]
    cur_start = rows[0][0]
    cur_end = rows[0][0]
    cur_count = 1

    def _flush():
        if cur_count >= min_run:
            runs.append(
                Monologue(
                    user_id=cur_uid,
                    name=cur_name,
                    msg_count=cur_count,
                    start=cur_start,
                    end=cur_end,
                )
            )

    for ts, uid, name, _m in rows[1:]:
        if uid == cur_uid:
            cur_count += 1
            cur_end = ts
        else:
            _flush()
            cur_uid = uid
            cur_name = name
            cur_start = ts
            cur_end = ts
            cur_count = 1
    _flush()

    runs.sort(key=lambda r: -r.msg_count)
    longest = runs[:top_n]

    per_user_longest: dict[str, Monologue] = {}
    for r in runs:
        if r.user_id not in per_user_longest:
            per_user_longest[r.user_id] = r

    return MonologueStats(longest=longest, per_user_longest=per_user_longest)
