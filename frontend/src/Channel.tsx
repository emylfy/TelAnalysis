import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, wordcloudUrl, type Sel } from "@/lib/api"
import { fmtInt } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { BarsH } from "@/components/charts"

export function Channel({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const k = [path, sel.chat, sel.from, sel.to]
  const c = useQuery({ queryKey: ["channel", ...k], queryFn: () => api.channel(path, sel), enabled: !!sel.chat })

  const d = c.data
  if (!d) return null

  return (
    <div className="space-y-8 pt-2">
      <div className="grid grid-cols-2 gap-3 sm:max-w-xs">
        <Card className="gap-1 border-border bg-card px-4 py-3">
          <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{t("channelTokens")}</div>
          <div className="text-2xl font-semibold tabular-nums">{fmtInt(d.token_count)}</div>
        </Card>
      </div>

      {d.has_wordcloud && (
        <section className="space-y-3">
          <h2 className="text-xl font-semibold tracking-tight">{t("wordcloud")}</h2>
          <Card className="flex items-center justify-center border-border bg-card p-3">
            <img
              src={wordcloudUrl(path, sel.chat, true)}
              alt={t("wordcloud")}
              className="max-h-[420px] w-full rounded-md object-contain"
            />
          </Card>
        </section>
      )}

      {d.top_words.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xl font-semibold tracking-tight">{t("topWords")}</h2>
          <Card className="border-border bg-card p-3">
            <BarsH data={d.top_words.slice(0, 25)} color="var(--chart-1)" />
          </Card>
        </section>
      )}
    </div>
  )
}
