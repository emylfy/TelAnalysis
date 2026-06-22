import i18n from "i18next"
import { initReactI18next } from "react-i18next"

// UI-chrome strings. Python-composed sentences (hero prose, highlight labels)
// arrive already localized from the API via ?lang=.
const ru = {
  // kpi
  messages: "Сообщений",
  participants: "Участников",
  daysActive: "Дней активно",
  media: "Медиа",
  voice: "Голосом",
  highlights: "Заметное",
  // tabs
  tab_overview: "Обзор",
  tab_network: "Сеть",
  tab_words: "Слова",
  tab_channel: "Канал",
  tab_peruser: "По участникам",
  // section headers
  howOften: "Как часто пишут",
  whenHours: "В какие часы",
  whatAbout: "Эмодзи, медиа и ссылки",
  whoToWhom: "Скорость ответа",
  topDomains: "Топ доменов",
  longestMonologues: "Самые длинные монологи",
  // latency
  halfFaster: "Половина ответов — быстрее",
  p90Faster: "90% ответов — быстрее",
  repliesCounted: "Ответов учтено",
  qSection: "Ответы на вопросы",
  qWithAnswer: "Вопросов с ответом",
  // sessions
  conversations: "Разговоров",
  perConvAvg: "Сообщ./разговор (среднее)",
  longestConv: "Самый долгий",
  convLength: "Длина разговоров",
  longestConvs: "Самые долгие разговоры",
  // latency caveats
  droppedCap: "{{n}} ответов дольше {{h}} ч не учтены",
  qaHint: "Сообщения с вопросом («?») и ответы на них — отвечают ли на вопросы быстрее обычного.",
  qaFaster: "на {{m}} мин быстрее обычного",
  qaSlower: "на {{m}} мин медленнее обычного",
  qaSame: "как в среднем",
  whoToWhomHint: "«Половина быстрее» — медиана: половина ответов приходит быстрее. «90% быстрее» — почти все, кроме самых долгих.",
  // anniversaries / html
  annivBase: "🎉 {{days}} {{w}} здесь",
  annivUpcoming: "ближайший рубеж «{{label}}» через {{n}} дн.",
  htmlWarning: "Это HTML-экспорт: в нём нет ID участников, поэтому «Сеть» и «По участникам» для групп менее точны. Для полной картины выгрузи JSON.",
  // voice
  voiceMessages: "Голосовые",
  voiceTotal: "Суммарно",
  voiceAvg: "В среднем",
  // period
  period: "Период",
  allHistory: "Вся история",
  allChats: "★ Все чаты",
  apply: "Применить",
  reset: "Сбросить",
  fromDate: "С",
  toDate: "По",
  // onboarding
  appTagline: "Аналитика переписок Telegram — локально и приватно",
  onboardDesc: "Укажи путь к выгруженному result.json (Telegram → Настройки → Экспорт данных) или открой демо.",
  pathPlaceholder: "/путь/к/result.json",
  load: "Открыть",
  pickFile: "Выбрать файл…",
  pickPrompt: "Выберите result.json из папки экспорта Telegram",
  pickUnavailable: "Системный диалог недоступен на этой ОС — вставьте путь ниже.",
  orDivider: "или",
  uploading: "Открываю диалог…",
  uploadError: "Не удалось открыть диалог выбора файла. Укажи путь вручную ниже.",
  uploadHint: "Откроется системный диалог. Выбирай result.json прямо из папки экспорта — тогда подхватятся стикеры и медиа. Файл не копируется и никуда не уходит.",
  demoPersonal: "Демо: личный чат",
  demoGroup: "Демо: группа",
  loadError: "Не удалось загрузить. Проверь путь к файлу.",
  changeSource: "Другой файл",
  loading: "Загрузка…",
  // empty
  noData: "Нет данных для этого чата.",
  tabError: "Не удалось загрузить данные.",
  retry: "Повторить",
  // tables
  user: "Участник",
  count: "Сообщений",
  // words tab
  topWords: "Топ слов",
  wordcloud: "Облако слов",
  phrases: "Повторяющиеся фразы",
  bigrams: "Пары слов",
  trigrams: "Тройки слов",
  vocabulary: "Богатство словаря",
  vocabHint: "MTLD — мера разнообразия лексики: чем выше, тем реже повторяются слова.",
  contacts: "Контакты в переписке",
  emailsN: "E-mail адресов",
  phonesN: "Телефонов",
  sentiment: "Тональность",
  sentimentAvg: "Средний тон",
  sentimentHint: "Шкала −1…+1 (негатив…позитив). Модель не понимает сарказм и шутки — читай со скепсисом.",
  sentimentOverTime: "Тон во времени",
  sentimentPerUser: "Тон по участникам",
  sentimentByHour: "Тон по часам",
  sentimentByWeekday: "Тон по дням недели",
  mostPositive: "Самые позитивные",
  mostNegative: "Самые негативные",
  totalTokens: "Слов всего",
  uniqueTokens: "Уникальных",
  mtld: "MTLD",
  // network tab
  networkDesc: "Кто кому отвечает. Размер кружка — сколько человек написал, толщина линии — сколько раз отвечали друг другу. Можно тянуть узлы и приближать колесом.",
  interactions: "Кто кому отвечает",
  msgsSent: "Сообщений",
  repliesSent: "Ответов отправил",
  repliesReceived: "Ответов получил",
  netNodes: "Участников",
  netEdges: "Связей",
  maxDepth: "Макс. глубина цепочки",
  avgDepth: "Средняя глубина",
  chainDepth: "Глубина reply-цепочек",
  downloadCsv: "Скачать CSV (для Gephi)",
  // per-user tab
  pickUser: "Участник",
  avgWords: "Слов в сообщении",
  questionShare: "С вопросом",
  replyShare: "Цитирует в ответ",
  timeOfDay: "Когда пишет",
  msgLength: "Длина сообщений",
  characteristicPhrases: "Характерные фразы",
  tod_night: "Ночь",
  tod_morning: "Утро",
  tod_day: "День",
  tod_evening: "Вечер",
  shareOfChat: "Доля чата",
  toneRadar: "Манера общения",
  axisQuestion: "Вопросы",
  axisExcl: "Восклицания",
  axisCaps: "КАПС",
  axisReply: "Цитирование",
  wakeup: "Во сколько просыпается",
  wakeupMedian: "Первое сообщение (медиана)",
  dailyActivity: "Активность по дням",
  hourWeekdayUser: "Час × день недели",
  reciprocity: "Скорость ответа (взаимность)",
  medianReply: "Медиана ответа",
  within5: "За 5 минут",
  within30: "За 30 минут",
  within60: "За час",
  streaks: "Стрики и молчания",
  longestStreak: "Самый длинный стрик",
  currentStreak: "Текущий стрик",
  activeDays: "Активных дней",
  longestSilences: "Самые долгие паузы",
  days: "дней",
  initiator: "Кто начинает разговоры",
  initiations: "Инициатив",
  initiatorShare: "Доля инициатив",
  forwards: "Форварды (репосты)",
  forwardShare: "Доля форвардов",
  latencyHist: "Распределение скорости ответа",
  emojisOfUser: "Эмодзи",
  stickersOfUser: "Любимые стикеры",
  vocabUser: "Словарь",
  matTitle: "Мат",
  matHelp: "Совпадение по корням. Hits/100 — попаданий на 100 сообщений.",
  matMsgs: "Сообщений",
  matWith: "С матом",
  matHits: "Попаданий",
  matPer100: "Hits/100",
  distinguishing: "Уникальный лексикон",
  distinguishingHelp: "Log-odds со сглаживанием: слова, по которым один отличается от другого.",
  onlyUser: "Только у",
  logOdds: "log-odds",
  // channel tab
  channelTokens: "Слов в постах",
  // types
  type_personal_chat: "Личный чат",
  type_private_group: "Группа",
  type_private_supergroup: "Группа",
  type_public_supergroup: "Группа",
  type_private_channel: "Канал",
  type_public_channel: "Канал",
  type_bot_chat: "Бот",
  type_saved_messages: "Избранное",
  type_multichat: "Объединённый",
  // onboarding help
  helpExport: "Как получить экспорт?",
  helpExportContentMd:
    "В **Telegram Desktop**:\n\n" +
    "- **Один чат** — `Настройки → Экспорт переписки`\n" +
    "- **Весь аккаунт** — `Настройки → Продвинутые настройки → Экспорт данных Telegram`\n\n" +
    "В окне экспорта выбери формат **JSON**. HTML тоже работает (папка или `messages.html`), но менее точен.",
  // sentiment-off info
  sentimentOffTitle: "Анализ тональности выключен",
  sentimentOffBody:
    "Нужны опциональные зависимости для RU/EN-оценок. Установи и перезапусти сервер:",
  sentimentOffNote:
    "Это ~1 ГБ (torch + transformers) и ~50 МБ модели при первом запуске. Модель не различает сарказм и шутки — вспомогательная метрика.",
  // PerUser char metrics
  msgLengthMedian: "Длина (медиана)",
  charsShort: "симв.",
  // PerUser captions
  wakeupOthers: "у других:",
  initiatorsLowN: "⚠ всего инициаций {{n}} — выборка маленькая, процент может быть случайным.",
  reciprocityReverse:
    "В обратную сторону ({{a}} → {{b}}): медиана {{m}}, за 5 мин {{p}}%. Разница 5-мин ответа: {{d}} pp.",
  // anniversaries milestone
  annivCrossed: "{{label}} с {{date}}",
  // calendar toggle
  calendarMode: "Режим",
  calendarCount: "по количеству",
  calendarBinary: "писали / нет",
  calendarYear: "Год",
  calendarLess: "меньше",
  calendarMore: "больше",
  calendarActiveDays: "Активных дней: {{a}} из {{t}} ({{p}}%)",
  // heatmap caplets
  capPeakHour: "пик активности — {{h}}:00",
  capNightShare: "ночью ({{from}}–{{to}}) — {{p}}% сообщений",
  // overlap chart
  overlapTitle: "Когда совпадают активности",
  overlapHint:
    "Бары нормализованы по пользователям — справедливо при разной активности. Пик совместной активности — около {{h}}:00.",
  overlapBoth: "оба активны",
  // accordion
  showAll: "Показать все ({{n}})",
  hideAll: "Скрыть",
  // channel
  channelTopCount: "Уникальных слов",
  // period presets
  preset7: "7 дн",
  preset30: "30 дн",
  preset90: "90 дн",
  presetAll: "Всё",
  // persona dictionaries (time_of_day + length_buckets)
  persona_night: "🌙 ночная сова",
  persona_morning: "🌅 жаворонок",
  persona_day: "☀️ дневной",
  persona_evening: "🌆 вечерний",
  lenpersona_short: "📝 односложно",
  lenpersona_med: "💬 коротко",
  lenpersona_long: "📄 подробно",
  lenpersona_xl: "📜 эссе",
  traitInitiator: "🚀 инициатор",
  traitFastReplier: "⚡ быстро отвечает",
  // section hints — «что отсюда понять»
  howOftenHint: "Объём сообщений по дням и календарь активности по годам.",
  whenHoursHint: "Тепловая карта час × день недели: когда переписка живее всего.",
  whatAboutHint: "Чем наполнен чат помимо текста — эмодзи, вложения и ссылки.",
  longestMonologuesHint: "Серии сообщений подряд без ответа собеседника.",
  topDomainsHint: "Домены ссылок, которыми делятся в чате.",
  emojiTop: "Любимые эмодзи",
  emojiTopHint: "Эмоциональный фон чата — какие эмодзи в ходу.",
  wordcloudHint: "Самые частые слова после чистки стоп-слов: крупнее — чаще.",
  wordcloudBuilding: "Собираем облако слов — это может занять несколько секунд…",
  wordcloudError: "Не удалось построить облако слов",
  wordcloudShuffle: "Перемешать",
  topWordsHint: "Частота отдельных слов.",
  phrasesHint: "Устойчивые пары и тройки слов — характерные обороты.",
  contactsHint: "E-mail и телефоны из переписки. Нажми, чтобы раскрыть и скопировать.",
  toneRadarHint: "Доля вопросов, восклицаний, КАПСА и цитирований — стиль участника.",
  wakeupHint: "Медиана времени первого сообщения за день.",
  dailyActivityHint: "Сообщения участника по дням.",
  hourWeekdayUserHint: "Час × день недели для выбранного участника.",
  reciprocityHint: "Как быстро участник отвечает собеседнику.",
  streaksHint: "Самые длинные серии активных дней и паузы в общении.",
  initiatorHint: "Сколько разговоров участник начал первым.",
  forwardsHint: "Доля пересланных сообщений и откуда их репостят.",
  latencyHistHint: "Сколько ответов попадает в каждый интервал времени.",
  emojisHelp: "Любимые эмодзи участника в тексте — эмоциональный почерк.",
  stickersHelp: "Самые часто отправляемые стикеры.",
  chainDepthHint: "Насколько длинные треды-ответы: глубже — длиннее обсуждение.",
  // stickers as images
  totalStickers: "Всего стикеров",
  stickersNoImg: "Картинки стикеров появятся, если открыть чат через путь к папке экспорта (кнопка загрузки копирует только result.json, без медиа).",
  // contacts list
  showEmails: "Показать e-mail",
  showPhones: "Показать телефоны",
  copy: "Копировать",
  copied: "Скопировано",
  // onboarding
  pathHint: "Или вставь путь к папке экспорта (или к result.json внутри неё) вручную — тоже со стикерами и медиа. Принимается и file://.",
}

