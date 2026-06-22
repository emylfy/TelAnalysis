"""Milestone & anniversary detection.

Walks the per-day timeline, finds the date when each cumulative-message
threshold (10k, 25k, 50k, ...) was crossed, and reports days-since-start
plus next upcoming time/count milestone. Pure functions, no IO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

import i18n

# Milestone thresholds — picked to feel like real anniversaries, not
# arbitrary round numbers. Anything bigger than 1M won't trigger for
# normal personal chats; cheap to keep as headroom.
_DAY_MILESTONES = [100, 365, 500, 730, 1000, 1825, 3650]
_COUNT_MILESTONES = [
    1_000,
    5_000,
    10_000,
    25_000,
    50_000,
    100_000,
    250_000,
    500_000,
    1_000_000,
]


@dataclass
class Milestone:
    label: str  # e.g. "1 год", "50 000 сообщений"
    value: int  # 365 or 50000 etc — the threshold itself
    when: date | None = None  # when crossed; None if not yet
    days_until: int | None = None  # only set when upcoming


@dataclass
class Anniversaries:
    days_since_start: int  # today - first_date
    total_messages: int
    crossed_days: list[Milestone] = field(default_factory=list)
    crossed_counts: list[Milestone] = field(default_factory=list)
    upcoming_day: Milestone | None = None
    upcoming_count: Milestone | None = None  # estimated by current avg/day rate


def _parse_iso(s: str | None) -> date | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


def compute(
    first_date: str | None,
    total_messages: int,
    per_day: list[tuple[str, int]],
    today: date | None = None,
) -> Anniversaries:
    """Build the milestones snapshot.

    `per_day` is the (iso_date, count) timeline used to find the date
    each cumulative count was crossed. `today` is overridable for tests.
    """
    today = today or date.today()
    start = _parse_iso(first_date)
    if start is None:
        return Anniversaries(days_since_start=0, total_messages=total_messages)

    days_since = (today - start).days
    crossed_days: list[Milestone] = []
    upcoming_day: Milestone | None = None
    for n in _DAY_MILESTONES:
        from datetime import timedelta as _td

        when = start + _td(days=n)
        if n <= days_since:
            crossed_days.append(Milestone(label=_label_days(n), value=n, when=when))
        elif upcoming_day is None:
            upcoming_day = Milestone(
                label=_label_days(n),
                value=n,
                when=when,
                days_until=n - days_since,
            )

    # Walk per_day to find the date each count milestone was first crossed.
    crossed_counts: list[Milestone] = []
    upcoming_count: Milestone | None = None
    cumulative = 0
    targets = list(_COUNT_MILESTONES)
    rows = sorted(per_day, key=lambda r: r[0])
    for d_iso, n in rows:
        cumulative += n
        while targets and cumulative >= targets[0]:
            t = targets.pop(0)
            d = _parse_iso(d_iso)
            crossed_counts.append(Milestone(label=_label_count(t), value=t, when=d))

    if targets:
        next_target = targets[0]
        # Estimate days-until at the average daily rate over the active span.
        if days_since > 0 and total_messages > 0:
            rate_per_day = total_messages / max(days_since, 1)
            remaining = max(next_target - total_messages, 0)
            est_days = int(remaining / rate_per_day) if rate_per_day > 0 else None
        else:
            est_days = None
        upcoming_count = Milestone(
            label=_label_count(next_target),
            value=next_target,
            days_until=est_days,
        )

    return Anniversaries(
        days_since_start=days_since,
        total_messages=total_messages,
        crossed_days=crossed_days,
        crossed_counts=crossed_counts,
        upcoming_day=upcoming_day,
        upcoming_count=upcoming_count,
    )


# Day thresholds that read better as round years than as a day count.
_DAY_AS_YEARS = {365: 1, 730: 2, 1825: 5, 3650: 10}


def _label_days(n: int) -> str:
    """Localized milestone label — resolved against the request's active
    language (i18n reads the per-request override), so labels never leak the
    other locale (e.g. "2 года" inside the English view)."""
    y = _DAY_AS_YEARS.get(n)
    if y:
        return f"{y} {i18n.plural(y, 'год', 'года', 'лет', 'year', 'years')}"
    return i18n.n_days(n)


def _label_count(n: int) -> str:
    word = i18n.plural(n, "сообщение", "сообщения", "сообщений", "message", "messages")
    if n >= 1_000_000:
        num = f"{n // 1_000_000} млн" if i18n.get_lang() == "ru" else f"{n // 1_000_000}M"
        return f"{num} {word}"
    if n >= 1_000:
        return f"{n // 1_000}k {word}"
    return f"{n} {word}"
