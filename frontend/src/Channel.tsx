import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { Cloud, Type } from "lucide-react"

import { api, wordcloudUrl, type Sel } from "@/lib/api"
import { fmtInt } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { BarsH } from "@/components/charts"
import { TabError, TabLoading } from "@/components/loading"
import { Section } from "@/components/section"
import { Collapsible } from "@/components/collapsible"

export function Channel({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const k = [path, sel.chat, sel.from, sel.to]
  const c = useQuery({ queryKey: ["channel", ...k], queryFn: () => api.channel(path, sel), enabled: !!sel.chat })

  const d = c.data
  if (c.isLoading) return <TabLoading />
  if (c.isError) return <TabError onRetry={c.refetch} />
  if (!d) return null

  return (
    <div className="space-y-8 pt-2">
      <div className="grid grid-cols-2 gap-3 sm:max-w-sm">
        <Card className="gap-1 border-border bg-card px-4 py-3">
          <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{t("channelTokens")}</div>
          <div className="text-2xl font-semibold tabular-nums">{fmtInt(d.token_count)}</div>
        </Card>
        <Card className="gap-1 border-border bg-card px-4 py-3">
          <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{t("channelTopCount")}</div>
          <div className="text-2xl font-semibold tabular-nums">{fmtInt(d.top_words.length)}</div>
        </Card>
      </div>

      {d.has_wordcloud && (
        <Section title={t("wordcloud")} hint={t("wordcloudHint")} icon={Cloud}>
          <Card className="flex items-center justify-center border-border bg-card p-3">
            <img
              src={wordcloudUrl(path, sel.chat, true)}
              alt={t("wordcloud")}
              className="max-h-[420px] w-full rounded-md object-contain"
            />
          </Card>
        </Section>
      )}

      {d.top_words.length > 0 && (
        <Section title={t("topWords")} hint={t("topWordsHint")} icon={Type}>
          <Card className="border-border bg-card p-3">
            <BarsH data={d.top_words.slice(0, 50)} color="var(--chart-1)" />
          </Card>
          {d.top_words.length > 50 && (
            <Collapsible label={t("showAll", { n: d.top_words.length })}>
              <Card className="max-h-96 overflow-auto border-border bg-card">
                <table className="w-full text-sm">
                  <tbody>
                    {d.top_words.map(([w, c], i) => (
                      <tr key={i} className="border-b border-border/60 last:border-0">
                        <td className="px-4 py-1.5">{w}</td>
                        <td className="px-4 py-1.5 text-right tabular-nums text-muted-foreground">{fmtInt(c)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            </Collapsible>
          )}
        </Section>
      )}
    </div>
  )
}
