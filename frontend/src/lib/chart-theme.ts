// Single source of truth for chart styling.
//
// ECharts renders to <canvas> and can't read CSS custom properties, so the
// palette lives here as resolved hex values. These MIRROR the `--chart-*` /
// `--pos` / `--neg` tokens in index.css — keep the two in sync. Anything that
// styles a chart pulls from this module instead of inlining hex, so a palette
// change is one edit and every chart stays coherent.

// structural ink — axes, gridlines, tick labels, the value labels on series
export const ink = {
  axis: "rgba(255,255,255,0.07)",
  grid: "rgba(255,255,255,0.045)",
  tick: "#7c8493", // muted, recedes behind the data
  label: "#e5e7eb", // foreground, for in-chart value labels
} as const

// brand coral — reserved for emphasis: the headline item, "you", the #1 bar.
// Used sparingly so it actually reads as emphasis and not decoration.
export const brand = "#ff6b6b"

// diverging / sentiment
export const pos = "#34d399"
export const neg = "#fb6f5d"

// Curated categorical palette. Harmonious on the #0e1117 surface and ordered
// most-distinct-first, so a 2- or 3-series chart gets maximally separable hues.
// `series[0]` (indigo) is the default "neutral data" colour across the app.
export const series = [
  "#6a8efb", // indigo  — primary data
  "#34d399", // emerald
  "#f5b740", // amber
  "#a78bfa", // violet
  "#38bdf8", // sky
  "#fb7185", // rose
  "#2dd4bf", // teal
  "#facc15", // gold
] as const

export const DATA = series[0] // canonical neutral data colour

// ── People ──────────────────────────────────────────────────────────────────
// A participant keeps the SAME hue everywhere — the overlap chart, the tone
// radar, the per-user sentiment lines, their own per-user accents — so the eye
// can track "me vs them" across the whole app instead of re-learning colours on
// every chart. The hue is derived from a stable hash of the name, which makes it
// consistent across the separately-fetched endpoints with zero plumbing.
const PERSON_HUES = [
  "#6a8efb", // indigo
  "#f5b740", // amber   (warm vs the cool indigo — best contrast for a 2-person DM)
  "#34d399", // emerald
  "#a78bfa", // violet
  "#38bdf8", // sky
  "#fb7185", // rose
  "#2dd4bf", // teal
  "#facc15", // gold
] as const

function hashStr(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (Math.imul(h, 31) + s.charCodeAt(i)) | 0
  return Math.abs(h)
}

/** Stable hue for one person — same name → same colour everywhere. */
export function personColor(name: string): string {
  return PERSON_HUES[hashStr(name) % PERSON_HUES.length]
}

/** Distinct stable hues for a known set of people: seed each from its hashed
 *  hue, then bump to the next free slot on collision so two people sharing one
 *  chart never get the same colour. Order the names canonically (we use
 *  most-active-first) so every component that builds it agrees. */
export function personPalette(names: string[]): Record<string, string> {
  const used = new Set<number>()
  const out: Record<string, string> = {}
  for (const name of names) {
    let idx = hashStr(name) % PERSON_HUES.length
    for (let k = 0; k < PERSON_HUES.length && used.has(idx); k++) idx = (idx + 1) % PERSON_HUES.length
    used.add(idx)
    out[name] = PERSON_HUES[idx]
  }
  return out
}

// Heatmap ramp (dark indigo → indigo → violet → brand coral), shared by the
// calendar and the hour×weekday grid. Stays in the app's cool→warm family (no
// out-of-palette gold), and the low end (#1b2740) sits clearly above the card
// background so small-but-nonzero days don't vanish into it.
export const heat = ["#1b2740", "#3b54c9", "#8b5cf6", "#ff6b6b"] as const

// Two-tone scale for the calendar's binary "wrote / didn't" mode — a single
// brand-indigo against near-background, so it reads as a calm presence map
// instead of the loud full heat ramp.
export const heatBinary = ["#1b2740", "#6a8efb"] as const

// Tooltip — rounded, soft shadow, faint blur. Consistent everywhere.
export const tooltip = {
  backgroundColor: "rgba(18,20,27,0.94)",
  borderColor: "rgba(255,255,255,0.08)",
  borderWidth: 1,
  padding: [8, 12] as [number, number],
  textStyle: { color: ink.label, fontSize: 12 },
  extraCssText:
    "border-radius:10px;box-shadow:0 10px 30px -8px rgba(0,0,0,0.6);backdrop-filter:blur(6px);",
}

export const base = {
  backgroundColor: "transparent",
  textStyle: { color: ink.tick, fontFamily: "inherit" },
  tooltip,
}

/** Shared value-axis styling (no axis line, faint split lines, muted ticks). */
export const valueAxis = {
  type: "value" as const,
  axisLine: { show: false },
  splitLine: { lineStyle: { color: ink.grid } },
  axisLabel: { color: ink.tick },
}

/** ECharts can't read CSS custom properties — `fillStyle = "var(--chart-2)"` is
 *  invalid and breaks hover/emphasis colour maths (the element flashes
 *  transparent). Resolve any `var(--token)` to its computed hex first; hex/rgb
 *  strings pass through untouched. */
export function resolveColor(c: string): string {
  if (typeof document === "undefined" || !c.startsWith("var(")) return c
  const name = c.slice(4, -1).trim() // "var(--chart-2)" -> "--chart-2"
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || c
}

/** Vertical top→bottom linear gradient between two colours — for area fills. */
export function vFill(top: string, bottom: string) {
  return {
    type: "linear" as const,
    x: 0,
    y: 0,
    x2: 0,
    y2: 1,
    colorStops: [
      { offset: 0, color: top },
      { offset: 1, color: bottom },
    ],
  }
}

/** Per-rank colour for a ranked bar series: the #1 bar gets the brand accent,
 *  the rest share one hue and fade in opacity down the ranking. Reads as
 *  "importance trailing off" — gives flat ranked bars a deliberate rhythm
 *  instead of a uniform slab. `i` is rank from the top (0 = largest). */
export function rankStyle(i: number, n: number, baseColor: string = DATA) {
  if (i === 0) return { color: brand }
  const t = n > 2 ? (i - 1) / (n - 2) : 0 // 0 just below the top … 1 at the tail
  return { color: baseColor, opacity: 1 - 0.42 * t }
}
