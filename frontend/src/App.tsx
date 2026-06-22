import { Suspense, lazy, useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { CalendarDays, FolderOpen } from "lucide-react"

import { api, type Chat, type Hero, type Highlight, type Kpis } from "@/lib/api"
import i18n, { chatTypeLabel, dayWord, fmtInt, humanizeDuration } from "@/lib/i18n"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TabLoading } from "@/components/loading"
import { Onboarding } from "@/Onboarding"

// Tabs are lazy: the heavy charting libs (ECharts) load only when a chart-bearing
// tab first mounts, keeping the initial bundle (shell + onboarding) small.
const Overview = lazy(() => import("@/Overview").then((m) => ({ default: m.Overview })))
const Words = lazy(() => import("@/Words").then((m) => ({ default: m.Words })))
const Network = lazy(() => import("@/Network").then((m) => ({ default: m.Network })))
const PerUser = lazy(() => import("@/PerUser").then((m) => ({ default: m.PerUser })))
const Channel = lazy(() => import("@/Channel").then((m) => ({ default: m.Channel })))

const LS_PATH = "tla.path"
const COMBINE = "__combine__"

/** Pull chat/from/to/tab/lang from the current URL on first paint, so a
 *  reload (or shared link) lands on the same view. */
function readUrlState(): { chat?: string; from?: string; to?: string; tab?: string; lang?: string } {
  if (typeof window === "undefined") return {}
  const q = new URLSearchParams(window.location.search)
  const out: { chat?: string; from?: string; to?: string; tab?: string; lang?: string } = {}
  for (const k of ["chat", "from", "to", "tab", "lang"] as const) {
    const v = q.get(k)
    if (v) out[k] = v
  }
  return out
}

/** Sync a subset of the app state into the URL. `replaceState` (not push) keeps
 *  the back-button useful — every chat-switch shouldn't create a history entry. */
function writeUrlState(s: { chat?: string; from?: string; to?: string; tab?: string; lang?: string }) {
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
  return (
    <svg width="26" height="26" viewBox="0 0 56 56" fill="none">
      <rect width="56" height="56" rx="14" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.10)" />
      <rect x="15" y="30" width="6" height="11" rx="2" fill="var(--chart-1)" />
      <rect x="25" y="22" width="6" height="19" rx="2" fill="var(--chart-2)" />
      <rect x="35" y="15" width="6" height="26" rx="2" fill="var(--primary)" />
    </svg>
  )
}

