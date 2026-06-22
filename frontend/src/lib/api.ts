// Thin client over the FastAPI backend (proxied at /api in dev, same-origin in prod).

const BASE = "/api"

async function get<T>(
  endpoint: string,
  params: Record<string, string | number | undefined>,
): Promise<T> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v != null && v !== "") qs.set(k, String(v))
  }
  const res = await fetch(`${BASE}/${endpoint}?${qs.toString()}`)
  if (!res.ok) throw new Error(`${endpoint} → ${res.status}`)
  return res.json() as Promise<T>
}

export interface Chat {
  id: string
  name: string
  type: string
  count: number
  sections: string[]
}
export interface ChannelResult {
  top_words: [string, number][]
  token_count: number
  has_wordcloud: boolean
}
export interface Kpis {
  total_messages: number
  unique_users: number
  first_date: string | null
  last_date: string | null
  days_active: number
  media_messages: number
}
export interface Hero {
  title: string
  prose_html: string
  meta: string
  chat_type: string
  chat_id: string
}
export interface Highlight {
  icon: string
  label: string
  value: string
  sub: string
}
export interface MediaStats {
  by_kind: Record<string, number>
  voice_count: number
  voice_total_seconds: number
  top_domains: [string, number][]
  total_links: number
}
export interface EmojiStats {
  chat_top: [string, number][]
  per_user: Record<string, [string, number][]>
  user_names: Record<string, string>
  total_emojis: number
  messages_with_emoji: number
}
export interface LatencyStats {
  overall_seconds: number[]
  per_user_seconds: Record<string, number[]>
  user_names: Record<string, string>
  median_seconds: number
  p90_seconds: number
  qa_seconds: number[]
  qa_median_seconds: number
  qa_p90_seconds: number
  dropped_over_cap: number
  cap_hours: number
}
export interface SessionsStats {
  sessions: { start: string; end: string; msg_count: number }[]
  avg_messages: number
  median_messages: number
  longest: { start: string; end: string; msg_count: number } | null
  duration_buckets: Record<string, number>
}
export interface MonologueRun {
  user_id: string
  name: string
  msg_count: number
  start: string
  end: string
  duration_seconds: number
}
export interface UserWords {
  user_id: string
  name: string
  msg_count: number
  avg_sentiment: number
  top_words: [string, number][]
  total_tokens: number
  unique_tokens: number
  mtld: number
  ttr: number
}
export interface WordsResult {
  chat_top_words: [string, number][]
  chat_avg_sentiment: number
  sentiment_available: boolean
  sarcasm_marked: number
  emails: string[]
  phones: string[]
  users: UserWords[]
}
export interface SpeakingStyle {
  user_id: string
  name: string
  msg_count: number
  avg_chars: number
  avg_words: number
  median_chars: number
  longest_chars: number
  question_ratio: number
  exclamation_ratio: number
  caps_ratio: number
  reply_count: number
  first_msg_minutes: number[]
  time_of_day: Record<string, number>
  length_buckets: Record<string, number>
}
export interface InteractionRow {
  user_id: string
  user: string
  sent: number
  replies_sent: number
  replies_received: number
}
export interface GraphResult {
  nodes: [string, string, number][]
  edges: [string, string, string][]
  communities: Record<string, number>
  summary: InteractionRow[]
}
export interface ChainStats {
  max_depth: number
  avg_depth: number
  chain_count: number
  depth_distribution: [number, number][]
}
export interface SentimentPoint {
  period?: string
  hour?: number
  weekday?: number
  user_id?: string
  avg: number
  count: number
}
export interface SentimentResult {
  available: boolean
  avg?: number
  sarcasm_marked?: number
  weekly?: SentimentPoint[]
  per_user_weekly?: SentimentPoint[]
  by_hour?: SentimentPoint[]
  by_weekday?: SentimentPoint[]
  user_names?: Record<string, string>
  positive?: [string, number, string][]
  negative?: [string, number, string][]
}
export interface Distinguishing {
  available: boolean
  a_name?: string
  b_name?: string
  a?: [string, number, number][]
  b?: [string, number, number][]
}
export interface DirectionStats {
  responder_id: string
  responder_name: string
  initiator_id: string
  initiator_name: string
  median_seconds: number
  p90_seconds: number
  within_5m: number
  within_30m: number
  within_60m: number
}
export interface Reciprocity {
  available: boolean
  a_to_b: DirectionStats | null
  b_to_a: DirectionStats | null
}
export interface StreakStats {
  longest_streak_days: number
  longest_streak_start: string | null
  longest_streak_end: string | null
  current_streak_days: number
  total_active_days: number
  longest_silences: [string, string, number][]
}
export interface InitiatorRow {
  user_id: string
  name: string
  initiations: number
  share: number
}
export interface InitiatorStats {
  gap_hours: number
  rows: InitiatorRow[]
  total_initiations: number
}
export interface UserForwards {
  user_id: string
  name: string
  total_messages: number
  forwarded_count: number
  top_sources: [string, number][]
}
export interface ForwardsStats {
  per_user: Record<string, UserForwards>
  chat_total_messages: number
  chat_forwarded_count: number
}
export interface UserMat {
  user_id: string
  name: string
  total_messages: number
  mat_messages: number
  mat_hits: number
}
export interface MatStats {
  per_user: Record<string, UserMat>
  weekly_totals: [string, number][]
}
export interface StickerRef {
  file: string
  thumbnail: string
  emoji: string
  count: number
}
export interface UserStickers {
  user_id: string
  name: string
  total_stickers: number
  top_emojis: [string, number][]
  top_stickers: StickerRef[]
}
export interface Milestone {
  label: string
  value: number
  when: string | null
  days_until: number | null
}
export interface Anniversaries {
  days_since_start: number
  total_messages: number
  crossed_days: Milestone[]
  crossed_counts: Milestone[]
  upcoming_day: Milestone | null
  upcoming_count: Milestone | null
}

