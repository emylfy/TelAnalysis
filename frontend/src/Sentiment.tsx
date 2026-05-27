import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, type Sel, type SentimentPoint } from "@/lib/api"
import { weekdayShort } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { DivergingBars, Lines } from "@/components/charts"

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h3 className="text-base font-semibold tracking-tight">{title}</h3>
      {children}
    </section>
  )
}

function ExtremeList({ title, rows, tone }: { title: string; rows: [string, number, string][]; tone: "pos" | "neg" }) {
  const color = tone === "pos" ? "text-[#5AD8A6]" : "text-[#E86452]"
  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold">{title}</div>
      <Card className="divide-y divide-border/60 border-border bg-card p-0">
        {rows.map(([text, score, name], i) => (
          <div key={i} className="flex items-start gap-3 px-4 py-2.5">
            <span className={`shrink-0 tabular-nums text-sm font-semibold ${color}`}>{score.toFixed(2)}</span>
            <div className="min-w-0">
              <div className="truncate text-sm" title={text}>{text}</div>
              <div className="text-xs text-muted-foreground">{name}</div>
            </div>
          </div>
        ))}
      </Card>
    </div>
  )
}

export function SentimentBlock({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const k = [path, sel.chat, sel.from, sel.to]
  const q = useQuery({ queryKey: ["sentiment", ...k], queryFn: () => api.sentiment(path, sel), enabled: !!sel.chat })

  const d = q.data
  if (!d) return null
  if (!d.available) return <p className="text-sm text-muted-foreground">{t("sentimentOff")}</p>

  const wd = weekdayShort()
  const weeklySeries = d.weekly?.length
    ? [{ name: t("sentimentAvg"), data: d.weekly.map((w) => [w.period!, +w.avg.toFixed(3)] as [string, number]) }]
    : []

  // group per-user weekly into one series per user
  const byUser = new Map<string, [string, number][]>()
  for (const p of d.per_user_weekly ?? []) {
    const arr = byUser.get(p.user_id!) ?? []
    arr.push([p.period!, +p.avg.toFixed(3)])
    byUser.set(p.user_id!, arr)
  }
  const userSeries = [...byUser.entries()].map(([uid, data]) => ({ name: d.user_names?.[uid] ?? uid, data }))

  const hourData: [string, number][] = (d.by_hour ?? []).map((h: SentimentPoint) => [String(h.hour), +h.avg.toFixed(3)])
  const wdData: [string, number][] = (d.by_weekday ?? []).map((w: SentimentPoint) => [wd[w.weekday!], +w.avg.toFixed(3)])

  return (
    <div className="space-y-8">
      <div className="flex items-baseline gap-3">
        <h2 className="text-xl font-semibold tracking-tight">{t("sentiment")}</h2>
        {d.avg != null && (
          <span className={`tabular-nums text-lg font-semibold ${d.avg >= 0 ? "text-[#5AD8A6]" : "text-[#E86452]"}`}>
            {d.avg >= 0 ? "+" : ""}{d.avg.toFixed(2)}
          </span>
        )}
      </div>
      <p className="-mt-6 text-sm text-muted-foreground">{t("sentimentHint")}</p>

      {weeklySeries.length > 0 && (
        <Section title={t("sentimentOverTime")}>
          <Card className="border-border bg-card p-3"><Lines series={weeklySeries} zeroLine /></Card>
        </Section>
      )}

      {userSeries.length > 1 && (
        <Section title={t("sentimentPerUser")}>
          <Card className="border-border bg-card p-3"><Lines series={userSeries} zeroLine /></Card>
        </Section>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {hourData.length > 0 && (
          <Section title={t("sentimentByHour")}>
            <Card className="border-border bg-card p-3"><DivergingBars data={hourData} /></Card>
          </Section>
        )}
        {wdData.length > 0 && (
          <Section title={t("sentimentByWeekday")}>
            <Card className="border-border bg-card p-3"><DivergingBars data={wdData} /></Card>
          </Section>
        )}
      </div>

      {((d.positive?.length ?? 0) > 0 || (d.negative?.length ?? 0) > 0) && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {d.positive?.length ? <ExtremeList title={t("mostPositive")} rows={d.positive} tone="pos" /> : null}
          {d.negative?.length ? <ExtremeList title={t("mostNegative")} rows={d.negative} tone="neg" /> : null}
        </div>
      )}
    </div>
  )
}