const en: typeof ru = {
  messages: "Messages",
  participants: "Participants",
  daysActive: "Days active",
  media: "Media",
  voice: "Voice time",
  highlights: "Highlights",
  tab_overview: "Overview",
  tab_network: "Network",
  tab_words: "Words",
  tab_channel: "Channel",
  tab_peruser: "Per user",
  howOften: "How often",
  whenHours: "When (by hour)",
  whatAbout: "Emoji, media & links",
  whoToWhom: "Reply speed",
  topDomains: "Top domains",
  longestMonologues: "Longest monologues",
  halfFaster: "Half of replies — faster than",
  p90Faster: "90% of replies — faster than",
  repliesCounted: "Replies counted",
  qSection: "Replies to questions",
  qWithAnswer: "Questions with a reply",
  conversations: "Conversations",
  perConvAvg: "Msgs/conversation (avg)",
  longestConv: "Longest",
  convLength: "Conversation length",
  longestConvs: "Longest conversations",
  droppedCap: "{{n}} replies slower than {{h}}h excluded",
  qaHint: "Messages with a question (“?”) and the replies to them — whether questions get answered faster than usual.",
  qaFaster: "{{m}} min faster than usual",
  qaSlower: "{{m}} min slower than usual",
  qaSame: "about average",
  whoToWhomHint: "“Half faster” is the median: half of replies arrive sooner. “90% faster” covers all but the slowest.",
  annivBase: "🎉 {{days}} {{w}} here",
  annivUpcoming: "next milestone “{{label}}” in {{n}} days",
  htmlWarning: "This is an HTML export: it has no participant IDs, so Network and Per-user are less accurate for groups. Export JSON for the full picture.",
  voiceMessages: "Voice messages",
  voiceTotal: "Total",
  voiceAvg: "Average",
  period: "Period",
  allHistory: "All history",
  allChats: "★ All chats",
  apply: "Apply",
  reset: "Reset",
  fromDate: "From",
  toDate: "To",
  appTagline: "Telegram chat analytics — local and private",
  onboardDesc: "Point to your exported result.json (Telegram → Settings → Export data) or open a demo.",
  pathPlaceholder: "/path/to/result.json",
  load: "Open",
  pickFile: "Pick a file…",
  pickPrompt: "Choose result.json from your Telegram export folder",
  pickUnavailable: "The native picker isn't available on this OS — paste a path below.",
  orDivider: "or",
  uploading: "Opening dialog…",
  uploadError: "Couldn't open the file dialog. Paste a path manually below.",
  uploadHint: "Opens a native dialog. Pick result.json straight from the export folder so stickers and media resolve. The file isn't copied and never leaves your machine.",
  demoPersonal: "Demo: personal chat",
  demoGroup: "Demo: group",
  loadError: "Couldn't load. Check the file path.",
  changeSource: "Change file",
  loading: "Loading…",
  noData: "No data for this chat.",
  tabError: "Couldn't load this data.",
  retry: "Retry",
  user: "User",
  count: "Messages",
  topWords: "Top words",
  wordcloud: "Word cloud",
  phrases: "Repeated phrases",
  bigrams: "Word pairs",
  trigrams: "Word triples",
  vocabulary: "Vocabulary richness",
  vocabHint: "MTLD measures lexical diversity — higher means words repeat less often.",
  contacts: "Contacts mentioned",
  emailsN: "E-mail addresses",
  phonesN: "Phone numbers",
  sentiment: "Sentiment",
  sentimentAvg: "Average tone",
  sentimentHint: "Scale −1…+1 (negative…positive). The model misses sarcasm and jokes — read with scepticism.",
  sentimentOverTime: "Sentiment over time",
  sentimentPerUser: "Sentiment by participant",
  sentimentByHour: "Sentiment by hour",
  sentimentByWeekday: "Sentiment by weekday",
  mostPositive: "Most positive",
  mostNegative: "Most negative",
  totalTokens: "Words total",
  uniqueTokens: "Unique",
  mtld: "MTLD",
  networkDesc: "Who replies to whom. Bubble size = messages sent, line width = replies exchanged. Drag nodes and scroll to zoom.",
  interactions: "Reply interactions",
  msgsSent: "Messages",
  repliesSent: "Replies sent",
  repliesReceived: "Replies received",
  netNodes: "Participants",
  netEdges: "Connections",
  maxDepth: "Max chain depth",
  avgDepth: "Average depth",
  chainDepth: "Reply-chain depth",
  downloadCsv: "Download CSV (for Gephi)",
  pickUser: "Participant",
  avgWords: "Words per message",
  questionShare: "With a question",
  replyShare: "Quotes in reply",
  timeOfDay: "When they write",
  msgLength: "Message length",
  characteristicPhrases: "Characteristic phrases",
  tod_night: "Night",
  tod_morning: "Morning",
  tod_day: "Day",
  tod_evening: "Evening",
  shareOfChat: "Share of chat",
  toneRadar: "Speaking tone",
  axisQuestion: "Questions",
  axisExcl: "Exclamations",
  axisCaps: "CAPS",
  axisReply: "Quote-replies",
  wakeup: "When they wake up",
  wakeupMedian: "First message (median)",
  dailyActivity: "Daily activity",
  hourWeekdayUser: "Hour × weekday",
  reciprocity: "Reply speed (reciprocity)",
  medianReply: "Median reply",
  within5: "Within 5 min",
  within30: "Within 30 min",
  within60: "Within 1 hour",
  streaks: "Streaks & silences",
  longestStreak: "Longest streak",
  currentStreak: "Current streak",
  activeDays: "Active days",
  longestSilences: "Longest silences",
  days: "days",
  initiator: "Who starts conversations",
  initiations: "Initiations",
  initiatorShare: "Initiation share",
  forwards: "Forwards (reposts)",
  forwardShare: "Forward share",
  latencyHist: "Reply-speed distribution",
  emojisOfUser: "Emoji",
  stickersOfUser: "Favourite stickers",
  vocabUser: "Vocabulary",
  matTitle: "Profanity",
  matHelp: "Root matching. Hits/100 = hits per 100 messages.",
  matMsgs: "Messages",
  matWith: "With profanity",
  matHits: "Hits",
  matPer100: "Hits/100",
  distinguishing: "Distinctive lexicon",
  distinguishingHelp: "Smoothed log-odds: words that set one apart from the other.",
  onlyUser: "Only",
  logOdds: "log-odds",
  channelTokens: "Words in posts",
  type_personal_chat: "Personal chat",
  type_private_group: "Group",
  type_private_supergroup: "Group",
  type_public_supergroup: "Group",
  type_private_channel: "Channel",
  type_public_channel: "Channel",
  type_bot_chat: "Bot",
  type_saved_messages: "Saved Messages",
  type_multichat: "Combined",
  helpExport: "How do I get the export?",
  helpExportContentMd:
    "In **Telegram Desktop**:\n\n" +
    "- **A single chat** — `Settings → Export chat history`\n" +
    "- **The whole account** — `Settings → Advanced → Export Telegram data`\n\n" +
    "In the export dialog choose **JSON**. HTML also works (a folder or `messages.html`), but is less accurate.",
  sentimentOffTitle: "Sentiment analysis is off",
  sentimentOffBody:
    "RU/EN sentiment needs optional dependencies. Install and restart the server:",
  sentimentOffNote:
    "It adds ~1 GB (torch + transformers) plus ~50 MB for the model on first run. The model misses sarcasm and jokes — it's a helper metric, not a diagnosis.",
  msgLengthMedian: "Length (median)",
  charsShort: "chars",
  wakeupOthers: "others:",
  initiatorsLowN: "⚠ only {{n}} initiations total — sample is small, the share may be noise.",
  reciprocityReverse:
    "Reverse direction ({{a}} → {{b}}): median {{m}}, within 5 min {{p}}%. 5-min reply gap: {{d}} pp.",
  annivCrossed: "{{label}} since {{date}}",
  calendarMode: "Mode",
  calendarCount: "by count",
  calendarBinary: "wrote / didn't",
  calendarYear: "Year",
  calendarLess: "less",
  calendarMore: "more",
  calendarActiveDays: "Active days: {{a}} of {{t}} ({{p}}%)",
  capPeakHour: "peak hour — {{h}}:00",
  capNightShare: "at night ({{from}}–{{to}}) — {{p}}% of messages",
  overlapTitle: "When you overlap",
  overlapHint:
    "Bars normalised per user — fair when activity differs. Peak shared activity around {{h}}:00.",
  overlapBoth: "both active",
  showAll: "Show all ({{n}})",
  hideAll: "Hide",
  channelTopCount: "Unique words",
  preset7: "7d",
  preset30: "30d",
  preset90: "90d",
  presetAll: "All",
  persona_night: "🌙 night owl",
  persona_morning: "🌅 early bird",
  persona_day: "☀️ daytime",
  persona_evening: "🌆 evening",
  lenpersona_short: "📝 one-liner",
  lenpersona_med: "💬 short",
  lenpersona_long: "📄 elaborate",
  lenpersona_xl: "📜 essayist",
  traitInitiator: "🚀 initiator",
  traitFastReplier: "⚡ fast replies",
  // section hints — "what you learn here"
  howOftenHint: "Message volume by day and a per-year activity calendar.",
  whenHoursHint: "An hour × weekday heatmap: when the chat is most alive.",
  whatAboutHint: "What fills the chat beyond text — emoji, attachments and links.",
  longestMonologuesHint: "Runs of consecutive messages with no reply from the other side.",
  topDomainsHint: "Domains of links shared in the chat.",
  emojiTop: "Top emoji",
  emojiTopHint: "The chat's emotional backdrop — which emoji are in play.",
  wordcloudHint: "Most frequent words after stop-word removal: larger = more frequent.",
  wordcloudBuilding: "Building the word cloud — this can take a few seconds…",
  wordcloudError: "Couldn't build the word cloud",
  wordcloudShuffle: "Shuffle",
  topWordsHint: "Frequency of individual words.",
  phrasesHint: "Recurring word pairs and triples — signature expressions.",
  contactsHint: "E-mails and phone numbers from the chat. Click to expand and copy.",
  toneRadarHint: "Share of questions, exclamations, CAPS and quoting — the person's style.",
  wakeupHint: "Median time of the first message each day.",
  dailyActivityHint: "The person's messages by day.",
  hourWeekdayUserHint: "Hour × weekday for the selected participant.",
  reciprocityHint: "How quickly the person replies to the other side.",
  streaksHint: "Longest runs of active days and the quietest gaps.",
  initiatorHint: "How many conversations the person started first.",
  forwardsHint: "Share of forwarded messages and where they're reposted from.",
  latencyHistHint: "How many replies fall into each time bucket.",
  emojisHelp: "The person's favourite emoji in text — an emotional fingerprint.",
  stickersHelp: "The stickers they send most.",
  chainDepthHint: "How long reply threads get: deeper = longer discussion.",
  // stickers as images
  totalStickers: "Total stickers",
  stickersNoImg: "Sticker images appear when the chat is opened via the export-folder path (the upload button copies only result.json, without media).",
  // contacts list
  showEmails: "Show e-mails",
  showPhones: "Show phone numbers",
  copy: "Copy",
  copied: "Copied",
  // onboarding
  pathHint: "Or paste the path to the export folder (or the result.json inside it) by hand — stickers and media work here too. file:// is accepted.",
}

