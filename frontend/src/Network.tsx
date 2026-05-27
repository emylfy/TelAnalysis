import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"

import { api, type Sel } from "@/lib/api"
import { fmtInt } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { Network as NetworkChart } from "@/components/charts"

export function Network({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const k = [path, sel.chat, sel.from, sel.to]
  const g = useQuery({ queryKey: ["graph", ...k], queryFn: () => api.graph(path, sel), enabled: !!sel.chat })

  const d = g.data
  if (!d) return null
  if (d.nodes.length < 2) return <div className="py-16 text-center text-sm text-muted-foreground">{t("noData")}</div>

  return (
    <div className="space-y-8 pt-2">
      <section className="space-y-3">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">{t("interactions")}</h2>
          <p className="mt-0.5 text-sm text-muted-foreground">{t("networkDesc")}</p>
        </div>
        <Card className="border-border bg-card p-3">
          <NetworkChart nodes={d.nodes} edges={d.edges} />
        </Card>
      </section>

      {d.summary.length > 0 && (
        <Card className="overflow-hidden border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-2 font-semibold">{t("user")}</th>
                <th className="px-4 py-2 text-right font-semibold">{t("msgsSent")}</th>
                <th className="px-4 py-2 text-right font-semibold">{t("repliesSent")}</th>
                <th className="px-4 py-2 text-right font-semibold">{t("repliesReceived")}</th>
              </tr>
            </thead>
            <tbody>
              {d.summary.slice(0, 30).map((r) => (
                <tr key={r.user_id} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-2 font-medium">{r.user}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(r.sent)}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(r.replies_sent)}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(r.replies_received)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
