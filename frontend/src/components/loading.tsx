import { useTranslation } from "react-i18next"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

/** Placeholder shown while a tab's primary query is in flight. */
export function TabLoading() {
  return (
    <div className="space-y-6 pt-2">
      <Skeleton className="h-7 w-48" />
      <Skeleton className="h-72 w-full" />
      <Skeleton className="h-7 w-40" />
      <Skeleton className="h-72 w-full" />
    </div>
  )
}

/** Shown when a tab's primary query fails — explains and offers a retry, instead
 *  of the silent blank section a bare `return null` would leave. */
export function TabError({ onRetry }: { onRetry?: () => void }) {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <p className="text-sm text-muted-foreground">{t("tabError")}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={() => onRetry()}>
          {t("retry")}
        </Button>
      )}
    </div>
  )
}
