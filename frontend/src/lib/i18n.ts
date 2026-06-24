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
  convTotalTime: "Время в разговорах",
  longestConv: "Самый долгий",
  mostMessagesConv: "Больше всего сообщений",
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
  voiceShare: "Доля сообщений",
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
  privacyNote: "Файл не загружается на сервер — весь анализ идёт локально, на твоём компьютере.",
  whatYouGet: "Что внутри",
  anniversaries: "Годовщины",
  enterPathManually: "Ввести путь вручную",
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
  settings: "Настройки",
  language: "Язык",
  loading: "Загрузка…",
  // empty
  noData: "Нет данных для этого чата.",
  networkTooSmall: "Граф связей доступен для чатов с 2+ участниками.",
  tabError: "Не удалось загрузить данные.",
  other: "Прочие",
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
  sentimentBreakdown: "По часам и дням недели",
  mostPositive: "Самые позитивные",
  mostNegative: "Самые негативные",
  totalTokens: "Слов всего",
  uniqueTokens: "Уникальных",
  mtld: "MTLD",
  // network tab
  networkDesc: "Кто кому отвечает. Размер кружка — сколько человек написал, толщина и стрелка линии — сколько раз и в какую сторону отвечали. Кликни узел, чтобы рассмотреть его связи; тяни мышью, приближай колесом.",
  interactions: "Кто кому отвечает",
  netFocusPrompt: "Кликни кружок в графе или выбери участника — увидишь, кому он отвечает и кто отвечает ему.",
  netReplyingTo: "Кому отвечает",
  netRepliedBy: "Кто отвечает ему",
  netShowTop: "Показывать участников",
  netMinReplies: "Мин. ответов в связи",
  netNoPartners: "Нет reply-связей с другими участниками.",
  netAllNodes: "Весь граф",
  // chat portrait + roles
  portraitTitle: "Портрет чата",
  portraitHint: "Что структура ответов говорит о чате",
  pcConnected: "В ответах участвуют {{connected}} из {{total}} — остальные пишут, но не переписываются.",
  pcDistributed: "Живое распределённое общение — ответы расходятся по многим (на топ-3 приходится {{p}}%).",
  pcCentralized: "Общение завязано на звёздах — {{p}}% всех ответов достаётся троим.",
  pcMixed: "Смешанная структура — на топ-3 приходится {{p}}% ответов.",
  pcSmall: "Небольшой чат — роли не очень показательны.",
  pcCommunities: "Кругов общения: {{n}}.",
  pcBridges: "Держится на: {{names}} — через них пересекаются разные группы.",
  pcMagnet: "Магнит внимания: {{name}} — ему отвечают в {{ratio}}× чаще, чем он сам.",
  pcIgnored: "Часто без ответа: {{name}} — отвечает в {{ratio}}× чаще, чем отвечают ему.",
  pcHub: "Самый связанный: {{name}} — {{n}} собеседников.",
  roleCol: "Роль",
  roleHint: "Структурная роль в графе ответов. Наведите на бейдж — там описание.",
  role_bridge: "Мост",
  role_magnet: "Магнит",
  role_echo: "Эхо",
  role_connector: "Ядро",
  role_periphery: "Периферия",
  role_regular: "Участник",
  role_bridge_desc: "Связывает разные группы — через него пересекаются круги общения.",
  role_magnet_desc: "Ему отвечают заметно чаще, чем он сам, — притягивает внимание.",
  role_echo_desc: "Много отвечает другим, но в ответ ему пишут редко.",
  role_connector_desc: "Общается со многими примерно на равных — ядро чата.",
  role_periphery_desc: "Почти не вступает в переписку — один собеседник или меньше.",
  role_regular_desc: "Обычный участник без выраженной структурной роли.",
  msgsSent: "Сообщений",
  repliesSent: "Ответов отправил",
  repliesReceived: "Ответов получил",
  downloadCsv: "Скачать CSV (для Gephi)",
  // per-user tab
  pickUser: "Участник",
  searchUser: "Поиск участника…",
  wholeChat: "Весь чат",
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
  axisEmoji: "Эмодзи",
  axisVerbosity: "Многословность",
  unitWords: "сл",
  axisReply: "Цитирование",
  chatAverage: "Среднее по чату",
  avgShort: "средн.",
  chipFirstOnline: "🌅 онлайн с ~{{time}}",
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
  lastWordShare: "Последнее слово",
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
  traitCloser: "🎤 последнее слово",
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
  toneRadarHint: "Вопросы, восклицания, эмодзи, цитирование и длина сообщений — почерк участника.",
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
  // chat manager
  manageChats: "Менеджер чатов",
  backToAnalytics: "К аналитике",
  managerTitle: "Чаты в бэкапе",
  managerHint: "Все чаты экспорта с размером на диске. Удаляй ненужные, чтобы освободить место — удалённое уходит в корзину и его можно вернуть.",
  managerReadonly: "Этот источник нельзя редактировать. Управление доступно, только если открыть папку экспорта целиком (с подпапкой chats/), а не загруженную копию result.json или HTML-экспорт.",
  managerSearch: "Поиск по названию",
  managerShowLeft: "Покинутые чаты",
  managerSelected: "Выбрано: {{n}}",
  managerFreeUp: "Освободится ≈ {{size}}",
  colChat: "Чат",
  colType: "Тип",
  colMessages: "Сообщений",
  colPeriod: "Период",
  colSize: "На диске",
  colFiles: "Файлов",
  deleteSelected: "Удалить выбранные",
  slim: "Облегчить",
  slimTitle: "Облегчить чат: {{name}}",
  slimHint: "Перенести тяжёлые медиа в корзину, оставив текст переписки. Ссылки на эти файлы в экспорте станут нерабочими.",
  slimApply: "Перенести в корзину",
  openFolder: "Открыть папку",
  openFolderFailed: "Не удалось открыть папку",
  confirmDeleteTitle: "Удалить {{n}} {{w}}?",
  confirmDeleteBody: "Будет удалено {{msgs}} {{w}}. Папки медиа переедут в корзину — место освободится после её очистки. Можно вернуть до очистки.",
  confirm: "Удалить",
  cancel: "Отмена",
  trash: "Корзина",
  trashEmpty: "Корзина пуста.",
  trashPending: "В корзине ≈ {{size}} — освободятся при очистке.",
  restore: "Вернуть",
  emptyTrash: "Очистить корзину",
  emptyTrashConfirm: "Очистить корзину? Это окончательно удалит {{size}} без возможности восстановления.",
  managerLeftBadge: "покинут",
  noChatsFound: "Чаты не найдены.",
  freedToast: "Освобождено {{size}}",
  loadingChats: "Считаю размеры чатов…",
  selectAll: "Выбрать все",
  tombstonesTitle: "Покинутые каналы без сообщений",
  tombstonesHint: "Только названия — Telegram хранит их после выхода. Места не занимают.",
  tombstonesRemove: "Убрать из бэкапа",
  confirmTombsTitle: "Убрать {{n}} {{w}}?",
  confirmTombsBody: "Это уберёт их записи из result.json и из HTML-списка экспорта. Место на диске не освобождается — каналы и так пустые. Можно вернуть из корзины до её очистки.",
  familyChannels: "Каналы",
  familyGroups: "Группы",
  familyPersonal: "Личные",
  familyBots: "Боты",
  tombSortName: "Имя",
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
  convTotalTime: "Time in conversations",
  longestConv: "Longest",
  mostMessagesConv: "Most messages",
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
  voiceShare: "Share of messages",
  period: "Period",
  allHistory: "All history",
  allChats: "★ All chats",
  apply: "Apply",
  reset: "Reset",
  fromDate: "From",
  toDate: "To",
  appTagline: "Telegram chat analytics — local and private",
  onboardDesc: "Point to your exported result.json (Telegram → Settings → Export data) or open a demo.",
  privacyNote: "Nothing is uploaded — all analysis runs locally, on your machine.",
  whatYouGet: "What you get",
  anniversaries: "Anniversaries",
  enterPathManually: "Enter path manually",
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
  settings: "Settings",
  language: "Language",
  loading: "Loading…",
  noData: "No data for this chat.",
  networkTooSmall: "The relationship graph needs at least 2 participants.",
  tabError: "Couldn't load this data.",
  other: "Other",
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
  sentimentBreakdown: "By hour & weekday",
  mostPositive: "Most positive",
  mostNegative: "Most negative",
  totalTokens: "Words total",
  uniqueTokens: "Unique",
  mtld: "MTLD",
  networkDesc: "Who replies to whom. Bubble size = messages sent, line width & arrow = how many replies and in which direction. Click a node to inspect its links; drag nodes and scroll to zoom.",
  interactions: "Reply interactions",
  netFocusPrompt: "Click a node in the graph or pick a participant to see who they reply to and who replies to them.",
  netReplyingTo: "Replies to",
  netRepliedBy: "Replied to by",
  netShowTop: "Show participants",
  netMinReplies: "Min replies per link",
  netNoPartners: "No reply links with other participants.",
  netAllNodes: "Whole graph",
  portraitTitle: "Chat portrait",
  portraitHint: "What the reply structure says about the chat",
  pcConnected: "{{connected}} of {{total}} take part in replies — the rest post but don't converse.",
  pcDistributed: "Lively, distributed talk — replies spread across many (top 3 get {{p}}%).",
  pcCentralized: "Talk revolves around a few stars — {{p}}% of all replies go to three people.",
  pcMixed: "Mixed structure — top 3 get {{p}}% of replies.",
  pcSmall: "Small chat — roles aren't very telling.",
  pcCommunities: "Conversation circles: {{n}}.",
  pcBridges: "Held together by: {{names}} — different groups meet through them.",
  pcMagnet: "Attention magnet: {{name}} — replied to {{ratio}}× more than they reply.",
  pcIgnored: "Often unanswered: {{name}} — replies {{ratio}}× more than they get back.",
  pcHub: "Most connected: {{name}} — {{n}} partners.",
  roleCol: "Role",
  roleHint: "Structural role in the reply graph. Hover a badge for its meaning.",
  role_bridge: "Bridge",
  role_magnet: "Magnet",
  role_echo: "Echo",
  role_connector: "Connector",
  role_periphery: "Periphery",
  role_regular: "Member",
  role_bridge_desc: "Connects separate groups — conversations cross through them.",
  role_magnet_desc: "Replied to noticeably more than they reply — draws attention.",
  role_echo_desc: "Replies to others a lot but rarely gets replies back.",
  role_connector_desc: "Talks with many people, fairly balanced — a hub.",
  role_periphery_desc: "One reply partner or none — sits on the edge.",
  role_regular_desc: "An ordinary participant with no pronounced structural role.",
  msgsSent: "Messages",
  repliesSent: "Replies sent",
  repliesReceived: "Replies received",
  downloadCsv: "Download CSV (for Gephi)",
  pickUser: "Participant",
  searchUser: "Search participant…",
  wholeChat: "Whole chat",
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
  axisEmoji: "Emoji",
  axisVerbosity: "Verbosity",
  unitWords: "w",
  axisReply: "Quote-replies",
  chatAverage: "Chat average",
  avgShort: "avg",
  chipFirstOnline: "🌅 online from ~{{time}}",
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
  lastWordShare: "Last word",
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
  traitCloser: "🎤 last word",
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
  toneRadarHint: "Questions, exclamations, emoji, quoting and message length — the person's fingerprint.",
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
  // chat manager
  manageChats: "Manage chats",
  backToAnalytics: "Analytics",
  managerTitle: "Chats in the backup",
  managerHint: "Every chat in the export with its size on disk. Delete the ones you don't need to reclaim space — deleted chats go to the trash and can be restored.",
  managerReadonly: "This source is read-only. Management is available only when you open the whole export folder (with its chats/ subfolder), not an uploaded copy of result.json or an HTML export.",
  managerSearch: "Search by name",
  managerShowLeft: "Left chats",
  managerSelected: "Selected: {{n}}",
  managerFreeUp: "Frees ≈ {{size}}",
  colChat: "Chat",
  colType: "Type",
  colMessages: "Messages",
  colPeriod: "Period",
  colSize: "On disk",
  colFiles: "Files",
  deleteSelected: "Delete selected",
  slim: "Slim down",
  slimTitle: "Slim chat: {{name}}",
  slimHint: "Move heavy media to the trash, keeping the chat's text. Links to these files in the export will stop working.",
  slimApply: "Move to trash",
  openFolder: "Open folder",
  openFolderFailed: "Couldn't open the folder",
  confirmDeleteTitle: "Delete {{n}} {{w}}?",
  confirmDeleteBody: "This removes {{msgs}} {{w}}. Media folders move to the trash — space is reclaimed when you empty it. Restorable until then.",
  confirm: "Delete",
  cancel: "Cancel",
  trash: "Trash",
  trashEmpty: "The trash is empty.",
  trashPending: "≈ {{size}} in trash — reclaimed when emptied.",
  restore: "Restore",
  emptyTrash: "Empty trash",
  emptyTrashConfirm: "Empty the trash? This permanently deletes {{size}} with no way back.",
  managerLeftBadge: "left",
  noChatsFound: "No chats found.",
  freedToast: "Reclaimed {{size}}",
  loadingChats: "Measuring chat sizes…",
  selectAll: "Select all",
  tombstonesTitle: "Left channels with no messages",
  tombstonesHint: "Names only — Telegram keeps these after you leave. They use no space.",
  tombstonesRemove: "Remove from backup",
  confirmTombsTitle: "Remove {{n}} {{w}}?",
  confirmTombsBody: "This clears their records from result.json and the export's HTML list. It frees no disk space — these channels are already empty. Restorable from the trash until you empty it.",
  familyChannels: "Channels",
  familyGroups: "Groups",
  familyPersonal: "Personal",
  familyBots: "Bots",
  tombSortName: "Name",
}

