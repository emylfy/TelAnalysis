import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { Smile } from "lucide-react"

import { api, type Sel, type SentimentPoint } from "@/lib/api"
import { fmtScore, fmtSigned, weekdayShort } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { DivergingBars, Lines } from "@/components/charts"
import { personPalette } from "@/lib/chart-theme"
import { Section } from "@/components/section"
import { Collapsible } from "@/components/collapsible"

/** Sub-section header inside the sentiment block (smaller than a tab Section). */
function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h3 className="text-base font-semibold tracking-tight">{title}</h3>
      {children}
    </section>
  )
}

export function ExtremeList({ title, rows, tone }: { title: string; rows: [string, number, string][]; tone: "pos" | "neg" }) {
  const color = tone === "pos" ? "text-pos" : "text-neg"
  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold">{title}</div>
      <Card className="divide-y divide-border/60 border-border bg-card p-0">
        {rows.map(([text, score, name], i) => (
          <div key={i} className="flex items-start gap-3 px-4 py-2.5">
            <span className={`shrink-0 tabular-nums text-sm font-semibold ${color}`}>{fmtScore(score)}</span>
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
  if (!d.available)
    return (
      <Card className="border-border bg-card p-5">
        <div className="text-sm font-semibold text-foreground">{t("sentimentOffTitle")}</div>
        <p className="mt-2 text-sm text-muted-foreground">{t("sentimentOffBody")}</p>
        <pre className="mt-3 overflow-x-auto rounded-md bg-muted px-3 py-2 text-xs text-foreground">
          pip install -r requirements-sentiment.txt
        </pre>
        <p className="mt-3 text-xs text-muted-foreground">{t("sentimentOffNote")}</p>
      </Card>
    )

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
  const userSeriesRaw = [...byUser.entries()].map(([uid, data]) => ({ name: d.user_names?.[uid] ?? uid, data }))
  // each participant keeps their app-wide hue so a line matches them elsewhere
  const userPal = personPalette(userSeriesRaw.map((s) => s.name))
  const userSeries = userSeriesRaw.map((s) => ({ ...s, color: userPal[s.name] }))

  const hourData: [string, number][] = (d.by_hour ?? []).map((h: SentimentPoint) => [String(h.hour), +h.avg.toFixed(3)])
  const wdData: [string, number][] = (d.by_weekday ?? []).map((w: SentimentPoint) => [wd[w.weekday!], +w.avg.toFixed(3)])

  const avgBadge =
    d.avg != null ? (
      <span className={`tabular-nums text-lg font-semibold ${Number(d.avg.toFixed(2)) < 0 ? "text-neg" : "text-pos"}`}>
        {fmtSigned(d.avg)}
      </span>
    ) : undefined

  return (
    <Section title={t("sentiment")} hint={t("sentimentHint")} icon={Smile} action={avgBadge}>
      <div className="space-y-8 pt-1">
        {weeklySeries.length > 0 && (
          <SubSection title={t("sentimentOverTime")}>
            <Card className="border-border bg-card p-3"><Lines series={weeklySeries} zeroLine /></Card>
          </SubSection>
        )}

        {userSeries.length > 1 && (
          <SubSection title={t("sentimentPerUser")}>
            <Card className="border-border bg-card p-3"><Lines series={userSeries} zeroLine /></Card>
          </SubSection>
        )}

        {(hourData.length > 0 || wdData.length > 0) && (
          // secondary cuts — tucked behind a disclosure so the block isn't four
          // charts deep by default
          <Collapsible label={t("sentimentBreakdown")}>
            <div className="grid grid-cols-1 gap-6 pt-2 lg:grid-cols-2">
              {hourData.length > 0 && (
                <SubSection title={t("sentimentByHour")}>
                  <Card className="border-border bg-card p-3"><DivergingBars data={hourData} /></Card>
                </SubSection>
              )}
              {wdData.length > 0 && (
                <SubSection title={t("sentimentByWeekday")}>
                  <Card className="border-border bg-card p-3"><DivergingBars data={wdData} /></Card>
                </SubSection>
              )}
            </div>
          </Collapsible>
        )}

        {((d.positive?.length ?? 0) > 0 || (d.negative?.length ?? 0) > 0) && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {d.positive?.length ? <ExtremeList title={t("mostPositive")} rows={d.positive} tone="pos" /> : null}
            {d.negative?.length ? <ExtremeList title={t("mostNegative")} rows={d.negative} tone="neg" /> : null}
          </div>
        )}
      </div>
    </Section>
  )
}
