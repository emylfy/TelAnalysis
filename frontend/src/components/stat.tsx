import type { ComponentType } from "react"

import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

/** A single KPI tile, shared across every tab (Overview / Per-user / Words /
 *  Channel). Three layers of richness, all optional:
 *   - `icon`  — a lucide glyph in a chip, matching the section-header / Highlights
 *               language so a grid of these reads as deliberate, not flat.
 *   - `sub`   — a small caption under the value (e.g. "avg 33 · max 345").
 *   - `meter` — a thin progress bar for ratio metrics, with an optional baseline
 *               tick (the chat average) so the number says *something* — "is 20%
 *               a lot?" is answered right there instead of left to the reader.
 *  Without any of these it degrades to the old label / value tile, so it can
 *  replace the three duplicate local `Stat` definitions verbatim. */
export type StatMeter = {
  /** filled fraction, 0..1 */
  value: number
  /** optional reference tick (e.g. chat average), 0..1 */
  baseline?: number
  /** caption under the bar, e.g. "avg 14%" */
  label?: string
  /** bar colour (defaults to the brand primary) */
  color?: string
}

export function Stat({
  label,
  value,
  sub,
  icon: Icon,
  meter,
  className,
}: {
  label: string
  value: string
  sub?: string
  icon?: ComponentType<{ className?: string }>
  meter?: StatMeter
  className?: string
}) {
  return (
    <Card
      className={cn(
        "gap-0 border-border bg-card px-4 py-3 ring-foreground/10 transition-colors hover:ring-foreground/20",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        {Icon && (
          <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-foreground/[0.04] ring-1 ring-foreground/10">
            <Icon className="size-4 text-primary/80" />
          </span>
        )}
        <div className="min-w-0 flex-1 space-y-0.5">
          <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</div>
          <div className="text-2xl font-semibold leading-none tabular-nums">{value}</div>
          {sub && <div className="pt-0.5 text-xs text-muted-foreground">{sub}</div>}
        </div>
      </div>
      {meter && <Meter {...meter} />}
    </Card>
  )
}

function Meter({ value, baseline, label, color = "var(--primary)" }: StatMeter) {
  const clamp = (x: number) => Math.max(0, Math.min(1, x))
  const fill = clamp(value) * 100
  const base = baseline != null ? clamp(baseline) * 100 : null
  return (
    <div className="relative mt-3">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-foreground/[0.08]">
        <div className="h-full rounded-full transition-[width]" style={{ width: `${fill}%`, background: color }} />
      </div>
      {base != null && (
        // chat-average tick — a thin riser straddling the bar
        <div
          aria-hidden
          className="absolute top-1/2 h-3 w-px -translate-x-1/2 -translate-y-1/2 bg-foreground/45"
          style={{ left: `${base}%` }}
        />
      )}
      {label && <div className="mt-1.5 text-[0.68rem] text-muted-foreground">{label}</div>}
    </div>
  )
}