function LangToggle({ lang, onLang }: { lang: "ru" | "en"; onLang: (l: "ru" | "en") => void }) {
  return (
    <div className="flex items-center rounded-lg border border-border bg-card p-0.5">
      {(["ru", "en"] as const).map((l) => (
        <button
          key={l}
          onClick={() => onLang(l)}
          className={`rounded-md px-3 py-1 text-sm transition-colors ${
            lang === l ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
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
    <div className="flex items-center gap-1.5">
      <div className="hidden items-center rounded-md border border-border bg-card p-0.5 sm:flex">
        {([
          { d: 7, k: "preset7" },
          { d: 30, k: "preset30" },
          { d: 90, k: "preset90" },
          { d: null, k: "presetAll" },
        ] as const).map((p) => (
          <button
            key={p.k}
            onClick={() => applyPreset(p.d)}
            className="rounded px-2 py-0.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            {t(p.k)}
          </button>
        ))}
      </div>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger className={cn(buttonVariants({ variant: "outline" }), "gap-2 font-normal")}>
          <CalendarDays className="size-4 text-muted-foreground" />
          <span className="tabular-nums">{label}</span>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-auto space-y-3">
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
    </div>
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
}) {
  const { t } = useTranslation()
  const { chats, value, onChat, bounds, from, to, onPeriod, lang, onLang, onChangeSource, onHome } = props
  const multi = chats.length > 1
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
          <span className="text-lg font-bold tracking-tight">TelAnalysis</span>
        </button>
        <div className="ml-auto flex flex-wrap items-center gap-3">
          {multi && (
            <Select value={value} onValueChange={(v) => v && onChat(v)}>
              <SelectTrigger className="w-[240px]">
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
          <PeriodPicker bounds={bounds} from={from} to={to} onApply={onPeriod} />
          <Button variant="outline" size="icon" onClick={onChangeSource} title={t("changeSource")}>
            <FolderOpen className="size-4" />
          </Button>
          <LangToggle lang={lang} onLang={onLang} />
        </div>
      </div>
    </header>
  )
}

function HeroBlock({ hero }: { hero: Hero }) {
  return (
    <Card className="border-border bg-card px-8 py-7">
      <h1 className="text-4xl font-bold tracking-tight">{hero.title}</h1>
      <p
        className="mt-3 text-base leading-relaxed text-foreground [&_b]:font-semibold [&_b]:text-primary"
        dangerouslySetInnerHTML={{ __html: hero.prose_html }}
      />
      <div className="mt-3 text-sm text-muted-foreground">
        {hero.meta} · {chatTypeLabel(hero.chat_type)}
      </div>
    </Card>
  )
}

function KpiCards({ kpis, voiceSeconds }: { kpis: Kpis; voiceSeconds?: number }) {
  const { t } = useTranslation()
  const items = [
    { label: t("messages"), value: fmtInt(kpis.total_messages) },
    { label: t("participants"), value: fmtInt(kpis.unique_users) },
    { label: t("daysActive"), value: fmtInt(kpis.days_active) },
    { label: t("media"), value: fmtInt(kpis.media_messages) },
  ]
  if (voiceSeconds && voiceSeconds > 0) items.push({ label: t("voice"), value: humanizeDuration(voiceSeconds) })
  return (
    <div className={`grid grid-cols-2 gap-3 sm:grid-cols-4 ${items.length === 5 ? "lg:grid-cols-5" : ""}`}>
      {items.map((it) => (
        <Card key={it.label} className="gap-1 border-border bg-card px-4 py-3">
          <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{it.label}</div>
          <div className="text-2xl font-semibold tabular-nums">{it.value}</div>
        </Card>
      ))}
    </div>
  )
}

function HighlightsRow({ items }: { items: Highlight[] }) {
  const { t } = useTranslation()
  if (!items.length) return null
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold">{t("highlights")}</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((h) => (
          <Card key={h.label} className="gap-1 border-border border-l-2 border-l-primary/45 bg-card px-4 py-3">
            <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{h.label}</div>
            <div className="text-lg font-semibold">{h.value}</div>
            <div className="text-xs text-muted-foreground">{h.sub}</div>
          </Card>
        ))}
      </div>
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
  const [lang, setLang] = useState<"ru" | "en">((initial.lang as "ru" | "en") ?? "ru")
  const [path, setPath] = useState<string | null>(() => localStorage.getItem(LS_PATH))
  const [chat, setChat] = useState<string | undefined>(initial.chat)
  const [from, setFrom] = useState<string | undefined>(initial.from)
  const [to, setTo] = useState<string | undefined>(initial.to)
  const [tab, setTab] = useState(initial.tab ?? "overview")

  useEffect(() => {
    i18n.changeLanguage(lang)
  }, [lang])

  // Mirror state into the URL whenever it changes — supports shared links and F5.
  useEffect(() => {
    writeUrlState({ chat, from, to, tab, lang })
  }, [chat, from, to, tab, lang])

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

  const boundsQ = useQuery({
    queryKey: ["bounds", path, sel],
    queryFn: () => api.bounds(path!, sel),
    enabled: !!path && !!sel,
  })

  const heroQ = useQuery({ queryKey: ["hero", path, sel, from, to, lang], queryFn: () => api.hero(path!, period), enabled: !!sel })
  const kpisQ = useQuery({ queryKey: ["kpis", path, sel, from, to], queryFn: () => api.kpis(path!, period), enabled: !!sel })
  const hlQ = useQuery({ queryKey: ["hl", path, sel, from, to, lang], queryFn: () => api.highlights(path!, period), enabled: !!sel })
  // shares its key with Overview (dedup); only used for the voice KPI card
  const mediaQ = useQuery({ queryKey: ["media", path, sel, from, to], queryFn: () => api.media(path!, period), enabled: !!sel })
  const annivQ = useQuery({ queryKey: ["anniv", path, sel, from, to, lang], queryFn: () => api.anniversaries(path!, period), enabled: !!sel })
  const isHtml = !!chatsQ.data && chatsQ.data.source !== "json"

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
  }
  const changeSource = () => {
    setPath(null)
    localStorage.removeItem(LS_PATH)
    setChat(undefined)
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
      />
      <main className="mx-auto max-w-[1320px] space-y-4 px-6 py-5">
        {isHtml && (
          <div className="rounded-lg border border-[#F6BD16]/30 bg-[#F6BD16]/10 px-4 py-2.5 text-sm text-[#F6BD16]">
            {t("htmlWarning")}
          </div>
        )}
        {heroQ.data ? <HeroBlock hero={heroQ.data} /> : <HeaderSkeleton />}
        {annivQ.data && annivQ.data.days_since_start > 0 && (() => {
          const a = annivQ.data
          const lastCrossed = [...(a.crossed_counts ?? []), ...(a.crossed_days ?? [])]
            .filter((m) => !!m.when)
            .sort((x, y) => (x.when! > y.when! ? -1 : 1))[0]
          const bits: string[] = []
          bits.push(t("annivBase", { days: fmtInt(a.days_since_start), w: dayWord(a.days_since_start) }))
          if (lastCrossed) bits.push(t("annivCrossed", { label: lastCrossed.label, date: lastCrossed.when }))
          if (a.upcoming_day)
            bits.push(t("annivUpcoming", { label: a.upcoming_day.label, n: fmtInt(a.upcoming_day.days_until ?? 0) }))
          return <div className="text-sm text-muted-foreground">{bits.join(" · ")}</div>
        })()}
        {kpisQ.data && <KpiCards kpis={kpisQ.data} voiceSeconds={mediaQ.data?.voice_total_seconds} />}
        {hlQ.data && <HighlightsRow items={hlQ.data.highlights} />}

        {sel && (
          <Tabs value={tab} onValueChange={setTab} className="pt-2">
            <TabsList>
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
      </main>
    </div>
  )
}
