"""TelAnalysis — Streamlit dashboard.

Run with:
    streamlit run app.py

Auto-detects single-chat vs full-archive Telegram exports.
Tabs adapt to chat type (channel/group/personal/saved).
"""

from __future__ import annotations

import os
import tempfile
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analysis import anniversaries as anniversaries_mod
from analysis import chains as chains_mod
from analysis import forwards as forwards_mod
from analysis import graph as graph_mod
from analysis import highlights as highlights_mod
from analysis import latency as latency_mod
from analysis import (
    loader,
    overview,
)
from analysis import mat as mat_mod
from analysis import media as media_mod
from analysis import monologues as monologues_mod
from analysis import (
    render as render_mod,
)
from analysis import theme as theme_mod
from analysis import (
    words as words_mod,
)
from ui import cache as ui_cache
from ui import components as ui_components
from ui import i18n

st.set_page_config(
    page_title="TelAnalysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme — locked to dark. Streamlit chrome is dark via .streamlit/config.toml
# and we don't expose a runtime switch.
theme_mod.set_mode("dark")
st.markdown(theme_mod.css(), unsafe_allow_html=True)


# Sidebar — file picker collapses after a file is loaded.
# State: st.session_state["loaded_path"] / ["loaded_label"]. While unset,
# the full Source toggle + uploader/path is shown. Once set, the uploader UI
# is replaced by a one-line file chip with a reset button.
with st.sidebar:
    # Language toggle — stable IDs ('ru' | 'en'); the visible label is the chip.
    _lang_current = st.session_state.get("lang", "ru")
    _lang_choice = st.radio(
        "Language",
        options=["ru", "en"],
        index=0 if _lang_current == "ru" else 1,
        format_func=lambda x: "RU" if x == "ru" else "EN",
        horizontal=True,
        label_visibility="collapsed",
        key="lang",
    )

    st.title("TelAnalysis")
    st.caption(i18n.t("анализ переписок telegram"))

    loaded_path = st.session_state.get("loaded_path")
    loaded_label = st.session_state.get("loaded_label")
    if loaded_path and not os.path.exists(loaded_path):
        # Stale (tmp file gone after Streamlit restart) — fall back to empty state.
        st.session_state.pop("loaded_path", None)
        st.session_state.pop("loaded_label", None)
        loaded_path = None

    json_path: str | None = None

    if loaded_path:
        with st.expander(f"📄 {loaded_label}", expanded=False):
            st.caption(loaded_path)
            if st.button(i18n.t("Загрузить другой файл"), use_container_width=True):
                st.session_state.pop("loaded_path", None)
                st.session_state.pop("loaded_label", None)
                # Drop chat / date filters that referenced the old file.
                for k in ("chat", "from", "to"):
                    if k in st.query_params:
                        del st.query_params[k]
                st.rerun()
        json_path = loaded_path
    else:
        src_mode = st.radio(
            i18n.t("Источник"),
            options=["upload", "path"],
            format_func=lambda x: i18n.t("Загрузить") if x == "upload" else i18n.t("Путь к файлу"),
            horizontal=True,
            help=i18n.t(
                "Drag & drop по умолчанию. Для экспортов 65MB+ выбирай «Путь к файлу» — "
                "быстрее, без base64 через WebSocket."
            ),
        )

        if src_mode == "upload":
            upload = st.file_uploader(
                i18n.t("Перетащи result.json сюда"),
                type=["json"],
                help=i18n.t("Или нажми и выбери файл вручную."),
            )
            if upload is not None:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", prefix="tla_")
                tmp.write(upload.read())
                tmp.close()
                json_path = tmp.name
                st.session_state["loaded_path"] = json_path
                st.session_state["loaded_label"] = upload.name
                st.rerun()
        else:
            path_input = st.text_input(
                i18n.t("Путь к result.json"),
                value=st.session_state.get("last_path", ""),
                placeholder="/Users/me/.../result.json",
            )
            if path_input:
                if os.path.exists(path_input):
                    json_path = path_input
                    st.session_state["last_path"] = path_input
                    st.session_state["loaded_path"] = json_path
                    st.session_state["loaded_label"] = os.path.basename(path_input)
                    st.rerun()
                else:
                    st.error(i18n.t("Файл не найден"))

if json_path is None:
    st.info(
        i18n.t(
            "Выбери JSON-экспорт telegram в сайдбаре слева.\n\n"
            "**Один чат** — `Настройки → Экспорт переписки`.\n\n"
            "**Весь аккаунт** — `Настройки → Продвинутые настройки → Экспорт данных Telegram`. "
            "Появится выбор чата."
        )
    )
    st.stop()

data = ui_cache.load_data(json_path, os.path.getmtime(json_path))
chats = loader.list_chats(data)

with st.sidebar:
    st.divider()
    if len(chats) == 1:
        chat = chats[0]
        st.success(i18n.t("Один чат: **{name}**").format(name=chat.name))
    else:
        st.success(i18n.t("Архив: **{n} чатов**").format(n=len(chats)))
        type_filter = st.multiselect(
            i18n.t("Тип чата"),
            sorted({c.type for c in chats}),
            default=[],
            help=i18n.t("Пусто = все типы"),
        )
        filtered = [c for c in chats if not type_filter or c.type in type_filter]

        combine_all = st.checkbox(
            i18n.t("Объединить все (отфильтрованные) чаты"),
            value=False,
            help=i18n.t(
                "Считать весь архив как один большой чат. Слова, эмоджи, ссылки, "
                "медиа и голосовые агрегируются по всему. Сеть и По участникам "
                "скрываются — они не имеют смысла на несвязанных чатах."
            ),
        )
        if combine_all:
            chat = loader.combined_chat(filtered)
            st.caption(
                i18n.t("Объединено: {n} чатов, {m} сообщений всего").format(
                    n=len(filtered), m=f"{len(chat.messages):,}".replace(",", " ")
                )
            )
        else:
            # Resolve chat preselection from URL (?chat=<id>) — falls back to 0.
            qp_chat = st.query_params.get("chat")
            default_idx = 0
            if qp_chat:
                for i, c in enumerate(filtered):
                    if str(c.id) == str(qp_chat):
                        default_idx = i
                        break
            idx = st.selectbox(
                i18n.t("Чат"),
                options=range(len(filtered)),
                format_func=lambda i: loader.chat_label(filtered[i]),
                index=default_idx,
            )
            chat = filtered[idx]
            st.query_params["chat"] = str(chat.id)

    st.caption(f"{i18n.t('ID чата')}: `{chat.id}`")

# Period filter — a compact popover button right-aligned above the hero,
# not a full-width filter strip. Label reflects current state, so the
# control IS the status indicator. Top-words slider lives inside Words tab.
bounds = overview.date_bounds(chat.messages)
date_range = None
init_from = init_to = min_d = max_d = None
prior_from = prior_to = None
if bounds is not None:
    import datetime as _dt

    min_d = _dt.date.fromisoformat(bounds[0])
    max_d = _dt.date.fromisoformat(bounds[1])
    qp_from = st.query_params.get("from")
    qp_to = st.query_params.get("to")
    try:
        init_from = _dt.date.fromisoformat(qp_from) if qp_from else min_d
        if init_from < min_d or init_from > max_d:
            init_from = min_d
    except ValueError:
        init_from = min_d
    try:
        init_to = _dt.date.fromisoformat(qp_to) if qp_to else max_d
        if init_to < min_d or init_to > max_d:
            init_to = max_d
    except ValueError:
        init_to = max_d
    prior_from = init_from.isoformat()
    prior_to = init_to.isoformat()

if bounds is not None:
    is_filtered_prior = (prior_from, prior_to) != bounds
    if is_filtered_prior:
        label = f"{i18n.t('Период')} · {prior_from} → {prior_to}"
    else:
        label = i18n.t("Период · вся история")
    _spacer, _period_col = st.columns([5, 2])
    with _period_col:
        with st.popover(label, use_container_width=True):
            date_range = st.date_input(
                i18n.t("Период"),
                value=(init_from, init_to),
                min_value=min_d,
                max_value=max_d,
                label_visibility="collapsed",
                help=i18n.t("Ограничивает анализ этим периодом. Отражается в URL."),
            )

if bounds is not None and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    from_d, to_d = date_range[0].isoformat(), date_range[1].isoformat()
elif bounds is not None:
    from_d, to_d = bounds
else:
    from_d, to_d = "0000-01-01", "9999-12-31"

is_filtered = bounds is not None and (from_d, to_d) != bounds
if is_filtered:
    st.query_params["from"] = from_d
    st.query_params["to"] = to_d
else:
    for k in ("from", "to"):
        if k in st.query_params:
            del st.query_params[k]

# Top-words count — default for tabs that don't expose their own slider
# (Channel, Per-user, Highlights). Words tab overrides this at its top.
most_com = 30

# Cache key — change identity when chat or date range changes so caches invalidate
cache_key = f"{json_path}::{chat.id}::{chat.type}::{from_d}::{to_d}"
sections = loader.sections_for_type(chat.type)

# Filter messages once and pass everywhere
if is_filtered:
    messages = ui_cache.filter_by_date(cache_key, chat.messages, from_d, to_d)
else:
    messages = chat.messages

# KPI row (computed on filtered set)
kpis = ui_cache.kpis(cache_key, messages)
if kpis.total_messages == 0:
    st.title(chat.name)
    st.warning(i18n.t("No messages in selected range."))
    st.stop()

# Hero block — auto-prose paragraph distilled from KPIs + timeline + grid
_per_day_data = ui_cache.per_day(cache_key, messages)
_grid_data = ui_cache.hour_weekday(cache_key, messages)
_streaks_data = ui_cache.streaks(cache_key, messages, None) if "highlights" in sections else None
hero = highlights_mod.build_hero(
    chat_name=chat.name,
    kpis=kpis,
    per_day=_per_day_data,
    grid=_grid_data,
    streaks=_streaks_data,
)
st.markdown(ui_components.hero_html(hero, chat.type, chat.id), unsafe_allow_html=True)

# Milestones — anniversary line under hero. Shows day-count, last-crossed
# message threshold, and time/messages until the next milestone. Skipped
# when there's no first_date (chat without dated messages).
_anniv = anniversaries_mod.compute(
    first_date=kpis.first_date,
    total_messages=kpis.total_messages,
    per_day=_per_day_data,
)
if _anniv.days_since_start > 0:
    _bits: list[str] = []
    _bits.append(
        i18n.t("{n}-й день вместе").format(n=ui_components.fmt_int(_anniv.days_since_start))
    )
    if _anniv.crossed_counts:
        _last = _anniv.crossed_counts[-1]
        if _last.when:
            _bits.append(
                i18n.t("{label} с {date}").format(
                    label=i18n.t(_last.label),
                    date=i18n.format_day(_last.when),
                )
            )
    if _anniv.upcoming_count and _anniv.upcoming_count.days_until is not None:
        _bits.append(
            i18n.t("до {label} ≈ {n} при текущем темпе").format(
                label=i18n.t(_anniv.upcoming_count.label),
                n=i18n.n_days(_anniv.upcoming_count.days_until),
            )
        )
    elif _anniv.upcoming_day:
        _bits.append(
            i18n.t("до {label} осталось {n}").format(
                label=i18n.t(_anniv.upcoming_day.label),
                n=i18n.n_days(_anniv.upcoming_day.days_until or 0),
            )
        )
    st.caption(" · ".join(_bits))

# Big-number cards. `Сервисных` (system events) was junk — replaced with
# voice-talked time, which says something about how the chat is actually used.
_ms_kpi = ui_cache.media(cache_key, messages)
_voice_str = (
    media_mod.humanize_duration(_ms_kpi.voice_total_seconds) if _ms_kpi.voice_count else "—"
)
_cols = st.columns(5)
_cards = [
    (i18n.t("Сообщений"), ui_components.fmt_int(kpis.total_messages)),
    (i18n.t("Участников"), ui_components.fmt_int(kpis.unique_users)),
    (i18n.t("Дней активно"), ui_components.fmt_int(kpis.days_active)),
    (i18n.t("Медиа"), ui_components.fmt_int(kpis.media_messages)),
    (i18n.t("Голосом"), _voice_str),
]
for col, (lbl, val) in zip(_cols, _cards):
    col.markdown(ui_components.bignum_html(lbl, val), unsafe_allow_html=True)

# Highlight cards — Spotify-Wrapped feel, max 4
_hl = highlights_mod.top_highlights(
    kpis=kpis, per_day=_per_day_data, grid=_grid_data, streaks=_streaks_data
)
if _hl:
    st.markdown(ui_components.highlights_grid_html(_hl), unsafe_allow_html=True)

# Build the tab list dynamically based on chat type
tab_specs = []
if "overview" in sections:
    tab_specs.append((i18n.t("Обзор"), "overview"))
if "graph" in sections:
    tab_specs.append((i18n.t("Сеть"), "graph"))
if "words" in sections:
    tab_specs.append((i18n.t("Слова"), "words"))
if "channel" in sections:
    tab_specs.append((i18n.t("Канал"), "channel"))
if "perusers" in sections:
    tab_specs.append((i18n.t("По участникам"), "perusers"))
if "highlights" in sections:
    tab_specs.append((i18n.t("Моменты"), "highlights"))

tabs = st.tabs([t[0] for t in tab_specs])

for tab, (_, key) in zip(tabs, tab_specs):
    with tab:
        if key == "overview":
            t0 = time.time()
            per_day = ui_cache.per_day(cache_key, messages)
            grid = ui_cache.hour_weekday(cache_key, messages)

            # Section 1: «Как часто» — timeline + calendar.
            # When streamlit-plotly-events is installed, clicking a point
            # on the timeline drills down to that day's stats below.
            try:
                from streamlit_plotly_events import plotly_events as _plotly_events
            except ImportError:
                _plotly_events = None

            st.markdown(f"### {i18n.t('Как часто пишут')}")
            if per_day:
                df = pd.DataFrame(per_day, columns=["date", "messages"])
                df["date"] = pd.to_datetime(df["date"])
                fig = px.area(df, x="date", y="messages", template="telanalysis")
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
                if _plotly_events is not None:
                    clicks = _plotly_events(
                        fig,
                        click_event=True,
                        hover_event=False,
                        select_event=False,
                        override_height=320,
                        key="overview_timeline",
                    )
                    if clicks:
                        clicked_iso = pd.to_datetime(clicks[0]["x"]).strftime("%Y-%m-%d")
                        st.session_state["selected_day"] = clicked_iso
                else:
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        i18n.t(
                            "Установите `streamlit-plotly-events` чтобы кликом по графику смотреть детали дня."
                        )
                    )

                cap = highlights_mod.caplet_peak_day(per_day)
                if cap:
                    st.caption(cap)
                cap_w = highlights_mod.caplet_peak_week(per_day)
                if cap_w:
                    st.caption(cap_w)

                # Drill-down panel for the selected day
                sel_day = st.session_state.get("selected_day")
                if sel_day:
                    drill_msgs = [
                        m
                        for m in messages
                        if isinstance(m, dict)
                        and isinstance(m.get("date"), str)
                        and m["date"].startswith(sel_day)
                    ]
                    dc1, dc2 = st.columns([4, 1])
                    dc1.markdown(
                        f"**{i18n.t('Выбран день: {d}').format(d=sel_day)}** · "
                        f"{i18n.n_messages(len(drill_msgs))}"
                    )
                    if dc2.button(f"× {i18n.t('очистить')}", key="clear_sel_day"):
                        del st.session_state["selected_day"]
                        st.rerun()
                    if drill_msgs:
                        from analysis import emoji_stats as _es

                        day_emoji = _es.analyze(drill_msgs)
                        if day_emoji.chat_top:
                            top3 = ", ".join(f"{e} ×{n}" for e, n in day_emoji.chat_top[:3])
                            st.caption(i18n.t("Топ эмоджи дня: {top}").format(top=top3))
                        sample = next(
                            (
                                m.get("text")
                                for m in drill_msgs
                                if isinstance(m.get("text"), str) and len(m.get("text")) > 20
                            ),
                            None,
                        )
                        if sample:
                            st.caption(i18n.t("пример: «{s}…»").format(s=sample[:140]))

                cal_fig = ui_components.calendar_heatmap_fig(df)
                if cal_fig is not None:
                    st.plotly_chart(cal_fig, use_container_width=True)
            else:
                st.info(i18n.t("No dated messages."))

            # Section 2: «Когда именно» — hour × weekday + 1-1 overlap + sessions
            if any(any(row) for row in grid):
                st.markdown(f"### {i18n.t('В какие часы')}")
                heat = go.Figure(
                    data=go.Heatmap(
                        z=grid,
                        x=list(range(24)),
                        y=i18n.weekday_short_labels(),
                        colorscale=theme_mod.HEAT_SCALE,
                        hovertemplate="%{y} %{x}:00<br>%{z}<extra></extra>",
                    )
                )
                heat.update_layout(
                    template="telanalysis",
                    height=280,
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(title="hour", dtick=2),
                    yaxis=dict(title=""),
                )
                st.plotly_chart(heat, use_container_width=True)
                cap_h = highlights_mod.caplet_peak_hour(grid)
                if cap_h:
                    st.caption(cap_h)
                cap_n = highlights_mod.caplet_night_share(grid)
                if cap_n:
                    st.caption(cap_n)

                user_hours = overview.hour_distribution_per_user(messages)
                if len(user_hours) == 2:
                    (uid_a, (name_a, hrs_a)), (uid_b, (name_b, hrs_b)) = list(user_hours.items())
                    total_a = sum(hrs_a) or 1
                    total_b = sum(hrs_b) or 1
                    norm_a = [h / total_a for h in hrs_a]
                    norm_b = [h / total_b for h in hrs_b]
                    ov = [min(a, b) for a, b in zip(norm_a, norm_b)]

                    fig_ovl = go.Figure()
                    fig_ovl.add_trace(
                        go.Bar(x=list(range(24)), y=norm_a, name=name_a, opacity=0.55)
                    )
                    fig_ovl.add_trace(
                        go.Bar(x=list(range(24)), y=norm_b, name=name_b, opacity=0.55)
                    )
                    fig_ovl.add_trace(
                        go.Bar(
                            x=list(range(24)),
                            y=ov,
                            name=i18n.t("оба активны"),
                            marker_color=theme_mod.PALETTE["success"],
                        )
                    )
                    fig_ovl.update_layout(
                        title=i18n.t("Когда совпадают активности"),
                        template="telanalysis",
                        height=280,
                        margin=dict(l=0, r=0, t=40, b=0),
                        xaxis=dict(title="hour", dtick=2),
                        yaxis=dict(title=""),
                        barmode="overlay",
                        legend=dict(orientation="h"),
                    )
                    st.plotly_chart(fig_ovl, use_container_width=True)
                    peak_overlap = max(range(24), key=lambda i: ov[i])
                    st.caption(
                        i18n.t(
                            "Пик совместной активности — около {h}:00. "
                            "Бары нормализованы пер-юзер — справедливо при разной активности."
                        ).format(h=f"{peak_overlap:02d}")
                    )

                # Conversation gap is chat-specific — couples talk in flurries
                # 5min apart, group chats might pause for hours mid-thread.
                # Slider lets the user pick what counts as a "session boundary".
                _gap_min = st.slider(
                    i18n.t("Граница разговора (минут паузы)"),
                    min_value=5,
                    max_value=180,
                    value=30,
                    step=5,
                    key="sessions_gap_min",
                    help=i18n.t("Если пауза между сообщениями больше — это уже новый разговор."),
                )
                sess_stats = ui_cache.sessions(cache_key, messages, gap_minutes=_gap_min)
                if sess_stats.sessions:
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric(i18n.t("Разговоров"), f"{len(sess_stats.sessions):,}")
                    sc2.metric(
                        i18n.t("Сообщ./разговор (avg)"),
                        f"{sess_stats.avg_messages:.1f}",
                        help=i18n.t("медиана {m}").format(m=sess_stats.median_messages),
                    )
                    if sess_stats.longest:
                        sc3.metric(
                            i18n.t("Самый долгий"),
                            i18n.n_messages(sess_stats.longest.msg_count),
                            help=(
                                f"{sess_stats.longest.start.date()} → "
                                f"{sess_stats.longest.end.date()}"
                            ),
                        )

                    # Conversation length distribution + top-10 longest.
                    # Avg/median above hide the shape — most chats are bursty
                    # (lots of 1-2 sessions and a fat tail of long ones).
                    if sess_stats.duration_buckets:
                        with st.expander(i18n.t("Распределение длин разговоров")):
                            dur_df = pd.DataFrame(
                                list(sess_stats.duration_buckets.items()),
                                columns=["bucket", "count"],
                            )
                            fig_dur = px.bar(
                                dur_df,
                                x="bucket",
                                y="count",
                                template="telanalysis",
                            )
                            fig_dur.update_layout(
                                height=240,
                                margin=dict(l=0, r=0, t=10, b=0),
                                xaxis=dict(title=i18n.t("сообщений в разговоре")),
                            )
                            st.plotly_chart(fig_dur, use_container_width=True)

                            # Top-10 longest sessions table — date, count, duration
                            top_sess = sorted(sess_stats.sessions, key=lambda s: -s.msg_count)[:10]
                            top_rows = []
                            for s in top_sess:
                                dur_min = int((s.end - s.start).total_seconds() / 60)
                                top_rows.append(
                                    {
                                        "date": s.start.strftime("%Y-%m-%d %H:%M"),
                                        "messages": s.msg_count,
                                        "duration": (
                                            f"{dur_min} min"
                                            if dur_min < 90
                                            else f"{dur_min // 60}h {dur_min % 60}m"
                                        ),
                                    }
                                )
                            st.dataframe(
                                pd.DataFrame(top_rows),
                                use_container_width=True,
                                hide_index=True,
                                height=320,
                            )

            # Section 3: «О чём говорят» — emojis + media + links
            es = ui_cache.emojis(cache_key, messages)
            ms = ui_cache.media(cache_key, messages)
            if es.chat_top or ms.by_kind:
                st.markdown(f"### {i18n.t('О чём говорят')}")

            if es.chat_top:
                emo_df = pd.DataFrame(es.chat_top, columns=["emoji", "count"])
                fig_emo = px.bar(emo_df.head(20), x="emoji", y="count", template="telanalysis")
                fig_emo.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_emo, use_container_width=True)
                cap_e = highlights_mod.caplet_top_emoji(es)
                if cap_e:
                    st.caption(cap_e)
                with st.expander(
                    i18n.t("Все эмоджи · {a} в {b} сообщ.").format(
                        a=f"{es.total_emojis:,}".replace(",", " "),
                        b=f"{es.messages_with_emoji:,}".replace(",", " "),
                    )
                ):
                    st.dataframe(emo_df, use_container_width=True, hide_index=True, height=300)

            if ms.by_kind:
                pie_df = pd.DataFrame(
                    [
                        {"kind": media_mod.kind_label(k), "count": v}
                        for k, v in sorted(ms.by_kind.items(), key=lambda x: -x[1])
                    ]
                )
                col_pie, col_voice = st.columns([2, 1])
                with col_pie:
                    fig_pie = px.pie(
                        pie_df,
                        names="kind",
                        values="count",
                        template="telanalysis",
                        title=i18n.t("Типы сообщений"),
                    )
                    fig_pie.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0))
                    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig_pie, use_container_width=True)
                with col_voice:
                    if ms.voice_count:
                        st.metric(i18n.t("Голосовые"), f"{ms.voice_count:,}")
                        st.metric(
                            i18n.t("Суммарно"),
                            media_mod.humanize_duration(ms.voice_total_seconds),
                        )
                        avg = ms.voice_total_seconds // ms.voice_count
                        st.metric(i18n.t("В среднем"), media_mod.humanize_duration(avg))
                cap_v = highlights_mod.caplet_voice_total(ms)
                if cap_v:
                    st.caption(cap_v)

                if ms.top_domains:
                    links_word = i18n.plural(
                        ms.total_links, "ссылка", "ссылки", "ссылок", "link", "links"
                    )
                    total_links_str = f"{ms.total_links:,}".replace(",", " ")
                    st.markdown(f"**{i18n.t('Топ доменов')}** · {total_links_str} {links_word}")
                    dom_df = pd.DataFrame(ms.top_domains, columns=["domain", "count"])
                    fig_dom = px.bar(dom_df.head(15), x="domain", y="count", template="telanalysis")
                    fig_dom.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig_dom, use_container_width=True)

            # Section 4: «Кто кому» — participants + reply latency
            participants = ui_cache.participants(cache_key, messages)
            lat = ui_cache.latency(cache_key, messages)
            if (participants and len(participants) > 1) or lat.overall_seconds:
                st.markdown(f"### {i18n.t('Кто кому')}")

            if lat.overall_seconds:
                lat_c1, lat_c2, lat_c3 = st.columns(3)
                lat_c1.metric(
                    i18n.t("Медиана ответа"),
                    latency_mod.humanize_seconds(lat.median_seconds),
                )
                lat_c2.metric(
                    i18n.t("p90 ответа"),
                    latency_mod.humanize_seconds(lat.p90_seconds),
                )
                lat_c3.metric(i18n.t("Всего ответов"), f"{len(lat.overall_seconds):,}")
                cap_l = highlights_mod.caplet_latency(lat)
                if cap_l:
                    st.caption(cap_l)
                if lat.dropped_over_cap:
                    _total_pairs = len(lat.overall_seconds) + lat.dropped_over_cap
                    _drop_pct = lat.dropped_over_cap * 100 / _total_pairs
                    st.caption(
                        i18n.t(
                            "{n} ответов (>{h}ч) не учтены в медиане/p90 — это {p}% всех пар."
                        ).format(
                            n=f"{lat.dropped_over_cap:,}".replace(",", " "),
                            h=lat.cap_hours,
                            p=f"{_drop_pct:.1f}",
                        )
                    )

                # Q&A subset — replies to messages containing '?'. Usually
                # faster than the chat-wide median (people respond quickly to
                # explicit questions); the gap shows responsiveness vs noise.
                if lat.qa_seconds:
                    delta = lat.qa_median_seconds - lat.median_seconds
                    delta_label = (
                        i18n.t("на {n} быстрее").format(n=latency_mod.humanize_seconds(abs(delta)))
                        if delta < 0
                        else i18n.t("на {n} медленнее").format(
                            n=latency_mod.humanize_seconds(delta)
                        )
                        if delta > 0
                        else i18n.t("так же")
                    )
                    qa_c1, qa_c2, qa_c3 = st.columns(3)
                    qa_c1.metric(
                        i18n.t("Q&A медиана"),
                        latency_mod.humanize_seconds(lat.qa_median_seconds),
                        help=i18n.t(
                            "Медиана ответа на сообщения с '?'. Сравнение с обычной "
                            "медианой ответа: {d}."
                        ).format(d=delta_label),
                    )
                    qa_c2.metric(
                        i18n.t("Q&A p90"),
                        latency_mod.humanize_seconds(lat.qa_p90_seconds),
                    )
                    qa_c3.metric(i18n.t("Q&A пар"), f"{len(lat.qa_seconds):,}")

            if participants:
                p_df = pd.DataFrame(participants, columns=["user_id", "name", "messages"])
                st.dataframe(p_df, use_container_width=True, hide_index=True, height=320)

            # Longest monologues — runs of N+ consecutive messages from one
            # user without anyone else interjecting. Storytelling vs venting
            # signal that the latency stats above completely hide.
            mono_stats = monologues_mod.analyze(messages, top_n=10, min_run=3)
            if mono_stats.longest:
                st.markdown(f"#### {i18n.t('Самые длинные монологи')}")
                st.caption(
                    i18n.t(
                        "Подряд N+ сообщений от одного юзера без ответа другого. "
                        "Высокий N — кто-то рассказывал длинную историю или выговаривался."
                    )
                )
                mono_rows = []
                for r in mono_stats.longest:
                    mins = int(r.duration_seconds / 60)
                    mono_rows.append(
                        {
                            "user": r.name,
                            "messages": r.msg_count,
                            "from": r.start.strftime("%Y-%m-%d %H:%M"),
                            "duration": f"{mins} min"
                            if mins < 90
                            else f"{mins // 60}h {mins % 60}m",
                        }
                    )
                st.dataframe(
                    pd.DataFrame(mono_rows),
                    use_container_width=True,
                    hide_index=True,
                    height=320,
                )

            st.caption(f"Rendered in {time.time() - t0:.1f}s")

        elif key == "graph":
            t0 = time.time()
            g = ui_cache.graph_data(cache_key, messages)
            chain_stats = chains_mod.analyze(messages)
            cgraph1, cgraph2, cgraph3, cgraph4 = st.columns(4)
            cgraph1.metric(i18n.t("Узлов"), f"{len(g.nodes):,}")
            cgraph2.metric(i18n.t("Связей"), f"{len(g.edges):,}")
            if chain_stats.chain_count:
                cgraph3.metric(
                    i18n.t("Макс. глубина reply"),
                    f"{chain_stats.max_depth}",
                    help=i18n.t(
                        "Длиннейшая цепочка quote-reply подряд. Глубина 1 = одиночный "
                        "ответ, 5+ = глубокая ветка с реплаями на реплаи."
                    ),
                )
                cgraph4.metric(
                    i18n.t("Сред. глубина reply"),
                    f"{chain_stats.avg_depth:.2f}",
                )
            if chain_stats.depth_distribution and chain_stats.max_depth > 1:
                cd_df = pd.DataFrame(chain_stats.depth_distribution, columns=["depth", "count"])
                fig_cd = px.bar(
                    cd_df,
                    x="depth",
                    y="count",
                    template="telanalysis",
                    title=i18n.t("Распределение глубины reply-цепочек"),
                )
                fig_cd.update_layout(
                    height=240,
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis=dict(title=i18n.t("глубина (хопов)"), dtick=1),
                )
                st.plotly_chart(fig_cd, use_container_width=True)

            if not g.nodes:
                st.info(i18n.t("No participants found in this chat (only service events?)."))
            else:
                # Interaction summary (always useful)
                summary = graph_mod.interaction_summary(messages)
                if summary:
                    sdf = pd.DataFrame(summary)
                    sdf_chart = sdf.melt(
                        id_vars=["user"],
                        value_vars=["sent", "replies_sent", "replies_received"],
                        var_name="metric",
                        value_name="count",
                    )
                    fig_int = px.bar(
                        sdf_chart,
                        x="user",
                        y="count",
                        color="metric",
                        barmode="group",
                        template="telanalysis",
                        title=i18n.t("Who messages, who replies"),
                    )
                    fig_int.update_layout(height=360, margin=dict(l=0, r=0, t=40, b=0))
                    st.plotly_chart(fig_int, use_container_width=True)
                    st.dataframe(
                        sdf.drop(columns=["user_id"]),
                        use_container_width=True,
                        hide_index=True,
                        height=240,
                    )

                # Force-directed graph only when there's structure to see
                if len(g.nodes) <= 3:
                    st.caption(
                        i18n.t(
                            "Граф скрыт: участников всего {n} — "
                            "бар-чарт выше уже рассказывает всю историю."
                        ).format(n=len(g.nodes))
                    )
                else:
                    with st.spinner(i18n.t("Drawing interactive graph…")):
                        html = graph_mod.render_pyvis_html(g, height="700px")
                    if html:
                        import streamlit.components.v1 as components

                        st.subheader(i18n.t("Граф ответов"))
                        components.html(html, height=720, scrolling=False)
                        st.caption(
                            i18n.t(
                                "Drag nodes · scroll to zoom · hover for details. "
                                "Edges merged by reply count, thickness ~ frequency. "
                                "Colours = communities (Louvain modularity)."
                            )
                        )
                    else:
                        st.warning(
                            i18n.t(
                                "Graph too large to render interactively "
                                "({n} nodes). Use the CSVs below in Gephi."
                            ).format(n=len(g.nodes))
                        )

            with st.expander(i18n.t("Download CSVs (Gephi-compatible)")):
                nodes_df = pd.DataFrame(g.nodes, columns=["id", "label", "weight"])
                edges_df = pd.DataFrame(g.edges, columns=["source", "target", "label"])
                c1, c2 = st.columns(2)
                c1.download_button(
                    "nodes.csv",
                    nodes_df.to_csv(index=False),
                    file_name=f"nodes_{chat.id}.csv",
                    mime="text/csv",
                )
                c2.download_button(
                    "edges.csv",
                    edges_df.to_csv(index=False),
                    file_name=f"edges_{chat.id}.csv",
                    mime="text/csv",
                )
            st.caption(f"Rendered in {time.time() - t0:.1f}s")

        elif key == "words":
            most_com = st.slider(
                i18n.t("Топ слов"),
                10,
                200,
                30,
                step=5,
                help=i18n.t("Сколько слов показывать в облаках и таблицах"),
            )
            t0 = time.time()
            res = ui_cache.words(cache_key, messages, most_com)

            cwords1, cwords2, cwords3 = st.columns(3)
            cwords1.metric(i18n.t("Проанализировано юзеров"), f"{len(res.users):,}")
            cwords2.metric(i18n.t("Email-ов"), f"{len(res.emails):,}")
            cwords3.metric(i18n.t("Телефонов"), f"{len(res.phones):,}")

            st.subheader(i18n.t("Топ {n} слов по чату").format(n=len(res.chat_top_words)))
            if res.chat_top_words:
                wc_png = render_mod.wordcloud_png(res.chat_top_words)
                if wc_png:
                    st.image(wc_png, caption=i18n.t("Облако слов (по всему чату)"))

                top_df = pd.DataFrame(res.chat_top_words, columns=["word", "count"])
                fig_top = px.bar(
                    top_df.head(30),
                    x="word",
                    y="count",
                    template="telanalysis",
                    title=i18n.t("Топ 30 из {total}").format(total=len(top_df)),
                )
                fig_top.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_top, use_container_width=True)
                st.dataframe(top_df, use_container_width=True, hide_index=True, height=300)
                if res.sentiment_available:
                    sarcasm_note = (
                        i18n.t(
                            " · {n} фрагментов уполовинены sarcasm-emoji эвристикой (🙃🤡🙄💀…)"
                        ).format(n=f"{res.sarcasm_marked:,}".replace(",", " "))
                        if res.sarcasm_marked
                        else ""
                    )
                    st.caption(
                        i18n.t(
                            "Средний сентимент (rubert-tiny2-russian-sentiment, RU/EN): "
                            "{s} (диапазон −1 негативно … +1 позитивно){extra}. "
                            "⚠ Не понимает сарказм, шутки и слэнг — числа берите со скепсисом."
                        ).format(s=f"{res.chat_avg_sentiment:+.3f}", extra=sarcasm_note)
                    )
                else:
                    st.info(
                        i18n.t(
                            "Сентимент-анализ **отключён** — установи опциональные "
                            "зависимости чтобы включить оценки RU/EN:\n\n"
                            "```\npip install -r requirements-sentiment.txt\n```\n\n"
                            "Добавит ~1GB (torch + transformers) плюс 50MB модель при "
                            "первом запуске. Перезапусти Streamlit после установки. "
                            "Модель не выкупает сарказм, шутки и слэнг — это curiosity-фича, не диагностика."
                        )
                    )

            # Sentiment over time (chat-wide + per-user)
            if res.sentiment_available and res.dated_scores:
                with st.expander(i18n.t("Сентимент во времени")):
                    series_chat = words_mod.sentiment_period_series(
                        res.dated_scores, granularity="week", per_user=False
                    )
                    if series_chat:
                        s_df = pd.DataFrame(series_chat)
                        s_df["period"] = pd.to_datetime(s_df["period"])
                        fig_chat = px.line(
                            s_df,
                            x="period",
                            y="avg",
                            template="telanalysis",
                            markers=True,
                            title=i18n.t("Средний сентимент по чату (по неделям)"),
                        )
                        fig_chat.add_hline(y=0, line_dash="dot", line_color="gray")
                        fig_chat.update_layout(
                            height=320,
                            margin=dict(l=0, r=0, t=40, b=0),
                            yaxis_title=i18n.t("среднее compound"),
                        )
                        st.plotly_chart(fig_chat, use_container_width=True)

                    # per-user overlay if 2+ users
                    if len(res.users) >= 2:
                        per_u = words_mod.sentiment_period_series(
                            res.dated_scores, granularity="week", per_user=True
                        )
                        if per_u:
                            u_df = pd.DataFrame(per_u)
                            u_df["period"] = pd.to_datetime(u_df["period"])
                            u_df["user"] = u_df["user_id"].map(
                                lambda uid: res.users.get(uid).name if res.users.get(uid) else uid
                            )
                            fig_u = px.line(
                                u_df,
                                x="period",
                                y="avg",
                                color="user",
                                template="telanalysis",
                                markers=True,
                                title=i18n.t("Средний сентимент по участникам (по неделям)"),
                            )
                            fig_u.add_hline(y=0, line_dash="dot", line_color="gray")
                            fig_u.update_layout(
                                height=380,
                                margin=dict(l=0, r=0, t=40, b=0),
                                yaxis_title=i18n.t("среднее compound"),
                                legend_title="",
                            )
                            st.plotly_chart(fig_u, use_container_width=True)

                    # Sentiment by hour-of-day & weekday — circadian / weekly
                    # rhythm of mood. Часто противоположно weekly trend:
                    # weekly показывает ровно, а hour может скакать утром vs вечером.
                    by_hour = words_mod.sentiment_by_hour(res.dated_scores)
                    by_wd = words_mod.sentiment_by_weekday(res.dated_scores)
                    if by_hour or by_wd:
                        s_h_col, s_wd_col = st.columns(2)
                        if by_hour:
                            with s_h_col:
                                hh_df = pd.DataFrame(by_hour)
                                fig_h = px.bar(
                                    hh_df,
                                    x="hour",
                                    y="avg",
                                    template="telanalysis",
                                    title=i18n.t("По часу дня"),
                                )
                                fig_h.add_hline(y=0, line_dash="dot", line_color="gray")
                                fig_h.update_layout(
                                    height=240,
                                    margin=dict(l=0, r=0, t=40, b=0),
                                    xaxis=dict(title=i18n.t("час"), dtick=2),
                                    yaxis=dict(title=i18n.t("среднее compound")),
                                )
                                st.plotly_chart(fig_h, use_container_width=True)
                        if by_wd:
                            with s_wd_col:
                                wd_df = pd.DataFrame(by_wd)
                                wd_labels = i18n.weekday_short_labels()
                                wd_df["weekday"] = wd_df["weekday"].map(lambda w: wd_labels[w])
                                fig_wd = px.bar(
                                    wd_df,
                                    x="weekday",
                                    y="avg",
                                    template="telanalysis",
                                    title=i18n.t("По дню недели"),
                                )
                                fig_wd.add_hline(y=0, line_dash="dot", line_color="gray")
                                fig_wd.update_layout(
                                    height=240,
                                    margin=dict(l=0, r=0, t=40, b=0),
                                    xaxis=dict(title=""),
                                    yaxis=dict(title=i18n.t("среднее compound")),
                                )
                                st.plotly_chart(fig_wd, use_container_width=True)

                    st.caption(
                        i18n.t(
                            "⚠ Sentiment не выкупает сарказм, шутки и слэнг. "
                            "Используй для тренда, не для абсолютных значений."
                        )
                    )

            # Extreme messages drill-down
            if res.sentiment_available and res.users:
                st.subheader(i18n.t("Крайние сообщения"))
                # Build a flat list of (text, sentiment, user_name)
                all_msgs = []
                for u in res.users.values():
                    for txt, s in u.messages:
                        if isinstance(s, float) and txt and abs(s) > 0.05:
                            all_msgs.append((txt, s, u.name))
                if all_msgs:
                    extr_n = st.slider(
                        i18n.t("Сколько крайних показывать"),
                        5,
                        50,
                        10,
                        step=5,
                        key="extr_n",
                    )
                    most_pos = sorted(all_msgs, key=lambda r: -r[1])[:extr_n]
                    most_neg = sorted(all_msgs, key=lambda r: r[1])[:extr_n]
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        st.caption(i18n.t("Самые позитивные ({n})").format(n=extr_n))
                        st.dataframe(
                            pd.DataFrame(most_pos, columns=["text", "sentiment", "user"]),
                            use_container_width=True,
                            hide_index=True,
                            height=400,
                        )
                    with ec2:
                        st.caption(i18n.t("Самые негативные ({n})").format(n=extr_n))
                        st.dataframe(
                            pd.DataFrame(most_neg, columns=["text", "sentiment", "user"]),
                            use_container_width=True,
                            hide_index=True,
                            height=400,
                        )

            # Repeated phrases (n-grams)
            st.subheader(i18n.t("Повторяющиеся фразы"))
            n_choice = st.radio(
                i18n.t("Длина фразы"),
                options=["bi", "tri"],
                format_func=lambda x: (
                    i18n.t("биграммы (2 слова)") if x == "bi" else i18n.t("триграммы (3 слова)")
                ),
                horizontal=True,
                key="phr_n",
            )
            n_words = 2 if n_choice == "bi" else 3
            phr = ui_cache.phrases(cache_key, messages, n=n_words, top=30)
            if phr:
                phr_df = pd.DataFrame(phr, columns=["phrase", "count"])
                fig_phr = px.bar(
                    phr_df,
                    x="phrase",
                    y="count",
                    template="telanalysis",
                )
                fig_phr.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_phr, use_container_width=True)
                st.dataframe(phr_df, use_container_width=True, hide_index=True, height=300)
            else:
                st.caption(i18n.t("Повторяющихся фраз не найдено."))

            # Word trend over time
            st.subheader(i18n.t("Слова во времени"))
            term_input = st.text_input(
                i18n.t("Слова для отслеживания (через запятую)"),
                placeholder=i18n.t("например: привет, спасибо, люблю"),
                key="word_trend_input",
            )
            if term_input.strip():
                terms = [t.strip() for t in term_input.split(",") if t.strip()]
                granularity = st.radio(
                    i18n.t("Гранулярность"),
                    options=["week", "day", "month"],
                    format_func=lambda x: i18n.t(
                        {"week": "неделя", "day": "день", "month": "месяц"}[x]
                    ),
                    index=0,
                    horizontal=True,
                    key="word_trend_gran",
                )
                with st.spinner(i18n.t("Считаю…")):
                    trends = words_mod.word_timeline(messages, terms, granularity=granularity)
                series_rows = []
                for term, series in trends.items():
                    for date_iso, count in series:
                        series_rows.append({"date": date_iso, "count": count, "term": term})
                if series_rows:
                    tdf = pd.DataFrame(series_rows)
                    tdf["date"] = pd.to_datetime(tdf["date"])
                    fig_tr = px.line(
                        tdf,
                        x="date",
                        y="count",
                        color="term",
                        template="telanalysis",
                        markers=True,
                    )
                    fig_tr.update_layout(
                        height=380,
                        margin=dict(l=0, r=0, t=10, b=0),
                        legend_title="",
                    )
                    st.plotly_chart(fig_tr, use_container_width=True)
                    totals = (
                        tdf.groupby("term")["count"]
                        .sum()
                        .reset_index()
                        .sort_values("count", ascending=False)
                    )
                    st.dataframe(
                        totals,
                        use_container_width=True,
                        hide_index=True,
                        height=200,
                    )
                else:
                    st.caption(i18n.t("Совпадений нет."))

            # Vocabulary richness — MTLD (length-insensitive lexical diversity)
            if res.users and any(u.total_tokens > 0 for u in res.users.values()):
                st.subheader(i18n.t("Богатство словаря"))
                voc_rows = [
                    {
                        "user": u.name,
                        "total_tokens": u.total_tokens,
                        "unique_tokens": u.unique_tokens,
                        "MTLD": round(u.mtld, 1),
                        "TTR": round(u.ttr, 3),
                    }
                    for u in res.users.values()
                    if u.total_tokens > 0
                ]
                voc_df = pd.DataFrame(voc_rows).sort_values("MTLD", ascending=False)
                st.caption(
                    i18n.t(
                        "MTLD = средняя длина прогона до того как TTR упадёт до 0.72. "
                        "Выше = разнообразнее словарь. В отличие от голого TTR, "
                        "не зависит от длины выборки — справедливо сравнивать. "
                        "MTLD < 50 для коротких выборок недостоверен."
                    )
                )
                st.dataframe(
                    voc_df,
                    use_container_width=True,
                    hide_index=True,
                    height=240,
                )

            if res.users:
                st.subheader(i18n.t("По участникам"))
                user_options = sorted(
                    res.users.values(),
                    key=lambda u: -len(u.messages),
                )
                pick = st.selectbox(
                    i18n.t("Участник"),
                    options=user_options,
                    format_func=lambda u: f"{u.name} · {i18n.n_messages(len(u.messages))}",
                )
                if pick is not None:
                    cu1, cu2 = st.columns(2)
                    with cu1:
                        if res.sentiment_available:
                            st.caption(
                                i18n.t(
                                    "Средний сентимент: {s} ⚠ не учитывает сарказм/шутки/слэнг"
                                ).format(s=f"{pick.avg_sentiment:+.2f}")
                            )
                        if pick.top_words:
                            tw = pd.DataFrame(pick.top_words, columns=["word", "count"])
                            st.dataframe(
                                tw,
                                use_container_width=True,
                                hide_index=True,
                                height=300,
                            )
                    with cu2:
                        if res.sentiment_available:
                            m_df = pd.DataFrame(
                                pick.messages,
                                columns=["text", "sentiment"],
                            )
                        else:
                            m_df = pd.DataFrame(
                                [(t,) for t, _ in pick.messages],
                                columns=["text"],
                            )
                        st.caption(
                            i18n.t("Все {n} фрагментов сообщений").format(
                                n=f"{len(m_df):,}".replace(",", " ")
                            )
                        )
                        st.dataframe(
                            m_df,
                            use_container_width=True,
                            hide_index=True,
                            height=400,
                        )

            if res.emails or res.phones:
                with st.expander(
                    i18n.t("Найдены контакты: {e} email, {p} телефонов").format(
                        e=len(res.emails), p=len(res.phones)
                    )
                ):
                    cc1, cc2 = st.columns(2)
                    cc1.dataframe(
                        pd.DataFrame(res.emails, columns=["email"]),
                        use_container_width=True,
                        hide_index=True,
                    )
                    cc2.dataframe(
                        pd.DataFrame(res.phones, columns=["phone"]),
                        use_container_width=True,
                        hide_index=True,
                    )
            st.caption(f"Rendered in {time.time() - t0:.1f}s")

        elif key == "channel":
            t0 = time.time()
            res = ui_cache.channel(cache_key, messages, most_com)
            cc1, cc2 = st.columns(2)
            cc1.metric(i18n.t("Топ слов"), f"{len(res.top_words):,}")
            cc2.metric(i18n.t("Токенов (raw)"), f"{res.token_count:,}")

            if res.wordcloud_png:
                st.image(res.wordcloud_png, caption=i18n.t("Облако слов"))
            else:
                st.info(i18n.t("Текста недостаточно для облака слов."))

            if res.top_words:
                top_df = pd.DataFrame(res.top_words, columns=["word", "count"])
                fig_top = px.bar(
                    top_df.head(50),
                    x="word",
                    y="count",
                    template="telanalysis",
                    title=i18n.t("Топ 50 из {total}").format(total=len(top_df)),
                )
                fig_top.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_top, use_container_width=True)
                st.dataframe(top_df, use_container_width=True, hide_index=True, height=400)
            st.caption(f"Rendered in {time.time() - t0:.1f}s")

        elif key == "perusers":
            t0 = time.time()
            participants = ui_cache.participants(cache_key, messages)
            if not participants:
                st.info(i18n.t("В этом чате нет идентифицируемых участников."))
            else:
                # Pick a user
                pu_options = participants  # already sorted desc by msg count
                pick_idx = st.selectbox(
                    i18n.t("Выбери участника"),
                    options=range(len(pu_options)),
                    format_func=lambda i: (
                        f"{pu_options[i][1]} · {i18n.n_messages(pu_options[i][2])}"
                    ),
                    key="pu_pick",
                )
                user_id, user_name, user_msg_count = pu_options[pick_idx]

                # Filter messages by this user once
                user_msgs = [
                    m
                    for m in messages
                    if isinstance(m, dict)
                    and (m.get("from_id") == user_id or m.get("actor_id") == user_id)
                ]

                pu_k1, pu_k2, pu_k3 = st.columns(3)
                pu_k1.metric(i18n.t("Участник"), user_name)
                pu_k2.metric(i18n.t("Сообщений"), f"{user_msg_count:,}")
                pu_k3.metric(
                    i18n.t("Доля чата"),
                    f"{100 * user_msg_count / max(kpis.total_messages, 1):.1f}%",
                )

                # Speaking style
                speak = ui_cache.speaking(cache_key, messages)
                style = speak.get(user_id)
                if style is not None:
                    st.subheader(i18n.t("Манера речи"))
                    # Three core length metrics. Median is primary (avg gets
                    # blown out by 5000-char outliers); avg is in the tooltip.
                    s1, s2, s3 = st.columns(3)
                    s1.metric(
                        i18n.t("Длина (медиана)"),
                        i18n.t("{n} симв.").format(n=f"{style.median_chars:,}"),
                        help=i18n.t("В среднем {a} симв., самое длинное {l}").format(
                            a=f"{style.avg_chars:.0f}",
                            l=f"{style.longest_chars:,}",
                        ),
                    )
                    s2.metric(i18n.t("Слов в сообщении"), f"{style.avg_words:.1f}")
                    s3.metric(
                        i18n.t("Самое длинное"),
                        i18n.t("{n} симв.").format(n=f"{style.longest_chars:,}"),
                    )

                    # First-message-of-day — earliest time per day (median).
                    # "When does this person actually wake up the chat" — much
                    # sharper than time_of_day buckets which conflate volume
                    # and earliness.
                    if style.first_msg_minutes:
                        f_med = style.first_msg_median_hhmm
                        f_other = [
                            (s.name, s.first_msg_median_hhmm)
                            for s in sorted(speak.values(), key=lambda x: -x.msg_count)
                            if s.user_id != user_id and s.first_msg_minutes
                        ]
                        f1, f2 = st.columns([1, 2])
                        f1.metric(
                            i18n.t("Первое сообщение дня (медиана)"),
                            f_med,
                            help=i18n.t(
                                "Самое раннее сообщение, усреднённое по всем активным дням. "
                                "Нижнее = жаворонок, более позднее = сова."
                            ),
                        )
                        if f_other:
                            f2.caption(
                                i18n.t("у других: ") + ", ".join(f"{n} — {t}" for n, t in f_other)
                            )

                        # Box plot across participants when there's >1 user
                        if len([s for s in speak.values() if s.first_msg_minutes]) >= 2:
                            fm_rows = []
                            for s in sorted(speak.values(), key=lambda x: -x.msg_count):
                                for mins in s.first_msg_minutes:
                                    fm_rows.append({"user": s.name, "hour": mins / 60})
                            if fm_rows:
                                fm_df = pd.DataFrame(fm_rows)
                                fig_fm = px.box(
                                    fm_df,
                                    x="user",
                                    y="hour",
                                    template="telanalysis",
                                    points=False,
                                )
                                fig_fm.update_layout(
                                    height=240,
                                    margin=dict(l=0, r=0, t=10, b=0),
                                    yaxis=dict(
                                        title=i18n.t("час дня"),
                                        range=[0, 24],
                                        dtick=4,
                                    ),
                                    xaxis=dict(title=""),
                                )
                                st.plotly_chart(fig_fm, use_container_width=True)

                    # Radar of tone signals — all participants overlaid so you
                    # can see how the picked user compares. Each axis is a
                    # ratio normalized to 0-100.
                    if len(speak) >= 2:
                        axes = [
                            i18n.t("вопросы %"),
                            i18n.t("восклицания %"),
                            i18n.t("ALL-CAPS %"),
                            i18n.t("реплаи %"),
                        ]
                        fig_rad = go.Figure()
                        for st_obj in sorted(speak.values(), key=lambda x: -x.msg_count):
                            vals = [
                                st_obj.question_ratio * 100,
                                st_obj.exclamation_ratio * 100,
                                st_obj.caps_ratio * 100,
                                st_obj.reply_ratio * 100,
                            ]
                            is_picked = st_obj.user_id == user_id
                            fig_rad.add_trace(
                                go.Scatterpolar(
                                    r=vals + [vals[0]],
                                    theta=axes + [axes[0]],
                                    fill="toself" if is_picked else "none",
                                    name=st_obj.name,
                                    opacity=1.0 if is_picked else 0.5,
                                )
                            )
                        fig_rad.update_layout(
                            template="telanalysis",
                            height=320,
                            margin=dict(l=0, r=0, t=10, b=0),
                            polar=dict(radialaxis=dict(visible=True)),
                            legend=dict(orientation="h"),
                        )
                        st.plotly_chart(fig_rad, use_container_width=True)
                    else:
                        # Single-user fallback to flat metrics
                        r1, r2, r3, r4 = st.columns(4)
                        r1.metric(
                            i18n.t("Доля вопросов"),
                            f"{style.question_ratio * 100:.1f}%",
                        )
                        r2.metric(
                            i18n.t("Доля восклицаний"),
                            f"{style.exclamation_ratio * 100:.1f}%",
                        )
                        r3.metric(
                            i18n.t("Доля ALL-CAPS"),
                            f"{style.caps_ratio * 100:.1f}%",
                        )
                        r4.metric(
                            i18n.t("Доля реплаев"),
                            f"{style.reply_ratio * 100:.1f}%",
                            help=i18n.t(
                                "Доля сообщений-ответов на конкретное другое (quote-reply)"
                            ),
                        )

                    # Forwards: %-of-msgs reshared from elsewhere + top sources.
                    # Surfaces "reposter" vs "original-thinker" stance.
                    fwd_stats = forwards_mod.analyze(messages, top_sources=5)
                    fwd = fwd_stats.per_user.get(user_id)
                    if fwd and fwd.total_messages and fwd.forwarded_count:
                        st.subheader(i18n.t("Пересылки"))
                        fc1, fc2 = st.columns([1, 3])
                        fc1.metric(
                            i18n.t("Доля пересылок"),
                            f"{fwd.forwarded_ratio * 100:.1f}%",
                            help=i18n.t("{n} из {t} сообщений — пересылки откуда-то ещё.").format(
                                n=fwd.forwarded_count, t=fwd.total_messages
                            ),
                        )
                        if fwd.top_sources:
                            with fc2:
                                st.caption(i18n.t("Топ источников:"))
                                src_df = pd.DataFrame(fwd.top_sources, columns=["source", "count"])
                                st.dataframe(
                                    src_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    height=180,
                                )
                    # Time-of-day persona + length distribution
                    cp1, cp2 = st.columns(2)
                    with cp1:
                        st.markdown(f"**{style.persona}** · {i18n.t('время суток')}")
                        tod_df = pd.DataFrame(
                            [
                                {"bucket": k, "count": style.time_of_day.get(k, 0)}
                                for k in ["night", "morning", "day", "evening"]
                            ]
                        )
                        fig_tod = px.bar(
                            tod_df,
                            x="bucket",
                            y="count",
                            template="telanalysis",
                            color_discrete_sequence=["#5B8FF9"],
                        )
                        fig_tod.update_layout(height=240, margin=dict(l=0, r=0, t=10, b=0))
                        st.plotly_chart(fig_tod, use_container_width=True)
                    with cp2:
                        st.markdown(f"**{style.length_persona}** · {i18n.t('длина сообщения')}")
                        lb_df = pd.DataFrame(
                            [
                                {"bucket": k, "count": style.length_buckets.get(k, 0)}
                                for k in ["<30", "30-100", "100-300", "300+"]
                            ]
                        )
                        fig_lb = px.bar(
                            lb_df,
                            x="bucket",
                            y="count",
                            template="telanalysis",
                            color_discrete_sequence=["#5AD8A6"],
                        )
                        fig_lb.update_layout(height=240, margin=dict(l=0, r=0, t=10, b=0))
                        st.plotly_chart(fig_lb, use_container_width=True)

                # Reciprocity (when 2-user chat)
                rec = ui_cache.reciprocity(cache_key, messages)
                if rec.available and rec.a_to_b and rec.b_to_a:
                    # Find direction where THIS user is the responder
                    my_dir = rec.a_to_b if rec.a_to_b.responder_id == user_id else rec.b_to_a
                    other_dir = rec.b_to_a if my_dir is rec.a_to_b else rec.a_to_b
                    if my_dir is not None:
                        st.subheader(i18n.t("Взаимность ответов"))
                        rec1, rec2, rec3 = st.columns(3)
                        rec1.metric(
                            i18n.t("{name}: медианный ответ").format(name=user_name),
                            latency_mod.humanize_seconds(my_dir.median_seconds),
                            help=i18n.t("к {n}").format(n=my_dir.initiator_name),
                        )
                        rec2.metric(
                            i18n.t("За 5 мин"),
                            f"{my_dir.within_5m * 100:.1f}%",
                        )
                        rec3.metric(
                            i18n.t("За 1 час"),
                            f"{my_dir.within_60m * 100:.1f}%",
                        )
                        # Comparison: how does this differ from the other direction
                        delta_5m = (my_dir.within_5m - other_dir.within_5m) * 100
                        st.caption(
                            i18n.t(
                                "Обратное — {a} → {b}: медиана {m}, "
                                "за 5м {p}%. Разница 5-мин ответа: **{d:+.1f} pp**"
                            ).format(
                                a=other_dir.initiator_name,
                                b=other_dir.responder_name,
                                m=latency_mod.humanize_seconds(other_dir.median_seconds),
                                p=f"{other_dir.within_5m * 100:.1f}",
                                d=delta_5m,
                            )
                        )

                # Streaks & silences for this user
                pu_streaks = ui_cache.streaks(cache_key, messages, filter_uid=user_id)
                if pu_streaks.total_active_days:
                    st.subheader(i18n.t("Стрики и молчания"))
                    sk1, sk2, sk3 = st.columns(3)
                    sk1.metric(
                        i18n.t("Самый длинный стрик"),
                        i18n.n_days(pu_streaks.longest_streak_days),
                        help=f"{pu_streaks.longest_streak_start} → {pu_streaks.longest_streak_end}",
                    )
                    sk2.metric(
                        i18n.t("Текущий стрик"),
                        i18n.n_days(pu_streaks.current_streak_days),
                    )
                    sk3.metric(
                        i18n.t("Всего активных дней"),
                        f"{pu_streaks.total_active_days:,}",
                    )
                    if pu_streaks.longest_silences:
                        sil_df = pd.DataFrame(
                            pu_streaks.longest_silences,
                            columns=["from", "to", "days"],
                        )
                        with st.expander(
                            i18n.t("Самые долгие молчания ({n})").format(n=len(sil_df))
                        ):
                            st.dataframe(
                                sil_df,
                                use_container_width=True,
                                hide_index=True,
                                height=240,
                            )

                # Conversation initiator share for this user
                pu_init = ui_cache.initiators(cache_key, messages, gap_hours=4)
                if pu_init.total_initiations:
                    my_row = next(
                        (r for r in pu_init.rows if r.user_id == user_id),
                        None,
                    )
                    if my_row is not None:
                        st.subheader(i18n.t("Кто начинает разговор"))
                        i1, i2 = st.columns(2)
                        i1.metric(
                            i18n.t("Инициаций после паузы 4ч+"),
                            f"{my_row.initiations:,}",
                        )
                        i2.metric(
                            i18n.t("Доля всех инициаций"),
                            f"{my_row.share * 100:.1f}%",
                        )
                        # Low-N caveat: with few initiations the share is noise.
                        # Surface this so the percentage isn't taken as fact.
                        if pu_init.total_initiations < 30:
                            st.caption(
                                i18n.t(
                                    "⚠ Всего инициаций {n} — выборка маленькая, "
                                    "процент может быть случайным."
                                ).format(n=pu_init.total_initiations)
                            )

                # Daily timeline
                pu_per_day = overview.messages_per_day(user_msgs)
                if pu_per_day:
                    pu_df = pd.DataFrame(pu_per_day, columns=["date", "messages"])
                    pu_df["date"] = pd.to_datetime(pu_df["date"])
                    fig_pu = px.area(
                        pu_df,
                        x="date",
                        y="messages",
                        template="telanalysis",
                        title=i18n.t("{name} — ежедневная активность").format(name=user_name),
                    )
                    fig_pu.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
                    st.plotly_chart(fig_pu, use_container_width=True)

                # Hour × weekday
                pu_grid = overview.hour_weekday_heatmap(user_msgs)
                if any(any(row) for row in pu_grid):
                    heat = go.Figure(
                        data=go.Heatmap(
                            z=pu_grid,
                            x=list(range(24)),
                            y=i18n.weekday_short_labels(),
                            colorscale="Plasma",
                            hovertemplate="%{y} %{x}:00<br>%{z}<extra></extra>",
                        )
                    )
                    heat.update_layout(
                        title=i18n.t("{name} — час × день недели").format(name=user_name),
                        template="telanalysis",
                        height=280,
                        margin=dict(l=0, r=0, t=40, b=0),
                        xaxis=dict(title="hour", dtick=2),
                    )
                    st.plotly_chart(heat, use_container_width=True)

                col_a, col_b = st.columns(2)

                # Top emojis for this user
                with col_a:
                    es = ui_cache.emojis(cache_key, messages)
                    user_emo = es.per_user.get(user_id, [])
                    st.subheader(i18n.t("Топ эмоджи"))
                    if user_emo:
                        emo_df = pd.DataFrame(user_emo, columns=["emoji", "count"])
                        st.dataframe(
                            emo_df,
                            use_container_width=True,
                            hide_index=True,
                            height=300,
                        )
                    else:
                        st.caption(i18n.t("Эмоджи не найдены."))

                # Reply latency for this user (responder)
                with col_b:
                    lat = ui_cache.latency(cache_key, messages)
                    user_lats = lat.per_user_seconds.get(user_id, [])
                    st.subheader(i18n.t("Скорость ответа"))
                    if user_lats:
                        sorted_lats = sorted(user_lats)
                        median = sorted_lats[len(sorted_lats) // 2]
                        p90 = sorted_lats[int(len(sorted_lats) * 0.9)]
                        st.caption(
                            i18n.t("Медиана {m} · p90 {p} · {n}").format(
                                m=latency_mod.humanize_seconds(median),
                                p=latency_mod.humanize_seconds(p90),
                                n=i18n.n_replies(len(user_lats)),
                            )
                        )
                        fig_lat_pu = px.histogram(
                            x=[s / 60 for s in user_lats],
                            nbins=60,
                            template="telanalysis",
                            log_y=True,
                        )
                        fig_lat_pu.update_layout(
                            height=260,
                            margin=dict(l=0, r=0, t=10, b=0),
                            xaxis_title=i18n.t("минут"),
                            yaxis_title=i18n.t("count (log)"),
                        )
                        st.plotly_chart(fig_lat_pu, use_container_width=True)
                    else:
                        st.caption(i18n.t("У этого участника нет ответов."))

                # Top words for this user (reuse words analyzer)
                wres = ui_cache.words(cache_key, messages, most_com)
                user_stat = wres.users.get(user_id)
                if user_stat and user_stat.total_tokens > 0:
                    vk1, vk2, vk3 = st.columns(3)
                    vk1.metric(i18n.t("Всего токенов"), f"{user_stat.total_tokens:,}")
                    vk2.metric(i18n.t("Уникальных токенов"), f"{user_stat.unique_tokens:,}")
                    vk3.metric(
                        i18n.t("MTLD (разнообразие)"),
                        f"{user_stat.mtld:.1f}" if user_stat.mtld else "—",
                        help=i18n.t(
                            "Measure of Textual Lexical Diversity. Длина прогона "
                            "до падения TTR ниже 0.72. Не зависит от длины выборки."
                        ),
                    )
                if user_stat and user_stat.top_words:
                    st.subheader(i18n.t("Топ {n} слов").format(n=len(user_stat.top_words)))
                    tw_df = pd.DataFrame(user_stat.top_words, columns=["word", "count"])
                    st.dataframe(
                        tw_df,
                        use_container_width=True,
                        hide_index=True,
                        height=300,
                    )

                # Mat (RU profanity) per-user table. Compares all participants
                # so you see who swears more in this chat — single user gives
                # only context-free numbers, comparison gives the relative.
                mat_stats = mat_mod.analyze(messages)
                if mat_stats.per_user and any(u.mat_hits > 0 for u in mat_stats.per_user.values()):
                    st.subheader(i18n.t("Мат"))
                    st.caption(
                        i18n.t(
                            "Совпадение по корням (хуй, пизд, ебат, бляд...) с word boundary. "
                            "Может ловить и редкие нейтральные слова."
                        )
                    )
                    mat_rows = []
                    for u in sorted(
                        mat_stats.per_user.values(),
                        key=lambda x: -x.hits_per_100,
                    ):
                        mat_rows.append(
                            {
                                "user": u.name,
                                "msgs": u.total_messages,
                                "msgs with mat": u.mat_messages,
                                "% msgs": round(u.msg_share * 100, 1),
                                "hits": u.mat_hits,
                                "hits/100msgs": round(u.hits_per_100, 1),
                            }
                        )
                    st.dataframe(
                        pd.DataFrame(mat_rows),
                        use_container_width=True,
                        hide_index=True,
                        height=180,
                    )

                # Distinguishing words (log-odds) — what THIS user says that
                # the other doesn't. Surfaces actual style signal, unlike raw
                # top_words which is dominated by words both share.
                if user_stat and len(wres.users) == 2:
                    other_uid = next(uid for uid in wres.users if uid != user_id)
                    other_stat = wres.users[other_uid]
                    if user_stat._tokens and other_stat._tokens:
                        a_dist, b_dist = words_mod.distinguishing_words(
                            user_stat._tokens,
                            other_stat._tokens,
                            top_n=15,
                        )
                        if a_dist or b_dist:
                            st.subheader(i18n.t("Уникальный лексикон"))
                            st.caption(
                                i18n.t(
                                    "Слова которые ОДИН говорит, а ДРУГОЙ — нет. "
                                    "Лог-odds с Дирихле-сглаживанием (α=0.01). "
                                    "Чем выше — тем характернее для этого участника."
                                )
                            )
                            d1, d2 = st.columns(2)
                            with d1:
                                st.caption(i18n.t("только {name}").format(name=user_name))
                                if a_dist:
                                    df_a = pd.DataFrame(
                                        [(w, round(lo, 2), c) for w, lo, c in a_dist],
                                        columns=["word", "log-odds", "count"],
                                    )
                                    st.dataframe(
                                        df_a,
                                        use_container_width=True,
                                        hide_index=True,
                                        height=400,
                                    )
                                else:
                                    st.caption("—")
                            with d2:
                                st.caption(i18n.t("только {name}").format(name=other_stat.name))
                                if b_dist:
                                    df_b = pd.DataFrame(
                                        [(w, round(lo, 2), c) for w, lo, c in b_dist],
                                        columns=["word", "log-odds", "count"],
                                    )
                                    st.dataframe(
                                        df_b,
                                        use_container_width=True,
                                        hide_index=True,
                                        height=400,
                                    )
                                else:
                                    st.caption("—")

                # Per-user extreme messages
                if user_stat and wres.sentiment_available and user_stat.messages:
                    user_msgs_scored = [
                        (txt, s)
                        for txt, s in user_stat.messages
                        if isinstance(s, float) and txt and abs(s) > 0.05
                    ]
                    if user_msgs_scored:
                        st.subheader(i18n.t("{name} — крайние сообщения").format(name=user_name))
                        u_extr_n = st.slider(
                            i18n.t("Сколько"),
                            5,
                            30,
                            10,
                            step=5,
                            key=f"extr_pu_{user_id}",
                        )
                        u_pos = sorted(user_msgs_scored, key=lambda r: -r[1])[:u_extr_n]
                        u_neg = sorted(user_msgs_scored, key=lambda r: r[1])[:u_extr_n]
                        e1, e2 = st.columns(2)
                        with e1:
                            st.caption(i18n.t("{name} — позитивные").format(name=user_name))
                            st.dataframe(
                                pd.DataFrame(u_pos, columns=["text", "sentiment"]),
                                use_container_width=True,
                                hide_index=True,
                                height=320,
                            )
                        with e2:
                            st.caption(i18n.t("{name} — негативные").format(name=user_name))
                            st.dataframe(
                                pd.DataFrame(u_neg, columns=["text", "sentiment"]),
                                use_container_width=True,
                                hide_index=True,
                                height=320,
                            )
            st.caption(f"Rendered in {time.time() - t0:.1f}s")

        elif key == "highlights":
            # Old Highlights tab dropped — was a markdown rehash of Overview/
            # Per-user metrics. Phase 5 will replace this with a story-timeline
            # of epochs (changepoint-detected periods with sample messages).
            st.info(
                i18n.t(
                    "Этот таб переделывается. Скоро здесь будет story-timeline "
                    "по эпохам — пока смотри Обзор и По участникам."
                )
            )
