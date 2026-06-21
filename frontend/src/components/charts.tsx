import ReactECharts from "echarts-for-react"

import { mediaKindLabel, weekdayShort } from "@/lib/i18n"

const AXIS = "rgba(255,255,255,0.10)"
const GRID = "rgba(255,255,255,0.06)"
const TICK = "#9ca3af"
const HEAT = ["#1F2937", "#3B5BDB", "#FF6B6B", "#FFE66D"]
const TOOLTIP = {
  backgroundColor: "#14161d",
  borderColor: "rgba(255,255,255,0.1)",
  textStyle: { color: "#e5e7eb" },
}
const base = {
  backgroundColor: "transparent",
  textStyle: { color: TICK, fontFamily: "inherit" },
  tooltip: { ...TOOLTIP },
}

function Chart({ option, height = 280 }: { option: object; height?: number }) {
  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      opts={{ renderer: "svg" }}
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
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK, interval: 1 },
          splitArea: { show: false },
        },
        yAxis: {
          type: "category",
          data: wd,
          inverse: true,
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK },
        },
        visualMap: { min: 0, max, show: false, inRange: { color: HEAT } },
        series: [{ type: "heatmap", data, itemStyle: { borderColor: "#0e1117", borderWidth: 1 } }],
      }}
    />
  )
}

export function Calendar({ perDay, binary = false }: { perDay: [string, number][]; binary?: boolean }) {
  // binary mode collapses every active day to "1" so the heatmap shows
  // wrote-vs-didn't rather than volume — useful for spotting silent streaks.
  const display: [string, number][] = binary
    ? perDay.map(([d, v]) => [d, v > 0 ? 1 : 0])
    : perDay
  const years = [...new Set(display.map((d) => d[0].slice(0, 4)))].sort()
  let max = 1
  for (const [, v] of display) if (v > max) max = v
  const calendar = years.map((y, i) => ({
    range: y,
    top: 30 + i * 140,
    left: 40,
    right: 16,
    cellSize: ["auto", 13],
    splitLine: { show: false },
    itemStyle: { color: "transparent", borderColor: GRID, borderWidth: 1 },
    dayLabel: { color: TICK, firstDay: 1 },
    monthLabel: { color: TICK },
    yearLabel: { show: true, color: "#e5e7eb", margin: 28 },
  }))
  const series = years.map((y, i) => ({
    type: "heatmap" as const,
    coordinateSystem: "calendar",
    calendarIndex: i,
    data: display.filter((d) => d[0].startsWith(y)),
  }))
  return (
    <Chart
      height={years.length * 140 + 30}
      option={{
        ...base,
        tooltip: { ...TOOLTIP },
        visualMap: { min: 0, max, show: false, inRange: { color: HEAT } },
        calendar,
        series,
      }}
    />
  )
}

export function MediaPie({ byKind }: { byKind: Record<string, number> }) {
  const data = Object.entries(byKind)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ name: mediaKindLabel(k), value: v }))
  const COLORS = ["#5B8FF9", "#5AD8A6", "#F6BD16", "#9270CA", "#5AD8F7", "#E86452", "#FF6B6B"]
  return (
    <Chart
      height={300}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "item", formatter: "{b}: {c} ({d}%)" },
        legend: { type: "scroll", orient: "vertical", right: 0, top: "center", textStyle: { color: TICK } },
        color: COLORS,
        series: [
          {
            type: "pie",
            radius: ["38%", "68%"],
            center: ["38%", "50%"],
            label: { color: "#e5e7eb" },
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
  color = "#5B8FF9",
}: {
  data: [string, number][]
  height?: number
  color?: string
}) {
  return (
    <Chart
      height={height}
      option={{
        ...base,
        grid: { left: 8, right: 8, top: 16, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: data.map((d) => d[0]),
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK, interval: 0, rotate: data.length > 12 ? 40 : 0 },
        },
        yAxis: {
          type: "value",
          axisLine: { show: false },
          splitLine: { lineStyle: { color: GRID } },
          axisLabel: { color: TICK },
        },
        series: [{ type: "bar", data: data.map((d) => d[1]), itemStyle: { color, borderRadius: [3, 3, 0, 0] } }],
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
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK, hideOverlap: true },
        },
        yAxis: { type: "value", axisLine: { show: false }, splitLine: { lineStyle: { color: GRID } }, axisLabel: { color: TICK } },
        series: [
          {
            type: "line",
            data: data.map((d) => d[1]),
            smooth: true,
            showSymbol: false,
            lineStyle: { color: "#5B8FF9", width: 1.5 },
            areaStyle: {
              color: {
                type: "linear", x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: "rgba(91,143,249,0.25)" },
                  { offset: 1, color: "rgba(91,143,249,0.02)" },
                ],
              },
            },
          },
        ],
      }}
    />
  )
}

const NET_COLORS = ["#5B8FF9", "#5AD8A6", "#F6BD16", "#9270CA", "#E86452", "#5AD8F7", "#FF6B6B", "#FFE66D"]
const POS = "#5AD8A6"
const NEG = "#E86452"

