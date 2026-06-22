"""Response reciprocity for 1-1 chats — directional response time stats.

For consecutive (msg_a, msg_b) pairs from different users, attribute the time
delta as a 'response by user_b to user_a'. Then compute share answered within
5 / 30 / 60 minutes per direction. This is a much fairer engagement metric
than the chat-wide reply-latency histogram, because it splits "you answer me"
from "I answer you"."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from .utils import display_name


@dataclass
class DirectionStats:
    responder_id: str
    responder_name: str
    initiator_id: str
    initiator_name: str
    median_seconds: float
    p90_seconds: float
    within_5m: float  # share answered within 5 minutes
    within_30m: float
    within_60m: float


@dataclass
class ReciprocityResult:
    available: bool  # only computed for exactly 2 distinct senders
    a_to_b: DirectionStats | None = None  # b answered after a
    b_to_a: DirectionStats | None = None  # a answered after b


def _parse(s) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def compute(messages: list[dict], cap_hours: int = 24) -> ReciprocityResult:
    """Compute per-direction response stats. Only meaningful for 2-user chats —
    returns available=False otherwise."""
    rows: list[tuple[datetime, str, str]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            continue
        ts = _parse(m.get("date"))
        if ts is None:
            continue
        rows.append((ts, str(uid), display_name(m.get("from"), uid)))
    rows.sort(key=lambda r: r[0])

    distinct = sorted({uid for _, uid, _ in rows})
    if len(distinct) != 2 or len(rows) < 2:
        return ReciprocityResult(available=False)

    cap_seconds = cap_hours * 3600
    by_dir: dict[tuple[str, str], list[int]] = defaultdict(list)
    name_of: dict[str, str] = {}
    for ts, uid, name in rows:
        name_of.setdefault(uid, name)

    for i in range(1, len(rows)):
        prev_ts, prev_uid, _ = rows[i - 1]
        ts, uid, _ = rows[i]
        if uid == prev_uid:
            continue
        delta = int((ts - prev_ts).total_seconds())
        if delta < 0 or delta > cap_seconds:
            continue
        by_dir[(prev_uid, uid)].append(delta)

    def stats(initiator_id: str, responder_id: str) -> DirectionStats | None:
        seq = by_dir.get((initiator_id, responder_id))
        if not seq:
            return None
        sorted_seq = sorted(seq)
        n = len(sorted_seq)
        med = sorted_seq[n // 2]
        p90 = sorted_seq[int(n * 0.9)] if n > 1 else sorted_seq[0]
        within = lambda thresh_s: sum(1 for x in sorted_seq if x <= thresh_s) / n
        return DirectionStats(
            responder_id=responder_id,
            responder_name=name_of.get(responder_id, responder_id),
            initiator_id=initiator_id,
            initiator_name=name_of.get(initiator_id, initiator_id),
            median_seconds=float(med),
            p90_seconds=float(p90),
            within_5m=within(5 * 60),
            within_30m=within(30 * 60),
            within_60m=within(60 * 60),
        )

    a, b = distinct
    return ReciprocityResult(
        available=True,
        a_to_b=stats(a, b),
        b_to_a=stats(b, a),
    )
