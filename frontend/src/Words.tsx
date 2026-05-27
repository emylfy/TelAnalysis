import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, wordcloudUrl, type Sel } from "@/lib/api"
import { fmtInt } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { BarsH } from "@/components/charts"

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
        {hint && <p className="mt-0.5 text-sm text-muted-foreground">{hint}</p>}
      </div>
      {children}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card className="gap-1 border-border bg-card px-4 py-3">
      <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
    </Card>
  )
}

export function Words({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const [n, setN] = useState<2 | 3>(2)
  const k = [path, sel.chat, sel.from, sel.to]
  const on = !!sel.chat

  const words = useQuery({ queryKey: ["words", ...k], queryFn: () => api.words(path, sel), enabled: on })
  const phrases = useQuery({ queryKey: ["phrases", ...k, n], queryFn: () => api.phrases(path, sel, n), enabled: on })

  const w = words.data
  if (!w) return null

  return (
    <div className="space-y-8 pt-2">
      <Section title={t("wordcloud")}>
        <Card className="flex items-center justify-center border-border bg-card p-3">
          <img
            src={wordcloudUrl(path, sel.chat)}
            alt={t("wordcloud")}
            className="max-h-[420px] w-full rounded-md object-contain"
          />
        </Card>
      </Section>

      {w.chat_top_words.length > 0 && (
        <Section title={t("topWords")}>
          <Card className="border-border bg-card p-3">
            <BarsH data={w.chat_top_words.slice(0, 25)} color="var(--chart-1)" />
          </Card>
        </Section>
      )}

      <Section title={t("phrases")}>
        <div className="flex items-center rounded-lg border border-border bg-card p-0.5 w-fit">
          {([2, 3] as const).map((v) => (
            <button
              key={v}
              onClick={() => setN(v)}
              className={`rounded-md px-3 py-1 text-sm transition-colors ${
                n === v ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {v === 2 ? t("bigrams") : t("trigrams")}
            </button>
          ))}
        </div>
        {phrases.data && phrases.data.phrases.length > 0 ? (
          <Card className="border-border bg-card p-3">
            <BarsH data={phrases.data.phrases.slice(0, 20)} color="var(--chart-4)" />
          </Card>
        ) : (
          <div className="text-sm text-muted-foreground">{t("noData")}</div>
        )}
      </Section>

      {w.users.length > 0 && (
        <Section title={t("vocabulary")} hint={t("vocabHint")}>
          <Card className="overflow-hidden border-border bg-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 font-semibold">{t("user")}</th>
                  <th className="px-4 py-2 text-right font-semibold">{t("totalTokens")}</th>
                  <th className="px-4 py-2 text-right font-semibold">{t("uniqueTokens")}</th>
                  <th className="px-4 py-2 text-right font-semibold">{t("mtld")}</th>
                </tr>
              </thead>
              <tbody>
                {w.users.map((u) => (
                  <tr key={u.user_id} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2 font-medium">{u.name}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(u.total_tokens)}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(u.unique_tokens)}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{u.mtld.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </Section>
      )}

      {(w.emails.length > 0 || w.phones.length > 0) && (
        <Section title={t("contacts")}>
          <div className="grid grid-cols-2 gap-3 sm:max-w-md">
            <Stat label={t("emailsN")} value={fmtInt(w.emails.length)} />
            <Stat label={t("phonesN")} value={fmtInt(w.phones.length)} />
          </div>
        </Section>
      )}

      {!w.sentiment_available && <p className="text-sm text-muted-foreground">{t("sentimentOff")}</p>}
    </div>
  )
}
