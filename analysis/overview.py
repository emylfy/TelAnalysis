"""KPIs and timeline data for the Overview tab.

All functions take a list of message dicts (Telegram export shape) and
return primitive structures the API serialises to JSON. No UI.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from .utils import display_name


@dataclass
class Kpis:
    total_messages: int
    unique_users: int
    first_date: str | None
    last_date: str | None
    days_active: int  # calendar span first→last (used by the hero prose)
    active_days: int  # distinct days that actually have ≥1 message
    media_messages: int


def _parse_date(s: str) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def compute_kpis(messages: list[dict]) -> Kpis:
    total = len(messages)
    users = set()
    active_dates: set[str] = set()
    media = 0
    first = None
    last = None
    for m in messages:
        if not isinstance(m, dict):
            continue
        if any(k in m for k in ("photo", "file", "media_type", "voice_message")):
            media += 1
        uid = m.get("from_id") or m.get("actor_id")
        if uid:
            users.add(uid)
        d = _parse_date(m.get("date"))
        if d:
            active_dates.add(d.strftime("%Y-%m-%d"))
            if first is None or d < first:
                first = d
            if last is None or d > last:
                last = d
    days_active = 0
    if first and last:
        days_active = (last.date() - first.date()).days + 1
    return Kpis(
        total_messages=total,
        unique_users=len(users),
        first_date=first.strftime("%Y-%m-%d") if first else None,
        last_date=last.strftime("%Y-%m-%d") if last else None,
        days_active=days_active,
        active_days=len(active_dates),
        media_messages=media,
    )


def messages_per_day(messages: list[dict]) -> list[tuple[str, int]]:
    """Return [(YYYY-MM-DD, count)] sorted ascending."""
    counts: Counter[str] = Counter()
    for m in messages:
        if not isinstance(m, dict):
            continue
        d = _parse_date(m.get("date"))
        if d:
            counts[d.strftime("%Y-%m-%d")] += 1
    return sorted(counts.items())


def hour_weekday_heatmap(messages: list[dict]) -> list[list[int]]:
    """Return a 7×24 matrix [weekday][hour] of message counts.
    Weekdays: 0 = Monday … 6 = Sunday."""
    grid = [[0] * 24 for _ in range(7)]
    for m in messages:
        if not isinstance(m, dict):
            continue
        d = _parse_date(m.get("date"))
        if d is None:
            continue
        grid[d.weekday()][d.hour] += 1
    return grid


def hour_distribution_per_user(
    messages: list[dict],
) -> dict[str, tuple[str, list[int]]]:
    """For each user_id, return (display_name, [counts by hour 0..23])."""
    out: dict[str, tuple[str, list[int]]] = {}
    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            continue
        d = _parse_date(m.get("date"))
        if d is None:
            continue
        if uid not in out:
            name = display_name(m.get("from"), uid)
            out[uid] = (name, [0] * 24)
        out[uid][1][d.hour] += 1
    return out


def date_bounds(messages: list[dict]) -> tuple[str, str] | None:
    """Min/max dated message timestamps as ISO strings, or None if no dated msgs."""
    first = None
    last = None
    for m in messages:
        if not isinstance(m, dict):
            continue
        d = _parse_date(m.get("date"))
        if d is None:
            continue
        if first is None or d < first:
            first = d
        if last is None or d > last:
            last = d
    if first is None:
        return None
    return first.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")


def filter_by_date(messages: list[dict], from_date: str, to_date: str) -> list[dict]:
    """Keep messages with date in [from_date, to_date]. Date strings YYYY-MM-DD.
    Undated messages (rare service events) are kept."""
    out = []
    for m in messages:
        if not isinstance(m, dict):
            out.append(m)
            continue
        d = _parse_date(m.get("date"))
        if d is None:
            out.append(m)
            continue
        ds = d.strftime("%Y-%m-%d")
        if from_date <= ds <= to_date:
            out.append(m)
    return out