// chat / period selector passed to every analysis call
type Sel = { chat?: string; from?: string; to?: string; lang?: string }
const p = (path: string, s: Sel = {}) => ({ path, chat: s.chat, from: s.from, to: s.to, lang: s.lang })

export const api = {
  chats: (path: string) => get<{ source: string; chats: Chat[] }>("chats", { path }),
  bounds: (path: string, chat?: string) =>
    get<{ bounds: [string, string] | null }>("bounds", { path, chat }),
  kpis: (path: string, s?: Sel) => get<Kpis>("kpis", p(path, s)),
  hero: (path: string, s?: Sel) => get<Hero>("hero", p(path, s)),
  highlights: (path: string, s?: Sel) => get<{ highlights: Highlight[] }>("highlights", p(path, s)),
  perDay: (path: string, s?: Sel, user?: string) =>
    get<{ per_day: [string, number][] }>("per-day", { ...p(path, s), user }),
  hourWeekday: (path: string, s?: Sel, user?: string) =>
    get<{ grid: number[][] }>("hour-weekday", { ...p(path, s), user }),
  hourByUser: (path: string, s?: Sel) =>
    get<{ users: { user_id: string; name: string; hours: number[] }[] }>("hour-by-user", p(path, s)),
  media: (path: string, s?: Sel) => get<MediaStats>("media", p(path, s)),
  emojis: (path: string, s?: Sel) => get<EmojiStats>("emojis", p(path, s)),
  latency: (path: string, s?: Sel) => get<LatencyStats>("latency", p(path, s)),
  sessions: (path: string, s?: Sel, gap = 30) =>
    get<SessionsStats>("sessions", { ...p(path, s), gap_minutes: gap }),
  monologues: (path: string, s?: Sel) => get<{ longest: MonologueRun[] }>("monologues", p(path, s)),
  words: (path: string, s?: Sel, top = 30) => get<WordsResult>("words", { ...p(path, s), top }),
  phrases: (path: string, s?: Sel, n = 2, top = 30) =>
    get<{ phrases: [string, number][] }>("phrases", { ...p(path, s), n, top }),
  graph: (path: string, s?: Sel) => get<GraphResult>("graph", p(path, s)),
  chains: (path: string, s?: Sel) => get<ChainStats>("chains", p(path, s)),
  channel: (path: string, s?: Sel) => get<ChannelResult>("channel", p(path, s)),
  speaking: (path: string, s?: Sel) => get<Record<string, SpeakingStyle>>("speaking", p(path, s)),
  perUserPhrases: (path: string, s?: Sel, n = 2, top = 15) =>
    get<Record<string, [string, number][]>>("per-user-phrases", { ...p(path, s), n, top }),
  sentiment: (path: string, s?: Sel, top = 10, user?: string) =>
    get<SentimentResult>("sentiment", { ...p(path, s), top, user }),
  distinguishing: (path: string, s?: Sel, top = 15) =>
    get<Distinguishing>("distinguishing", { ...p(path, s), top }),
  reciprocity: (path: string, s?: Sel) => get<Reciprocity>("reciprocity", p(path, s)),
  streaks: (path: string, s?: Sel, user?: string) =>
    get<StreakStats>("streaks", { ...p(path, s), user }),
  initiators: (path: string, s?: Sel) => get<InitiatorStats>("initiators", p(path, s)),
  forwards: (path: string, s?: Sel) => get<ForwardsStats>("forwards", p(path, s)),
  mat: (path: string, s?: Sel) => get<MatStats>("mat", p(path, s)),
  stickers: (path: string, s?: Sel) => get<Record<string, UserStickers>>("stickers", p(path, s)),
  anniversaries: (path: string, s?: Sel) => get<Anniversaries>("anniversaries", p(path, s)),
}

