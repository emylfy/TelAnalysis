import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, type Sel } from "@/lib/api"
import { dayWord, fmtInt, personaForLength, personaForTimeOfDay, timeBucketLabel } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Bars, BarsH, Box, HourWeekday, Lines, Radar } from "@/components/charts"
import { TabError, TabLoading } from "@/components/loading"
import { ExtremeList } from "@/Sentiment"

const TIME_ORDER = ["night", "morning", "day", "evening"]
const LEN_ORDER = ["<30", "30-100", "100-300", "300+"]
const LAT_BUCKETS: [string, number][] = [
  ["<1m", 60],
  ["1–5m", 300],
  ["5–15m", 900],
  ["15–60m", 3600],
  ["1–6h", 21600],
  ["6–24h", 86400],
]

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card className="gap-1 border-border bg-card px-4 py-3">
      <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
    </Card>
  )
}

function H3({ children }: { children: React.ReactNode }) {
  return <h3 className="text-lg font-semibold tracking-tight">{children}</h3>
}

const pct = (x: number) => `${Math.round(x * 100)}%`
const median = (xs: number[]) => {
  if (!xs.length) return 0
  const s = [...xs].sort((a, b) => a - b)
  return s[Math.floor(s.length / 2)]
}
const hhmm = (min: number) => `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(Math.floor(min % 60)).padStart(2, "0")}`

