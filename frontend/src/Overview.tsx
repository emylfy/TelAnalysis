import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { Activity, Clock, MessageSquareText, Mic, Sparkles, Timer } from "lucide-react"

import { api, type LatencyStats, type SessionsStats, type Sel } from "@/lib/api"
import { fmtInt, humanizeDuration } from "@/lib/i18n"
import { useState } from "react"
import { Card } from "@/components/ui/card"
import { AreaTimeline, BarsH, Calendar, HeatLegend, HourOverlap, HourWeekday, MediaPie } from "@/components/charts"
import { TabError, TabLoading } from "@/components/loading"
import { Hint } from "@/components/hint"
import { Section } from "@/components/section"
import { RankTable } from "@/components/rank-table"
import { Collapsible } from "@/components/collapsible"
import { Stat } from "@/components/stat"

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
      {/* needs a few answered questions: at ≤2 the median equals p90 and the two
          stats read as the same number twice */}
      {l.qa_seconds?.length > 2 && (
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
  const longest = [...s.sessions]
    .map((se) => ({ ...se, dur: (new Date(se.end).getTime() - new Date(se.start).getTime()) / 1000 }))
    .sort((a, b) => b.dur - a.dur)
    .slice(0, 10)
  // total wall-clock time spent in conversations (+ the per-conversation average).
  // Replaces the median tile: median only restated "typical size", which the
  // average beside it already gives — this adds the time dimension the
  // message-count tiles never showed.
  const totalDur = s.sessions.reduce((acc, se) => acc + (new Date(se.end).getTime() - new Date(se.start).getTime()) / 1000, 0)
  const avgDur = totalDur / s.sessions.length
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label={t("conversations")} value={fmtInt(s.sessions.length)} />
        <Stat label={t("perConvAvg")} value={s.avg_messages.toFixed(1)} />
        <Stat label={t("convTotalTime")} value={humanizeDuration(totalDur)} sub={`${t("avgShort")} ${humanizeDuration(avgDur)}`} />
        {/* "most messages" (by count) — the longest-by-duration list below ranks
            differently, so this card no longer calls itself "longest" */}
        {s.longest && <Stat label={t("mostMessagesConv")} value={`${fmtInt(s.longest.msg_count)}`} sub={s.longest.start.slice(0, 10)} />}
      </div>
      {longest.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-semibold">{t("longestConvs")}</div>
          {/* ranked by duration (the "longest" metric) — so the bar, the figure
              and the rank all agree; message count rides along on the sub-line */}
          <RankTable
            color="var(--chart-2)"
            rows={longest.map((se) => ({
              label: se.start.slice(0, 16).replace("T", " "),
              sub: `${fmtInt(se.msg_count)} ${t("messages").toLowerCase()}`,
              value: Math.round(se.dur),
              valueText: humanizeDuration(se.dur),
            }))}
          />
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
  // shares its key with the App shell (dedup) — used only for the voice share %
  const kpis = useQuery({ queryKey: ["kpis", ...k], queryFn: () => api.kpis(path, sel), enabled: on })
  const emojis = useQuery({ queryKey: ["emojis", ...k], queryFn: () => api.emojis(path, sel), enabled: on })
  const lat = useQuery({ queryKey: ["lat", ...k], queryFn: () => api.latency(path, sel), enabled: on })
  const sess = useQuery({ queryKey: ["sess", ...k], queryFn: () => api.sessions(path, sel), enabled: on })
  const mono = useQuery({ queryKey: ["mono", ...k], queryFn: () => api.monologues(path, sel), enabled: on })

  if (pd.isLoading) return <TabLoading />
  if (pd.isError) return <TabError onRetry={pd.refetch} />

  return (
    <div className="space-y-8 pt-2">
      <Section title={t("howOften")} hint={t("howOftenHint")} icon={Activity}>
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
                {/* keep cells at full size on narrow screens — scroll sideways
                    instead of squishing the year grid into an unreadable strip */}
                <div className="overflow-x-auto">
                  <div className="min-w-[680px]">
                    <Calendar perDay={pd.data.per_day} binary={calMode === "binary"} year={activeYear} />
                  </div>
                </div>
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
        <Section title={t("whenHours")} hint={t("whenHoursHint")} icon={Clock}>
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

      <Section title={t("whatAbout")} hint={t("whatAboutHint")} icon={Sparkles}>
        {emojis.data && emojis.data.chat_top.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">{t("emojiTop")}</div>
            <p className="-mt-1 text-xs text-muted-foreground">{t("emojiTopHint")}</p>
            <Card className="border-border bg-card p-3">
              {/* horizontal: emoji read clearly as row labels (vertical bars
                  squeezed them into illegible x-axis ticks). Bigger glyphs +
                  taller rows so the emoji themselves are legible, not tiny. */}
              <BarsH data={emojis.data.chat_top.slice(0, 15)} color="var(--chart-4)" labelSize={20} rowHeight={32} />
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
            {media.data.voice_count > 1 && (() => {
              // need >1: a single voice note makes «суммарно» == «в среднем»,
              // two identical numbers in one card.
              // one compact card (not three stacked) so it doesn't read as
              // "tacked on" beside the pie; share added when KPIs are loaded.
              const v = media.data
              const total = kpis.data?.total_messages ?? 0
              const cells: [string, string][] = [
                [fmtInt(v.voice_count), t("voiceMessages")],
                [humanizeDuration(v.voice_total_seconds), t("voiceTotal")],
                [humanizeDuration(Math.floor(v.voice_total_seconds / v.voice_count)), t("voiceAvg")],
              ]
              if (total > 0) cells.push([`${((v.voice_count * 100) / total).toFixed(1)}%`, t("voiceShare")])
              return (
                <Card className="flex flex-col justify-center gap-4 border-border bg-card p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold">
                    <Mic className="size-4 text-muted-foreground" /> {t("voice")}
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-4">
                    {cells.map(([value, label]) => (
                      <div key={label}>
                        <div className="text-xl font-semibold tabular-nums">{value}</div>
                        <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</div>
                      </div>
                    ))}
                  </div>
                </Card>
              )
            })()}
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
        <Section title={t("whoToWhom")} hint={t("whoToWhomHint")} icon={Timer}>
          <LatencyBlock l={lat.data} />
        </Section>
      )}

      {mono.data && mono.data.longest.length > 0 && (
        <Section title={t("longestMonologues")} hint={t("longestMonologuesHint")} icon={MessageSquareText}>
          <RankTable
            color="var(--chart-1)"
            unit={t("messages").toLowerCase()}
            rows={mono.data.longest.slice(0, 8).map((r) => ({
              label: r.name,
              sub: r.start.slice(0, 16).replace("T", " "),
              value: r.msg_count,
            }))}
          />
        </Section>
      )}
    </div>
  )
}
