"""Streamlit @cache_data wrappers around analysis modules.

Extracted from app.py to keep the entry point thin. All wrappers take a
hashable `cache_key` (str) plus the messages list (`_messages` — leading
underscore tells Streamlit not to hash it).
"""

from __future__ import annotations

import streamlit as st

from analysis import (
    channel as ch_mod,
)
from analysis import (
    emoji_stats as emoji_mod,
)
from analysis import (
    graph as graph_mod,
)
from analysis import (
    latency as latency_mod,
)
from analysis import (
    loader,
    overview,
)
from analysis import (
    media as media_mod,
)
from analysis import (
    phrases as phrases_mod,
)
from analysis import (
    reciprocity as reciprocity_mod,
)
from analysis import (
    render as render_mod,
)
from analysis import (
    sessions as sessions_mod,
)
from analysis import (
    speaking as speaking_mod,
)
from analysis import (
    timing as timing_mod,
)
from analysis import (
    words as words_mod,
)


@st.cache_data(show_spinner="Loading export…")
def load_data(path: str, mtime: float) -> dict:
    """Cached load by (path, mtime). mtime ensures cache invalidates on edit.

    Dispatches JSON vs HTML via loader.load_export.
    """
    return loader.load_export(path)


@st.cache_data(show_spinner="Computing KPIs…")
def kpis(cache_key: str, _messages: list) -> overview.Kpis:
    return overview.compute_kpis(_messages)


@st.cache_data(show_spinner="Computing daily activity…")
def per_day(cache_key: str, _messages: list):
    return overview.messages_per_day(_messages)


@st.cache_data(show_spinner="Computing hour-of-day map…")
def hour_weekday(cache_key: str, _messages: list):
    return overview.hour_weekday_heatmap(_messages)


@st.cache_data(show_spinner="Computing participants…")
def participants(cache_key: str, _messages: list):
    return overview.participants_table(_messages)


@st.cache_data(show_spinner="Building graph…")
def graph_data(cache_key: str, _messages: list) -> graph_mod.GraphData:
    return graph_mod.build(_messages)


# `cache_resource` instead of `cache_data` because WordsResult holds per-user
# message lists that can be 30k+ tuples on long chats, and one user reported
# pickle failing on it (likely from a non-string text fragment slipping in
# from a malformed text_entity). cache_resource keeps the object in-process
# without serialisation; the cache_key still scopes it per-(chat, range).
@st.cache_resource(show_spinner="Analysing words…")
def words(cache_key: str, _messages: list, most_com: int):
    return words_mod.analyze(_messages, most_com=most_com)


@st.cache_data(show_spinner="Analysing channel…")
def channel(cache_key: str, _messages: list, most_com: int):
    return ch_mod.analyze(_messages, most_com=most_com)


@st.cache_data(show_spinner="Counting emojis…")
def emojis(cache_key: str, _messages: list):
    return emoji_mod.analyze(_messages)


@st.cache_data(show_spinner="Computing reply latency…")
def latency(cache_key: str, _messages: list):
    return latency_mod.compute(_messages)


@st.cache_data(show_spinner="Counting media…")
def media(cache_key: str, _messages: list):
    return media_mod.analyze(_messages)


@st.cache_data(show_spinner="Profiling speaking style…")
def speaking(cache_key: str, _messages: list):
    return speaking_mod.analyze(_messages)


@st.cache_data(show_spinner="Computing streaks…")
def streaks(cache_key: str, _messages: list, filter_uid: str | None = None):
    return timing_mod.streaks_and_silences(_messages, filter_uid=filter_uid)


@st.cache_data(show_spinner="Computing initiators…")
def initiators(cache_key: str, _messages: list, gap_hours: int):
    return timing_mod.conversation_initiators(_messages, gap_hours=gap_hours)


@st.cache_data(show_spinner="Splitting into conversations…")
def sessions(cache_key: str, _messages: list, gap_minutes: int):
    sess = sessions_mod.split_into_sessions(_messages, gap_minutes=gap_minutes)
    return sessions_mod.stats(sess)


@st.cache_data(show_spinner="Mining phrases…")
def phrases(cache_key: str, _messages: list, n: int, top: int):
    return phrases_mod.top_phrases(_messages, n=n, top=top)


@st.cache_data(show_spinner="Mining per-user phrases…")
def per_user_phrases(cache_key: str, _messages: list, n: int, top: int):
    # Computed once per chat for all users; the Per-User tab indexes the result
    # by the selected user_id, so switching users doesn't recompute.
    return phrases_mod.per_user_phrases(_messages, n=n, top=top)


@st.cache_data(show_spinner="Computing reciprocity…")
def reciprocity(cache_key: str, _messages: list):
    return reciprocity_mod.compute(_messages)


@st.cache_data(show_spinner="Filtering by date…")
def filter_by_date(cache_key: str, _messages: list, from_d: str, to_d: str):
    return overview.filter_by_date(_messages, from_d, to_d)


@st.cache_data(show_spinner="Rendering wordcloud…")
def wordcloud(cache_key: str, words_with_counts: list[tuple[str, int]]) -> bytes | None:
    # Pure tuple list → hashable → safe under cache_data; cache_key scopes by chat.
    return render_mod.wordcloud_png(words_with_counts)
