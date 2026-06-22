import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, type LatencyStats, type SessionsStats, type Sel } from "@/lib/api"
import { fmtInt, humanizeDuration } from "@/lib/i18n"
import { useState } from "react"
import { Card } from "@/components/ui/card"
import { AreaTimeline, Bars, BarsH, Calendar, HeatLegend, HourOverlap, HourWeekday, MediaPie } from "@/components/charts"
import { TabError, TabLoading } from "@/components/loading"
import { Hint } from "@/components/hint"
import { Collapsible } from "@/components/collapsible"

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
        {title}
        {hint && <Hint text={hint} />}
      </h2>
      {children}
    </section>
  )
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card className="gap-1 border-border bg-card px-4 py-3">
      <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
    </Card>
  )
}

function LatencyBlock({ l }: { l: LatencyStats }) {
  const { t } = useTranslation()
  if (!l.overall_seconds?.length) return null
  const diff = l.qa_median_seconds - l.median_seconds
  const qaDelta =
    Math.abs(diff) < 30
      ? t("qaSame")
      : diff < 0
        ? t("qaFaster", { m: Math.round(-diff / 60) })
        : t("qaSlower", { m: Math.round(diff / 60) })
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Stat label={t("halfFaster")} value={humanizeDuration(l.median_seconds)} />
        <Stat label={t("p90Faster")} value={humanizeDuration(l.p90_seconds)} />
        <Stat label={t("repliesCounted")} value={fmtInt(l.overall_seconds.length)} />
      </div>
      {l.dropped_over_cap > 0 && (
        <p className="text-xs text-muted-foreground">{t("droppedCap", { n: fmtInt(l.dropped_over_cap), h: l.cap_hours })}</p>
      )}
      {l.qa_seconds?.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            {t("qSection")}
            <Hint text={t("qaHint")} />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Stat label={t("halfFaster")} value={humanizeDuration(l.qa_median_seconds)} sub={qaDelta} />
            <Stat label={t("p90Faster")} value={humanizeDuration(l.qa_p90_seconds)} />
            <Stat label={t("qWithAnswer")} value={fmtInt(l.qa_seconds.length)} />
          </div>
        </div>
      )}
    </div>
  )
}

