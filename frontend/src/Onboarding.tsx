import { useState } from "react"
import { useTranslation } from "react-i18next"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"

const DEMO_PERSONAL = "demo/personal_demo.json"
const DEMO_GROUP = "demo/group_demo.json"

function Logo() {
  return (
    <svg width="40" height="40" viewBox="0 0 56 56" fill="none">
      <rect width="56" height="56" rx="14" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.10)" />
      <rect x="15" y="30" width="6" height="11" rx="2" fill="var(--chart-1)" />
      <rect x="25" y="22" width="6" height="19" rx="2" fill="var(--chart-2)" />
      <rect x="35" y="15" width="6" height="26" rx="2" fill="var(--primary)" />
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

  const submit = () => {
    const p = path.trim()
    if (p) onLoad(p)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <div className="absolute right-6 top-6 flex items-center rounded-lg border border-border bg-card p-0.5">
        {(["ru", "en"] as const).map((l) => (
          <button
            key={l}
            onClick={() => onLang(l)}
            className={`rounded-md px-3 py-1 text-sm transition-colors ${
              lang === l ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {l.toUpperCase()}
          </button>
        ))}
      </div>

      <Card className="w-full max-w-xl border-border bg-card px-8 py-9">
        <div className="flex items-center gap-3">
          <Logo />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">TelAnalysis</h1>
            <p className="text-sm text-muted-foreground">{t("appTagline")}</p>
          </div>
        </div>

        <p className="mt-6 text-sm leading-relaxed text-muted-foreground">{t("onboardDesc")}</p>

        <div className="mt-4 flex gap-2">
          <Input
            value={path}
            onChange={(e) => setPath(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder={t("pathPlaceholder")}
            aria-invalid={error || undefined}
            autoFocus
          />
          <Button onClick={submit} disabled={!path.trim()}>
            {t("load")}
          </Button>
        </div>
        {error && <p className="mt-2 text-sm text-destructive">{t("loadError")}</p>}

        <div className="mt-6 flex flex-wrap gap-2 border-t border-border pt-5">
          <Button variant="secondary" size="sm" onClick={() => onLoad(DEMO_PERSONAL)}>
            {t("demoPersonal")}
          </Button>
          <Button variant="secondary" size="sm" onClick={() => onLoad(DEMO_GROUP)}>
            {t("demoGroup")}
          </Button>
        </div>
      </Card>
    </div>
  )
}