i18n.use(initReactI18next).init({
  resources: { ru: { translation: ru }, en: { translation: en } },
  lng: "ru",
  fallbackLng: "ru",
  interpolation: { escapeValue: false },
})

const isRu = () => i18n.language === "ru"

export function chatTypeLabel(t: string): string {
  const v = i18n.t(`type_${t}`)
  return v === `type_${t}` ? t : v
}

const KIND_RU: Record<string, string> = {
  text: "Текст", photo: "Фото", video_file: "Видео", video_message: "Кружок",
  voice_message: "Голосовое", audio_file: "Аудио", sticker: "Стикер",
  animation: "GIF", file: "Файл", location: "Геопозиция", contact: "Контакт",
  poll: "Опрос", service: "Сервисное", other: "Другое",
}
const KIND_EN: Record<string, string> = {
  text: "Text", photo: "Photo", video_file: "Video", video_message: "Video msg",
  voice_message: "Voice", audio_file: "Audio", sticker: "Sticker",
  animation: "Animation/GIF", file: "File", location: "Location", contact: "Contact",
  poll: "Poll", service: "Service", other: "Other",
}
export function mediaKindLabel(code: string): string {
  return (isRu() ? KIND_RU : KIND_EN)[code] ?? code
}

/** Plural form of "day" — Russian needs день/дня/дней by the number. */
export function dayWord(n: number): string {
  if (!isRu()) return n === 1 ? "day" : "days"
  const m100 = n % 100
  const m10 = n % 10
  if (m100 >= 11 && m100 <= 14) return "дней"
  if (m10 === 1) return "день"
  if (m10 >= 2 && m10 <= 4) return "дня"
  return "дней"
}

