import { fmtInt } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { brand, DATA, resolveColor } from "@/lib/chart-theme"

export type RankRow = {
  label: string
  value: number
  /** secondary line under the label (date, duration, …) */
  sub?: string
  /** overrides the right-hand figure when it isn't just `value` formatted */
  valueText?: string
}

/** Compact leaderboard: rank · label (over a faint proportional bar) · figure.
 *
 *  Replaces the flat ranked tables that read as undifferentiated rows of numbers.
 *  The inline bar restores the at-a-glance "shape" a bare number column loses,
 *  the rank number anchors position, and the #1 row takes the brand accent — so
 *  it earns its place as a distinct block archetype next to the bar charts
 *  instead of being a fourth identical horizontal-bar field. */
export function RankTable({
  rows,
  color,
  unit,
  columns,
  max = 8,
}: {
  rows: RankRow[]
  color?: string
  /** appended after the figure, e.g. "сообщений" */
  unit?: string
  /** optional header row: [label column, figure column] */
  columns?: [string, string]
  max?: number
}) {
  const baseColor = color ? resolveColor(color) : DATA
  const shown = rows.slice(0, max)
  const peak = Math.max(1, ...shown.map((r) => r.value))
  return (
    <Card className="overflow-hidden border-border bg-card p-0">
      {columns && (
        <div className="flex items-center gap-3 border-b border-border px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <span className="w-4 shrink-0" />
          <span className="min-w-0 flex-1">{columns[0]}</span>
          <span className="shrink-0 tabular-nums">{columns[1]}</span>
        </div>
      )}
      <ol>
        {shown.map((r, i) => {
          const top = i === 0
          const c = top ? brand : baseColor
          return (
            <li
              key={i}
              className="relative flex items-center gap-3 border-b border-border/50 px-4 py-2.5 last:border-0"
            >
              {/* proportional track behind the row — the leaderboard "shape" */}
              <span
                aria-hidden
                className="pointer-events-none absolute inset-y-1 left-0 rounded-r-md"
                style={{ width: `${(r.value / peak) * 100}%`, background: c, opacity: top ? 0.16 : 0.09 }}
              />
              <span className="relative w-4 shrink-0 text-right text-xs font-semibold tabular-nums text-muted-foreground">
                {i + 1}
              </span>
              <div className="relative min-w-0 flex-1">
                <div className="truncate text-sm font-medium" title={r.label}>
                  {r.label}
                </div>
                {r.sub && <div className="truncate text-xs text-muted-foreground">{r.sub}</div>}
              </div>
              <span
                className="relative shrink-0 text-sm font-semibold tabular-nums"
                style={top ? { color: brand } : undefined}
              >
                {r.valueText ?? fmtInt(r.value)}
                {unit ? <span className="ml-1 text-xs font-normal text-muted-foreground">{unit}</span> : null}
              </span>
            </li>
          )
        })}
      </ol>
    </Card>
  )
}
