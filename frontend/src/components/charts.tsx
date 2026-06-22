import ReactECharts from "echarts-for-react"

import { fmtDateTick, fmtInt, mediaKindLabel, monthShort, weekdayShort } from "@/lib/i18n"
import {
  base,
  brand,
  DATA,
  heat,
  ink,
  neg,
  personColor,
  pos,
  rankStyle,
  resolveColor,
  series as PALETTE,
  tooltip as TOOLTIP,
  valueAxis,
  vFill,
} from "@/lib/chart-theme"

function Chart({ option, height = 280 }: { option: object; height?: number }) {
  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      opts={{ renderer: "canvas" }}
      notMerge
    />
  )
}

export function HourWeekday({ grid }: { grid: number[][] }) {
  const wd = weekdayShort()
  const data: [number, number, number][] = []
  let max = 1
  grid.forEach((row, w) =>
    row.forEach((v, h) => {
      data.push([h, w, v])
      if (v > max) max = v
    }),
  )
  return (
    <Chart
      height={260}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, position: "top" },
        grid: { left: 36, right: 8, top: 8, bottom: 24 },
        xAxis: {
          type: "category",
          data: [...Array(24).keys()],
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick, interval: 1 },
          splitArea: { show: false },
        },
        yAxis: {
          type: "category",
          data: wd,
          inverse: true,
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick },
        },
        visualMap: { min: 0, max, show: false, inRange: { color: [...heat] } },
        series: [{ type: "heatmap", data, itemStyle: { borderColor: "#0e1117", borderWidth: 1 } }],
      }}
    />
  )
}

export function Calendar({
  perDay,
  binary = false,
  year,
}: {
  perDay: [string, number][]
  binary?: boolean
  year?: string
}) {
  // binary mode collapses every active day to "1" so the heatmap shows
  // wrote-vs-didn't rather than volume — useful for spotting silent streaks.
  const display: [string, number][] = binary
    ? perDay.map(([d, v]) => [d, v > 0 ? 1 : 0])
    : perDay
  const years = [...new Set(display.map((d) => d[0].slice(0, 4)))].sort()
  // One year at a time (caller switches via tabs); fall back to the latest.
  const activeYear = year && years.includes(year) ? year : years[years.length - 1]
  let max = 1
  for (const [, v] of display) if (v > max) max = v
  // All 7 weekday labels, localized. ECharts' nameMap is indexed by day-of-week
  // (0 = Sunday), but weekdayShort() is Monday-first — reorder to Sun-first.
  const wd = weekdayShort()
  const dayNameMap = [wd[6], wd[0], wd[1], wd[2], wd[3], wd[4], wd[5]]
  const months = monthShort()
  // Let the grid breathe: taller, near-square cells and the canvas sized to the
  // content (7 weekday rows) so there's no dead space below — only deliberate
  // top/bottom air. (Was 16px cells in a fixed 196px box → cramped + a big gap.)
  const TOP = 36
  const CELL = 24
  return (
    <Chart
      height={TOP + 7 * CELL + 28}
      option={{
        ...base,
        tooltip: {
          ...TOOLTIP,
          formatter: (p: { value: [string, number] }) => {
            const [, m, d] = p.value[0].split("-")
            return `${Number(d)} ${months[Number(m) - 1]} · ${fmtInt(p.value[1])}`
          },
        },
        visualMap: { min: 0, max, show: false, inRange: { color: [...heat] } },
        calendar: {
          range: activeYear,
          top: TOP,
          left: 44,
          right: 16,
          cellSize: ["auto", CELL],
          splitLine: { show: false },
          itemStyle: { color: "transparent", borderColor: ink.grid, borderWidth: 1 },
          dayLabel: { color: ink.tick, firstDay: 1, nameMap: dayNameMap, margin: 8, fontSize: 11 },
          monthLabel: { color: ink.tick, margin: 10, nameMap: months },
          yearLabel: { show: false },
        },
        series: {
          type: "heatmap",
          coordinateSystem: "calendar",
          data: display.filter((d) => d[0].startsWith(activeYear)),
        },
      }}
    />
  )
}

/** Tiny "less → more" gradient key for the calendar heat scale. */
export function HeatLegend({ less, more }: { less: string; more: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span>{less}</span>
      <span className="h-2 w-16 rounded-full" style={{ background: `linear-gradient(to right, ${heat.join(", ")})` }} />
      <span>{more}</span>
    </div>
  )
}

