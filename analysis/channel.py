"""Channel (broadcast) text analysis: word frequencies + wordcloud."""

from __future__ import annotations

from dataclasses import dataclass

import jmespath

from utils import remove_emojis
import nltk_analyse


@dataclass
class ChannelResult:
    top_words: list[tuple[str, int]]
    token_count: int
    wordcloud_png: bytes | None  # raw PNG bytes if generation succeeded


def _gather_texts(messages: list[dict]) -> list[str]:
    """Pull text from messages, taking text_entities into account so we don't
    miss formatted parts (links, bold, mentions)."""
    out: list[str] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        t = m.get("text")
        if isinstance(t, str) and t.strip():
            out.append(remove_emojis(t))
        elif isinstance(t, list):
            for item in t:
                if isinstance(item, str):
                    out.append(remove_emojis(item))
                elif isinstance(item, dict) and "text" in item:
                    out.append(remove_emojis(item["text"]))
        ents = jmespath.search("text_entities[*].text", m)
        if ents:
            for e in ents:
                if e:
                    out.append(remove_emojis(e))
        c = m.get("caption")
        if isinstance(c, str) and c.strip():
            out.append(remove_emojis(c))
    return [s for s in out if s and len(s) > 4]


def analyze(messages: list[dict], most_com: int = 100) -> ChannelResult:
    texts = _gather_texts(messages)
    if not texts:
        return ChannelResult(top_words=[], token_count=0, wordcloud_png=None)

    fdist, tokens = nltk_analyse.analyse(texts, most_com)
    all_tokens = list(tokens)
    top, top_words = nltk_analyse.analyse_all(all_tokens, most_com)

    png: bytes | None = None
    try:
        from io import BytesIO

        from wordcloud import WordCloud

        text_raw = " ".join(top_words)
        if text_raw.strip():
            wc = WordCloud(
                width=1200,
                height=600,
                background_color=None,
                mode="RGBA",
                colormap="viridis",
            ).generate(text_raw)
            buf = BytesIO()
            wc.to_image().save(buf, format="PNG")
            png = buf.getvalue()
    except Exception:
        png = None

    return ChannelResult(
        top_words=list(top), token_count=len(tokens), wordcloud_png=png
    )
