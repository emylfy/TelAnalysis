"""Single source of truth for the visual palette.

These constants are consumed by the analysis layer (wordcloud colours via
`COLORWAY`, community colours in the reply graph) and the FastAPI backend.
The React SPA owns its own theming in `frontend/src/index.css`; this module is
intentionally dependency-free (no plotly, no streamlit) so it imports cleanly
in the API process.
"""

from __future__ import annotations

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
