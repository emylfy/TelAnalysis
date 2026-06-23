import { useState } from "react"
import { useTranslation } from "react-i18next"
import { ChevronDown, FolderOpen, Loader2, ShieldCheck } from "lucide-react"

import { browse } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"

const DEMO_PERSONAL = "demo/personal_demo.json"
const DEMO_GROUP = "demo/group_demo.json"

/** Accept what a user actually pastes. Finder "Copy as Pathname" gives a bare
 *  path, but dragging a file or copying its URL yields a `file://` URL with
 *  percent-encoded spaces — strip the scheme and decode so both work. */
function normalizePath(raw: string): string {
  let s = raw.trim()
  // strip surrounding quotes (shells / "Copy as Pathname" sometimes add them)
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    s = s.slice(1, -1)
  }
  if (/^file:\/\//i.test(s)) {
    s = s.replace(/^file:\/\//i, "")
    // file://localhost/Users/… and file:///Users/… both reduce to /Users/…
    if (s.toLowerCase().startsWith("localhost/")) s = s.slice("localhost".length)
    try {
      s = decodeURIComponent(s)
    } catch {
      /* malformed %xx — keep the raw form */
    }
  }
  return s.trim()
}

function Logo() {
  // Same mark as the in-app header (filled message bubble + knocked-out ascending
  // bars), at landing size. Distinct mask id so it never collides with the header
  // instance. See App.tsx Logo() for the rationale.
  return (
    <svg width="40" height="40" viewBox="0 0 56 56" fill="none" aria-hidden="true">
      <mask id="tla-onb-bars">
        <rect width="56" height="56" fill="white" />
        <rect x="18" y="26" width="5" height="9" rx="1.5" fill="black" />
        <rect x="25.5" y="21" width="5" height="14" rx="1.5" fill="black" />
        <rect x="33" y="16" width="5" height="19" rx="1.5" fill="black" />
      </mask>
      <path
        d="M14 8 H44 a8 8 0 0 1 8 8 V32 a8 8 0 0 1 -8 8 H22 l-10 9 l3 -9 h-1 a8 8 0 0 1 -8 -8 V16 a8 8 0 0 1 8 -8 Z"
        fill="var(--primary)"
        mask="url(#tla-onb-bars)"
      />
    </svg>
  )
}