export function PerUser({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const k = [path, sel.chat, sel.from, sel.to]
  const on = !!sel.chat

  const speaking = useQuery({ queryKey: ["speaking", ...k], queryFn: () => api.speaking(path, sel), enabled: on })
  const words = useQuery({ queryKey: ["words", ...k], queryFn: () => api.words(path, sel), enabled: on })
  const phrases = useQuery({ queryKey: ["pup", ...k], queryFn: () => api.perUserPhrases(path, sel), enabled: on })
  const emojisQ = useQuery({ queryKey: ["emojis", ...k], queryFn: () => api.emojis(path, sel), enabled: on })
  const stickersQ = useQuery({ queryKey: ["stickers", ...k], queryFn: () => api.stickers(path, sel), enabled: on })
  const latencyQ = useQuery({ queryKey: ["lat", ...k], queryFn: () => api.latency(path, sel), enabled: on })
  const recipQ = useQuery({ queryKey: ["recip", ...k], queryFn: () => api.reciprocity(path, sel), enabled: on })
  const initQ = useQuery({ queryKey: ["init", ...k], queryFn: () => api.initiators(path, sel), enabled: on })
  const fwdQ = useQuery({ queryKey: ["fwd", ...k], queryFn: () => api.forwards(path, sel), enabled: on })
  const matQ = useQuery({ queryKey: ["mat", ...k], queryFn: () => api.mat(path, sel), enabled: on })
  const distQ = useQuery({ queryKey: ["dist", ...k], queryFn: () => api.distinguishing(path, sel), enabled: on })

  const styles = speaking.data
  const [uid, setUid] = useState<string | undefined>(undefined)
  const ordered = styles ? Object.values(styles).sort((a, b) => b.msg_count - a.msg_count) : []
  // Active user is derived, not stored in an effect: fall back to the most
  // active participant until one is picked, and after a chat switch where the
  // previously-selected uid no longer exists.
  const activeUid = (uid && styles?.[uid]?.user_id) || ordered[0]?.user_id

  // per-user queries (refetch on user change)
  const pdU = useQuery({ queryKey: ["pdU", ...k, activeUid], queryFn: () => api.perDay(path, sel, activeUid), enabled: on && !!activeUid })
  const hwU = useQuery({ queryKey: ["hwU", ...k, activeUid], queryFn: () => api.hourWeekday(path, sel, activeUid), enabled: on && !!activeUid })
  const streakQ = useQuery({ queryKey: ["streak", ...k, activeUid], queryFn: () => api.streaks(path, sel, activeUid), enabled: on && !!activeUid })
  const sentU = useQuery({ queryKey: ["sentU", ...k, activeUid], queryFn: () => api.sentiment(path, sel, 8, activeUid), enabled: on && !!activeUid })

  if (speaking.isLoading) return <TabLoading />
  if (speaking.isError) return <TabError onRetry={speaking.refetch} />
  if (!styles || !ordered.length) return null
  const s = (activeUid && styles[activeUid]) || ordered[0]
  const id = s.user_id
  const total = ordered.reduce((a, u) => a + u.msg_count, 0)
  const twoUsers = ordered.length === 2

  const tod: [string, number][] = TIME_ORDER.filter((b) => s.time_of_day[b] != null).map((b) => [timeBucketLabel(b), s.time_of_day[b] ?? 0])
  const len: [string, number][] = LEN_ORDER.filter((b) => s.length_buckets[b] != null).map((b) => [b, s.length_buckets[b] ?? 0])
  const userWords = words.data?.users.find((u) => u.user_id === id)
  const userPhrases = phrases.data?.[id] ?? []
  const userEmojis = emojisQ.data?.per_user?.[id] ?? []
  const userStickers = stickersQ.data?.[id]?.top_emojis ?? []
  const userLat = latencyQ.data?.per_user_seconds?.[id] ?? []

  // tone radar across all users
  const radarSeries = ordered.map((u) => ({
    name: u.name,
    highlight: u.user_id === id,
    values: [
      Math.round(u.question_ratio * 100),
      Math.round(u.exclamation_ratio * 100),
      Math.round(u.caps_ratio * 100),
      Math.round(u.msg_count ? (u.reply_count / u.msg_count) * 100 : 0),
    ],
  }))
  // auto-scale axes to the data so the polygon fills the chart
  const radarMax = Math.max(10, Math.ceil(Math.max(...radarSeries.flatMap((r) => r.values), 0) / 10) * 10)
  const indicators = [t("axisQuestion"), t("axisExcl"), t("axisCaps"), t("axisReply")].map((name) => ({ name, max: radarMax }))

  // wakeup
  const wakeMin = median(s.first_msg_minutes ?? [])
  const wakeGroups = ordered.filter((u) => (u.first_msg_minutes?.length ?? 0) > 3).map((u) => ({ name: u.name, values: u.first_msg_minutes }))

  // latency histogram (cumulative bucket match)
  const latData: [string, number][] = (() => {
    if (!userLat.length) return []
    const counts = new Array(LAT_BUCKETS.length + 1).fill(0)
    for (const sec of userLat) {
      const idx = LAT_BUCKETS.findIndex(([, cap]) => sec < cap)
      counts[idx === -1 ? LAT_BUCKETS.length : idx]++
    }
    const labels = [...LAT_BUCKETS.map((b) => b[0]), ">24h"]
    return labels.map((l, i) => [l, counts[i]] as [string, number]).filter((d) => d[1] > 0)
  })()

  // reciprocity: direction where the selected user is the responder
  const recip = recipQ.data
  const dir =
    recip?.available && recip
      ? [recip.a_to_b, recip.b_to_a].find((d) => d && String(d.responder_id) === String(id)) ?? null
      : null

  const initRow = initQ.data?.rows.find((r) => String(r.user_id) === String(id))
  const fwd = fwdQ.data?.per_user?.[id]
  const matRows = matQ.data ? Object.values(matQ.data.per_user).sort((a, b) => b.mat_hits / Math.max(1, b.total_messages) - a.mat_hits / Math.max(1, a.total_messages)) : []
  const dist = distQ.data

  return (
    <div className="space-y-8 pt-2">
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">{t("pickUser")}</span>
        <Select value={id} onValueChange={(v) => v && setUid(v)}>
          <SelectTrigger className="w-[280px]">
            {/* base-ui Select.Value shows the raw value by default — map to name */}
            <SelectValue>
              {(v: string) => {
                const u = ordered.find((x) => x.user_id === v)
                return u ? `${u.name} · ${fmtInt(u.msg_count)}` : v
              }}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {ordered.map((u) => (
              <SelectItem key={u.user_id} value={u.user_id}>{u.name} · {fmtInt(u.msg_count)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Stat label={t("messages")} value={fmtInt(s.msg_count)} />
        <Stat label={t("shareOfChat")} value={pct(total ? s.msg_count / total : 0)} />
        <Stat
          label={t("msgLengthMedian")}
          value={`${fmtInt(s.median_chars)} ${t("charsShort")}`}
          sub={`avg ${s.avg_chars.toFixed(0)} · max ${fmtInt(s.longest_chars)}`}
        />
        <Stat label={t("avgWords")} value={s.avg_words.toFixed(1)} />
        <Stat label={t("questionShare")} value={pct(s.question_ratio)} />
        <Stat label={t("replyShare")} value={pct(s.msg_count ? s.reply_count / s.msg_count : 0)} />
      </div>

      {ordered.length >= 2 && (
        <section className="space-y-3">
          <H3>{t("toneRadar")}</H3>
          <Card className="border-border bg-card p-3"><Radar indicators={indicators} series={radarSeries} /></Card>
        </section>
      )}

      {(s.first_msg_minutes?.length ?? 0) > 0 && (
        <section className="space-y-3">
          <H3>{t("wakeup")}</H3>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <Stat label={t("wakeupMedian")} value={hhmm(wakeMin)} />
            {wakeGroups.length >= 2 && (
              <Card className="border-border bg-card p-3 lg:col-span-2"><Box groups={wakeGroups} asTime /></Card>
            )}
          </div>
          {(() => {
            const others = ordered
              .filter((u) => u.user_id !== id && (u.first_msg_minutes?.length ?? 0) > 0)
              .map((u) => ({ name: u.name, hhmm: hhmm(median(u.first_msg_minutes)) }))
            if (!others.length) return null
            return (
              <p className="text-xs text-muted-foreground">
                {t("wakeupOthers")} {others.map((o) => `${o.name} — ${o.hhmm}`).join(", ")}
              </p>
            )
          })()}
        </section>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {pdU.data && pdU.data.per_day.length > 0 && (
          <section className="space-y-3">
            <H3>{t("dailyActivity")}</H3>
            <Card className="border-border bg-card p-3">
              <Lines series={[{ name: s.name, data: pdU.data.per_day }]} />
            </Card>
          </section>
        )}
        {hwU.data && hwU.data.grid.some((r) => r.some((v) => v > 0)) && (
          <section className="space-y-3">
            <H3>{t("hourWeekdayUser")}</H3>
            <Card className="border-border bg-card p-3"><HourWeekday grid={hwU.data.grid} /></Card>
          </section>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {tod.some((b) => b[1] > 0) && (
          <section className="space-y-3">
            <H3>{t("timeOfDay")}</H3>
            <p className="-mt-2 text-sm text-muted-foreground">{personaForTimeOfDay(s.time_of_day)}</p>
            <Card className="border-border bg-card p-3"><Bars data={tod} height={240} color="var(--chart-2)" /></Card>
          </section>
        )}
        {len.some((b) => b[1] > 0) && (
          <section className="space-y-3">
            <H3>{t("msgLength")}</H3>
            <p className="-mt-2 text-sm text-muted-foreground">{personaForLength(s.length_buckets)}</p>
            <Card className="border-border bg-card p-3"><Bars data={len} height={240} color="var(--chart-3)" /></Card>
          </section>
        )}
      </div>

      {dir && (
        <section className="space-y-3">
          <H3>{t("reciprocity")}</H3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label={t("medianReply")} value={`${Math.round(dir.median_seconds / 60)}m`} />
            <Stat label={t("within5")} value={pct(dir.within_5m)} />
            <Stat label={t("within30")} value={pct(dir.within_30m)} />
            <Stat label={t("within60")} value={pct(dir.within_60m)} />
          </div>
          {(() => {
            const other = recip?.a_to_b === dir ? recip?.b_to_a : recip?.a_to_b
            if (!other) return null
            const delta = (dir.within_5m - other.within_5m) * 100
            return (
              <p className="text-xs text-muted-foreground">
                {t("reciprocityReverse", {
                  a: other.initiator_name,
                  b: other.responder_name,
                  m: `${Math.round(other.median_seconds / 60)}m`,
                  p: (other.within_5m * 100).toFixed(1),
                  d: (delta >= 0 ? "+" : "") + delta.toFixed(1),
                })}
              </p>
            )
          })()}
        </section>
      )}

      {streakQ.data && streakQ.data.total_active_days > 0 && (
        <section className="space-y-3">
          <H3>{t("streaks")}</H3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <Stat label={t("longestStreak")} value={`${fmtInt(streakQ.data.longest_streak_days)} ${dayWord(streakQ.data.longest_streak_days)}`} sub={streakQ.data.longest_streak_start ?? undefined} />
            <Stat label={t("currentStreak")} value={`${fmtInt(streakQ.data.current_streak_days)} ${dayWord(streakQ.data.current_streak_days)}`} />
            <Stat label={t("activeDays")} value={fmtInt(streakQ.data.total_active_days)} />
          </div>
          {streakQ.data.longest_silences.length > 0 && (
            <Card className="overflow-hidden border-border bg-card">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="px-4 py-2 font-semibold">{t("longestSilences")}</th>
                    <th className="px-4 py-2 text-right font-semibold">{t("days")}</th>
                  </tr>
                </thead>
                <tbody>
                  {streakQ.data.longest_silences.slice(0, 5).map(([from, to, d], i) => (
                    <tr key={i} className="border-b border-border/60 last:border-0">
                      <td className="px-4 py-2 text-muted-foreground">{from.slice(0, 10)} → {to.slice(0, 10)}</td>
                      <td className="px-4 py-2 text-right tabular-nums">{fmtInt(d)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </section>
      )}

      {initRow && (
        <section className="space-y-3">
          <H3>{t("initiator")}</H3>
          <div className="grid grid-cols-2 gap-3 sm:max-w-md">
            <Stat label={t("initiations")} value={fmtInt(initRow.initiations)} />
            <Stat label={t("initiatorShare")} value={pct(initRow.share)} />
          </div>
          {initQ.data && initQ.data.total_initiations < 30 && (
            <p className="text-xs text-muted-foreground">
              {t("initiatorsLowN", { n: initQ.data.total_initiations })}
            </p>
          )}
        </section>
      )}

      {fwd && fwd.forwarded_count > 0 && (
        <section className="space-y-3">
          <H3>{t("forwards")}</H3>
          <div className="grid grid-cols-1 gap-3 sm:max-w-xs">
            <Stat label={t("forwardShare")} value={pct(fwd.total_messages ? fwd.forwarded_count / fwd.total_messages : 0)} sub={`${fmtInt(fwd.forwarded_count)} / ${fmtInt(fwd.total_messages)}`} />
          </div>
          {fwd.top_sources.length > 0 && (
            <Card className="border-border bg-card p-3"><BarsH data={fwd.top_sources} color="var(--chart-5)" /></Card>
          )}
        </section>
      )}

      {latData.length > 0 && (
        <section className="space-y-3">
          <H3>{t("latencyHist")}</H3>
          <div className="text-sm text-muted-foreground">
            {t("medianReply")}: {Math.round(median(userLat) / 60)}m · {fmtInt(userLat.length)}
          </div>
          <Card className="border-border bg-card p-3"><Bars data={latData} height={240} color="var(--chart-1)" /></Card>
        </section>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {userWords && userWords.top_words.length > 0 && (
          <section className="space-y-3">
            <H3>{t("topWords")}</H3>
            <Card className="border-border bg-card p-3"><BarsH data={userWords.top_words.slice(0, 15)} color="var(--chart-1)" /></Card>
          </section>
        )}
        {userPhrases.length > 0 && (
          <section className="space-y-3">
            <H3>{t("characteristicPhrases")}</H3>
            <Card className="border-border bg-card p-3"><BarsH data={userPhrases.slice(0, 15)} color="var(--chart-4)" /></Card>
          </section>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {userEmojis.length > 0 && (
          <section className="space-y-3">
            <H3>{t("emojisOfUser")}</H3>
            <Card className="border-border bg-card p-3"><BarsH data={userEmojis.slice(0, 12)} color="#9270CA" /></Card>
          </section>
        )}
        {userStickers.length > 0 && (
          <section className="space-y-3">
            <H3>{t("stickersOfUser")}</H3>
            <Card className="border-border bg-card p-3"><BarsH data={userStickers.slice(0, 12)} color="#5AD8F7" /></Card>
          </section>
        )}
      </div>

      {userWords && userWords.total_tokens > 0 && (
        <section className="space-y-3">
          <H3>{t("vocabUser")}</H3>
          <div className="grid grid-cols-3 gap-3 sm:max-w-lg">
            <Stat label={t("totalTokens")} value={fmtInt(userWords.total_tokens)} />
            <Stat label={t("uniqueTokens")} value={fmtInt(userWords.unique_tokens)} />
            <Stat label={t("mtld")} value={userWords.mtld.toFixed(1)} />
          </div>
        </section>
      )}

      {sentU.data?.available && ((sentU.data.positive?.length ?? 0) > 0 || (sentU.data.negative?.length ?? 0) > 0) && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {sentU.data.positive?.length ? <ExtremeList title={t("mostPositive")} rows={sentU.data.positive} tone="pos" /> : null}
          {sentU.data.negative?.length ? <ExtremeList title={t("mostNegative")} rows={sentU.data.negative} tone="neg" /> : null}
        </div>
      )}

      {twoUsers && dist?.available && ((dist.a?.length ?? 0) > 0 || (dist.b?.length ?? 0) > 0) && (
        <section className="space-y-3">
          <H3>{t("distinguishing")}</H3>
          <p className="-mt-1 text-sm text-muted-foreground">{t("distinguishingHelp")}</p>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {[{ name: dist.a_name, rows: dist.a }, { name: dist.b_name, rows: dist.b }].map((side, i) => (
              <Card key={i} className="overflow-hidden border-border bg-card">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="px-4 py-2 font-semibold">{t("onlyUser")} {side.name}</th>
                      <th className="px-4 py-2 text-right font-semibold">{t("logOdds")}</th>
                      <th className="px-4 py-2 text-right font-semibold">{t("count")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(side.rows ?? []).slice(0, 12).map(([w, lo, c], j) => (
                      <tr key={j} className="border-b border-border/60 last:border-0">
                        <td className="px-4 py-2 font-medium">{w}</td>
                        <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{lo.toFixed(2)}</td>
                        <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(c)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            ))}
          </div>
        </section>
      )}

      {matRows.some((m) => m.mat_hits > 0) && (
        <section className="space-y-3">
          <H3>{t("matTitle")}</H3>
          <p className="-mt-1 text-sm text-muted-foreground">{t("matHelp")}</p>
          <Card className="overflow-hidden border-border bg-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 font-semibold">{t("user")}</th>
                  <th className="px-4 py-2 text-right font-semibold">{t("matMsgs")}</th>
                  <th className="px-4 py-2 text-right font-semibold">{t("matWith")}</th>
                  <th className="px-4 py-2 text-right font-semibold">{t("matHits")}</th>
                  <th className="px-4 py-2 text-right font-semibold">{t("matPer100")}</th>
                </tr>
              </thead>
              <tbody>
                {matRows.map((m) => (
                  <tr key={m.user_id} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2 font-medium">{m.name}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(m.total_messages)}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(m.mat_messages)}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(m.mat_hits)}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{(m.total_messages ? (m.mat_hits * 100) / m.total_messages : 0).toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </section>
      )}
    </div>
  )
}
