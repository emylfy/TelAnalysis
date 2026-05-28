"""Lightweight i18n. RU is canonical (used as keys), EN derived from dict.

Default lang is "ru". When Streamlit isn't available (tests, CLI),
get_lang() falls back to "ru" so pure-function tests stay green.

Usage:
    from ui.i18n import t, plural, n_days, format_day, weekday_name

    st.caption(t("анализ переписок telegram"))
    st.metric(t("Сообщений"), kpis.total_messages)
    f"написали {n_messages(74189)} за {n_days(750)}"
"""

from __future__ import annotations

import contextvars
from datetime import date as _date

try:
    import streamlit as _st
except ImportError:
    _st = None


EN: dict[str, str] = {
    # sidebar / chrome
    "анализ переписок telegram": "Telegram Chat Analytics",
    "result.json": "result.json",
    "Путь к result.json": "Path to result.json",
    "Файл не найден": "File not found",
    "Загрузить другой файл": "Load Another File",
    "Загрузка файла (<65MB)": "File upload (<65MB)",
    "Один чат: **{name}**": "Single Chat: **{name}**",
    "Архив: **{n} чатов**": "Archive: **{n} chats**",
    "Тип чата": "Chat Type",
    "Пусто = все типы": "Empty = all types",
    "Объединить все (отфильтрованные) чаты": "Merge All (Filtered) Chats",
    "Считать весь архив как один большой чат. Слова, эмоджи, ссылки, медиа и голосовые агрегируются по всему. Сеть и По участникам скрываются — они не имеют смысла на несвязанных чатах.": "Treat the whole archive as one big chat. Words, emojis, links, media and voice are aggregated across everything. Network and Per-User tabs are hidden — they don't make sense across disjoint chats.",
    "Объединено: {n} чатов, {m} сообщений всего": "Merged: {n} chats, {m} messages total",
    "Чат": "Chat",
    "ID чата": "Chat ID",
    # empty state / onboarding
    "Локальная аналитика Telegram-переписок — данные не покидают устройство": "Local Telegram chat analytics — your data never leaves your machine",
    "Перетаскивание экспорта сюда или выбор файла": "Drop your export here or pick a file",
    "Открыть демо": "Open Demo",
    "Демо · групповой чат": "Demo · group chat",
    "Заметное": "Highlights",
    "Архив": "Archive",
    "Все чаты": "All chats",
    "Демо · личный чат": "Demo · personal chat",
    "Групповой чат": "Group chat",
    "Личный чат": "Personal chat",
    "Посмотреть на демо-данных:": "Try it on demo data:",
    "Нет своего экспорта? Посмотреть демо": "No export of your own? Try the demo",
    "Путь к файлу или папке экспорта": "Path to the export file or folder",
    "Путь — без лимита по размеру, быстрее для больших архивов.": "Path mode has no size limit and is faster for big archives.",
    "Как получить экспорт?": "How to get the export?",
    "До 200 МБ · JSON / HTML": "Up to 200 MB · JSON / HTML",
    "Выбрать файл": "Choose a file",
    "В **Telegram Desktop**:\n\n- **Один чат** — `Настройки → Экспорт переписки`\n- **Весь аккаунт** — `Настройки → Продвинутые настройки → Экспорт данных Telegram`\n\nВ окне экспорта нужно выбрать формат **JSON**. HTML тоже работает (папка или `messages.html`), но менее точен.": "In **Telegram Desktop**:\n\n- **Single chat** — `Settings → Export Chat History`\n- **Full account** — `Settings → Advanced → Export Telegram Data`\n\nIn the export dialog choose **JSON**. HTML also works (folder or `messages.html`), but it's less accurate.",
    "HTML-экспорт: текст и время разобраны точно, но идентификаторы участников восстановлены по имени. В группах вкладки «Сеть» и «По участникам» менее точны (тёзки/переименования сольются). Для полного анализа экспортируй в формате JSON.": "HTML export: text and timestamps are parsed exactly, but participant identities are reconstructed from display names. In groups the Network and Per-User tabs are less accurate (namesakes/renames collapse together). Export as JSON for full analysis.",
    # period filter
    "Период · вся история": "Period · Full History",
    "Период": "Period",
    "Ограничивает анализ этим периодом. Отражается в URL.": "Limits analysis to this period. Reflected in URL.",
    # KPI tile labels
    "Сообщений": "Messages",
    "Участников": "Participants",
    "Дней активно": "Days Active",
    "Медиа": "Media",
    "Сервисных": "Service",
    "Голосом": "Voice",
    "{n}-й день вместе": "Day {n} together",
    "{label} с {date}": "{label} since {date}",
    "до {label} ≈ {n} при текущем темпе": "to {label} ≈ {n} at current rate",
    "до {label} осталось {n}": "{n} remaining to {label}",
    "100 дней": "100 days",
    "1 год": "1 year",
    "500 дней": "500 days",
    "2 года": "2 years",
    "1000 дней": "1000 days",
    "5 лет": "5 years",
    "10 лет": "10 years",
    "1k сообщений": "1k messages",
    "5k сообщений": "5k messages",
    "10k сообщений": "10k messages",
    "25k сообщений": "25k messages",
    "50k сообщений": "50k messages",
    "100k сообщений": "100k messages",
    "250k сообщений": "250k messages",
    "500k сообщений": "500k messages",
    "1 млн сообщений": "1M messages",
    "Этот таб переделывается. Скоро здесь будет story-timeline по эпохам — пока доступны Обзор и По участникам.": "This tab is being rebuilt. A story-timeline by epochs is coming — for now use Overview and Per User.",
    # tabs
    "Обзор": "Overview",
    "Сеть": "Network",
    "Слова": "Words",
    "Канал": "Channel",
    "По участникам": "Per User",
    "Моменты": "Highlights",
    # section headers — Overview
    "Как часто пишут": "How Often",
    "В какие часы": "When",
    "О чём говорят": "What About",
    "Кто кому": "Who To Whom",
    # Overview — captions / sub-elements
    "Выбран день: {d}": "Selected Day: {d}",
    "очистить": "Clear",
    "Топ эмоджи дня: {top}": "Top Emojis Of The Day: {top}",
    "пример: «{s}…»": "example: «{s}…»",
    "Когда совпадают активности": "When Activities Overlap",
    "оба активны": "Both Active",
    "Пик совместной активности — около {h}:00. Бары нормализованы по пользователям — справедливо при разной активности.": "Peak shared activity around {h}:00. Bars normalized per user — fair when activity differs.",
    "Разговоров": "Conversations",
    "Граница разговора (минут паузы)": "Conversation Boundary (Min Pause)",
    "Если пауза между сообщениями больше — это уже новый разговор.": "If the pause between messages is longer than this — it's a new conversation.",
    "Сообщ./разговор (среднее)": "Msgs/conversation (avg)",
    "медиана {m}": "median {m}",
    "Самый долгий": "Longest",
    "Все эмоджи · {a} в {b} сообщ.": "All Emojis · {a} in {b} msgs",
    "Топ доменов": "Top Domains",
    "Типы сообщений": "Message Types",
    "Голосовые": "Voice",
    "Суммарно": "Total",
    "В среднем": "Average",
    # tabs — Network
    "Узлов": "Nodes",
    "Связей": "Edges",
    "Граф скрыт: участников всего {n} — бар-чарт выше уже рассказывает всю историю.": "Graph hidden: only {n} participants — the bar chart above tells the whole story.",
    "Построение интерактивного графа…": "Drawing interactive graph…",
    "Граф ответов": "Reply Graph",
    "Перетаскивание узлов · колесо — зум · наведение для деталей. Рёбра объединены по числу ответов, толщина ~ частоте. Цвета — сообщества (Louvain modularity).": "Drag nodes · scroll to zoom · hover for details. Edges merged by reply count, thickness ~ frequency. Colours = communities (Louvain modularity).",
    "Граф слишком большой для интерактивного рендера ({n} узлов). CSV для Gephi — ниже.": "Graph too large to render interactively ({n} nodes). Use the CSVs below in Gephi.",
    "Скачать CSV (для Gephi)": "Download CSVs (Gephi-compatible)",
    "Узлы (CSV)": "Nodes (CSV)",
    "Связи (CSV)": "Edges (CSV)",
    "Кто пишет, кто отвечает": "Who messages, who replies",
    "В этом чате нет участников (только сервисные события?).": "No participants found in this chat (only service events?).",
    # tabs — Words
    "Топ слов": "Top Words",
    "Сколько слов показывать в облаках и таблицах": "How many words to show in clouds and tables",
    "Проанализировано пользователей": "Users Analysed",
    "Email-ов": "Emails",
    "Телефонов": "Phones",
    "Топ {n} слов по чату": "Top {n} Words Across The Chat",
    "Облако слов (по всему чату)": "Wordcloud (Chat-Wide)",
    "Топ 30 из {total}": "Top 30 of {total}",
    "Средний сентимент (rubert-tiny2-russian-sentiment, RU/EN): {s} (диапазон −1 негативно … +1 позитивно){extra}. ⚠ Не различает сарказм, шутки и слэнг — цифры условны.": "Average sentiment (rubert-tiny2-russian-sentiment, RU/EN): {s} (range −1 negative … +1 positive){extra}. ⚠ Doesn't catch sarcasm, jokes or slang — take numbers with skepticism.",
    " · {n} фрагментов уполовинены sarcasm-emoji эвристикой (🙃🤡🙄💀…)": " · {n} fragments halved by sarcasm-emoji heuristic (🙃🤡🙄💀…)",
    "минут до ответа": "minutes to reply",
    "минут": "minutes",
    "count (log)": "count (log)",
    "Совпадений нет.": "No matches.",
    "Повторяющихся фраз не найдено.": "No repeated phrases found.",
    "Слова для отслеживания (через запятую)": "Words To Track (Comma-Separated)",
    "например: привет, спасибо, люблю": "e.g.: hello, thanks, love",
    "Гранулярность": "Granularity",
    "неделя": "week",
    "день": "day",
    "месяц": "month",
    "Считаю…": "Counting…",
    "Длина фразы": "Phrase Length",
    "биграммы (2 слова)": "bigrams (2 words)",
    "триграммы (3 слова)": "trigrams (3 words)",
    "Сколько крайних показывать": "How many extremes to show",
    "Сколько": "How many",
    "TTR = уникальные / всего токенов (после фильтра стоп-слов). Выше = разнообразнее словарь. TTR зависит от длины — короткие выборки получают выше; корректно сравнивать пользователей с похожим количеством токенов.": "TTR = unique / total tokens (after stop-word filter). Higher = more diverse vocabulary. TTR is length-sensitive — shorter samples score higher; compare users with similar token counts.",
    "Участник": "Participant",
    "Облако слов — {name}": "Wordcloud — {name}",
    "Средний сентимент: {s} ⚠ не учитывает сарказм/шутки/слэнг": "Average Sentiment: {s} ⚠ doesn't account for sarcasm/jokes/slang",
    "Все {n} фрагментов сообщений": "All {n} message fragments",
    "Поиск по сообщениям": "Search Messages",
    "часть текста…": "fragment of text…",
    "Найдено {n} (показаны первые {k})": "Found {n} (showing first {k})",
    "Последние {k} из {n} · введи поиск чтобы найти конкретное": "Last {k} of {n} · use search to find specific ones",
    "Найдено {n} (первые {k})": "Found {n} (first {k})",
    "Последние {k} из {n}": "Last {k} of {n}",
    "Полная таблица ({n})": "Full table ({n})",
    "Найдены контакты: {e} email, {p} телефонов": "Found Contacts: {e} emails, {p} phones",
    "Сентимент во времени": "Sentiment Over Time",
    "Средний сентимент по чату (по неделям)": "Chat-Wide Weekly Average Sentiment",
    "Средний сентимент по участникам (по неделям)": "Per-User Weekly Average Sentiment",
    "среднее compound": "avg compound",
    "Крайние сообщения": "Extreme Messages",
    "How many extremes to show": "How many extremes to show",
    "Самые позитивные ({n})": "Most Positive ({n})",
    "Самые негативные ({n})": "Most Negative ({n})",
    "Повторяющиеся фразы": "Repeated Phrases",
    "Phrase length": "Phrase length",
    "bigrams (2 words)": "bigrams (2 words)",
    "trigrams (3 words)": "trigrams (3 words)",
    "Слова во времени": "Words Over Time",
    "Words to track (comma-separated)": "Words to track (comma-separated)",
    "Granularity": "Granularity",
    "week": "week",
    "day": "day",
    "month": "month",
    "Counting…": "Counting…",
    "Богатство словаря": "Vocabulary Richness",
    "TTR = unique / total tokens (after stop-word filtering). Higher = more diverse vocabulary. TTR is length-sensitive — shorter samples score higher; compare users with similar token counts.": "TTR = unique / total tokens (after stop-word filtering). Higher = more diverse vocabulary. TTR is length-sensitive — shorter samples score higher; compare users with similar token counts.",
    "Per-user": "Per User",
    "User": "User",
    "Wordcloud — {name}": "Wordcloud — {name}",
    "Average sentiment: {s} ⚠ не учитывает сарказм/шутки/слэнг": "Average sentiment: {s} ⚠ does not account for sarcasm/jokes/slang",
    "All {n} message fragments": "All {n} message fragments",
    "Found contacts: {e} emails, {p} phones": "Found Contacts: {e} emails, {p} phones",
    # Words tab — sentiment hint
    "Сентимент-анализ **отключён** — требуются опциональные зависимости для RU/EN-оценок:\n\n```\npip install -r requirements-sentiment.txt\n```\n\nДобавит ~1GB (torch + transformers) плюс 50MB модель при первом запуске. После установки нужен рестарт Streamlit. Модель не различает сарказм, шутки и слэнг — вспомогательная метрика, не диагностика.": "Sentiment analysis is **disabled** — optional deps required for RU/EN sentiment scores:\n\n```\npip install -r requirements-sentiment.txt\n```\n\nAdds ~1GB (torch + transformers) plus a 50MB model on first use. Restart Streamlit afterwards. Model doesn't catch sarcasm, jokes or slang — supplementary metric, not diagnosis.",
    " · {n} fragments halved by sarcasm-emoji heuristic (🙃🤡🙄💀…)": " · {n} fragments halved by sarcasm-emoji heuristic (🙃🤡🙄💀…)",
    "⚠ Sentiment не различает сарказм, шутки и слэнг. Подходит для тренда, не для абсолютных значений.": "⚠ Sentiment doesn't catch sarcasm, jokes or slang. Use for trends, not absolute values.",
    # tabs — Channel
    "Топ слов: {n}": "Top Words: {n}",
    "Токенов (raw)": "Tokens (Raw)",
    "Облако слов": "Word Cloud",
    "Текста недостаточно для облака слов.": "Not enough text for a word cloud.",
    "Топ 50 из {total}": "Top 50 Of {total}",
    # tabs — Per-user
    "В этом чате нет идентифицируемых участников.": "No identifiable participants in this chat.",
    "Доля чата": "Share Of Chat",
    "Манера речи": "Speaking Style",
    "Средняя длина": "Avg Msg Length",
    "Длина (медиана)": "Length (Median)",
    "В среднем {a} симв., самое длинное {l}": "Avg {a} chars, longest {l}",
    "вопросы %": "questions %",
    "восклицания %": "exclamations %",
    "ALL-CAPS %": "ALL-CAPS %",
    "реплаи %": "replies %",
    "Доля реплаев": "Reply Rate",
    "Доля сообщений-ответов на конкретное другое (quote-reply)": "Share of messages that quote-reply to another message",
    "Пересылки": "Forwards",
    "Доля пересылок": "Forward Rate",
    "{n} из {t} сообщений — пересылки откуда-то ещё.": "{n} of {t} messages — forwarded from elsewhere.",
    "Топ источников:": "Top Sources:",
    "Самые длинные монологи": "Longest Monologues",
    "Подряд N+ сообщений от одного пользователя без ответа другого. Высокий N — кто-то рассказывал длинную историю или выговаривался.": "N+ consecutive messages from one user with no reply in between. High N = someone told a long story or vented.",
    "Мат": "Profanity",
    "Совпадение по корням (хуй, пизд, ебат, бляд...) с word boundary. Может ловить и редкие нейтральные слова.": "Match by Russian profanity roots with word boundary. May catch occasional neutral words.",
    "Q&A медиана": "Q&A Median",
    "Q&A p90": "Q&A p90",
    "Q&A пар": "Q&A Pairs",
    "По часу дня": "By Hour Of Day",
    "По дню недели": "By Weekday",
    "час": "hour",
    "Макс. глубина reply": "Max Reply Depth",
    "Сред. глубина reply": "Avg Reply Depth",
    "Длиннейшая цепочка quote-reply подряд. Глубина 1 = одиночный ответ, 5+ = глубокая ветка с реплаями на реплаи.": "Longest consecutive quote-reply chain. Depth 1 = single reply, 5+ = deep branch with replies-on-replies.",
    "Распределение глубины reply-цепочек": "Reply Chain Depth Distribution",
    "глубина (хопов)": "depth (hops)",
    "Распределение длин разговоров": "Conversation Length Distribution",
    "сообщений в разговоре": "messages per conversation",
    "Стикеры": "Stickers",
    "{n} всего, эмодзи в которые помечены:": "{n} total, emojis they're tagged with:",
    "Календарь": "Calendar",
    "по количеству": "by count",
    "писали/нет": "wrote/not",
    "Активных дней: {a} из {t} ({p}%) — серым месяцы без сообщений.": "Active days: {a} of {t} ({p}%) — grey for days without messages.",
    "на {n} быстрее": "{n} faster",
    "на {n} медленнее": "{n} slower",
    "так же": "same",
    "Медиана ответа на сообщения с '?'. Сравнение с обычной медианой ответа: {d}.": "Median reply time for messages containing '?'. Compared to overall reply median: {d}.",
    "Первое сообщение дня (медиана)": "First Message Of Day (Median)",
    "Самое раннее сообщение, усреднённое по всем активным дням. Нижнее = жаворонок, более позднее = сова.": "Earliest message averaged over all active days. Earlier = early bird, later = night owl.",
    "у других: ": "others: ",
    "час дня": "hour of day",
    "Уникальный лексикон": "Distinctive Lexicon",
    "Слова которые ОДИН говорит, а ДРУГОЙ — нет. Лог-odds с Дирихле-сглаживанием (α=0.01). Чем выше — тем характернее для этого участника.": "Words ONE says that the OTHER doesn't. Log-odds with Dirichlet smoothing (α=0.01). Higher = more characteristic of that participant.",
    "только {name}": "only {name}",
    "Слов в сообщении": "Words/Msg",
    "Медиана символов": "Median Chars",
    "Самое длинное": "Longest",
    "Доля вопросов": "Question Rate",
    "Доля сообщений с '?'": "Share of messages containing '?'",
    "Доля восклицаний": "Exclamation Rate",
    "Доля сообщений с '!'": "Share of messages containing '!'",
    "Доля ALL-CAPS": "ALL-CAPS Rate",
    "Доля сообщений где >60% букв заглавные (≥5 букв)": "Share of messages where >60% of letters are uppercase (≥5 letters)",
    "Самое длинное сообщение ({n} симв.)": "Longest Message ({n} chars)",
    "{n} симв.": "{n} chars",
    "… (обрезано, полная длина {n})": "… (truncated, full length {n})",
    "время суток": "time of day",
    "длина сообщения": "message length",
    "Взаимность ответов": "Response Reciprocity",
    "{name}: медианный ответ": "{name}: Median Response",
    "к {n}": "to {n}",
    "За 5 мин": "Within 5 Min",
    "За 30 мин": "Within 30 Min",
    "За 1 час": "Within 1 Hour",
    "Обратное — {a} → {b}: медиана {m}, за 5м {p}%. Разница 5-мин ответа: **{d:+.1f} pp**": "Reverse — {a} → {b}: median {m}, 5m {p}%. Difference in 5-min response rate: **{d:+.1f} pp**",
    "Стрики и молчания": "Streaks & Silences",
    "Самый длинный стрик": "Longest Streak",
    "Самое долгое молчание": "Longest Silence",
    "Текущий стрик": "Current Streak",
    "Всего активных дней": "Total Active Days",
    "Самые долгие молчания ({n})": "Longest Silences ({n})",
    "Кто начинает разговор": "Conversation Initiator",
    "Инициаций после паузы 4ч+": "Initiations After 4h+ Silence",
    "Доля всех инициаций": "Share Of All Initiations",
    "⚠ Всего инициаций {n} — выборка маленькая, процент может быть случайным.": "⚠ Only {n} initiations total — small sample, percentage may be noise.",
    "{name} — ежедневная активность": "{name} — Daily Activity",
    "{name} — час × день недели": "{name} — Hour × Weekday",
    "Топ эмоджи": "Top Emojis",
    "Скорость ответа": "Reply Latency",
    "Эмоджи не найдены.": "No emojis found.",
    "У этого участника нет ответов.": "No replies recorded for this user.",
    "Обычно за {m} · 90% быстрее {p} · {n}": "Usually {m} · 90% within {p} · {n}",
    "Всего токенов": "Total Tokens",
    "Уникальных токенов": "Unique Tokens",
    "TTR (разнообразие)": "TTR (Diversity)",
    "MTLD (разнообразие)": "MTLD (Diversity)",
    "Type-token ratio. 1.0 = каждое слово уникально. Зависит от длины: короткие выборки получают выше.": "Type-token ratio. 1.0 = every word is unique. Length-sensitive: shorter samples score higher.",
    "Measure of Textual Lexical Diversity. Длина прогона до падения TTR ниже 0.72. Не зависит от длины выборки.": "Measure of Textual Lexical Diversity. Run length until TTR drops below 0.72. Sample-length-independent.",
    "MTLD = средняя длина прогона до того как TTR упадёт до 0.72. Выше = разнообразнее словарь. В отличие от голого TTR, не зависит от длины выборки — справедливо сравнивать. MTLD < 50 для коротких выборок недостоверен.": "MTLD = average run length until TTR drops to 0.72. Higher = more diverse vocabulary. Unlike raw TTR, it's sample-length-independent — fair to compare. MTLD < 50 for short samples is unreliable.",
    "Топ {n} слов": "Top {n} Words",
    "{name} — крайние сообщения": "{name} — Extreme Messages",
    "{name} — позитивные": "{name} — Positive",
    "{name} — негативные": "{name} — Negative",
    # tabs — Highlights
    "{name} — моменты": "{name} — Highlights",
    "Голосом наговорено": "Voice Talked",
    "Ссылок": "Links",
    "**Самый активный день:** `{d}` — **{n}** сообщений": "**Most Active Day:** `{d}` — **{n}** messages",
    "**Пиковый час:** `{h}:00` ({n} сообщений)": "**Peak Hour:** `{h}:00` ({n} messages)",
    "**Топ эмоджи:** {emo}": "**Top Emojis:** {emo}",
    "**Топ доменов:** {dom}": "**Top Domains:** {dom}",
    "**Скорость ответа:** медиана `{m}`, p90 `{p}` ({n} ответов)": "**Reply Speed:** median `{m}`, p90 `{p}` ({n} replies)",
    "**Самый долгий стрик:** `{d}` дней (`{a}` → `{b}`) · сейчас: `{c}` дней": "**Longest Streak:** `{d}` days (`{a}` → `{b}`) · current: `{c}` days",
    "**Самое долгое молчание:** `{d}` дней (`{a}` → `{b}`)": "**Longest Silence:** `{d}` days (`{a}` → `{b}`)",
    "**Кто начинает разговор (после паузы 4+ часа):**": "**Conversation Initiators (after 4+ hour silence):**",
    "**Манера речи:**": "**Speaking Style:**",
    "**Облако слов:**": "**Word Cloud:**",
    "**Топ-5 позитивных моментов**": "**Top 5 Positive Moments**",
    "**Топ-5 негативных моментов**": "**Top 5 Negative Moments**",
    # data — empty / errors
    "Нет сообщений в выбранном периоде.": "No messages in selected range.",
    "Нет сообщений с датами.": "No dated messages.",
    "👆 Клик по точке на графике раскрывает день.": "👆 Click a point on the chart to drill into that day.",
    # hero prose templates
    "За {days} здесь написали {messages} — это в среднем {avg} в день.": "Over {days} here wrote {messages} — that's {avg} a day on average.",
    "Самый шумный день — {date}, {messages} за сутки.": "Loudest day — {date}, {messages} in 24 hours.",
    "Чаще всего пишут в {weekday} около {hour}.": "Most active on {weekday} around {hour}.",
    "Самое долгое молчание — {days} в {when}.": "Longest silence — {days} in {when}.",
    "Нет дат у сообщений — анализ ограничен.": "No dated messages — analysis limited.",
    "{first} → {last}  ·  {users}": "{first} → {last}  ·  {users}",
    # hero hour-of-day phrases
    "полночь": "midnight",
    "{h}:00 ночи": "{h}:00 at night",
    "{h}:00 утра": "{h}:00 in the morning",
    "полдень": "noon",
    "{h}:00 дня": "{h}:00 in the afternoon",
    "{h}:00 вечера": "{h}:00 in the evening",
    # caplets
    "Пик активности — {when}: {n} сообщений за день.": "Peak activity — {when}: {n} messages in a day.",
    "Самая горячая неделя: {a} → {b} ({n} сообщений).": "Hottest week: {a} → {b} ({n} messages).",
    "Пик: {wd}, {h}:00 — {n} сообщений за этот слот.": "Peak: {wd}, {h}:00 — {n} messages in that slot.",
    "{p}% сообщений — ночью (00:00–06:00).": "{p}% of messages — at night (00:00–06:00).",
    "Любимая эмоджи: {em} ({n} раз, {p}% всех эмоджи).": "Favorite emoji: {em} ({n} times, {p}% of all emojis).",
    "Голосовых: {n} ({total} суммарно, в среднем {avg}).": "Voice: {n} ({total} total, {avg} on average).",
    "Отвечают обычно за {m}, в 90% случаев — быстрее {p}.": "Usually reply in {m}, 90% of the time within {p}.",
    # highlight cards (top_highlights) — labels also reused by other tabs
    "Пиковый час": "Peak Hour",
    "Самый громкий день": "Loudest Day",
    "Любимая эмоджи": "Favorite Emoji",
    # "Самый длинный стрик" / "Самое долгое молчание" already defined above (per-user streaks block)
    "Медиана ответа": "Median Reply",
    "p90 ответа": "p90 Reply",
    "Всего ответов": "Total Replies",
    "Обычно отвечают за": "Usually reply within",
    "90% ответов — быстрее": "90% of replies — faster than",
    "Пар вопрос-ответ": "Question→reply pairs",
    "Ответы на вопросы (на сообщения с «?»)": "Replies to questions (messages with '?')",
    "Половина ответов — быстрее": "Half of replies — faster than",
    "Ответов учтено": "Replies counted",
    "Вопросов с ответом": "Questions with a reply",
    "Сколько ответов вошло в расчёт времени выше. Ответы дольше суток в расчёт не входят.": "How many replies feed the times above. Replies slower than a day are excluded.",
    "Сколько вопросов получили ответ и вошли в расчёт времени выше.": "How many questions got a reply and feed the times above.",
    "Половина ответов на вопросы — быстрее этого значения. По сравнению с ответами на все сообщения: {d}.": "Half of replies to questions are faster than this. Versus replies to all messages: {d}.",
    "Половина быстрее {m} · 90% быстрее {p} · {n}": "Half within {m} · 90% within {p} · {n}",
    "Серединное время ответа: половина ответов быстрее этого значения, половина — медленнее. Медиана, а не среднее, чтобы редкие очень поздние ответы не искажали цифру.": "Middle reply time: half of all replies are faster than this, half slower. Median, not average, so a few very late replies don't skew the number.",
    "90-й перцентиль: 90% ответов укладываются в это время, и только самые медленные 10% — дольше. Это «почти худший» случай, а не среднее.": "90th percentile: 90% of replies land within this time; only the slowest 10% take longer. The near-worst case, not the average.",
    "Сколько пар «сообщение → ответ» учтено в медиане и p90.": "How many 'message → reply' pairs feed the median and p90.",
    "90-й перцентиль времени ответа на сообщения с вопросом («?»): 90% таких ответов быстрее этого значения.": "90th-percentile reply time for messages with a question ('?'): 90% of such replies are faster than this.",
    "Сколько пар «вопрос → ответ» (сообщения с «?») учтено.": "How many 'question → reply' pairs (messages with '?') were counted.",
    "{n} ответов (>{h}ч) не вошли в расчёт — это {p}% всех пар.": "{n} replies (>{h}h) excluded from the stats — that's {p}% of all pairs.",
    "между сообщениями": "between messages",
    # media kind labels (RU keys for translation)
    "Текст": "Text",
    "Фото": "Photo",
    "Видео": "Video",
    "Видеосообщение": "Video Message",
    "Голосовое": "Voice Msg",
    "Аудио": "Audio",
    "Стикер": "Sticker",
    "Анимация/GIF": "Animation/GIF",
    "Файл": "File",
    "Локация": "Location",
    "Контакт": "Contact",
    "Опрос": "Poll",
    "Сервисное": "Service",
    "Другое": "Other",
}


