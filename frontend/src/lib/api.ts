// Thin client over the FastAPI backend (proxied at /api in dev, same-origin in prod).

const BASE = "/api"

async function get<T>(
  endpoint: string,
  params: Record<string, string | undefined>,
): Promise<T> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v != null && v !== "") qs.set(k, v)
  const res = await fetch(`${BASE}/${endpoint}?${qs.toString()}`)
  if (!res.ok) throw new Error(`${endpoint} → ${res.status}`)
  return res.json() as Promise<T>
}

export interface Chat {
  id: string
  name: string
  type: string
  count: number
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

export const api = {
  chats: (path: string) => get<{ source: string; chats: Chat[] }>("chats", { path }),
  kpis: (path: string, chat?: string, lang?: string) =>
    get<Kpis>("kpis", { path, chat, lang }),
  hero: (path: string, chat?: string, lang?: string) =>
    get<Hero>("hero", { path, chat, lang }),
  highlights: (path: string, chat?: string, lang?: string) =>
    get<{ highlights: Highlight[] }>("highlights", { path, chat, lang }),
  perDay: (path: string, chat?: string, lang?: string) =>
    get<{ per_day: [string, number][] }>("per-day", { path, chat, lang }),
}
