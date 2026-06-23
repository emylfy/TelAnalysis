/** Tiny activity sparkline rendered as pure inline SVG — no ECharts, so it can
 *  live in the eager hero without pulling the lazy chart bundle. Area + line with
 *  a soft gradient fill; the stroke stays uniform via non-scaling-stroke despite
 *  the stretched viewBox. */
export function Sparkline({ data, className }: { data: [string, number][]; className?: string }) {
  if (data.length < 2) return null

  // Down-sample very long series (multi-year chats) so the path string stays
  // small; the overall shape is preserved.
  const step = Math.ceil(data.length / 480)
  const vals = step > 1 ? data.filter((_, i) => i % step === 0).map((d) => d[1]) : data.map((d) => d[1])

  const max = Math.max(...vals, 1)
  const W = 100
  const H = 28
  const n = vals.length
  const pts = vals.map((v, i): [number, number] => [(i / (n - 1)) * W, H - (v / max) * (H - 2) - 1])
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`).join(" ")
  const area = `${line} L${W},${H} L0,${H} Z`

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className={className} aria-hidden>
      <defs>
        <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--brand-2)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--brand-2)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#spark-fill)" />
      <path
        d={line}
        fill="none"
        stroke="var(--brand-2)"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}