export function MediaPie({ byKind }: { byKind: Record<string, number> }) {
  const data = Object.entries(byKind)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ name: mediaKindLabel(k), value: v }))
  return (
    <Chart
      height={300}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "item", formatter: "{b}: {c} ({d}%)" },
        legend: { type: "scroll", orient: "vertical", right: 0, top: "center", textStyle: { color: ink.tick } },
        color: [...PALETTE],
        series: [
          {
            type: "pie",
            radius: ["42%", "70%"],
            center: ["38%", "50%"],
            // Slice labels + leader lines crowd and overlap on the left for the
            // long tail of media kinds — the legend already names every slice.
            label: { show: false },
            labelLine: { show: false },
            itemStyle: { borderColor: "#14161d", borderWidth: 2 },
            data,
          },
        ],
      }}
    />
  )
}

export function Bars({
  data,
  height = 280,
  color,
  accent = false,
}: {
  data: [string, number][]
  height?: number
  color?: string
  // colour the single tallest bar with the brand accent (focal point)
  accent?: boolean
}) {
  const baseColor = color ? resolveColor(color) : DATA
  const maxIdx = accent ? data.reduce((m, d, i, a) => (d[1] > a[m][1] ? i : m), 0) : -1
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "axis", axisPointer: { type: "shadow" } },
        grid: { left: 8, right: 8, top: 16, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: data.map((d) => d[0]),
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick, interval: 0, rotate: data.length > 12 ? 40 : 0 },
        },
        yAxis: valueAxis,
        series: [
          {
            type: "bar",
            data: data.map((d, i) => ({
              value: d[1],
              itemStyle: { color: i === maxIdx ? brand : baseColor, borderRadius: [3, 3, 0, 0] },
            })),
          },
        ],
      }}
    />
  )
}

/** Single-series filled area over a date axis — message volume per day. */
export function AreaTimeline({ data, height = 280 }: { data: [string, number][]; height?: number }) {
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "axis" },
        grid: { left: 8, right: 12, top: 12, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: data.map((d) => d[0]),
          boundaryGap: false,
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick, hideOverlap: true, formatter: fmtDateTick },
        },
        yAxis: valueAxis,
        series: [
          {
            type: "line",
            data: data.map((d) => d[1]),
            smooth: 0.3,
            showSymbol: false,
            sampling: "lttb", // downsample the daily hairball to a clean stroke
            lineStyle: { color: DATA, width: 2 },
            areaStyle: { color: vFill("rgba(106,142,251,0.28)", "rgba(106,142,251,0.01)") },
          },
        ],
      }}
    />
  )
}

/** Multi-series line over a shared category axis (e.g. sentiment over time). */
export function Lines({
  series,
  height = 300,
  zeroLine = false,
}: {
  series: { name: string; data: [string, number][]; color?: string }[]
  height?: number
  zeroLine?: boolean
}) {
  const cats = [...new Set(series.flatMap((s) => s.data.map((d) => d[0])))].sort()
  const ech = series.map((s, i) => {
    const m = new Map(s.data)
    return {
      name: s.name,
      type: "line" as const,
      smooth: true,
      showSymbol: false,
      connectNulls: true,
      data: cats.map((c) => (m.has(c) ? m.get(c)! : null)),
      // Thin & slightly translucent when many series overlap (e.g. per-user
      // sentiment) so the spaghetti stays readable; legend toggles individuals.
      lineStyle: { width: series.length > 4 ? 1.2 : 2, opacity: series.length > 4 ? 0.85 : 1 },
      // per-person hue when supplied (consistent across the app), else palette order
      itemStyle: { color: s.color ? resolveColor(s.color) : PALETTE[i % PALETTE.length] },
      ...(zeroLine && i === 0
        ? { markLine: { silent: true, symbol: "none", lineStyle: { color: "rgba(255,255,255,0.22)", type: "dashed" }, data: [{ yAxis: 0 }] } }
        : {}),
    }
  })
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "axis" },
        legend: series.length > 1 ? { top: 0, textStyle: { color: ink.tick } } : undefined,
        grid: { left: 8, right: 12, top: series.length > 1 ? 32 : 12, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: cats,
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick, hideOverlap: true, formatter: fmtDateTick },
        },
        yAxis: valueAxis,
        series: ech,
      }}
    />
  )
}

/** Bars coloured by sign — green positive, red negative, with a zero baseline. */
export function DivergingBars({
  data,
  height = 240,
}: {
  data: [string, number][]
  height?: number
}) {
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "axis", axisPointer: { type: "shadow" } },
        grid: { left: 8, right: 8, top: 12, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: data.map((d) => d[0]),
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick },
        },
        yAxis: valueAxis,
        series: [
          {
            type: "bar",
            data: data.map((d) => ({ value: d[1], itemStyle: { color: d[1] >= 0 ? pos : neg, borderRadius: d[1] >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] } })),
          },
        ],
      }}
    />
  )
}