export function timeBucketLabel(code: string): string {
  const v = i18n.t(`tod_${code}`)
  return v === `tod_${code}` ? code : v
}

/** Persona label for the dominant time_of_day bucket (mirrors SpeakingStyle.persona). */
export function personaForTimeOfDay(buckets: Record<string, number>): string {
  let dom: string | null = null
  let best = -1
  for (const [k, v] of Object.entries(buckets)) {
    if (v > best) {
      best = v
      dom = k
    }
  }
  if (!dom) return "—"
  return i18n.t(`persona_${dom}`)
}

/** Persona label for the dominant length bucket (mirrors SpeakingStyle.length_persona). */
export function personaForLength(buckets: Record<string, number>): string {
  let dom: string | null = null
  let best = -1
  for (const [k, v] of Object.entries(buckets)) {
    if (v > best) {
      best = v
      dom = k
    }
  }
  const map: Record<string, string> = {
    "<30": "lenpersona_short",
    "30-100": "lenpersona_med",
    "100-300": "lenpersona_long",
    "300+": "lenpersona_xl",
  }
  return dom && map[dom] ? i18n.t(map[dom]) : "—"
}

export function weekdayShort(): string[] {
  return isRu()
    ? ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    : ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
}

/** Short month names, January first (index 0 = Jan) — matches ECharts
 *  calendar `monthLabel.nameMap`. */