# Per-request language override for non-Streamlit callers (the FastAPI backend
# sets this from a ?lang= param). contextvars keep it correct under async /
# threadpool concurrency. Streamlit path is unaffected (override stays None).
_lang_override: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tla_lang_override", default=None
)


def set_lang(lang: str | None) -> None:
    """Force the active language for the current context (FastAPI request)."""
    _lang_override.set(lang)


def get_lang() -> str:
    """Active language. Override (API) > Streamlit session > 'ru' fallback."""
    override = _lang_override.get()
    if override in ("ru", "en"):
        return override
    if _st is None:
        return "ru"
    try:
        return _st.session_state.get("lang", "ru")
    except Exception:
        return "ru"


def t(s: str) -> str:
    if get_lang() == "ru":
        return s
    return EN.get(s, s)


def plural(n: int, ru_one: str, ru_few: str, ru_many: str, en_one: str, en_many: str) -> str:
    if get_lang() == "ru":
        return _plural_ru(n, ru_one, ru_few, ru_many)
    return en_one if n == 1 else en_many


def _plural_ru(n: int, one: str, few: str, many: str) -> str:
    n10, n100 = abs(n) % 10, abs(n) % 100
    if 11 <= n100 <= 14:
        return many
    if n10 == 1:
        return one
    if 2 <= n10 <= 4:
        return few
    return many


