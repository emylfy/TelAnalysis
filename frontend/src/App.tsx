import { Suspense, lazy, useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import {
  BarChart3,
  CalendarCheck,
  CalendarDays,
  Clock,
  Flame,
  FolderCog,
  FolderOpen,
  Image as ImageIcon,
  Link2,
  MessageSquare,
  Mic,
  MoonStar,
  MoreVertical,
  Reply,
  Smile,
  Sparkles,
  Users,
  type LucideIcon,
} from "lucide-react"

import { api, type Chat, type Hero, type Highlight, type Kpis } from "@/lib/api"
import i18n, { chatTypeLabel, dayWord, fmtInt, humanizeDuration, participantWord } from "@/lib/i18n"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TabLoading } from "@/components/loading"
import { Stat } from "@/components/stat"
import { FadeItem, Stagger } from "@/components/motion"
import { Sparkline } from "@/components/sparkline"
import { Onboarding } from "@/Onboarding"

// Tabs are lazy: the heavy charting libs (ECharts) load only when a chart-bearing
// tab first mounts, keeping the initial bundle (shell + onboarding) small.
const Overview = lazy(() => import("@/Overview").then((m) => ({ default: m.Overview })))
const Words = lazy(() => import("@/Words").then((m) => ({ default: m.Words })))
const Network = lazy(() => import("@/Network").then((m) => ({ default: m.Network })))
const PerUser = lazy(() => import("@/PerUser").then((m) => ({ default: m.PerUser })))
const Channel = lazy(() => import("@/Channel").then((m) => ({ default: m.Channel })))
const ChatManager = lazy(() => import("@/ChatManager").then((m) => ({ default: m.ChatManager })))

const LS_PATH = "tla.path"
const COMBINE = "__combine__"

/** Pull chat/from/to/tab/lang from the current URL on first paint, so a
 *  reload (or shared link) lands on the same view. */
function readUrlState(): { chat?: string; from?: string; to?: string; tab?: string; lang?: string; view?: string } {
  if (typeof window === "undefined") return {}
  const q = new URLSearchParams(window.location.search)
  const out: { chat?: string; from?: string; to?: string; tab?: string; lang?: string; view?: string } = {}
  for (const k of ["chat", "from", "to", "tab", "lang", "view"] as const) {
    const v = q.get(k)
    if (v) out[k] = v
  }
  return out
}

/** Sync a subset of the app state into the URL. `replaceState` (not push) keeps
 *  the back-button useful — every chat-switch shouldn't create a history entry. */
function writeUrlState(s: { chat?: string; from?: string; to?: string; tab?: string; lang?: string; view?: string }) {
  if (typeof window === "undefined") return
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(s)) {
    if (v) q.set(k, v)
  }
  const qs = q.toString()
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname
  window.history.replaceState(null, "", url)
}

// section name (from API, mirrors loader.sections_for_type) → tab definition
const TAB_DEFS = [
  { section: "overview", id: "overview", labelKey: "tab_overview" },
  { section: "graph", id: "network", labelKey: "tab_network" },
  { section: "words", id: "words", labelKey: "tab_words" },
  { section: "channel", id: "channel", labelKey: "tab_channel" },
  { section: "perusers", id: "peruser", labelKey: "tab_peruser" },
] as const

function Logo() {
  // A filled chat-message bubble (pointed tail, bottom-left) with three ascending
  // bars knocked out of it — "analytics inside a message" in one mark. The bars
  // are a real SVG mask (transparent holes), so they read correctly on any
  // background and in both themes. Single brand colour (var(--primary)); the
  // multi-colour palette stays reserved for the actual charts.
  return (
    <svg width="26" height="26" viewBox="0 0 56 56" fill="none" aria-hidden="true">
      <mask id="tla-logo-bars">
        <rect width="56" height="56" fill="white" />
        <rect x="18" y="26" width="5" height="9" rx="1.5" fill="black" />
        <rect x="25.5" y="21" width="5" height="14" rx="1.5" fill="black" />
        <rect x="33" y="16" width="5" height="19" rx="1.5" fill="black" />
      </mask>
      <path
        d="M14 8 H44 a8 8 0 0 1 8 8 V32 a8 8 0 0 1 -8 8 H22 l-10 9 l3 -9 h-1 a8 8 0 0 1 -8 -8 V16 a8 8 0 0 1 8 -8 Z"
        fill="var(--primary)"
        mask="url(#tla-logo-bars)"
      />
    </svg>
  )
}