/** Reply graph — force-directed, draggable & zoomable. Reuses ECharts (no extra dep).
 *  Parallel edges are aggregated; the heaviest nodes are kept for readability. */
export function Network({
  nodes,
  edges,
  communities,
  maxNodes = 60,
}: {
  nodes: [string, string, number][]
  edges: [string, string, string][]
  communities?: Record<string, number>
  maxNodes?: number
}) {
  const kept = [...nodes].sort((a, b) => b[2] - a[2]).slice(0, maxNodes)
  const keep = new Set(kept.map((n) => n[0]))
  const maxW = Math.max(1, ...kept.map((n) => n[2]))

  // aggregate parallel edges into one weighted link per unordered pair (skip self-loops)
  const pair = new Map<string, number>()
  for (const [s, t] of edges) {
    if (s === t || !keep.has(s) || !keep.has(t)) continue
    const key = s < t ? `${s} ${t}` : `${t} ${s}`
    pair.set(key, (pair.get(key) ?? 0) + 1)
  }
  const maxE = Math.max(1, ...pair.values())

  // Colour by Louvain community when the backend supplies one (clusters read
  // as groups); otherwise fall back to a per-node hue.
  const hasComm = !!communities && Object.keys(communities).length > 0
  const data = kept.map((n, i) => ({
    id: n[0],
    name: n[1],
    symbolSize: 14 + 42 * Math.sqrt(n[2] / maxW),
    itemStyle: {
      color: PALETTE[(hasComm ? (communities![n[0]] ?? 0) : i) % PALETTE.length],
      borderColor: "rgba(255,255,255,0.14)",
      borderWidth: 1,
      shadowColor: "rgba(0,0,0,0.4)",
      shadowBlur: 8,
    },
    label: { show: kept.length <= 30 },
  }))
  const links = [...pair.entries()].map(([key, w]) => {
    const [source, target] = key.split(" ")
    return { source, target, lineStyle: { width: 1 + 5 * (w / maxE), opacity: 0.45 } }
  })

  // Small graphs (e.g. a 7-person group) cluster in the middle of a big canvas;
  // push them apart and shrink the height so they fill the space instead.
  const small = kept.length <= 12
  return (
    <Chart
      height={small ? 420 : 540}
      option={{
        ...base,
        tooltip: { ...TOOLTIP },
        series: [
          {
            type: "graph",
            layout: "force",
            roam: true,
            draggable: true,
            data,
            links,
            label: { color: ink.label, position: "right", fontSize: 12, fontWeight: 500 },
            emphasis: { focus: "adjacency", lineStyle: { width: 6 }, label: { fontSize: 13 } },
            lineStyle: { color: "rgba(255,255,255,0.22)", curveness: 0.06 },
            force: {
              repulsion: small ? 900 : 260,
              edgeLength: small ? [110, 240] : [50, 150],
              gravity: small ? 0.04 : 0.08,
            },
          },
        ],
      }}
    />
  )
}

/** Radar — overlay several entities across shared axes (e.g. speaking tone). */
export function Radar({
  indicators,
  series,
  height = 340,
}: {
  indicators: { name: string; max: number }[]
  series: { name: string; values: number[]; highlight?: boolean; color?: string }[]
  height?: number
}) {
  const hue = (s: { color?: string }, i: number) => (s.color ? resolveColor(s.color) : PALETTE[i % PALETTE.length])
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP },
        legend: { bottom: 0, textStyle: { color: ink.tick }, type: "scroll" },
        radar: {
          indicator: indicators,
          axisName: { color: ink.tick },
          splitLine: { lineStyle: { color: ink.grid } },
          splitArea: { areaStyle: { color: ["transparent"] } },
          axisLine: { lineStyle: { color: ink.grid } },
        },
        // per-person hue when supplied, so a participant matches their colour elsewhere
        color: series.map((s, i) => hue(s, i)),
        series: [
          {
            type: "radar",
            data: series.map((s, i) => ({
              name: s.name,
              value: s.values,
              symbol: "none",
              lineStyle: { width: s.highlight ? 2.5 : 1, opacity: s.highlight ? 1 : 0.4 },
              areaStyle: s.highlight ? { color: hue(s, i), opacity: 0.15 } : undefined,
            })),
          },
        ],
      }}
    />
  )
}

function quantile(sorted: number[], q: number): number {
  const pos = (sorted.length - 1) * q
  const base = Math.floor(pos)
  const rest = pos - base
  return sorted[base + 1] !== undefined ? sorted[base] + rest * (sorted[base + 1] - sorted[base]) : sorted[base]
}