i18n.use(initReactI18next).init({
  resources: { ru: { translation: ru }, en: { translation: en } },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
})

const isRu = () => i18n.language === "ru"

export function chatTypeLabel(t: string): string {
  const v = i18n.t(`type_${t}`)
  return v === `type_${t}` ? t : v
}

export type ChatFamily = "channel" | "group" | "personal" | "bot"

/** Coarse family of a chat type, for filter chips and grouping. Telegram's raw
 *  types collapse to four buckets: `*_channel` → channel, `*_group`/
 *  `*_supergroup` → group, `*bot*` → bot, everything else (personal_chat,
 *  saved_messages, …) → personal. */
export function chatTypeFamily(t: string): ChatFamily {
  if (t.includes("channel")) return "channel"
  if (t.includes("group")) return "group"
  if (t.includes("bot")) return "bot"
  return "personal"
}

/** Plural-aware family label for chips/headers (Каналы / Группы / Личные / Боты). */
export function chatFamilyLabel(f: ChatFamily): string {
  return i18n.t(
    { channel: "familyChannels", group: "familyGroups", personal: "familyPersonal", bot: "familyBots" }[f],
  )
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

/** Plural form of "participant" — Russian needs участник/участника/участников. */
export function participantWord(n: number): string {
  if (!isRu()) return n === 1 ? "participant" : "participants"
  const m100 = n % 100
  const m10 = n % 10
  if (m100 >= 11 && m100 <= 14) return "участников"
  if (m10 === 1) return "участник"
  if (m10 >= 2 && m10 <= 4) return "участника"
  return "участников"
}

/** Plural form of "chat" — Russian needs чат/чата/чатов. */
export function chatWord(n: number): string {
  if (!isRu()) return n === 1 ? "chat" : "chats"
  const m100 = n % 100
  const m10 = n % 10
  if (m100 >= 11 && m100 <= 14) return "чатов"
  if (m10 === 1) return "чат"
  if (m10 >= 2 && m10 <= 4) return "чата"
  return "чатов"
}

/** Plural form of "message" — Russian needs сообщение/сообщения/сообщений. */
export function messageWord(n: number): string {
  if (!isRu()) return n === 1 ? "message" : "messages"
  const m100 = n % 100
  const m10 = n % 10
  if (m100 >= 11 && m100 <= 14) return "сообщений"
  if (m10 === 1) return "сообщение"
  if (m10 >= 2 && m10 <= 4) return "сообщения"
  return "сообщений"
}

/** Signed score with a fixed sign, but never a "-0.00"/"+0.00" — a rounded zero
 *  is plain. Used for sentiment averages where the sign carries meaning. */
export function fmtSigned(v: number, digits = 2): string {
  const r = v.toFixed(digits)
  const n = Number(r)
  if (n > 0) return `+${r}`
  if (n === 0) return (0).toFixed(digits)
  return r
}

/** Same as toFixed but collapses a rounded "-0.00" to "0.00" (no forced sign). */
export function fmtScore(v: number, digits = 2): string {
  const r = v.toFixed(digits)
  return Number(r) === 0 ? (0).toFixed(digits) : r
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

/** Human-readable byte size: 6.8 GB / 391 MB / 0 B. Binary (1024) units, the
 *  decimal kept only below 10 of a unit so big figures stay compact. */
export function fmtBytes(n: number): string {
  if (!n || n < 1) return isRu() ? "0 Б" : "0 B"
  const units = isRu()
    ? ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    : ["B", "KB", "MB", "GB", "TB"]
  const i = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)))
  const v = n / Math.pow(1024, i)
  const digits = i === 0 ? 0 : v < 10 ? 1 : 0
  return `${new Intl.NumberFormat(isRu() ? "ru-RU" : "en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(v)} ${units[i]}`
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