def _fmt_int(n: int) -> str:
    return f"{int(n):,}".replace(",", " ")


def n_days(n: int) -> str:
    word = plural(n, "день", "дня", "дней", "day", "days")
    return f"{_fmt_int(n)} {word}"


def n_messages(n: int) -> str:
    word = plural(n, "сообщение", "сообщения", "сообщений", "message", "messages")
    return f"{_fmt_int(n)} {word}"


def n_chats(n: int) -> str:
    word = plural(n, "чат", "чата", "чатов", "chat", "chats")
    return f"{_fmt_int(n)} {word}"


def n_replies(n: int) -> str:
    word = plural(n, "ответ", "ответа", "ответов", "reply", "replies")
    return f"{_fmt_int(n)} {word}"


# date / month names

_RU_MONTHS_GEN = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]
_RU_MONTHS_PREP = [
    "январе",
    "феврале",
    "марте",
    "апреле",
    "мае",
    "июне",
    "июле",
    "августе",
    "сентябре",
    "октябре",
    "ноябре",
    "декабре",
]
_EN_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
_RU_WEEKDAYS = [
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
]
_EN_WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
_RU_WD_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
_EN_WD_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def format_day(d: _date) -> str:
    """e.g. '5 января 2023' / 'January 5, 2023'."""
    if get_lang() == "ru":
        return f"{d.day} {_RU_MONTHS_GEN[d.month - 1]} {d.year}"
    return f"{_EN_MONTHS[d.month - 1]} {d.day}, {d.year}"


