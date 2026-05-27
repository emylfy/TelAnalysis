"""Shared UI helpers: HTML cards, calendar heatmap figure builder.

Pure rendering — no analytics. All functions return Streamlit-renderable
artifacts (HTML strings or plotly Figures), never side-effect into the page.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis import theme as theme_mod
from ui import i18n


def fmt_int(n: int) -> str:
    """Thin-space-grouped integer (Russian convention)."""
    return f"{int(n):,}".replace(",", " ")


def logo_svg(size: int = 56) -> str:
    """Brand mark — a rounded tile with three ascending bars in the palette.
    Shared by the onboarding welcome and the sidebar brand so they stay in sync.
    """
    p = theme_mod.PALETTE
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 56 56' fill='none' "
        "style='display:inline-block;vertical-align:middle'>"
        "<rect width='56' height='56' rx='14' fill='rgba(255,255,255,0.04)' "
        "stroke='rgba(255,255,255,0.10)'/>"
        f"<rect x='15' y='30' width='6' height='11' rx='2' fill='{p['primary']}'/>"
        f"<rect x='25' y='22' width='6' height='19' rx='2' fill='{p['success']}'/>"
        f"<rect x='35' y='15' width='6' height='26' rx='2' fill='{p['accent']}'/>"
        "</svg>"
    )


def bignum_html(label: str, value: str, context: str = "") -> str:
    ctx = f'<div class="tla-bignum-context">{context}</div>' if context else ""
    return (
        '<div class="tla-bignum">'
        f'<div class="tla-bignum-label">{label}</div>'
        f'<div class="tla-bignum-value">{value}</div>'
        f"{ctx}</div>"
    )


def hero_html(hero, chat_type: str, chat_id) -> str:
    """Render the hero block from HeroData. Used at the top of the page.

    The raw chat type is humanized (personal_chat → «Личный чат») and the
    technical chat ID is dropped from the visible meta — kept only as a hover
    title for debugging.
    """
    return (
        f'<div class="tla-hero">'
        f'<h1 class="tla-hero-title">{hero.title}</h1>'
        f'<p class="tla-hero-prose">{hero.prose_html}</p>'
        f'<div class="tla-hero-meta" title="ID {chat_id}">'
        f"{hero.meta}  ·  {i18n.chat_type_label(chat_type)}</div>"
        f"</div>"
    )


def highlights_grid_html(items) -> str:
    """Wrap a list of Highlight dataclass instances into the responsive grid."""
    if not items:
        return ""
    cards = "".join(
        '<div class="tla-hl-card">'
        f'<div class="tla-hl-label">{h.label}</div>'
        f'<div class="tla-hl-value">{h.value}</div>'
        f'<div class="tla-hl-sub">{h.sub}</div>'
        "</div>"
        for h in items
    )
    return f'<div class="tla-hl-grid">{cards}</div>'


def calendar_heatmap_fig(df: pd.DataFrame, binary: bool = False) -> go.Figure | None:
    """GitHub-contributions-style calendar heatmap. df has columns
    ['date', 'messages']. Returns None on empty df.

    binary=True paints "did we talk that day at all" instead of count —
    useful for seeing commitment patterns (long uninterrupted runs vs
    sparse weeks) without high-volume days washing everything else out.
    """
    if df is None or len(df) == 0:
        return None
    cal = df.copy()
    cal["date"] = pd.to_datetime(cal["date"])
    full = pd.date_range(cal["date"].min(), cal["date"].max(), freq="D")
    cal = cal.set_index("date").reindex(full, fill_value=0).reset_index()
    cal.columns = ["date", "messages"]
    if binary:
        cal["messages"] = (cal["messages"] > 0).astype(int)
    cal["year"] = cal["date"].dt.year
    cal["weekday"] = cal["date"].dt.weekday
    cal["week"] = cal["date"].dt.isocalendar().week

    years = sorted(cal["year"].unique())
    weekdays_lbl = i18n.weekday_short_labels()
    fig = make_subplots(
        rows=len(years),
        cols=1,
        subplot_titles=[str(y) for y in years],
        vertical_spacing=0.08,
    )
    hovertemplate = (
        "%{y} · week %{x}<br>%{z}<extra></extra>"
        if binary
        else "%{y} · week %{x}<br>messages: %{z}<extra></extra>"
    )
    colorscale = (
        [[0.0, "#0E1117"], [1.0, theme_mod.PALETTE.get("success", "#5AD8A6")]]
        if binary
        else theme_mod.HEAT_SCALE
    )
    for idx, y in enumerate(years, start=1):
        sub = cal[cal["year"] == y].copy()
        sub["week"] = sub["date"].dt.strftime("%U").astype(int)
        pivot = sub.pivot_table(
            index="weekday",
            columns="week",
            values="messages",
            aggfunc="sum",
            fill_value=0,
        ).reindex(range(7), fill_value=0)
        fig.add_trace(
            go.Heatmap(
                z=pivot.values,
                x=[f"W{w}" for w in pivot.columns],
                y=weekdays_lbl,
                colorscale=colorscale,
                showscale=(idx == 1) and not binary,
                hovertemplate=hovertemplate,
            ),
            row=idx,
            col=1,
        )
    title = i18n.t("Календарь")
    if binary:
        title = f"{title} · {i18n.t('писали/нет')}"
    fig.update_layout(
        title=title,
        template="telanalysis",
        height=180 * len(years) + 40,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    for r in range(1, len(years) + 1):
        fig.update_xaxes(showticklabels=False, row=r, col=1)
    return fig


__all__ = [
    "fmt_int",
    "logo_svg",
    "bignum_html",
    "hero_html",
    "highlights_grid_html",
    "calendar_heatmap_fig",
]
