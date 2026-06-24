import type { ComponentType } from "react"

import { Card } from "@/components/ui/card"
import { AnimatedInt } from "@/components/motion"
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
  valueNum,
  sub,
  icon: Icon,
  meter,
  className,
}: {
  label: string
  value: string
  /** when set (plain integer), the value animates via NumberFlow; `value` is the
   *  static/reduced-motion fallback. Omit for durations / % / decimals. */
  valueNum?: number
  sub?: string
  icon?: ComponentType<{ className?: string }>
  meter?: StatMeter
  className?: string
}) {
  return (
    <Card
      className={cn(
        "gap-0 px-4 py-3 transition-[transform,box-shadow] hover:-translate-y-0.5",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        {Icon && (
          <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 ring-1 ring-foreground/[0.08]">
            <Icon className="size-4 text-primary/80" />
          </span>
        )}
        <div className="min-w-0 flex-1 space-y-0.5">
          <div className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</div>
          <div className="text-[1.75rem] font-semibold leading-none tracking-tight tabular-nums">
            {valueNum != null ? <AnimatedInt value={valueNum} /> : value}
          </div>
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
    <div className="mt-3">
      {/* positioning context is just the bar row, so the baseline tick centres on
          the bar — not on the whole block (label included), where it used to drift
          down and overlap the caption text. */}
      <div className="relative">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2">
          <div className="h-full rounded-full transition-[width]" style={{ width: `${fill}%`, background: color }} />
        </div>
        {base != null && (
          // chat-average tick — a thin rounded riser straddling the bar
          <div
            aria-hidden
            className="absolute top-1/2 h-3 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-foreground/55"
            style={{ left: `${base}%` }}
          />
        )}
      </div>
      {label && <div className="mt-1.5 text-[0.68rem] text-muted-foreground">{label}</div>}
    </div>
  )
}
