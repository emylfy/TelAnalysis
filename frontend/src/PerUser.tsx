import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, type Sel } from "@/lib/api"
import { fmtInt, timeBucketLabel } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Bars, BarsH } from "@/components/charts"

const TIME_ORDER = ["night", "morning", "day", "evening"]
const LEN_ORDER = ["<30", "30-100", "100-300", "300+"]

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card className="gap-1 border-border bg-card px-4 py-3">
      <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
    </Card>
  )
}

function pct(x: number): string {
  return `${Math.round(x * 100)}%`
}

export function PerUser({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const k = [path, sel.chat, sel.from, sel.to]
  const on = !!sel.chat

  const speaking = useQuery({ queryKey: ["speaking", ...k], queryFn: () => api.speaking(path, sel), enabled: on })
  const words = useQuery({ queryKey: ["words", ...k], queryFn: () => api.words(path, sel), enabled: on })
  const phrases = useQuery({ queryKey: ["pup", ...k], queryFn: () => api.perUserPhrases(path, sel), enabled: on })

  const styles = speaking.data
  const [uid, setUid] = useState<string | undefined>(undefined)

  // default to the most active participant once data arrives
  const ordered = styles
    ? Object.values(styles).sort((a, b) => b.msg_count - a.msg_count)
    : []
  useEffect(() => {
    if (ordered.length && (!uid || !styles?.[uid])) setUid(ordered[0].user_id)
  }, [styles]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!styles || !ordered.length) return null
  const s = (uid && styles[uid]) || ordered[0]

  const tod: [string, number][] = TIME_ORDER.filter((b) => s.time_of_day[b] != null).map((b) => [
    timeBucketLabel(b),
    s.time_of_day[b] ?? 0,
  ])
  const len: [string, number][] = LEN_ORDER.filter((b) => s.length_buckets[b] != null).map((b) => [
    b,
    s.length_buckets[b] ?? 0,
  ])
  const userWords = words.data?.users.find((u) => u.user_id === s.user_id)
  const userPhrases = phrases.data?.[s.user_id] ?? []

  return (
    <div className="space-y-8 pt-2">
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">{t("pickUser")}</span>
        <Select value={s.user_id} onValueChange={(v) => v && setUid(v)}>
          <SelectTrigger className="w-[280px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ordered.map((u) => (
              <SelectItem key={u.user_id} value={u.user_id}>
                {u.name} · {fmtInt(u.msg_count)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Stat label={t("messages")} value={fmtInt(s.msg_count)} />
        <Stat label={t("avgWords")} value={s.avg_words.toFixed(1)} />
        <Stat label={t("questionShare")} value={pct(s.question_ratio)} />
        <Stat label={t("exclShare")} value={pct(s.exclamation_ratio)} />
        <Stat label={t("capsShare")} value={pct(s.caps_ratio)} />
        <Stat label={t("replyShare")} value={pct(s.msg_count ? s.reply_count / s.msg_count : 0)} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {tod.some((b) => b[1] > 0) && (
          <section className="space-y-3">
            <h2 className="text-lg font-semibold tracking-tight">{t("timeOfDay")}</h2>
            <Card className="border-border bg-card p-3">
              <Bars data={tod} height={240} color="var(--chart-2)" />
            </Card>
          </section>
        )}
        {len.some((b) => b[1] > 0) && (
          <section className="space-y-3">
            <h2 className="text-lg font-semibold tracking-tight">{t("msgLength")}</h2>
            <Card className="border-border bg-card p-3">
              <Bars data={len} height={240} color="var(--chart-3)" />
            </Card>
          </section>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {userWords && userWords.top_words.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-lg font-semibold tracking-tight">{t("topWords")}</h2>
            <Card className="border-border bg-card p-3">
              <BarsH data={userWords.top_words.slice(0, 15)} color="var(--chart-1)" />
            </Card>
          </section>
        )}
        {userPhrases.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-lg font-semibold tracking-tight">{t("characteristicPhrases")}</h2>
            <Card className="border-border bg-card p-3">
              <BarsH data={userPhrases.slice(0, 15)} color="var(--chart-4)" />
            </Card>
          </section>
        )}
      </div>
    </div>
  )
}
