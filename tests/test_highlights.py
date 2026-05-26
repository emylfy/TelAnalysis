"""Tests for analysis.highlights — hero prose composer and highlight cards."""

from __future__ import annotations

from analysis import highlights, overview


def _make_grid(weekday: int, hour: int, count: int):
    grid = [[0] * 24 for _ in range(7)]
    grid[weekday][hour] = count
    return grid


def _kpis(**overrides):
    base = dict(
        total_messages=10_000,
        unique_users=2,
        first_date="2023-01-01",
        last_date="2024-12-31",
        days_active=731,
        media_messages=400,
    )
    base.update(overrides)
    return overview.Kpis(**base)


# build_hero


def test_build_hero_includes_count_and_avg():
    hero = highlights.build_hero(
        chat_name="Alice",
        kpis=_kpis(total_messages=23_000, days_active=100),
        per_day=[("2024-03-08", 412)],
        grid=_make_grid(weekday=6, hour=23, count=200),
    )
    assert hero.title == "Alice"
    # 23 000 messages / 100 days = 230/day avg
    assert "23 000" in hero.prose_html
    assert "230" in hero.prose_html
    assert "100 дней" in hero.prose_html


def test_build_hero_mentions_peak_day_in_genitive_month():
    """Date phrasing should use genitive case ('8 марта'), not prepositional."""
    hero = highlights.build_hero(
        chat_name="Test",
        kpis=_kpis(),
        per_day=[("2024-03-08", 999)],
        grid=_make_grid(0, 12, 1),
    )
    assert "8 марта" in hero.prose_html
    assert "8 марте" not in hero.prose_html  # prep case would be wrong here
    assert "999" in hero.prose_html


def test_build_hero_handles_empty_data():
    hero = highlights.build_hero(
        chat_name="Empty",
        kpis=_kpis(total_messages=0, days_active=0, first_date=None, last_date=None),
        per_day=[],
        grid=[[0] * 24 for _ in range(7)],
    )
    assert hero.title == "Empty"
    assert "ограничен" in hero.prose_html or hero.prose_html


def test_build_hero_meta_has_date_range():
    hero = highlights.build_hero(
        chat_name="X",
        kpis=_kpis(first_date="2023-01-01", last_date="2024-12-31"),
        per_day=[("2024-01-01", 1)],
        grid=_make_grid(0, 0, 1),
    )
    assert "2023-01-01" in hero.meta
    assert "2024-12-31" in hero.meta


# top_highlights


def test_top_highlights_returns_at_most_4():
    cards = highlights.top_highlights(
        kpis=_kpis(),
        per_day=[("2024-01-01", 50), ("2024-03-08", 412)],
        grid=_make_grid(weekday=6, hour=23, count=200),
    )
    assert 0 < len(cards) <= 4


def test_top_highlights_peak_hour_card():
    cards = highlights.top_highlights(
        kpis=_kpis(),
        per_day=[("2024-01-01", 50)],
        grid=_make_grid(weekday=2, hour=14, count=999),
    )
    peak_card = next((c for c in cards if "Пиковый" in c.label), None)
    assert peak_card is not None
    assert "Среда" in peak_card.value
    assert "14:00" in peak_card.value


def test_top_highlights_skips_voice_when_zero():
    class FakeMedia:
        voice_count = 0
        voice_total_seconds = 0
        total_links = 0
        top_domains = []

    cards = highlights.top_highlights(
        kpis=_kpis(),
        per_day=[("2024-01-01", 50)],
        grid=_make_grid(0, 12, 1),
        media=FakeMedia(),
    )
    assert all("Голосовые" not in c.label for c in cards)


def test_top_highlights_includes_emoji_when_provided():
    class FakeEmoji:
        chat_top = [("🔥", 247), ("👍", 132)]

    cards = highlights.top_highlights(
        kpis=_kpis(),
        per_day=[("2024-01-01", 50)],
        grid=_make_grid(0, 12, 1),
        emojis=FakeEmoji(),
    )
    em_card = next((c for c in cards if "эмоджи" in c.label.lower()), None)
    assert em_card is not None
    assert em_card.value == "🔥"
    assert "247" in em_card.sub


def test_top_highlights_streak_fallback():
    class FakeStreaks:
        longest_streak_days = 47
        longest_streak_start = "2024-01-01"
        longest_streak_end = "2024-02-16"
        longest_silences = []

    cards = highlights.top_highlights(
        kpis=_kpis(),
        per_day=[("2024-01-01", 50)],
        grid=_make_grid(0, 12, 1),
        streaks=FakeStreaks(),
    )
    streak_card = next((c for c in cards if "стрик" in c.label.lower()), None)
    assert streak_card is not None
    assert "47" in streak_card.value