export function monthShort(): string[] {
  return isRu()
    ? ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    : ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
}

/** Compact, locale-aware date for chart axis ticks: "15.01.24" (ru) /
 *  "01/15/24" (en). Built from parts (no UTC parse) to avoid timezone shifts;
 *  returns the raw value unchanged for non-date ticks. */
export function fmtDateTick(v: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v)
  if (!m) return v
  const dt = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  return new Intl.DateTimeFormat(isRu() ? "ru-RU" : "en-US", {
    year: "2-digit",
    month: "2-digit",
    day: "2-digit",
  }).format(dt)
}

export function fmtInt(n: number): string {
  return new Intl.NumberFormat(isRu() ? "ru-RU" : "en-US").format(n)
}

/** Humanized duration, mirrors analysis humanize_seconds (ч/м/с/д vs h/m/s/d). */
export function humanizeDuration(seconds: number): string {
  const s = Math.floor(seconds)
  const u = isRu()
    ? { s: "с", m: "м", h: "ч", d: "д" }
    : { s: "s", m: "m", h: "h", d: "d" }
  if (s < 60) return `${s}${u.s}`
  if (s < 3600) return `${Math.floor(s / 60)}${u.m} ${s % 60}${u.s}`
  if (s < 86400) return `${Math.floor(s / 3600)}${u.h} ${Math.floor((s % 3600) / 60)}${u.m}`
  return `${Math.floor(s / 86400)}${u.d} ${Math.floor((s % 86400) / 3600)}${u.h}`
}

export default i18n