/** Box plot across categories. `asTime` formats the y-axis as HH:MM (minutes-from-midnight). */
export function Box({
  groups,
  asTime = false,
  height = 300,
}: {
  groups: { name: string; values: number[] }[]
  asTime?: boolean
  height?: number
}) {
  const cats = groups.map((g) => g.name)
  const data = groups.map((g) => {
    const s = [...g.values].sort((a, b) => a - b)
    return [s[0], quantile(s, 0.25), quantile(s, 0.5), quantile(s, 0.75), s[s.length - 1]]
  })
  const hhmm = (v: number) => `${String(Math.floor(v / 60)).padStart(2, "0")}:${String(Math.floor(v % 60)).padStart(2, "0")}`
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "item" },
        grid: { left: 8, right: 8, top: 12, bottom: 24, containLabel: true },
        xAxis: { type: "category", data: cats, axisLine: { lineStyle: { color: ink.axis } }, axisLabel: { color: ink.tick } },
        yAxis: {
          ...valueAxis,
          min: asTime ? 0 : undefined,
          max: asTime ? 1440 : undefined,
          axisLabel: { color: ink.tick, formatter: asTime ? (v: number) => hhmm(v) : undefined },
        },
        series: [{ type: "boxplot", data, itemStyle: { color: "rgba(106,142,251,0.22)", borderColor: DATA } }],
      }}
    />
  )
}

/** "When you overlap" — 3 bar series for a 2-user chat: A normalized, B
 *  normalized, and min(A, B) — the chunk of the day where both are active. */
export function HourOverlap({
  a,
  b,
  overlapLabel,
}: {
  a: { name: string; hours: number[] }
  b: { name: string; hours: number[] }
  overlapLabel: string
}) {
  const totA = a.hours.reduce((s, v) => s + v, 0) || 1
  const totB = b.hours.reduce((s, v) => s + v, 0) || 1
  const normA = a.hours.map((v) => v / totA)
  const normB = b.hours.map((v) => v / totB)
  const ov = normA.map((v, i) => Math.min(v, normB[i]))
  return (
    <Chart
      height={260}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "axis" },
        legend: { top: 0, textStyle: { color: ink.tick } },
        grid: { left: 8, right: 8, top: 32, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: [...Array(24).keys()],
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick, interval: 1 },
        },
        yAxis: {
          ...valueAxis,
          axisLabel: { color: ink.tick, formatter: (v: number) => `${Math.round(v * 100)}%` },
        },
        series: [
          // each person keeps their app-wide hue; the overlap is the shared green
          { name: a.name, type: "bar", data: normA, itemStyle: { color: personColor(a.name), opacity: 0.5 }, barGap: "-100%" },
          { name: b.name, type: "bar", data: normB, itemStyle: { color: personColor(b.name), opacity: 0.5 }, barGap: "-100%" },
          { name: overlapLabel, type: "bar", data: ov, itemStyle: { color: pos }, barGap: "-100%" },
        ],
      }}
    />
  )
}

/** Horizontal bars — readable for long labels (phrases, words). Sorted desc,
 *  biggest on top. By default the leader takes the brand accent and the rest
 *  fade in opacity down the ranking (`rank`), giving the field a deliberate
 *  rhythm; pass `accent={false}` for a flat single-hue field. */
export function BarsH({
  data,
  height,
  color,
  accent = true,
}: {
  data: [string, number][]
  height?: number
  color?: string
  accent?: boolean
}) {
  const rows = [...data].sort((a, b) => a[1] - b[1]) // ECharts y-category draws bottom→top
  const baseColor = color ? resolveColor(color) : DATA
  const n = rows.length
  return (
    <Chart
      height={height ?? Math.max(160, rows.length * 26 + 32)}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "axis", axisPointer: { type: "shadow" } },
        grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
        xAxis: { ...valueAxis, axisLabel: { color: ink.tick } },
        yAxis: {
          type: "category",
          data: rows.map((d) => d[0]),
          axisLine: { lineStyle: { color: ink.axis } },
          axisLabel: { color: ink.tick },
        },
        series: [
          {
            type: "bar",
            // rows are ascending, so rank from the top is (n-1 - i)
            data: rows.map((d, i) => ({
              value: d[1],
              itemStyle: {
                borderRadius: [0, 3, 3, 0],
                ...(accent ? rankStyle(n - 1 - i, n, baseColor) : { color: baseColor }),
              },
            })),
            label: { show: true, position: "right", color: ink.tick, fontSize: 11 },
          },
        ],
      }}
    />
  )
}
