import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { Loader2, Shuffle } from "lucide-react"

import { Card } from "@/components/ui/card"

/** Server-rendered word cloud (an <img> from /api/wordcloud). The PNG is slow
 *  to generate on the first hit, so show an explicit "building…" state instead
 *  of a blank box, and surface a retry on failure. The backend caches the PNG
 *  per `seed`, so re-entry is instant and the picture stays stable — while the
 *  "shuffle" button bumps the seed to get a fresh (but then equally stable and
 *  cached) arrangement on demand. */
export function WordCloud({ src, alt }: { src: string; alt: string }) {
  const { t } = useTranslation()
  const [state, setState] = useState<"loading" | "ready" | "error">("loading")
  const [seed, setSeed] = useState(0)
  const ref = useRef<HTMLImageElement>(null)

  const url = `${src}${src.includes("?") ? "&" : "?"}seed=${seed}`

  // A cached image may already be `complete` before React attaches onLoad, in
  // which case the event never fires — catch that here so it doesn't hang on the
  // spinner forever.
  useEffect(() => {
    if (ref.current?.complete && ref.current.naturalWidth > 0) setState("ready")
  }, [url])

  const shuffle = () => {
    setState("loading")
    setSeed((s) => s + 1)
  }

  return (
    <Card className="relative flex min-h-[260px] items-center justify-center border-border bg-card p-3">
      {state === "ready" && (
        <button
          type="button"
          onClick={shuffle}
          className="absolute right-3 top-3 z-20 inline-flex items-center gap-1.5 rounded-md border border-border bg-card/80 px-2.5 py-1 text-xs text-muted-foreground backdrop-blur transition-colors hover:text-foreground"
        >
          <Shuffle className="size-3.5" /> {t("wordcloudShuffle")}
        </button>
      )}

      {state !== "ready" && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 px-4 text-center text-muted-foreground">
          {state === "loading" ? (
            <>
              <Loader2 className="size-6 animate-spin" />
              <p className="text-sm">{t("wordcloudBuilding")}</p>
            </>
          ) : (
            <>
              <p className="text-sm">{t("wordcloudError")}</p>
              <button
                type="button"
                onClick={shuffle}
                className="rounded-md border border-border px-3 py-1 text-sm text-foreground transition-colors hover:bg-foreground/5"
              >
                {t("retry")}
              </button>
            </>
          )}
        </div>
      )}

      <img
        ref={ref}
        key={seed}
        src={url}
        alt={alt}
        onLoad={() => setState("ready")}
        onError={() => setState("error")}
        className={`max-h-[420px] w-full rounded-md object-contain transition-opacity duration-300 ${
          state === "ready" ? "opacity-100" : "opacity-0"
        }`}
      />
    </Card>
  )
}
