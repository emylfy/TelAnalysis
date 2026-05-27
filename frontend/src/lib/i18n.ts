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
  whatAbout: "О чём говорят",
  whoToWhom: "Кто кому",
  messageTypes: "Типы сообщений",
  topDomains: "Топ доменов",
  longestMonologues: "Самые длинные монологи",
  allEmoji: "Все эмоджи",
  calendar: "Календарь",
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
  // voice
  voiceMessages: "Голосовые",
  voiceTotal: "Суммарно",
  voiceAvg: "В среднем",
  // period
  period: "Период",
  allHistory: "вся история",
  // empty
  noData: "Нет данных для этого чата.",
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
  sentimentNote: "Средний тон переписки",
  sentimentOff: "Анализ тональности выключен.",
  totalTokens: "Слов всего",
  uniqueTokens: "Уникальных",
  mtld: "MTLD",
  // network tab
  networkDesc: "Кто кому отвечает. Размер кружка — сколько человек написал, толщина линии — сколько раз отвечали друг другу. Можно тянуть узлы и приближать колесом.",
  interactions: "Кто кому отвечает",
  msgsSent: "Сообщений",
  repliesSent: "Ответов отправил",
  repliesReceived: "Ответов получил",
  // per-user tab
  pickUser: "Участник",
  avgWords: "Слов в сообщении",
  questionShare: "С вопросом",
  exclShare: "С восклицанием",
  capsShare: "КАПСОМ",
  replyShare: "Цитирует в ответ",
  timeOfDay: "Когда пишет",
  msgLength: "Длина сообщений",
  characteristicPhrases: "Характерные фразы",
  tod_night: "Ночь",
  tod_morning: "Утро",
  tod_day: "День",
  tod_evening: "Вечер",
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
  whatAbout: "What about",
  whoToWhom: "Who replies to whom",
  messageTypes: "Message types",
  topDomains: "Top domains",
  longestMonologues: "Longest monologues",
  allEmoji: "All emoji",
  calendar: "Calendar",
  halfFaster: "Half of replies — faster than",
  p90Faster: "90% of replies — faster than",
  repliesCounted: "Replies counted",
  qSection: "Replies to questions",
  qWithAnswer: "Questions with a reply",
  conversations: "Conversations",
  perConvAvg: "Msgs/conversation (avg)",
  longestConv: "Longest",
  voiceMessages: "Voice messages",
  voiceTotal: "Total",
  voiceAvg: "Average",
  period: "Period",
  allHistory: "all history",
  noData: "No data for this chat.",
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
  sentimentNote: "Average tone",
  sentimentOff: "Sentiment analysis is off.",
  totalTokens: "Words total",
  uniqueTokens: "Unique",
  mtld: "MTLD",
  networkDesc: "Who replies to whom. Bubble size = messages sent, line width = replies exchanged. Drag nodes and scroll to zoom.",
  interactions: "Reply interactions",
  msgsSent: "Messages",
  repliesSent: "Replies sent",
  repliesReceived: "Replies received",
  pickUser: "Participant",
  avgWords: "Words per message",
  questionShare: "With a question",
  exclShare: "With an exclamation",
  capsShare: "IN CAPS",
  replyShare: "Quotes in reply",
  timeOfDay: "When they write",
  msgLength: "Message length",
  characteristicPhrases: "Characteristic phrases",
  tod_night: "Night",
  tod_morning: "Morning",
  tod_day: "Day",
  tod_evening: "Evening",
  type_personal_chat: "Personal chat",
  type_private_group: "Group",
  type_private_supergroup: "Group",
  type_public_supergroup: "Group",
  type_private_channel: "Channel",
  type_public_channel: "Channel",
  type_bot_chat: "Bot",
  type_saved_messages: "Saved Messages",
  type_multichat: "Combined",
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

export function timeBucketLabel(code: string): string {
  const v = i18n.t(`tod_${code}`)
  return v === `tod_${code}` ? code : v
}

export function weekdayShort(): string[] {
  return isRu()
    ? ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    : ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
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