export function Onboarding({
  onLoad,
  error,
  lang,
  onLang,
}: {
  onLoad: (path: string) => void
  error?: boolean
  lang: "ru" | "en"
  onLang: (l: "ru" | "en") => void
}) {
  const { t } = useTranslation()
  const [path, setPath] = useState("")
  const [busy, setBusy] = useState(false)
  const [pickErr, setPickErr] = useState(false)
  const [unavailable, setUnavailable] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)
  const [pathOpen, setPathOpen] = useState(false)
  // surface the manual path field automatically when it's the only way forward
  // (native picker unavailable) or when a manual entry just failed
  const showPath = pathOpen || unavailable || error

  const submitPath = () => {
    const p = normalizePath(path)
    if (p) onLoad(p)
  }

  // Native OS file picker via the local server — returns the REAL path, so the
  // adjacent media (chats/…) resolves and stickers/photos load. Browsers hide
  // the path on <input type=file>, which is why the old upload route silently
  // dropped the media folder.
  const pickFile = async () => {
    setBusy(true)
    setPickErr(false)
    setUnavailable(false)
    try {
      const r = await browse(t("pickPrompt"))
      if (r.path) onLoad(r.path)
      else if (r.unavailable) setUnavailable(true)
      // r.cancelled → user backed out; do nothing
    } catch {
      setPickErr(true)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-background px-6 py-12 text-foreground">
      {/* soft brand glow behind the card — gives the landing some atmosphere
          instead of a flat card on flat black, echoing the in-app summary card */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-0 size-[44rem] -translate-x-1/2 -translate-y-1/3 rounded-full bg-primary/10 blur-3xl"
      />

      <div className="absolute right-6 top-6 flex items-center rounded-lg border border-border bg-card p-0.5">
        {(["en", "ru"] as const).map((l) => (
          <button
            key={l}
            onClick={() => onLang(l)}
            aria-pressed={lang === l}
            className={`rounded-md px-3 py-1 text-sm transition-colors ${
              lang === l ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {l.toUpperCase()}
          </button>
        ))}
      </div>

      <Card className="relative w-full max-w-xl border-border bg-card px-8 py-9 shadow-e3">
        <div className="flex items-center gap-3">
          <Logo />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <span className="text-muted-foreground">Tel</span>Analysis
            </h1>
            <p className="text-sm text-muted-foreground">{t("appTagline")}</p>
          </div>
        </div>

        {/* privacy is THE reassurance for a tool that ingests private chats —
            surface it, don't bury it in a hint */}
        <div className="mt-5 flex items-start gap-2 rounded-lg border border-primary/15 bg-primary/[0.04] px-3 py-2 text-xs leading-relaxed text-muted-foreground">
          <ShieldCheck className="mt-px size-4 shrink-0 text-primary" />
          <span>{t("privacyNote")}</span>
        </div>

        {/* a peek at what the export turns into, so the value is clear before
            the user commits to picking a file */}
        <div className="mt-5">
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground/80">{t("whatYouGet")}</div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {[t("sentiment"), t("tab_network"), t("tab_words"), t("tab_peruser"), t("anniversaries")].map((c) => (
              <span
                key={c}
                className="rounded-full border border-border bg-muted/30 px-2.5 py-0.5 text-xs text-muted-foreground"
              >
                {c}
              </span>
            ))}
          </div>
        </div>

        <p className="mt-5 text-sm leading-relaxed text-muted-foreground">{t("onboardDesc")}</p>

        {/* primary action: native OS file picker (keeps media resolvable) */}
        <Button onClick={pickFile} disabled={busy} className="mt-4 w-full gap-2" size="lg">
          {busy ? <Loader2 className="size-4 animate-spin" /> : <FolderOpen className="size-4" />}
          {busy ? t("uploading") : t("pickFile")}
        </Button>
        <p className="mt-2 text-xs text-muted-foreground">{t("uploadHint")}</p>
        {pickErr && <p className="mt-2 text-sm text-destructive">{t("uploadError")}</p>}

        <div className="my-5 flex items-center gap-3 text-xs uppercase tracking-wide text-muted-foreground">
          <div className="h-px flex-1 bg-border" />
          {t("orDivider")}
          <div className="h-px flex-1 bg-border" />
        </div>

        {/* zero-friction entry: try a bundled demo without exporting anything */}
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="lg" className="flex-1" onClick={() => onLoad(DEMO_PERSONAL)} disabled={busy}>
            {t("demoPersonal")}
          </Button>
          <Button variant="secondary" size="lg" className="flex-1" onClick={() => onLoad(DEMO_GROUP)} disabled={busy}>
            {t("demoGroup")}
          </Button>
        </div>

        {/* advanced fallback: type a path (export folders / large archives). Folded
            so it doesn't compete with the primary flow; auto-opens when it's the
            only option (no native dialog) or after a failed manual entry. */}
        <div className="mt-5 border-t border-border pt-4">
          <button
            type="button"
            onClick={() => setPathOpen((v) => !v)}
            aria-expanded={showPath}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <ChevronDown className={`size-3.5 transition-transform ${showPath ? "rotate-180" : ""}`} />
            {t("enterPathManually")}
          </button>
          {showPath && (
            <div className="mt-3">
              <div className="flex gap-2">
                <Input
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && submitPath()}
                  placeholder={t("pathPlaceholder")}
                  aria-invalid={error || undefined}
                  disabled={busy}
                />
                <Button onClick={submitPath} disabled={!path.trim() || busy} variant="secondary">
                  {t("load")}
                </Button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">{t("pathHint")}</p>
              {unavailable && <p className="mt-2 text-sm text-muted-foreground">{t("pickUnavailable")}</p>}
              {error && <p className="mt-2 text-sm text-destructive">{t("loadError")}</p>}
            </div>
          )}
        </div>

        <div className="mt-3">
          <button
            type="button"
            onClick={() => setHelpOpen((v) => !v)}
            aria-expanded={helpOpen}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <ChevronDown className={`size-3.5 transition-transform ${helpOpen ? "rotate-180" : ""}`} />
            {t("helpExport")}
          </button>
          {helpOpen && <HelpExportContent text={t("helpExportContentMd")} />}
        </div>
      </Card>
    </div>
  )
}

/** Tiny markdown subset (bold, inline code, bullet lists) for the export-help
 *  card — enough for the static blurb without pulling in a markdown library. */
function HelpExportContent({ text }: { text: string }) {
  const paragraphs = text.split(/\n\n+/)
  const renderInline = (s: string): React.ReactNode[] => {
    const out: React.ReactNode[] = []
    let i = 0
    let key = 0
    while (i < s.length) {
      const codeStart = s.indexOf("`", i)
      const boldStart = s.indexOf("**", i)
      const next = [codeStart, boldStart].filter((n) => n >= 0).sort((a, b) => a - b)[0]
      if (next === undefined) {
        out.push(s.slice(i))
        break
      }
      if (next > i) out.push(s.slice(i, next))
      if (next === codeStart) {
        const end = s.indexOf("`", next + 1)
        if (end < 0) {
          out.push(s.slice(next))
          break
        }
        out.push(
          <code key={key++} className="rounded bg-muted px-1.5 py-0.5 text-[0.85em] text-foreground">
            {s.slice(next + 1, end)}
          </code>,
        )
        i = end + 1
      } else {
        const end = s.indexOf("**", next + 2)
        if (end < 0) {
          out.push(s.slice(next))
          break
        }
        out.push(
          <strong key={key++} className="font-semibold text-foreground">
            {s.slice(next + 2, end)}
          </strong>,
        )
        i = end + 2
      }
    }
    return out
  }
  return (
    <div className="mt-3 space-y-2 text-sm leading-relaxed text-muted-foreground">
      {paragraphs.map((para, pi) => {
        const lines = para.split("\n")
        if (lines.every((l) => l.startsWith("- "))) {
          return (
            <ul key={pi} className="ml-4 list-disc space-y-1">
              {lines.map((l, li) => (
                <li key={li}>{renderInline(l.slice(2))}</li>
              ))}
            </ul>
          )
        }
        return <p key={pi}>{renderInline(para)}</p>
      })}
    </div>
  )
}
