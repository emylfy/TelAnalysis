"""Image rendering helpers."""

from __future__ import annotations

from io import BytesIO


def wordcloud_png(
    words_with_counts: list[tuple[str, int]],
    *,
    max_words: int = 150,
    width: int = 1200,
    height: int = 500,
    colormap: str = "viridis",
    colors: list[str] | None = None,
) -> bytes | None:
    """Render top words as a wordcloud PNG (transparent background, RGBA).
    Returns raw bytes or None if the input is empty / wordcloud lib fails.

    Pass ``colors`` (a palette of hex strings) to colour words by random pick
    from that palette instead of ``colormap`` — useful for staying bright on a
    dark UI, where viridis' dark end vanishes."""
    if not words_with_counts:
        return None
    freq = {w: int(c) for w, c in words_with_counts[:max_words] if w and c}
    if not freq:
        return None
    try:
        import random

        from wordcloud import WordCloud

        color_func = None
        if colors:
            def color_func(*_args, random_state=None, **_kwargs):  # noqa: ANN001
                rng = random_state or random
                return str(rng.choice(colors))

        wc = WordCloud(
            width=width,
            height=height,
            background_color=None,
            mode="RGBA",
            colormap=colormap,
            color_func=color_func,
            max_words=max_words,
            collocations=False,
            prefer_horizontal=0.85,
        ).generate_from_frequencies(freq)
        buf = BytesIO()
        wc.to_image().save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None
