"""Timing-based analytics: streaks, silences, conversation initiators."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .utils import display_name


@dataclass
class StreakStats:
    longest_streak_days: int
    longest_streak_start: str | None  # YYYY-MM-DD
    longest_streak_end: str | None
    current_streak_days: int  # ending at last message date
    total_active_days: int
    longest_silences: list[tuple[str, str, int]]  # (gap_start, gap_end, days)


@dataclass
class InitiatorRow:
    user_id: str
    name: str
    initiations: int
    share: float


@dataclass
class InitiatorStats:
    gap_hours: int
    rows: list[InitiatorRow] = field(default_factory=list)
    total_initiations: int = 0


def _parse(s) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _unique_dates(messages: list[dict], filter_uid: str | None = None) -> list[date]:
    out: set[date] = set()
    for m in messages:
        if not isinstance(m, dict):
            continue
        if filter_uid is not None and m.get("from_id") != filter_uid:
            continue
        d = _parse(m.get("date"))
        if d is not None:
            out.add(d.date())
    return sorted(out)


def streaks_and_silences(
    messages: list[dict],
    filter_uid: str | None = None,
    top_silences: int = 5,
) -> StreakStats:
    """Find longest streak of consecutive active days, current streak, and the
    longest silences (gaps between active days).

    `filter_uid` restricts to one user's messages."""
    dates = _unique_dates(messages, filter_uid=filter_uid)
    if not dates:
        return StreakStats(0, None, None, 0, 0, [])

    # Walk the sorted list, group runs of consecutive days.
    runs: list[tuple[date, date, int]] = []  # (start, end, length)
    run_start = dates[0]
    run_end = dates[0]
    for d in dates[1:]:
        if d == run_end + timedelta(days=1):
            run_end = d
        else:
            runs.append((run_start, run_end, (run_end - run_start).days + 1))
            run_start = d
            run_end = d
    runs.append((run_start, run_end, (run_end - run_start).days + 1))

    longest = max(runs, key=lambda r: r[2])
    current = runs[-1]

    # Silences = gaps between consecutive runs
    silences: list[tuple[date, date, int]] = []
    for i in range(len(runs) - 1):
        gap_start = runs[i][1] + timedelta(days=1)
        gap_end = runs[i + 1][0] - timedelta(days=1)
        gap_days = (gap_end - gap_start).days + 1
        if gap_days > 0:
            silences.append((gap_start, gap_end, gap_days))
    silences.sort(key=lambda s: -s[2])
    top = [(s.isoformat(), e.isoformat(), n) for s, e, n in silences[:top_silences]]

    return StreakStats(
        longest_streak_days=longest[2],
        longest_streak_start=longest[0].isoformat(),
        longest_streak_end=longest[1].isoformat(),
        current_streak_days=current[2],
        total_active_days=len(dates),
        longest_silences=top,
    )


def conversation_initiators(
    messages: list[dict],
    gap_hours: int = 4,
) -> InitiatorStats:
    """For every gap > `gap_hours` between consecutive messages, attribute the
    next message to its sender as a conversation initiation."""
    if not messages:
        return InitiatorStats(gap_hours=gap_hours)

    # Build (timestamp, from_id, name) sorted by timestamp.
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

    if len(rows) < 2:
        return InitiatorStats(gap_hours=gap_hours)

    gap_seconds = gap_hours * 3600
    counts: Counter = Counter()
    names: dict[str, str] = {}
    # First message also counts as an initiation.
    counts[rows[0][1]] += 1
    names[rows[0][1]] = rows[0][2]
    for i in range(1, len(rows)):
        prev_ts, _, _ = rows[i - 1]
        ts, uid, name = rows[i]
        if (ts - prev_ts).total_seconds() >= gap_seconds:
            counts[uid] += 1
            names.setdefault(uid, name)

    total = sum(counts.values())
    out_rows = [
        InitiatorRow(
            user_id=uid,
            name=names.get(uid, uid),
            initiations=n,
            share=n / total if total else 0.0,
        )
        for uid, n in counts.most_common()
    ]
    return InitiatorStats(gap_hours=gap_hours, rows=out_rows, total_initiations=total)
