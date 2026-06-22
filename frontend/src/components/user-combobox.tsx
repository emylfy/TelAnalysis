import { useState } from "react"
import { useTranslation } from "react-i18next"
import { ChevronsUpDown } from "lucide-react"

import { fmtInt } from "@/lib/i18n"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

/** Minimal shape the picker needs — both SpeakingStyle and UserWords satisfy it. */
export type ComboUser = { user_id: string; name: string; msg_count: number }

/** Searchable participant picker. A plain <select> with 200+ options (half of
 *  them anonymous) is unnavigable, so this is a Popover with a filter input over
 *  a scrollable list, sorted by message count (most active first). Pass
 *  `allLabel` to add a leading reset entry (e.g. "Whole chat") mapped to the
 *  empty-string value. */
export function UserCombobox({
  users,
  value,
  onChange,
  allLabel,
}: {
  users: ComboUser[]
  value: string
  onChange: (id: string) => void
  allLabel?: string
}) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState("")
  const current = users.find((u) => u.user_id === value)
  const ql = q.trim().toLowerCase()
  const filtered = ql ? users.filter((u) => u.name.toLowerCase().includes(ql)) : users
  return (
    <Popover open={open} onOpenChange={(o) => { setOpen(o); if (!o) setQ("") }}>
      <PopoverTrigger className="flex h-9 w-[280px] items-center justify-between gap-2 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs transition-colors hover:bg-muted/40 focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none">
        <span className="truncate">{current ? `${current.name} · ${fmtInt(current.msg_count)}` : (allLabel ?? t("pickUser"))}</span>
        <ChevronsUpDown className="size-4 shrink-0 text-muted-foreground" />
      </PopoverTrigger>
      <PopoverContent align="start" className="w-[280px] gap-0 p-0">
        <div className="border-b border-border p-2">
          <Input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("searchUser")} className="h-8" />
        </div>
        <div className="max-h-72 overflow-auto p-1">
          {allLabel && !ql && (
            <button
              type="button"
              onClick={() => { onChange(""); setOpen(false); setQ("") }}
              className={`flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm transition-colors hover:bg-muted ${value === "" ? "bg-muted/60 font-medium" : ""}`}
            >
              <span className="truncate">{allLabel}</span>
            </button>
          )}
          {filtered.length === 0 ? (
            <div className="px-2 py-3 text-sm text-muted-foreground">{t("noData")}</div>
          ) : (
            filtered.map((u) => (
              <button
                key={u.user_id}
                type="button"
                onClick={() => { onChange(u.user_id); setOpen(false); setQ("") }}
                className={`flex w-full items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-left text-sm transition-colors hover:bg-muted ${u.user_id === value ? "bg-muted/60 font-medium" : ""}`}
              >
                <span className="truncate">{u.name}</span>
                <span className="shrink-0 tabular-nums text-xs text-muted-foreground">{fmtInt(u.msg_count)}</span>
              </button>
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
