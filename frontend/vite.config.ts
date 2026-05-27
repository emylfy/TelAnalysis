import path from "node:path"

import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// Dev: Vite on :5173 proxies /api → FastAPI on :8000, so the SPA always calls
// same-origin /api (matches production, where FastAPI serves the built SPA).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
})
