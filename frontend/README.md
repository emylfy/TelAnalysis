# TelAnalysis — frontend

React + TypeScript + Vite SPA for [TelAnalysis](../README.md). It renders the
dashboard (Overview, Network, Words, Channel, Per-User, Sentiment) by calling
the FastAPI backend under `/api`. Charts use ECharts; styling is Tailwind +
shadcn-style primitives; data fetching is React Query; i18n is i18next (RU/EN).

## Normal use

You don't run this directly — from the repo root, `./run.sh` builds this SPA
and serves it same-origin with the API on <http://127.0.0.1:8000>.

## Frontend development (hot reload)

Run the API and the Vite dev server in two terminals; Vite proxies `/api` to
the backend:

```bash
# repo root — terminal 1
.venv/bin/uvicorn api.main:app --reload --port 8000

# frontend/ — terminal 2
npm install
npm run dev          # http://localhost:5173
```

## Scripts

| Command           | What it does                                  |
| ----------------- | --------------------------------------------- |
| `npm run dev`     | Vite dev server with HMR (proxies `/api`)     |
| `npm run build`   | `tsc -b` typecheck + production build to `dist/` |
| `npm run lint`    | ESLint over the source                        |
| `npm run preview` | Serve the built `dist/` locally               |

## Layout

- `src/*.tsx` — one component per tab (`Overview`, `Network`, `Words`, …)
- `src/components/charts.tsx` — ECharts wrappers (timelines, heatmaps, graph, radar)
- `src/components/ui/` — shared primitives (button, card, tabs, …)
- `src/lib/api.ts` — typed client + response interfaces for every `/api` endpoint
- `src/lib/i18n.ts` — language setup and locale-aware formatters