def format_day_short(d: _date) -> str:
    """e.g. '5 января' / 'January 5'."""
    if get_lang() == "ru":
        return f"{d.day} {_RU_MONTHS_GEN[d.month - 1]}"
    return f"{_EN_MONTHS[d.month - 1]} {d.day}"


def format_month_year(d: _date) -> str:
    """e.g. 'январе 2023' / 'January 2023'. RU is prepositional case."""
    if get_lang() == "ru":
        return f"{_RU_MONTHS_PREP[d.month - 1]} {d.year}"
    return f"{_EN_MONTHS[d.month - 1]} {d.year}"


def weekday_name(wd: int) -> str:
    """0=Mon ... 6=Sun. Lowercase noun (used inside sentences)."""
    if get_lang() == "ru":
        return _RU_WEEKDAYS[wd]
    return _EN_WEEKDAYS[wd]


def weekday_name_cap(wd: int) -> str:
    return weekday_name(wd).capitalize()


def weekday_short_labels() -> list[str]:
    """For heatmap axis labels (3-letter)."""
    return _RU_WD_SHORT if get_lang() == "ru" else _EN_WD_SHORT


# hour-of-day humanizer, lang-aware


def hour_to_human(h: int) -> str:
    if h == 0:
        return t("полночь")
    if h == 12:
        return t("полдень")
    if h < 5:
        return t("{h}:00 ночи").format(h=h)
    if h < 12:
        return t("{h}:00 утра").format(h=h)
    if h < 18:
        return t("{h}:00 дня").format(h=h)
    return t("{h}:00 вечера").format(h=h)