/** Multi-series line over a shared category axis (e.g. sentiment over time). */
export function Lines({
  series,
  height = 300,
  zeroLine = false,
}: {
  series: { name: string; data: [string, number][] }[]
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
      lineStyle: { width: 2 },
      itemStyle: { color: NET_COLORS[i % NET_COLORS.length] },
      ...(zeroLine && i === 0
        ? { markLine: { silent: true, symbol: "none", lineStyle: { color: "rgba(255,255,255,0.25)", type: "dashed" }, data: [{ yAxis: 0 }] } }
        : {}),
    }
  })
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP, trigger: "axis" },
        legend: series.length > 1 ? { top: 0, textStyle: { color: TICK } } : undefined,
        grid: { left: 8, right: 12, top: series.length > 1 ? 32 : 12, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: cats,
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK, hideOverlap: true },
        },
        yAxis: { type: "value", axisLine: { show: false }, splitLine: { lineStyle: { color: GRID } }, axisLabel: { color: TICK } },
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
        grid: { left: 8, right: 8, top: 12, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: data.map((d) => d[0]),
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK },
        },
        yAxis: { type: "value", axisLine: { show: false }, splitLine: { lineStyle: { color: GRID } }, axisLabel: { color: TICK } },
        series: [
          {
            type: "bar",
            data: data.map((d) => ({ value: d[1], itemStyle: { color: d[1] >= 0 ? POS : NEG, borderRadius: d[1] >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] } })),
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
    symbolSize: 12 + 38 * Math.sqrt(n[2] / maxW),
    itemStyle: {
      color: NET_COLORS[(hasComm ? (communities![n[0]] ?? 0) : i) % NET_COLORS.length],
    },
    label: { show: kept.length <= 30 },
  }))
  const links = [...pair.entries()].map(([key, w]) => {
    const [source, target] = key.split(" ")
    return { source, target, lineStyle: { width: 1 + 5 * (w / maxE), opacity: 0.5 } }
  })

  return (
    <Chart
      height={520}
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
            label: { color: "#e5e7eb", position: "right", fontSize: 11 },
            emphasis: { focus: "adjacency", lineStyle: { width: 6 } },
            lineStyle: { color: "rgba(255,255,255,0.25)", curveness: 0.05 },
            force: { repulsion: 220, edgeLength: [40, 140], gravity: 0.08 },
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
  series: { name: string; values: number[]; highlight?: boolean }[]
  height?: number
}) {
  return (
    <Chart
      height={height}
      option={{
        ...base,
        tooltip: { ...TOOLTIP },
        legend: { bottom: 0, textStyle: { color: TICK }, type: "scroll" },
        radar: {
          indicator: indicators,
          axisName: { color: TICK },
          splitLine: { lineStyle: { color: GRID } },
          splitArea: { areaStyle: { color: ["transparent"] } },
          axisLine: { lineStyle: { color: GRID } },
        },
        color: NET_COLORS,
        series: [
          {
            type: "radar",
            data: series.map((s, i) => ({
              name: s.name,
              value: s.values,
              symbol: "none",
              lineStyle: { width: s.highlight ? 2.5 : 1, opacity: s.highlight ? 1 : 0.4 },
              areaStyle: s.highlight ? { color: NET_COLORS[i % NET_COLORS.length], opacity: 0.15 } : undefined,
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
        xAxis: { type: "category", data: cats, axisLine: { lineStyle: { color: AXIS } }, axisLabel: { color: TICK } },
        yAxis: {
          type: "value",
          min: asTime ? 0 : undefined,
          max: asTime ? 1440 : undefined,
          axisLine: { show: false },
          splitLine: { lineStyle: { color: GRID } },
          axisLabel: { color: TICK, formatter: asTime ? (v: number) => hhmm(v) : undefined },
        },
        series: [{ type: "boxplot", data, itemStyle: { color: "rgba(91,143,249,0.25)", borderColor: "#5B8FF9" } }],
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
        legend: { top: 0, textStyle: { color: TICK } },
        grid: { left: 8, right: 8, top: 32, bottom: 24, containLabel: true },
        xAxis: {
          type: "category",
          data: [...Array(24).keys()],
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK, interval: 1 },
        },
        yAxis: {
          type: "value",
          axisLine: { show: false },
          splitLine: { lineStyle: { color: GRID } },
          axisLabel: { color: TICK, formatter: (v: number) => `${Math.round(v * 100)}%` },
        },
        series: [
          { name: a.name, type: "bar", data: normA, itemStyle: { color: "#5B8FF9", opacity: 0.55 }, barGap: "-100%" },
          { name: b.name, type: "bar", data: normB, itemStyle: { color: "#9270CA", opacity: 0.55 }, barGap: "-100%" },
          { name: overlapLabel, type: "bar", data: ov, itemStyle: { color: "#5AD8A6" }, barGap: "-100%" },
        ],
      }}
    />
  )
}

/** Horizontal bars — readable for long labels (phrases, words). Sorted desc, biggest on top. */
export function BarsH({
  data,
  height,
  color = "#5B8FF9",
}: {
  data: [string, number][]
  height?: number
  color?: string
}) {
  const rows = [...data].sort((a, b) => a[1] - b[1]) // ECharts y-category draws bottom→top
  return (
    <Chart
      height={height ?? Math.max(160, rows.length * 26 + 32)}
      option={{
        ...base,
        grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
        xAxis: {
          type: "value",
          axisLine: { show: false },
          splitLine: { lineStyle: { color: GRID } },
          axisLabel: { color: TICK },
        },
        yAxis: {
          type: "category",
          data: rows.map((d) => d[0]),
          axisLine: { lineStyle: { color: AXIS } },
          axisLabel: { color: TICK },
        },
        series: [
          {
            type: "bar",
            data: rows.map((d) => d[1]),
            itemStyle: { color, borderRadius: [0, 3, 3, 0] },
            label: { show: true, position: "right", color: TICK, fontSize: 11 },
          },
        ],
      }}
    />
  )
}