/** Upload a local file (the browser hides its filesystem path for privacy);
 *  the backend saves a copy under the OS temp dir and returns its abs path,
 *  which all other path-based endpoints can then use. */
export async function uploadFile(file: File): Promise<{ path: string; size: number }> {
  const fd = new FormData()
  fd.append("file", file)
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: fd })
  if (!res.ok) throw new Error(`upload → ${res.status}`)
  return res.json()
}

/** Open a NATIVE OS file picker on the local server and get back the REAL path.
 *  Unlike uploadFile this keeps the file in place, so adjacent media (chats/…)
 *  resolves and stickers/photos load. `unavailable` is returned on non-macOS so
 *  the caller can fall back to the manual path field. */
export async function browse(
  prompt: string,
): Promise<{ path?: string; cancelled?: boolean; unavailable?: boolean }> {
  const qs = new URLSearchParams({ prompt })
  const res = await fetch(`${BASE}/browse?${qs.toString()}`, { method: "POST" })
  if (res.status === 501) return { unavailable: true }
  if (!res.ok) throw new Error(`browse → ${res.status}`)
  return res.json()
}

/** Wordcloud is an image endpoint — build the URL for an <img src>. */
export function wordcloudUrl(path: string, chat?: string, channel = false): string {
  const qs = new URLSearchParams({ path })
  if (chat) qs.set("chat", chat)
  return `${BASE}/${channel ? "channel/wordcloud" : "wordcloud"}?${qs.toString()}`
}

/** A sticker / thumbnail file served from the export folder — URL for <img src>.
 *  Resolves only when the chat was loaded from the export folder (an uploaded
 *  copy of result.json has no media; the endpoint then 404s and the UI falls
 *  back to emoji tags). `rel` is the relative media path from the API. */
export function stickerFileUrl(path: string, rel: string): string {
  const qs = new URLSearchParams({ path, rel })
  return `${BASE}/sticker-file?${qs.toString()}`
}

export type { Sel }