# duration-unit suffixes, lang-aware


def dur_unit(kind: str) -> str:
    """Short duration-unit suffix for humanized times. kind ∈ {'s','m','h','d'}.

    Single Russian letters mirror the English layout exactly
    ("9h 25m" → "9ч 25м"), so the compact metric-card formatting stays
    identical across languages.
    """
    ru = {"s": "с", "m": "м", "h": "ч", "d": "д"}
    en = {"s": "s", "m": "m", "h": "h", "d": "d"}
    return (ru if get_lang() == "ru" else en).get(kind, kind)


# chat-type → human label, lang-aware

_CHAT_TYPE: dict[str, tuple[str, str]] = {
    "personal_chat": ("Личный чат", "Personal chat"),
    "private_group": ("Группа", "Group"),
    "private_supergroup": ("Группа", "Group"),
    "public_supergroup": ("Группа", "Group"),
    "private_channel": ("Канал", "Channel"),
    "public_channel": ("Канал", "Channel"),
    "saved_messages": ("Избранное", "Saved Messages"),
    "bot_chat": ("Бот", "Bot"),
    "multichat": ("Объединённый", "Combined"),
}


def chat_type_label(chat_type: str) -> str:
    """Human-readable chat type, e.g. 'personal_chat' → «Личный чат» / 'Personal chat'.
    Unknown types fall back to the raw string."""
    ru, en = _CHAT_TYPE.get(chat_type, (chat_type, chat_type))
    return ru if get_lang() == "ru" else en


__all__ = [
    "EN",
    "get_lang",
    "t",
    "plural",
    "n_days",
    "n_messages",
    "n_chats",
    "n_replies",
    "format_day",
    "format_day_short",
    "format_month_year",
    "weekday_name",
    "weekday_name_cap",
    "weekday_short_labels",
    "hour_to_human",
]
