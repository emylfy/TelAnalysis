import type { ComponentType } from "react"

/** Top-level section header for a dashboard tab: an icon chip, the title, and an
 *  optional one-line description shown inline (not hover-only) so the long
 *  vertical scroll reads as distinct, labelled blocks instead of a flat run of
 *  charts. Sub-sections inside a block use a plain <h3>. */
export function Section({
  title,
  hint,
  icon: Icon,
  action,
  children,
}: {
  title: string
  hint?: string
  icon?: ComponentType<{ className?: string }>
  action?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="space-y-3">
      <div className="flex items-start gap-3">
        {Icon && (
          <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg bg-foreground/[0.04] ring-1 ring-foreground/10">
            <Icon className="size-[18px] text-primary/85" />
          </span>
        )}
        <div className="min-w-0 space-y-0.5">
          <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
          {hint && <p className="text-sm leading-relaxed text-muted-foreground">{hint}</p>}
        </div>
        {action && <div className="ml-auto shrink-0">{action}</div>}
      </div>
      {children}
    </section>
  )
}