/** Overflow menu for set-once chrome (language, change source) — folded out of
 *  the main bar so the header keeps a clear primary/secondary hierarchy and
 *  stops wrapping at mid widths. */
function SettingsMenu({
  lang,
  onLang,
  onChangeSource,
}: {
  lang: "ru" | "en"
  onLang: (l: "ru" | "en") => void
  onChangeSource: () => void
}) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={t("settings")}
        className={cn(buttonVariants({ variant: "outline", size: "icon" }))}
      >
        <MoreVertical className="size-4" />
      </PopoverTrigger>
      <PopoverContent align="end" className="w-52 gap-1 p-1.5">
        <div className="px-2 pt-1 text-xs font-medium text-muted-foreground">{t("language")}</div>
        <div className="flex items-center gap-1 px-1 pb-1">
          {(["en", "ru"] as const).map((l) => (
            <button
              key={l}
              onClick={() => onLang(l)}
              className={cn(
                "flex-1 rounded-md px-2 py-1 text-sm transition-colors",
                lang === l
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="my-1 border-t border-border" />
        <button
          onClick={() => {
            setOpen(false)
            onChangeSource()
          }}
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-foreground transition-colors hover:bg-muted"
        >
          <FolderOpen className="size-4 text-muted-foreground" />
          {t("changeSource")}
        </button>
      </PopoverContent>
    </Popover>
  )
}

function PeriodPicker({
  bounds,
  from,
  to,
  onApply,
}: {
  bounds?: [string, string] | null
  from?: string
  to?: string
  onApply: (from?: string, to?: string) => void
}) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const min = bounds?.[0]?.slice(0, 10)
  const max = bounds?.[1]?.slice(0, 10)
  const [f, setF] = useState(from ?? min ?? "")
  const [tt, setTt] = useState(to ?? max ?? "")
  // Re-seed the editable inputs when the applied period or the date bounds
  // change — done during render (the documented alternative to an effect) so
  // there's no extra commit/flash. A changed `seed` triggers an immediate
  // re-render that React discards before painting.
  const [seed, setSeed] = useState({ from, to, min, max })
  if (seed.from !== from || seed.to !== to || seed.min !== min || seed.max !== max) {
    setSeed({ from, to, min, max })
    setF(from ?? min ?? "")
    setTt(to ?? max ?? "")
  }

  const label = from && to ? `${from} → ${to}` : t("allHistory")
  // Preset = last N days ending at max bound. "all" clears the filter so the
  // dashboard recomputes against the full history (different cache key).
  const applyPreset = (days: number | null) => {
    if (days == null || !max) {
      onApply(undefined, undefined)
      return
    }
    const end = new Date(max)
    const start = new Date(end)
    start.setDate(end.getDate() - days + 1)
    const isoStart = start.toISOString().slice(0, 10)
    onApply(isoStart < (min ?? isoStart) ? min : isoStart, max)
  }
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger className={cn(buttonVariants({ variant: "outline" }), "gap-2 font-normal")}>
        <CalendarDays className="size-4 text-muted-foreground" />
        <span className="tabular-nums">{label}</span>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-auto space-y-3">
        {/* quick presets — folded in from the old inline bar so the period has a
            single affordance instead of two competing ones in the header */}
        <div className="flex items-center gap-1">
          {([
            { d: 7, k: "preset7" },
            { d: 30, k: "preset30" },
            { d: 90, k: "preset90" },
            { d: null, k: "presetAll" },
          ] as const).map((p) => (
            <button
              key={p.k}
              onClick={() => {
                applyPreset(p.d)
                setOpen(false)
              }}
              className="rounded-md border border-border px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {t(p.k)}
            </button>
          ))}
        </div>
        <div className="flex items-end gap-2">
          <label className="space-y-1 text-xs text-muted-foreground">
            {t("fromDate")}
            <input
              type="date"
              min={min}
              max={tt || max}
              value={f}
              onChange={(e) => setF(e.target.value)}
              className="block h-9 rounded-md border border-input bg-transparent px-2 text-sm text-foreground [color-scheme:dark]"
            />
          </label>
          <label className="space-y-1 text-xs text-muted-foreground">
            {t("toDate")}
            <input
              type="date"
              min={f || min}
              max={max}
              value={tt}
              onChange={(e) => setTt(e.target.value)}
              className="block h-9 rounded-md border border-input bg-transparent px-2 text-sm text-foreground [color-scheme:dark]"
            />
          </label>
        </div>
        <div className="flex justify-between gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              onApply(undefined, undefined)
              setOpen(false)
            }}
          >
            {t("reset")}
          </Button>
          <Button
            size="sm"
            disabled={!f || !tt}
            onClick={() => {
              onApply(f, tt)
              setOpen(false)
            }}
          >
            {t("apply")}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}

