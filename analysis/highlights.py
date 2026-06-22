"""Spotify-Wrapped style insight generator.

Takes the already-computed analytics structures (kpis, per-day timeline,
hour×weekday grid, emojis, media, streaks, latency) and turns them into:
- a hero prose paragraph ("За 847 дней вы написали 23 451 сообщений…"),
- a small set of "highlight" cards (peak day, peak hour, top emoji, voice).

Pure functions — no Streamlit, no IO. Strings flow through i18n so the
same composer renders RU or EN depending on the active language.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import i18n


@dataclass
class Highlight:
    icon: str
    label: str
    value: str
    sub: str = ""


@dataclass
class HeroData:
    title: str
    prose_html: str
    meta: str


def _fmt_int(n: int | float) -> str:
    return f"{int(n):,}".replace(",", " ")


def _bold(s: Any) -> str:
    return f"<b>{s}</b>"


def _peak_hour_weekday(grid: list[list[int]]) -> tuple[int, int, int] | None:
    """(weekday 0..6, hour 0..23, count) for the hottest cell. None if all zero."""
    best = None
    for wd, row in enumerate(grid):
        for h, c in enumerate(row):
            if best is None or c > best[2]:
                best = (wd, h, c)
    if best is None or best[2] == 0:
        return None
    return best


def _peak_day(per_day: list[tuple[str, int]]) -> tuple[str, int] | None:
    if not per_day:
        return None
    return max(per_day, key=lambda x: x[1])


def _avg_per_active_day(total: int, days: int) -> float:
    return total / days if days > 0 else 0.0


def build_hero(
    chat_name: str,
    kpis,
    per_day: list[tuple[str, int]],
    grid: list[list[int]],
    streaks=None,
) -> HeroData:
    """Compose the hero block: title + prose paragraph + meta line.
    Required: kpis (Kpis dataclass), per_day, grid. streaks optional.
    """
    parts: list[str] = []

    if kpis.days_active and kpis.total_messages:
        avg = _avg_per_active_day(kpis.total_messages, kpis.days_active)
        parts.append(
            i18n.t("За {days} здесь написали {messages} — это в среднем {avg} в день.").format(
                days=i18n.n_days(kpis.days_active),
                messages=_bold(i18n.n_messages(kpis.total_messages)),
                avg=f"{avg:.0f}",
            )
        )

    peak = _peak_day(per_day)
    if peak and peak[1] > 0:
        d_iso, n = peak
        try:
            dt = datetime.fromisoformat(d_iso)
            day_str = i18n.format_day(dt.date())
        except (ValueError, IndexError):
            day_str = d_iso
        parts.append(
            i18n.t("Самый шумный день — {date}, {messages} за сутки.").format(
                date=day_str,
                messages=i18n.n_messages(n),
            )
        )

    peak_hw = _peak_hour_weekday(grid)
    if peak_hw is not None:
        wd, h, _ = peak_hw
        parts.append(
            i18n.t("Чаще всего пишут в {weekday} около {hour}.").format(
                weekday=i18n.weekday_name(wd),
                hour=i18n.hour_to_human(h),
            )
        )

    if streaks is not None and streaks.longest_silences:
        gap_start, gap_end, days = streaks.longest_silences[0]
        try:
            dt = datetime.fromisoformat(gap_start)
            when = i18n.format_month_year(dt.date())
        except (ValueError, IndexError):
            when = gap_start
        parts.append(
            i18n.t("Самое долгое молчание — {days} в {when}.").format(
                days=i18n.n_days(days),
                when=when,
            )
        )

    if not parts:
        prose = i18n.t("Нет дат у сообщений — анализ ограничен.")
    else:
        prose = " ".join(parts)

    if kpis.first_date and kpis.last_date:
        users_label = i18n.plural(
            kpis.unique_users,
            "участн.",
            "участн.",
            "участн.",
            "user",
            "users",
        )
        meta = (
            f"{kpis.first_date} → {kpis.last_date}  ·  {_fmt_int(kpis.unique_users)} {users_label}"
        )
    else:
        users_label = i18n.plural(
            kpis.unique_users,
            "участн.",
            "участн.",
            "участн.",
            "user",
            "users",
        )
        meta = f"{_fmt_int(kpis.unique_users)} {users_label}"

    return HeroData(title=chat_name, prose_html=prose, meta=meta)


def top_highlights(
    kpis,
    per_day: list[tuple[str, int]],
    grid: list[list[int]],
    emojis=None,
    media=None,
    streaks=None,
    latency=None,
) -> list[Highlight]:
    """Up to 4 highlight cards picked from a weighted pool, not a fixed
    priority list. Each candidate gets a score reflecting how striking the
    underlying number is; top 4 win. Previously the order was hardcoded
    (peak_hour first, peak_day second, ...) so longest_streak / silence /
    latency / links never appeared if the first slots were filled."""
    import math

    pool: list[tuple[float, Highlight]] = []

    peak_hw = _peak_hour_weekday(grid)
    if peak_hw is not None:
        wd, h, count = peak_hw
        times_word = i18n.plural(
            count, "сообщение", "сообщения", "сообщений", "message", "messages"
        )
        pool.append(
            (
                math.log10(max(count, 1) + 1),
                Highlight(
                    icon="⏰",
                    label=i18n.t("Пиковый час"),
                    value=f"{i18n.weekday_name_cap(wd)}, {h:02d}:00",
                    sub=f"{_fmt_int(count)} {times_word}",
                ),
            )
        )

    peak = _peak_day(per_day)
    if peak and peak[1] > 0:
        d_iso, n = peak
        try:
            dt = datetime.fromisoformat(d_iso)
            day_str = i18n.format_day_short(dt.date())
        except (ValueError, IndexError):
            day_str = d_iso
        pool.append(
            (
                math.log10(max(n, 1) + 1) * 1.1,  # slightly heavier than peak hour
                Highlight(
                    icon="🔥",
                    label=i18n.t("Самый громкий день"),
                    value=day_str,
                    sub=i18n.n_messages(n),
                ),
            )
        )

    if emojis is not None and getattr(emojis, "chat_top", None):
        top_em, em_count = emojis.chat_top[0]
        times_word = i18n.plural(em_count, "раз", "раза", "раз", "time", "times")
        pool.append(
            (
                math.log10(max(em_count, 1) + 1) * 0.7,
                Highlight(
                    icon="😄",
                    label=i18n.t("Любимая эмоджи"),
                    value=top_em,
                    sub=f"{_fmt_int(em_count)} {times_word}",
                ),
            )
        )

    if media is not None and getattr(media, "voice_count", 0):
        from . import media as media_mod

        pool.append(
            (
                math.log10(max(media.voice_total_seconds // 60, 1) + 1),
                Highlight(
                    icon="🎙️",
                    label=i18n.t("Голосовые"),
                    value=media_mod.humanize_duration(media.voice_total_seconds),
                    sub=i18n.n_messages(media.voice_count),
                ),
            )
        )

    if streaks is not None and getattr(streaks, "longest_streak_days", 0) > 1:
        pool.append(
            (
                streaks.longest_streak_days / 20,  # 30 days = score 1.5
                Highlight(
                    icon="🏃",
                    label=i18n.t("Самый длинный стрик"),
                    value=i18n.n_days(streaks.longest_streak_days),
                    sub=f"{streaks.longest_streak_start} → {streaks.longest_streak_end}",
                ),
            )
        )

    if streaks is not None and getattr(streaks, "longest_silences", None):
        gap_start, gap_end, days = streaks.longest_silences[0]
        pool.append(
            (
                days / 30,  # longer silences interesting; 30 days = score 1
                Highlight(
                    icon="🤫",
                    label=i18n.t("Самое долгое молчание"),
                    value=i18n.n_days(days),
                    sub=f"{gap_start} → {gap_end}",
                ),
            )
        )

    if latency is not None and getattr(latency, "median_seconds", None):
        from . import media as media_mod

        # Fast median = more interesting (high score); >1h = low score.
        med = max(latency.median_seconds, 1)
        score = max(0.5, 4 - math.log10(med))
        pool.append(
            (
                score,
                Highlight(
                    icon="↩️",
                    label=i18n.t("Медиана ответа"),
                    value=media_mod.humanize_duration(int(latency.median_seconds)),
                    sub=i18n.t("между сообщениями"),
                ),
            )
        )

    if media is not None and getattr(media, "total_links", 0):
        pool.append(
            (
                math.log10(max(media.total_links, 1) + 1) * 0.6,
                Highlight(
                    icon="🔗",
                    label=i18n.t("Ссылок"),
                    value=_fmt_int(media.total_links),
                    sub=(media.top_domains[0][0] if media.top_domains else ""),
                ),
            )
        )

    pool.sort(key=lambda x: -x[0])
    return [h for _, h in pool[:4]]
