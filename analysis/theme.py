"""Single source of truth for visual identity: colors, plotly template, CSS.

Used by app.py and every analysis module that builds a figure. Replaces the
ad-hoc `template="plotly_dark"` + per-trace `marker_color="rgba(...)"` pattern
that produced the "fruit-salad of palettes" effect across tabs.

Dark-only. A previous version exposed a runtime light/dark switch, but
Streamlit's chrome theme is set at startup via `.streamlit/config.toml` and
can't be flipped at runtime — mixing a light card palette over a dark chrome
makes text unreadable, and inverting just the plotly template leaves charts
floating on a black page. Either is worse than no switch.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

PALETTE: dict[str, str] = {
    "accent": "#FF6B6B",
    "primary": "#5B8FF9",
    "secondary": "#E86452",
    "success": "#5AD8A6",
    "warning": "#F6BD16",
    "violet": "#9270CA",
    "cyan": "#5AD8F7",
    "neutral_bright": "#E5E7EB",
    "neutral_dim": "#9CA3AF",
    "neutral_dark": "#374151",
    "bg": "#0E1117",
    "bg_card": "rgba(255,255,255,0.04)",
    "bg_card_hover": "rgba(255,255,255,0.08)",
    "border": "rgba(255,255,255,0.08)",
}

HEAT_SCALE: list = [
    [0.0, "#0E1117"],
    [0.15, "#1F2937"],
    [0.4, "#3B5BDB"],
    [0.7, "#FF6B6B"],
    [1.0, "#FFE66D"],
]

COLORWAY: list[str] = [
    PALETTE["primary"],
    PALETTE["secondary"],
    PALETTE["success"],
    PALETTE["warning"],
    PALETTE["violet"],
    PALETTE["cyan"],
    PALETTE["accent"],
]

TEMPLATE_NAME = "telanalysis"


def _build_template() -> go.layout.Template:
    base = pio.templates["plotly_dark"]
    t = go.layout.Template(base)
    t.layout.paper_bgcolor = "rgba(0,0,0,0)"
    t.layout.plot_bgcolor = "rgba(0,0,0,0)"
    t.layout.colorway = COLORWAY
    t.layout.font = dict(
        family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        size=13,
        color=PALETTE["neutral_bright"],
    )
    t.layout.title = dict(
        font=dict(size=16, color=PALETTE["neutral_bright"]),
        x=0,
        xanchor="left",
    )
    t.layout.xaxis = dict(
        gridcolor=PALETTE["border"],
        zerolinecolor=PALETTE["border"],
        linecolor=PALETTE["border"],
    )
    t.layout.yaxis = dict(
        gridcolor=PALETTE["border"],
        zerolinecolor=PALETTE["border"],
        linecolor=PALETTE["border"],
    )
    t.layout.legend = dict(bgcolor="rgba(0,0,0,0)", borderwidth=0)
    return t


pio.templates[TEMPLATE_NAME] = _build_template()


def apply(fig: go.Figure, *, height: int | None = None, title: str | None = None) -> go.Figure:
    """Apply the unified template + tight margins to a figure."""
    fig.update_layout(
        template=TEMPLATE_NAME,
        margin=dict(l=0, r=0, t=40 if title else 10, b=0),
    )
    if height is not None:
        fig.update_layout(height=height)
    if title is not None:
        fig.update_layout(title=title)
    return fig


CSS = f"""
<style>
:root {{
    --tla-accent: {PALETTE["accent"]};
    --tla-primary: {PALETTE["primary"]};
    --tla-success: {PALETTE["success"]};
    --tla-warning: {PALETTE["warning"]};
    --tla-violet: {PALETTE["violet"]};
    --tla-bright: {PALETTE["neutral_bright"]};
    --tla-dim: {PALETTE["neutral_dim"]};
    --tla-card: {PALETTE["bg_card"]};
    --tla-card-hover: {PALETTE["bg_card_hover"]};
    --tla-border: {PALETTE["border"]};
    --tla-bg: {PALETTE["bg"]};
}}

.tla-hero {{
    margin: 0.5rem 0 1.5rem 0;
    padding: 1.5rem 1.75rem;
    border-radius: 12px;
    background: var(--tla-card);
    border: 1px solid var(--tla-border);
}}
.tla-hero-title {{
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.15;
    margin: 0 0 0.5rem 0;
    color: var(--tla-bright);
    letter-spacing: -0.01em;
}}
.tla-hero-prose {{
    font-size: 1.05rem;
    line-height: 1.55;
    color: var(--tla-bright);
    margin: 0;
}}
.tla-hero-prose b {{ color: var(--tla-accent); font-weight: 600; }}
.tla-hero-meta {{
    margin-top: 0.75rem;
    font-size: 0.85rem;
    color: var(--tla-dim);
    font-variant-numeric: tabular-nums;
}}

.tla-bignum {{
    padding: 0.75rem 1rem;
    border-radius: 10px;
    background: var(--tla-card);
    border: 1px solid var(--tla-border);
    transition: background 0.15s ease;
    height: 100%;
}}
.tla-bignum:hover {{ background: var(--tla-card-hover); }}
.tla-bignum-label {{
    font-size: 0.7rem;
    color: var(--tla-dim);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
    margin: 0 0 0.2rem 0;
}}
.tla-bignum-value {{
    font-size: 1.75rem;
    font-weight: 600;
    line-height: 1.05;
    color: var(--tla-bright);
    font-variant-numeric: tabular-nums;
    margin: 0;
    white-space: nowrap;
    letter-spacing: -0.01em;
}}
.tla-bignum-context {{
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: var(--tla-dim);
}}

.tla-hl-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.5rem;
    margin: 0.5rem 0 1.25rem 0;
}}
.tla-hl-card {{
    padding: 0.7rem 0.9rem;
    border-radius: 10px;
    background: var(--tla-card);
    border: 1px solid var(--tla-border);
    transition: background 0.15s ease;
}}
.tla-hl-card:hover {{
    background: var(--tla-card-hover);
}}
.tla-hl-label {{
    font-size: 0.7rem;
    color: var(--tla-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin: 0 0 0.2rem 0;
}}
.tla-hl-value {{
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--tla-bright);
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.01em;
}}
.tla-hl-sub {{
    font-size: 0.75rem;
    color: var(--tla-dim);
    margin-top: 0.15rem;
}}

/* Tabs: sticky on scroll */
div[data-baseweb="tab-list"] {{
    position: sticky;
    top: 2.875rem;
    z-index: 99;
    background: var(--tla-bg);
    backdrop-filter: blur(10px);
}}
button[data-baseweb="tab"] {{
    font-size: 0.95rem;
    padding: 0.5rem 0.75rem;
}}

/* Lift selectbox / popover portals above the sticky tab bar (z-index: 99). */
div[data-baseweb="popover"] {{
    z-index: 1000 !important;
}}
</style>
"""