function TopBar(props: {
  chats: Chat[]
  value?: string
  onChat: (id: string) => void
  bounds?: [string, string] | null
  from?: string
  to?: string
  onPeriod: (from?: string, to?: string) => void
  lang: "ru" | "en"
  onLang: (l: "ru" | "en") => void
  onChangeSource: () => void
  onHome: () => void
  view: "analyze" | "manager"
  onToggleManager: () => void
}) {
  const { t } = useTranslation()
  const { chats, value, onChat, bounds, from, to, onPeriod, lang, onLang, onChangeSource, onHome, view, onToggleManager } = props
  const multi = chats.length > 1
  const manager = view === "manager"
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-[1320px] flex-wrap items-center gap-3 px-6 py-2.5">
        {/* Brand acts as "reset within file": first chat, no period filter,
            Overview tab, scrolled to top. Doesn't unload the file (that's the
            folder icon on the right). */}
        <button
          type="button"
          onClick={onHome}
          className="flex items-center gap-2 rounded-md transition-opacity hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Home"
        >
          <Logo />
          {/* select-none: the wordmark is identity (chrome), not selectable
              content — Firefox/Zen otherwise lets it drag-highlight. Two-tone
              ties the muted "Tel" prefix to the full-weight "Analysis". */}
          <span className="select-none text-lg font-bold tracking-tight">
            <span className="text-muted-foreground">Tel</span>Analysis
          </span>
        </button>
        <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
          {multi && (
            <Button
              variant="outline"
              onClick={onToggleManager}
              aria-label={t(manager ? "backToAnalytics" : "manageChats")}
              title={t(manager ? "backToAnalytics" : "manageChats")}
            >
              {manager ? <BarChart3 className="size-4" /> : <FolderCog className="size-4" />}
              <span className="hidden sm:inline">{t(manager ? "backToAnalytics" : "manageChats")}</span>
            </Button>
          )}
          {/* analysis controls only matter in analytics view */}
          {!manager && multi && (
            <Select value={value} onValueChange={(v) => v && onChat(v)}>
              <SelectTrigger className="w-[200px] sm:w-[240px]">
                <SelectValue>
                  {/* base-ui's Value renders the raw `value` by default — we
                      need a render-prop to map id → name (otherwise the chat
                      id like "3055506314" shows in the trigger). */}
                  {(v: string) =>
                    v === COMBINE
                      ? t("allChats")
                      : (() => {
                          const c = chats.find((x) => x.id === v)
                          return c ? `${c.name} · ${chatTypeLabel(c.type)}` : v
                        })()
                  }
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={COMBINE}>{t("allChats")}</SelectItem>
                {chats.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name} · {chatTypeLabel(c.type)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          {!manager && <PeriodPicker bounds={bounds} from={from} to={to} onApply={onPeriod} />}
          {/* thin rule separates set-once chrome (language, source) from the
              data-scope controls above — visual hierarchy, not just spacing */}
          <div aria-hidden className="mx-0.5 hidden h-5 w-px bg-border sm:block" />
          <SettingsMenu lang={lang} onLang={onLang} onChangeSource={onChangeSource} />
        </div>
      </div>
    </header>
  )
}

/** The "wrapped" summary poster: the chat's identity, the narrative recap, the
 *  relationship anniversary line, and a strip of headline figures — one cohesive
 *  card (with a soft brand glow) instead of a plain title + a separate KPI row.
 *  Shown above the tabs, so it frames every view. */
function SummaryCard({
  hero,
  kpis,
  voiceSeconds,
  annivBits,
  perDay,
  compact = false,
}: {
  hero: Hero
  kpis: Kpis
  voiceSeconds?: number
  annivBits?: string[]
  /** daily message counts — drives the hero activity sparkline (overview only) */
  perDay?: [string, number][]
  // slim identity bar (title + figures only) for non-overview tabs, so the full
  // narrative poster isn't repeated above every view
  compact?: boolean
}) {
  const { t } = useTranslation()
  const figures: { label: string; value: string; num?: number; icon: LucideIcon }[] = [
    { label: t("messages"), value: fmtInt(kpis.total_messages), num: kpis.total_messages, icon: MessageSquare },
    { label: t("daysActive"), value: fmtInt(kpis.active_days), num: kpis.active_days, icon: CalendarCheck },
    { label: participantWord(kpis.unique_users), value: fmtInt(kpis.unique_users), num: kpis.unique_users, icon: Users },
    { label: t("media"), value: fmtInt(kpis.media_messages), num: kpis.media_messages, icon: ImageIcon },
  ]
  if (voiceSeconds && voiceSeconds > 0) figures.push({ label: t("voice"), value: humanizeDuration(voiceSeconds), icon: Mic })

  // Date range for the eyebrow, humanised in the active locale ("Jan 13 – May 30,
  // 2026"). Falls back silently when the chat has no dated messages.
  const locale = i18n.language === "ru" ? "ru-RU" : "en-US"
  const fmtDate = (s: string) => {
    const d = new Date(s)
    return Number.isNaN(d.getTime()) ? s : d.toLocaleDateString(locale, { day: "numeric", month: "short", year: "numeric" })
  }
  const dateRange = kpis.first_date && kpis.last_date ? `${fmtDate(kpis.first_date)} – ${fmtDate(kpis.last_date)}` : null
  const eyebrow = [chatTypeLabel(hero.chat_type), dateRange].filter(Boolean).join("  ·  ")

  if (compact) {
    return (
      <Card className="border-border bg-card px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-3">
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight">{hero.title}</h1>
            <span className="rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[0.7rem] font-medium text-muted-foreground">
              {chatTypeLabel(hero.chat_type)}
            </span>
          </div>
          <div className="flex flex-wrap items-baseline gap-x-7 gap-y-2">
            {figures.map((f) => (
              <div key={f.label} className="flex items-baseline gap-1.5">
                <span className="text-base font-semibold tabular-nums">{f.value}</span>
                <span className="text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">{f.label}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="relative overflow-hidden border-border bg-card px-8 py-7">
      {/* gradient mesh: a coral catch-light top-right + an indigo one bottom-left,
          both very soft — gives the poster depth without a loud full-card wash */}
      <div aria-hidden className="pointer-events-none absolute -right-28 -top-28 size-72 rounded-full bg-primary/10 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-32 -left-24 size-80 rounded-full bg-brand-2/10 blur-3xl" />
      <div className="relative">
        {/* eyebrow: chat type + date range — the context that used to sit in a
            muted meta line below, lifted above the title where dashboards put it */}
        {eyebrow && (
          <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{eyebrow}</div>
        )}
        <h1 className="mt-1.5 bg-gradient-to-br from-foreground to-foreground/65 bg-clip-text text-4xl font-bold tracking-tight text-transparent sm:text-5xl">
          {hero.title}
        </h1>
        <p
          className="mt-2.5 max-w-3xl text-base leading-relaxed text-foreground [&_b]:font-semibold [&_b]:text-primary"
          dangerouslySetInnerHTML={{ __html: hero.prose_html }}
        />
        {perDay && perDay.length > 1 && <Sparkline data={perDay} className="mt-5 h-10 w-full opacity-90" />}
        <Stagger className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {figures.map((f) => (
            <FadeItem key={f.label}>
              <Stat icon={f.icon} label={f.label} value={f.value} valueNum={f.num} className="h-full bg-surface-2" />
            </FadeItem>
          ))}
        </Stagger>
        {annivBits && annivBits.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {annivBits.map((b) => (
              <span
                key={b}
                className="rounded-full border border-border bg-muted/40 px-3 py-1 text-xs font-medium text-muted-foreground"
              >
                {b}
              </span>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}

// stable highlight kind (from the backend) → lucide icon, so the cards match the
// icon language of the section headers instead of mixing in emoji.
const HIGHLIGHT_ICONS: Record<string, LucideIcon> = {
  peak_hour: Clock,
  loudest_day: Flame,
  top_emoji: Smile,
  voice: Mic,
  streak: CalendarCheck,
  silence: MoonStar,
  latency: Reply,
  links: Link2,
}

function HighlightsRow({ items }: { items: Highlight[] }) {
  const { t } = useTranslation()
  if (!items.length) return null
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold">{t("highlights")}</h2>
      <Stagger className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((h) => {
          // map kind → lucide; Sparkles is a neutral fallback for unknown kinds.
          const Icon = (h.kind && HIGHLIGHT_ICONS[h.kind]) || Sparkles
          return (
          <FadeItem key={h.label}>
          <Card className="h-full flex-row items-center gap-3 border-border bg-card px-4 py-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-foreground/[0.04] ring-1 ring-foreground/10">
              <Icon className="size-5 text-muted-foreground" />
            </span>
            <div className="min-w-0">
              <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{h.label}</div>
              <div className="text-lg font-semibold leading-tight">{h.value}</div>
              <div className="truncate text-xs text-muted-foreground" title={h.sub}>{h.sub}</div>
            </div>
          </Card>
          </FadeItem>
          )
        })}
      </Stagger>
    </section>
  )
}

function HeaderSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-40 w-full" />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20" />
        ))}
      </div>
    </div>
  )
}

export default function App() {
  const { t } = useTranslation()
  const initial = readUrlState()
  const [lang, setLang] = useState<"ru" | "en">((initial.lang as "ru" | "en") ?? "en")
  const [path, setPath] = useState<string | null>(() => localStorage.getItem(LS_PATH))
  const [chat, setChat] = useState<string | undefined>(initial.chat)
  const [from, setFrom] = useState<string | undefined>(initial.from)
  const [to, setTo] = useState<string | undefined>(initial.to)
  const [tab, setTab] = useState(initial.tab ?? "overview")
  const [view, setView] = useState<"analyze" | "manager">(initial.view === "manager" ? "manager" : "analyze")

  useEffect(() => {
    i18n.changeLanguage(lang)
  }, [lang])

  // Mirror state into the URL whenever it changes — supports shared links and F5.
  useEffect(() => {
    writeUrlState({ chat, from, to, tab, lang, view: view === "manager" ? "manager" : undefined })
  }, [chat, from, to, tab, lang, view])

  const chatsQ = useQuery({
    queryKey: ["chats", path],
    queryFn: () => api.chats(path!),
    enabled: !!path,
    retry: false,
  })
  const chats = chatsQ.data?.chats ?? []
  const sel = chat ?? chats[0]?.id
  const selChat = chats.find((c) => c.id === sel)
  const period = { chat: sel, from, to, lang }
  // The chat manager is a backup-level view; honor ?view=manager only for full
  // archives (multi-chat). In manager mode the per-chat analytics queries below
  // are paused so we don't fire ~5 requests for a chat the user isn't viewing.
  const inManager = view === "manager" && chats.length > 1

  const boundsQ = useQuery({
    queryKey: ["bounds", path, sel],
    queryFn: () => api.bounds(path!, sel),
    enabled: !!path && !!sel && !inManager,
  })

  const heroQ = useQuery({ queryKey: ["hero", path, sel, from, to, lang], queryFn: () => api.hero(path!, period), enabled: !!sel && !inManager })
  const kpisQ = useQuery({ queryKey: ["kpis", path, sel, from, to], queryFn: () => api.kpis(path!, period), enabled: !!sel && !inManager })
  const hlQ = useQuery({ queryKey: ["hl", path, sel, from, to, lang], queryFn: () => api.highlights(path!, period), enabled: !!sel && !inManager })
  // shares its key with Overview (dedup); only used for the voice KPI card
  const mediaQ = useQuery({ queryKey: ["media", path, sel, from, to], queryFn: () => api.media(path!, period), enabled: !!sel && !inManager })
  const annivQ = useQuery({ queryKey: ["anniv", path, sel, from, to, lang], queryFn: () => api.anniversaries(path!, period), enabled: !!sel && !inManager })
  // shares its key with the Overview "per day" query (dedup) — feeds the hero sparkline
  const pdQ = useQuery({ queryKey: ["pd", path, sel, from, to], queryFn: () => api.perDay(path!, period), enabled: !!sel && !inManager })
  const isHtml = !!chatsQ.data && chatsQ.data.source !== "json"

  // Relationship recap chips for the summary card: ["N days together", "crossed
  // <milestone> on <date>", "<milestone> in M days"] — rendered as pills.
  const annivBits = (() => {
    const a = annivQ.data
    if (!a || a.days_since_start <= 0) return undefined
    const lastCrossed = [...(a.crossed_counts ?? []), ...(a.crossed_days ?? [])]
      .filter((m) => !!m.when)
      .sort((x, y) => (x.when! > y.when! ? -1 : 1))[0]
    const bits: string[] = []
    bits.push(t("annivBase", { days: fmtInt(a.days_since_start), w: dayWord(a.days_since_start) }))
    if (lastCrossed) bits.push(t("annivCrossed", { label: lastCrossed.label, date: lastCrossed.when }))
    if (a.upcoming_day) bits.push(t("annivUpcoming", { label: a.upcoming_day.label, n: fmtInt(a.upcoming_day.days_until ?? 0) }))
    return bits
  })()

  // available tabs for this chat type; reset active tab if it vanished.
  // The combined archive view is synthetic (multichat → overview + words).
  const availTabs = useMemo(() => {
    const secs = new Set(sel === COMBINE ? ["overview", "words"] : selChat?.sections ?? ["overview"])
    return TAB_DEFS.filter((d) => secs.has(d.section))
  }, [selChat, sel])
  // If the active tab isn't available for this chat type, fall back to the
  // first available one. Done during render (not in an effect) so the wrong
  // tab never paints; React discards this render and re-runs with the new tab.
  // Guard on isSuccess: until chats load, availTabs is the ["overview"]
  // placeholder, which would clobber a deep-linked ?tab=words on first paint.
  if (chatsQ.isSuccess && availTabs.length && !availTabs.some((d) => d.id === tab)) {
    setTab(availTabs[0].id)
  }

  const load = (p: string) => {
    setPath(p)
    localStorage.setItem(LS_PATH, p)
    setChat(undefined)
    setFrom(undefined)
    setTo(undefined)
    setTab("overview")
    setView("analyze")
  }
  const changeSource = () => {
    setPath(null)
    localStorage.removeItem(LS_PATH)
    setChat(undefined)
    setView("analyze")
  }
  const toggleManager = () => {
    setView((v) => (v === "manager" ? "analyze" : "manager"))
    if (typeof window !== "undefined") window.scrollTo({ top: 0 })
  }
  const pickChat = (id: string) => {
    setChat(id)
    setFrom(undefined)
    setTo(undefined)
  }
  const applyPeriod = (f?: string, t2?: string) => {
    setFrom(f)
    setTo(t2)
  }
  // Brand click — "home in the current file": clear chat/period/tab back to
  // defaults and scroll to top. Keeps the file loaded.
  const goHome = () => {
    setChat(undefined)
    setFrom(undefined)
    setTo(undefined)
    setTab("overview")
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" })
  }

  if (!path || chatsQ.isError) {
    return <Onboarding onLoad={load} error={chatsQ.isError} lang={lang} onLang={setLang} />
  }

  const renderTab = (id: string) => {
    const props = { path: path!, sel: period }
    switch (id) {
      case "overview": return <Overview {...props} />
      case "network": return <Network {...props} />
      case "words": return <Words {...props} />
      case "channel": return <Channel {...props} />
      case "peruser": return <PerUser {...props} />
      default: return null
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopBar
        chats={chats}
        value={sel}
        onChat={pickChat}
        bounds={boundsQ.data?.bounds}
        from={from}
        to={to}
        onPeriod={applyPeriod}
        lang={lang}
        onLang={setLang}
        onChangeSource={changeSource}
        onHome={goHome}
        view={inManager ? "manager" : "analyze"}
        onToggleManager={toggleManager}
      />
      <main className="mx-auto max-w-[1320px] space-y-4 px-6 py-5">
        {inManager ? (
          <Suspense fallback={<TabLoading />}>
            <ChatManager path={path!} />
          </Suspense>
        ) : (
          <>
            {isHtml && (
              <div className="rounded-lg border border-[#F6BD16]/30 bg-[#F6BD16]/10 px-4 py-2.5 text-sm text-[#F6BD16]">
                {t("htmlWarning")}
              </div>
            )}
            {heroQ.data && kpisQ.data ? (
              <SummaryCard
                hero={heroQ.data}
                kpis={kpisQ.data}
                voiceSeconds={mediaQ.data?.voice_total_seconds}
                annivBits={annivBits}
                perDay={tab === "overview" ? pdQ.data?.per_day : undefined}
                compact={tab !== "overview"}
              />
            ) : (
              <HeaderSkeleton />
            )}
            {tab === "overview" && hlQ.data && <HighlightsRow items={hlQ.data.highlights} />}

            {sel && (
              <Tabs value={tab} onValueChange={setTab} className="pt-2">
                <TabsList variant="line" className="w-full justify-start gap-6 border-b border-border">
                  {availTabs.map((d) => (
                    <TabsTrigger key={d.id} value={d.id}>
                      {t(d.labelKey)}
                    </TabsTrigger>
                  ))}
                </TabsList>
                {/* Render only the active tab — mounting every tab's panel triggers
                    its own useQuery calls, so rendering all of them on chat-load fired
                    ~15 requests up front. react-query still caches by key on return.
                    Suspense covers the lazy chunk download for that tab. */}
                <div className="mt-2" key={tab}>
                  <Suspense fallback={<TabLoading />}>{renderTab(tab)}</Suspense>
                </div>
              </Tabs>
            )}
          </>
        )}
      </main>
    </div>
  )
}