function SessionsBlock({ s }: { s: SessionsStats }) {
  const { t } = useTranslation()
  if (!s.sessions?.length) return null
  const buckets = Object.entries(s.duration_buckets ?? {}) as [string, number][]
  const longest = [...s.sessions]
    .map((se) => ({ ...se, dur: (new Date(se.end).getTime() - new Date(se.start).getTime()) / 1000 }))
    .sort((a, b) => b.dur - a.dur)
    .slice(0, 10)
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Stat label={t("conversations")} value={fmtInt(s.sessions.length)} />
        <Stat label={t("perConvAvg")} value={s.avg_messages.toFixed(1)} />
        {s.longest && <Stat label={t("longestConv")} value={`${fmtInt(s.longest.msg_count)}`} sub={s.longest.start.slice(0, 10)} />}
      </div>
      {buckets.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-semibold">{t("convLength")}</div>
          <Card className="border-border bg-card p-3"><Bars data={buckets} height={220} color="var(--chart-2)" /></Card>
        </div>
      )}
      {longest.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-semibold">{t("longestConvs")}</div>
          <Card className="overflow-hidden border-border bg-card">
            <table className="w-full text-sm">
              <tbody>
                {longest.map((se, i) => (
                  <tr key={i} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2 text-muted-foreground">{se.start.slice(0, 16).replace("T", " ")}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{fmtInt(se.msg_count)} · {t("messages").toLowerCase()}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{humanizeDuration(se.dur)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}
    </div>
  )
}

export function Overview({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const k = [path, sel.chat, sel.from, sel.to]
  const on = !!sel.chat
  const [calMode, setCalMode] = useState<"count" | "binary">("count")
  const [calYear, setCalYear] = useState<string | null>(null)

  const pd = useQuery({ queryKey: ["pd", ...k], queryFn: () => api.perDay(path, sel), enabled: on })
  const hw = useQuery({ queryKey: ["hw", ...k], queryFn: () => api.hourWeekday(path, sel), enabled: on })
  const hbu = useQuery({ queryKey: ["hbu", ...k], queryFn: () => api.hourByUser(path, sel), enabled: on })
  const media = useQuery({ queryKey: ["media", ...k], queryFn: () => api.media(path, sel), enabled: on })
  const emojis = useQuery({ queryKey: ["emojis", ...k], queryFn: () => api.emojis(path, sel), enabled: on })
  const lat = useQuery({ queryKey: ["lat", ...k], queryFn: () => api.latency(path, sel), enabled: on })
  const sess = useQuery({ queryKey: ["sess", ...k], queryFn: () => api.sessions(path, sel), enabled: on })
  const mono = useQuery({ queryKey: ["mono", ...k], queryFn: () => api.monologues(path, sel), enabled: on })

  if (pd.isLoading) return <TabLoading />
  if (pd.isError) return <TabError onRetry={pd.refetch} />

  return (
    <div className="space-y-8 pt-2">
      <Section title={t("howOften")} hint={t("howOftenHint")}>
        {pd.data && <Card className="border-border bg-card p-3"><AreaTimeline data={pd.data.per_day} /></Card>}
        {pd.data && pd.data.per_day.length > 0 && (() => {
          const calYears = [...new Set(pd.data.per_day.map(([d]) => d.slice(0, 4)))].sort()
          const activeYear = calYear && calYears.includes(calYear) ? calYear : calYears[calYears.length - 1]
          const yearDays = pd.data.per_day.filter(([d]) => d.startsWith(activeYear))
          const yearActive = yearDays.filter(([, v]) => v > 0).length
          return (
            <>
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span>{t("calendarMode")}:</span>
                  <div className="flex items-center rounded-md border border-border bg-card p-0.5">
                    {(["count", "binary"] as const).map((m) => (
                      <button
                        key={m}
                        onClick={() => setCalMode(m)}
                        className={`rounded px-2 py-0.5 text-xs transition-colors ${
                          calMode === m ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {m === "count" ? t("calendarCount") : t("calendarBinary")}
                      </button>
                    ))}
                  </div>
                </div>
                {calYears.length > 1 && (
                  <div className="flex items-center gap-2">
                    <span>{t("calendarYear")}:</span>
                    <div className="flex items-center rounded-md border border-border bg-card p-0.5">
                      {calYears.map((y) => (
                        <button
                          key={y}
                          onClick={() => setCalYear(y)}
                          className={`rounded px-2 py-0.5 text-xs transition-colors ${
                            activeYear === y ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                          }`}
                        >
                          {y}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {calMode === "count" && <HeatLegend less={t("calendarLess")} more={t("calendarMore")} />}
              </div>
              <Card className="border-border bg-card p-3">
                <Calendar perDay={pd.data.per_day} binary={calMode === "binary"} year={activeYear} />
              </Card>
              {calMode === "binary" && (
                <p className="text-xs text-muted-foreground">
                  {t("calendarActiveDays", {
                    a: yearActive,
                    t: yearDays.length,
                    p: ((yearActive * 100) / yearDays.length).toFixed(1),
                  })}
                </p>
              )}
            </>
          )
        })()}
      </Section>

      {hw.data && hw.data.grid.some((r) => r.some((v) => v > 0)) && (
        <Section title={t("whenHours")} hint={t("whenHoursHint")}>
          <Card className="border-border bg-card p-3"><HourWeekday grid={hw.data.grid} /></Card>
          {(() => {
            // Surface two insights right under the heatmap. Both are derived from
            // the same grid the chart uses, so no extra fetch.
            const sumH = Array(24).fill(0) as number[]
            let nightTotal = 0
            let grandTotal = 0
            for (const row of hw.data.grid) {
              row.forEach((v, h) => {
                sumH[h] += v
                grandTotal += v
                if (h < 6) nightTotal += v
              })
            }
            const peakH = sumH.indexOf(Math.max(...sumH))
            const nightP = grandTotal ? ((nightTotal * 100) / grandTotal).toFixed(0) : "0"
            return (
              <p className="text-xs text-muted-foreground">
                {t("capPeakHour", { h: String(peakH).padStart(2, "0") })} · {t("capNightShare", { from: "00", to: "06", p: nightP })}
              </p>
            )
          })()}
          {hbu.data && hbu.data.users.length === 2 && (() => {
            const [a, b] = hbu.data.users
            const totA = a.hours.reduce((s, v) => s + v, 0) || 1
            const totB = b.hours.reduce((s, v) => s + v, 0) || 1
            let bestH = 0
            let bestV = -1
            for (let h = 0; h < 24; h++) {
              const v = Math.min(a.hours[h] / totA, b.hours[h] / totB)
              if (v > bestV) { bestV = v; bestH = h }
            }
            return (
              <>
                <h3 className="pt-2 text-base font-semibold tracking-tight">{t("overlapTitle")}</h3>
                <Card className="border-border bg-card p-3">
                  <HourOverlap a={a} b={b} overlapLabel={t("overlapBoth")} />
                </Card>
                <p className="text-xs text-muted-foreground">{t("overlapHint", { h: String(bestH).padStart(2, "0") })}</p>
              </>
            )
          })()}
          {sess.data && <SessionsBlock s={sess.data} />}
        </Section>
      )}

      <Section title={t("whatAbout")} hint={t("whatAboutHint")}>
        {emojis.data && emojis.data.chat_top.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">{t("emojiTop")}</div>
            <p className="-mt-1 text-xs text-muted-foreground">{t("emojiTopHint")}</p>
            <Card className="border-border bg-card p-3">
              {/* horizontal: emoji read clearly as row labels (vertical bars
                  squeezed them into illegible x-axis ticks) */}
              <BarsH data={emojis.data.chat_top.slice(0, 15)} color="#9270CA" />
            </Card>
            {emojis.data.chat_top.length > 20 && (
              <Collapsible label={t("showAll", { n: emojis.data.chat_top.length })}>
                <Card className="max-h-96 overflow-auto border-border bg-card">
                  <table className="w-full text-sm">
                    <tbody>
                      {emojis.data.chat_top.map(([e, c], i) => (
                        <tr key={i} className="border-b border-border/60 last:border-0">
                          <td className="px-4 py-1.5 text-lg">{e}</td>
                          <td className="px-4 py-1.5 text-right tabular-nums text-muted-foreground">{fmtInt(c)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              </Collapsible>
            )}
          </div>
        )}
        {media.data && Object.keys(media.data.by_kind).length > 0 && (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <Card className="border-border bg-card p-3 lg:col-span-2"><MediaPie byKind={media.data.by_kind} /></Card>
            {media.data.voice_count > 0 && (
              <div className="grid grid-cols-1 gap-3">
                <Stat label={t("voiceMessages")} value={fmtInt(media.data.voice_count)} />
                <Stat label={t("voiceTotal")} value={humanizeDuration(media.data.voice_total_seconds)} />
                <Stat label={t("voiceAvg")} value={humanizeDuration(Math.floor(media.data.voice_total_seconds / media.data.voice_count))} />
              </div>
            )}
          </div>
        )}
        {media.data && media.data.top_domains.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">{t("topDomains")}</div>
            <p className="-mt-1 text-xs text-muted-foreground">{t("topDomainsHint")}</p>
            <Card className="border-border bg-card p-3"><BarsH data={media.data.top_domains.slice(0, 15)} /></Card>
          </div>
        )}
      </Section>

      {lat.data && lat.data.overall_seconds.length > 0 && (
        <Section title={t("whoToWhom")} hint={t("whoToWhomHint")}>
          <LatencyBlock l={lat.data} />
        </Section>
      )}

      {mono.data && mono.data.longest.length > 0 && (
        <Section title={t("longestMonologues")} hint={t("longestMonologuesHint")}>
          <Card className="overflow-hidden border-border bg-card">
            <table className="w-full text-sm">
              <tbody>
                {mono.data.longest.slice(0, 8).map((r, i) => (
                  <tr key={i} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2 font-medium">{r.name}</td>
                    <td className="px-4 py-2 tabular-nums text-muted-foreground">{fmtInt(r.msg_count)}</td>
                    <td className="px-4 py-2 text-muted-foreground">{r.start.slice(0, 16).replace("T", " ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </Section>
      )}
    </div>
  )
}
