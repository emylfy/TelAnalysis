import { useState } from "react"
import { ChevronDown } from "lucide-react"

/** Lightweight disclosure: button toggles a child block. Used for "Show all"
 *  tables that would otherwise dominate vertical space. */
export function Collapsible({ label, children }: { label: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground"
      >
        <ChevronDown className={`size-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        {label}
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
  )
}
