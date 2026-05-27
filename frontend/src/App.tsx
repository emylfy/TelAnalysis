import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, type Chat, type Hero, type Highlight, type Kpis } from "@/lib/api"
import i18n, { chatTypeLabel, fmtInt } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Overview } from "@/Overview"
import { Words } from "@/Words"
import { Network } from "@/Network"
import { PerUser } from "@/PerUser"

const DEMO_PATH = "demo/personal_demo.json"

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

function TopBar(props: {
  chats: Chat[]
  value?: string
  onChat: (id: string) => void
  lang: "ru" | "en"
  onLang: (l: "ru" | "en") => void
}) {
  const { chats, value, onChat, lang, onLang } = props
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-[1320px] items-center gap-4 px-6 py-2.5">
        <div className="flex items-center gap-2">
          <Logo />
          <span className="text-lg font-bold tracking-tight">TelAnalysis</span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          {chats.length > 1 && (
            <Select value={value} onValueChange={(v) => v && onChat(v)}>
              <SelectTrigger className="w-[260px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {chats.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name} · {chatTypeLabel(c.type)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
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

function KpiCards({ kpis }: { kpis: Kpis }) {
  const { t } = useTranslation()
  const items = [
    { label: t("messages"), value: fmtInt(kpis.total_messages) },
    { label: t("participants"), value: fmtInt(kpis.unique_users) },
    { label: t("daysActive"), value: fmtInt(kpis.days_active) },
    { label: t("media"), value: fmtInt(kpis.media_messages) },
  ]
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
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

export default function App() {
  const { t } = useTranslation()
  const [lang, setLang] = useState<"ru" | "en">("ru")
  const [chat, setChat] = useState<string | undefined>(undefined)
  const path = DEMO_PATH

  useEffect(() => {
    i18n.changeLanguage(lang)
  }, [lang])

  const chatsQ = useQuery({ queryKey: ["chats", path], queryFn: () => api.chats(path) })
  const chats = chatsQ.data?.chats ?? []
  const sel = chat ?? chats[0]?.id

  const heroQ = useQuery({ queryKey: ["hero", path, sel, lang], queryFn: () => api.hero(path, { chat: sel, lang }), enabled: !!sel })
  const kpisQ = useQuery({ queryKey: ["kpis", path, sel], queryFn: () => api.kpis(path, { chat: sel }), enabled: !!sel })
  const hlQ = useQuery({ queryKey: ["hl", path, sel, lang], queryFn: () => api.highlights(path, { chat: sel, lang }), enabled: !!sel })

  const tabs = [
    { id: "overview", label: t("tab_overview") },
    { id: "network", label: t("tab_network") },
    { id: "words", label: t("tab_words") },
    { id: "peruser", label: t("tab_peruser") },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopBar chats={chats} value={sel} onChat={setChat} lang={lang} onLang={setLang} />
      <main className="mx-auto max-w-[1320px] space-y-4 px-6 py-5">
        {heroQ.data && <HeroBlock hero={heroQ.data} />}
        {kpisQ.data && <KpiCards kpis={kpisQ.data} />}
        {hlQ.data && <HighlightsRow items={hlQ.data.highlights} />}

        <Tabs defaultValue="overview" className="pt-2">
          <TabsList>
            {tabs.map((tb) => (
              <TabsTrigger key={tb.id} value={tb.id}>
                {tb.label}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value="overview">
            <Overview path={path} sel={{ chat: sel, lang }} />
          </TabsContent>
          <TabsContent value="network">
            <Network path={path} sel={{ chat: sel, lang }} />
          </TabsContent>
          <TabsContent value="words">
            <Words path={path} sel={{ chat: sel, lang }} />
          </TabsContent>
          <TabsContent value="peruser">
            <PerUser path={path} sel={{ chat: sel, lang }} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
