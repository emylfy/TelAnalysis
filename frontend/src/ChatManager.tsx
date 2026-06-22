import { useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import {
  AlertTriangle,
  ChevronDown,
  RotateCcw,
  Scissors,
  Trash2,
  X,
} from "lucide-react"

import { api, type BackupChat } from "@/lib/api"
import {
  chatFamilyLabel,
  chatTypeFamily,
  chatTypeLabel,
  chatWord,
  fmtBytes,
  fmtInt,
  messageWord,
  type ChatFamily,
} from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

// media subdir → label. Keys mirror the on-disk folder names Telegram writes.
const MEDIA_LABELS: Record<"ru" | "en", Record<string, string>> = {
  ru: {
    photos: "Фото", video_files: "Видео", voice_messages: "Голосовые",
    round_video_messages: "Кружки", stickers: "Стикеры", files: "Файлы",
    audio_files: "Аудио", animations: "GIF", video_messages: "Видео-сообщения",
    _root: "Прочее",
  },
  en: {
    photos: "Photos", video_files: "Videos", voice_messages: "Voice",
    round_video_messages: "Round videos", stickers: "Stickers", files: "Files",
    audio_files: "Audio", animations: "GIF", video_messages: "Video msgs",
    _root: "Other",
  },
}

type SortKey = "name" | "type" | "msg_count" | "disk_bytes" | "file_count"

// Fixed display order for type-family filter chips and tombstone sub-sections.
const FAMILY_ORDER: ChatFamily[] = ["channel", "group", "personal", "bot"]

function yearRange(first: string | null, last: string | null): string {
  const a = first?.slice(0, 4)
  const b = last?.slice(0, 4)
  if (!a && !b) return "—"
  if (a === b) return a ?? b ?? "—"
  return `${a ?? "?"}–${b ?? "?"}`
}

/** A bare-bones centred modal — the project has no dialog primitive, and the
 *  destructive actions here want an explicit, blocking confirm. */
function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-background/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <Card
        className="w-full max-w-md gap-3 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </Card>
    </div>
  )
}

export function ChatManager({ path }: { path: string }) {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const lang = (i18n.language === "en" ? "en" : "ru") as "ru" | "en"
  const mediaLabel = (k: string) => MEDIA_LABELS[lang][k] ?? k

  const chatsQ = useQuery({ queryKey: ["backup-chats", path], queryFn: () => api.backupChats(path) })
  const canManage = !!chatsQ.data?.can_manage
  const trashQ = useQuery({
    queryKey: ["backup-trash", path],
    queryFn: () => api.backupTrash(path),
    enabled: canManage,
  })

  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [search, setSearch] = useState("")
  const [sortKey, setSortKey] = useState<SortKey>("disk_bytes")
  const [sortDir, setSortDir] = useState<1 | -1>(-1)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<BackupChat[] | null>(null)
  const [slimFor, setSlimFor] = useState<BackupChat | null>(null)
  const [confirmEmpty, setConfirmEmpty] = useState(false)
  // empty left channels ("tombstones") live in their own collapsible section,
  // with a separate selection so the main free-up bar isn't polluted by 0-byte rows.
  const [tombsOpen, setTombsOpen] = useState(false)
  const [tombSel, setTombSel] = useState<Set<string>>(new Set())
  const [confirmTombs, setConfirmTombs] = useState<BackupChat[] | null>(null)
  // main-table type filter (families in the set are HIDDEN; empty = show all)
  const [hiddenFam, setHiddenFam] = useState<Set<ChatFamily>>(new Set())
  // tombstone name sort within each type sub-section (1 = A→Я, -1 = Я→A)
  const [tombSortDir, setTombSortDir] = useState<1 | -1>(1)

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["backup-chats", path] })
    qc.invalidateQueries({ queryKey: ["backup-trash", path] })
    // the analytics layer reads the same export — its chat list changed too
    qc.invalidateQueries({ queryKey: ["chats", path] })
  }

  const deleteMut = useMutation({
    mutationFn: (ids: string[]) => api.deleteChats(path, ids),
    onSuccess: () => {
      setSelected(new Set())
      setConfirmDelete(null)
      setTombSel(new Set())
      setConfirmTombs(null)
      invalidate()
    },
  })
  const slimMut = useMutation({
    mutationFn: (v: { id: string; types: string[] }) => api.slimChat(path, v.id, v.types),
    onSuccess: () => {
      setSlimFor(null)
      invalidate()
    },
  })
  const restoreMut = useMutation({
    mutationFn: (id: string) => api.restoreTrash(path, id),
    onSuccess: invalidate,
  })
  const emptyMut = useMutation({
    mutationFn: () => api.emptyTrash(path),
    onSuccess: () => {
      setConfirmEmpty(false)
      invalidate()
    },
  })

  const rows = chatsQ.data?.chats ?? []
  const maxDisk = useMemo(() => Math.max(1, ...rows.map((r) => r.disk_bytes)), [rows])

  // A "tombstone" is a left channel/group Telegram kept by name only: no
  // messages, nothing on disk. These flood the main table and free no space,
  // so they get a dedicated section instead.
  const isTomb = (r: BackupChat) => r.is_left && r.msg_count === 0 && r.disk_bytes === 0

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    const out = rows.filter((r) => {
      if (isTomb(r)) return false
      if (hiddenFam.has(chatTypeFamily(r.type))) return false
      if (q && !r.name.toLowerCase().includes(q)) return false
      return true
    })
    out.sort((a, b) => {
      let d: number
      if (sortKey === "name") d = a.name.localeCompare(b.name)
      else if (sortKey === "type") d = a.type.localeCompare(b.type)
      else d = (a[sortKey] as number) - (b[sortKey] as number)
      return d * sortDir
    })
    return out
  }, [rows, search, sortKey, sortDir, hiddenFam])

  // type-family chip data for the main table: counts over non-tombstone rows
  // (stable as you search), only families actually present.
  const famCounts = useMemo(() => {
    const c = { channel: 0, group: 0, personal: 0, bot: 0 } as Record<ChatFamily, number>
    rows.forEach((r) => { if (!isTomb(r)) c[chatTypeFamily(r.type)]++ })
    return c
  }, [rows])
  const presentFamilies = FAMILY_ORDER.filter((f) => famCounts[f] > 0)
  const toggleFam = (f: ChatFamily) =>
    setHiddenFam((prev) => {
      const next = new Set(prev)
      next.has(f) ? next.delete(f) : next.add(f)
      return next
    })

  const selectedRows = rows.filter((r) => selected.has(r.id))
  const selBytes = selectedRows.reduce((s, r) => s + r.disk_bytes, 0)
  const allFilteredSelected = filtered.length > 0 && filtered.every((r) => selected.has(r.id))
  const someFilteredSelected = filtered.some((r) => selected.has(r.id))

  // tombstones: full set (for the header count) and the search-filtered view.
  const allTombs = useMemo(() => rows.filter(isTomb), [rows])
  const tombs = useMemo(() => {
    const q = search.trim().toLowerCase()
    return q ? allTombs.filter((r) => r.name.toLowerCase().includes(q)) : allTombs
  }, [allTombs, search])
  const tombSelRows = allTombs.filter((r) => tombSel.has(r.id))
  const allTombsSelected = tombs.length > 0 && tombs.every((r) => tombSel.has(r.id))
  const someTombsSelected = tombs.some((r) => tombSel.has(r.id))

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  const toggleAll = () =>
    setSelected((prev) => {
      const next = new Set(prev)
      if (allFilteredSelected) filtered.forEach((r) => next.delete(r.id))
      else filtered.forEach((r) => next.add(r.id))
      return next
    })
  const toggleTomb = (id: string) =>
    setTombSel((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  const toggleAllTombs = () =>
    setTombSel((prev) => {
      const next = new Set(prev)
      if (allTombsSelected) tombs.forEach((r) => next.delete(r.id))
      else tombs.forEach((r) => next.add(r.id))
      return next
    })
  // tombstones split into type sub-sections (channels / groups / …), each name-sorted
  const tombFamilies = FAMILY_ORDER.filter((f) => allTombs.some((r) => chatTypeFamily(r.type) === f))
  const famTombRows = (f: ChatFamily) =>
    tombs
      .filter((r) => chatTypeFamily(r.type) === f)
      .sort((a, b) => a.name.localeCompare(b.name) * tombSortDir)
  const toggleFamAll = (f: ChatFamily) =>
    setTombSel((prev) => {
      const next = new Set(prev)
      const fam = famTombRows(f)
      const allOn = fam.length > 0 && fam.every((r) => next.has(r.id))
      fam.forEach((r) => (allOn ? next.delete(r.id) : next.add(r.id)))
      return next
    })
  const sortBy = (k: SortKey) => {
    if (k === sortKey) setSortDir((d) => (d === 1 ? -1 : 1))
    else {
      setSortKey(k)
      setSortDir(k === "name" || k === "type" ? 1 : -1)
    }
  }

  if (chatsQ.isLoading) {
    return (
      <div className="space-y-3 pt-2">
        <Skeleton className="h-9 w-72" />
        <Skeleton className="h-96 w-full" />
        <p className="text-sm text-muted-foreground">{t("loadingChats")}</p>
      </div>
    )
  }

  const header = (label: string, k: SortKey, extra?: string) => (
    <button
      onClick={() => sortBy(k)}
      className={cn(
        "flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground transition-colors hover:text-foreground",
        extra,
      )}
    >
      {label}
      {sortKey === k && <span className="text-[0.6rem]">{sortDir === 1 ? "▲" : "▼"}</span>}
    </button>
  )

  return (
    <div className="space-y-4 pt-1">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">{t("managerTitle")}</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">{t("managerHint")}</p>
      </div>

      {!canManage && (
        <div className="flex items-start gap-2 rounded-lg border border-[#F6BD16]/30 bg-[#F6BD16]/10 px-4 py-2.5 text-sm text-[#F6BD16]">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <span>{t("managerReadonly")}</span>
        </div>
      )}

      {/* controls */}
      <div className="flex flex-wrap items-center gap-2">
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t("managerSearch")}
          className="h-8 w-56"
        />
        {presentFamilies.length >= 2 && (
          <div className="flex flex-wrap items-center gap-1.5">
            {presentFamilies.map((f) => {
              const shown = !hiddenFam.has(f)
              return (
                <button
                  key={f}
                  onClick={() => toggleFam(f)}
                  aria-pressed={shown}
                  className={cn(
                    "flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-sm transition-colors",
                    shown
                      ? "border-primary/40 bg-primary/10 text-foreground"
                      : "border-border bg-card text-muted-foreground opacity-60 hover:opacity-100",
                  )}
                >
                  {chatFamilyLabel(f)}
                  <span className="text-xs tabular-nums text-muted-foreground">{famCounts[f]}</span>
                </button>
              )
            })}
          </div>
        )}
        <div className="ml-auto flex items-center gap-2">
          {selected.size > 0 && (
            <>
              <span className="text-xs text-muted-foreground">
                {t("managerSelected", { n: selected.size })} · {t("managerFreeUp", { size: fmtBytes(selBytes) })}
              </span>
              <Button
                variant="destructive"
                size="sm"
                disabled={!canManage || deleteMut.isPending}
                onClick={() => setConfirmDelete(selectedRows)}
              >
                <Trash2 className="size-3.5" />
                {t("deleteSelected")}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* table */}
      <Card className="gap-0 overflow-hidden p-0">
        <div className="flex items-center gap-3 border-b border-border px-3 py-2.5">
          <Checkbox
            checked={allFilteredSelected}
            indeterminate={someFilteredSelected && !allFilteredSelected}
            onCheckedChange={toggleAll}
            disabled={!canManage}
            aria-label="select all"
          />
          <div className="flex-1">{header(t("colChat"), "name")}</div>
          <div className="hidden w-24 sm:block">{header(t("colType"), "type")}</div>
          <div className="hidden w-24 text-right md:block">{header(t("colMessages"), "msg_count", "justify-end w-full")}</div>
          <div className="hidden w-24 text-right lg:block text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("colPeriod")}</div>
          <div className="w-28 text-right">{header(t("colSize"), "disk_bytes", "justify-end w-full")}</div>
          <div className="w-7" />
        </div>

        {filtered.length === 0 ? (
          <div className="px-4 py-10 text-center text-sm text-muted-foreground">{t("noChatsFound")}</div>
        ) : (
          <ol>
            {filtered.map((r) => {
              const sel = selected.has(r.id)
              const isOpen = expanded === r.id
              const mediaTypes = Object.keys(r.media).filter((k) => r.media[k] > 0)
              return (
                <li key={r.id} className="border-b border-border/50 last:border-0">
                  <div
                    className={cn(
                      "relative flex items-center gap-3 px-3 py-2.5 transition-colors",
                      sel ? "bg-primary/[0.05]" : "hover:bg-muted/20",
                    )}
                  >
                    {/* proportional disk-size track */}
                    <span
                      aria-hidden
                      className="pointer-events-none absolute inset-y-1 left-0 rounded-r-md bg-primary"
                      style={{ width: `${(r.disk_bytes / maxDisk) * 100}%`, opacity: 0.06 }}
                    />
                    <Checkbox
                      checked={sel}
                      onCheckedChange={() => toggle(r.id)}
                      disabled={!canManage}
                      aria-label={r.name}
                      className="relative shrink-0"
                    />
                    <div className="relative min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm font-medium" title={r.name}>{r.name}</span>
                        {r.is_left && (
                          <span className="shrink-0 rounded-full border border-border bg-muted/40 px-1.5 py-0.5 text-[0.6rem] uppercase text-muted-foreground">
                            {t("managerLeftBadge")}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground sm:hidden">
                        {chatTypeLabel(r.type)} · {fmtInt(r.msg_count)}
                      </div>
                    </div>
                    <div className="relative hidden w-24 truncate text-sm text-muted-foreground sm:block">{chatTypeLabel(r.type)}</div>
                    <div className="relative hidden w-24 text-right text-sm tabular-nums md:block">{fmtInt(r.msg_count)}</div>
                    <div className="relative hidden w-24 text-right text-xs tabular-nums text-muted-foreground lg:block">{yearRange(r.first_date, r.last_date)}</div>
                    <div className="relative w-28 text-right text-sm font-semibold tabular-nums">
                      {r.disk_bytes > 0 ? fmtBytes(r.disk_bytes) : <span className="text-muted-foreground">—</span>}
                      {r.file_count > 0 && (
                        <div className="text-[0.65rem] font-normal text-muted-foreground">{fmtInt(r.file_count)} {t("colFiles").toLowerCase()}</div>
                      )}
                    </div>
                    <div className="relative w-7 text-right">
                      {mediaTypes.length > 0 && (
                        <button
                          onClick={() => setExpanded(isOpen ? null : r.id)}
                          className="rounded p-1 text-muted-foreground transition-colors hover:text-foreground"
                          aria-label="media breakdown"
                        >
                          <ChevronDown className={cn("size-4 transition-transform", isOpen && "rotate-180")} />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* media breakdown / slim entry point */}
                  {isOpen && mediaTypes.length > 0 && (
                    <div className="border-t border-border/40 bg-muted/20 px-3 py-3 pl-10">
                      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5">
                        {mediaTypes
                          .sort((a, b) => r.media[b] - r.media[a])
                          .map((k) => (
                            <span key={k} className="text-xs text-muted-foreground">
                              {mediaLabel(k)} <span className="font-semibold text-foreground tabular-nums">{fmtBytes(r.media[k])}</span>
                            </span>
                          ))}
                        {canManage && (
                          <Button variant="outline" size="xs" className="ml-auto" onClick={() => setSlimFor(r)}>
                            <Scissors className="size-3" />
                            {t("slim")}
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </li>
              )
            })}
          </ol>
        )}
      </Card>

      {/* empty left channels ("tombstones") — names only, free no disk */}
      {allTombs.length > 0 && (
        <Card className="gap-0 overflow-hidden p-0">
          <button
            onClick={() => setTombsOpen((o) => !o)}
            aria-expanded={tombsOpen}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-muted/20"
          >
            <ChevronDown className={cn("size-4 shrink-0 text-muted-foreground transition-transform", tombsOpen && "rotate-180")} />
            <h2 className="text-sm font-semibold">{t("tombstonesTitle")}</h2>
            <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs font-medium tabular-nums text-muted-foreground">
              {fmtInt(allTombs.length)}
            </span>
            <span className="hidden truncate text-xs text-muted-foreground md:block">{t("tombstonesHint")}</span>
          </button>

          {tombsOpen && (
            <>
              <div className="flex items-center gap-3 border-t border-border px-4 py-2">
                <Checkbox
                  checked={allTombsSelected}
                  indeterminate={someTombsSelected && !allTombsSelected}
                  onCheckedChange={toggleAllTombs}
                  disabled={!canManage}
                  aria-label="select all empty channels"
                />
                <span className="text-xs text-muted-foreground">
                  {tombSel.size > 0 ? t("managerSelected", { n: tombSel.size }) : t("selectAll")}
                </span>
                <button
                  onClick={() => setTombSortDir((d) => (d === 1 ? -1 : 1))}
                  className="flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
                >
                  {t("tombSortName")}
                  <span className="text-[0.6rem]">{tombSortDir === 1 ? "▲" : "▼"}</span>
                </button>
                {tombSel.size > 0 && (
                  <Button
                    variant="destructive"
                    size="xs"
                    className="ml-auto"
                    disabled={!canManage || deleteMut.isPending}
                    onClick={() => setConfirmTombs(tombSelRows)}
                  >
                    <Trash2 className="size-3.5" />
                    {t("tombstonesRemove")}
                  </Button>
                )}
              </div>
              {tombs.length === 0 ? (
                <div className="border-t border-border/50 px-4 py-6 text-center text-sm text-muted-foreground">{t("noChatsFound")}</div>
              ) : (
                <div className="max-h-80 overflow-auto">
                  {tombFamilies.map((f) => {
                    const fam = famTombRows(f)
                    if (fam.length === 0) return null
                    const allSel = fam.every((r) => tombSel.has(r.id))
                    const someSel = fam.some((r) => tombSel.has(r.id))
                    return (
                      <div key={f}>
                        {/* sticky type header so it stays visible while scrolling 377 channels */}
                        <div className="sticky top-0 z-10 flex items-center gap-3 border-t border-border bg-card/95 px-4 py-1.5 backdrop-blur">
                          <Checkbox
                            checked={allSel}
                            indeterminate={someSel && !allSel}
                            onCheckedChange={() => toggleFamAll(f)}
                            disabled={!canManage}
                            aria-label={`select all ${f}`}
                          />
                          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{chatFamilyLabel(f)}</span>
                          <span className="rounded-full bg-muted px-1.5 py-0.5 text-[0.65rem] font-medium tabular-nums text-muted-foreground">{fmtInt(fam.length)}</span>
                        </div>
                        <ol>
                          {fam.map((r) => {
                            const sel = tombSel.has(r.id)
                            return (
                              <li key={r.id}>
                                <button
                                  type="button"
                                  onClick={() => canManage && toggleTomb(r.id)}
                                  className={cn(
                                    "flex w-full items-center gap-3 border-t border-border/30 px-4 py-1.5 text-left transition-colors",
                                    sel ? "bg-primary/[0.05]" : "hover:bg-muted/20",
                                    !canManage && "cursor-not-allowed",
                                  )}
                                >
                                  <Checkbox checked={sel} disabled={!canManage} tabIndex={-1} className="pointer-events-none shrink-0" aria-label={r.name} />
                                  <span className="min-w-0 flex-1 truncate text-sm" title={r.name}>{r.name}</span>
                                </button>
                              </li>
                            )
                          })}
                        </ol>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}
        </Card>
      )}

      {/* trash */}
      {canManage && (trashQ.data?.entries.length ?? 0) > 0 && (
        <Card className="gap-0 overflow-hidden p-0">
          <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
            <Trash2 className="size-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold">{t("trash")}</h2>
            <span className="text-xs text-muted-foreground">
              {t("trashPending", { size: fmtBytes(chatsQ.data?.trash_bytes ?? 0) })}
            </span>
            <Button
              variant="destructive"
              size="xs"
              className="ml-auto"
              disabled={emptyMut.isPending}
              onClick={() => setConfirmEmpty(true)}
            >
              {t("emptyTrash")}
            </Button>
          </div>
          <ol>
            {trashQ.data!.entries.map((e) => (
              <li key={e.id} className="flex items-center gap-3 border-b border-border/50 px-4 py-2 last:border-0">
                <span className="min-w-0 flex-1 truncate text-sm" title={e.chat_names.join(", ")}>
                  {e.kind === "slim" ? <Scissors className="mr-1 inline size-3 text-muted-foreground" /> : null}
                  {e.label}
                </span>
                <span className="shrink-0 text-xs tabular-nums text-muted-foreground">{fmtBytes(e.bytes)}</span>
                <Button
                  variant="ghost"
                  size="xs"
                  disabled={restoreMut.isPending}
                  onClick={() => restoreMut.mutate(e.id)}
                >
                  <RotateCcw className="size-3" />
                  {t("restore")}
                </Button>
              </li>
            ))}
          </ol>
        </Card>
      )}

      {/* delete confirmation */}
      {confirmDelete && (
        <Modal onClose={() => setConfirmDelete(null)}>
          <div className="flex items-center gap-2">
            <span className="flex size-9 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
              <Trash2 className="size-4" />
            </span>
            <h2 className="text-base font-semibold">
              {t("confirmDeleteTitle", { n: confirmDelete.length, w: chatWord(confirmDelete.length) })}
            </h2>
          </div>
          <p className="text-sm text-muted-foreground">
            {(() => {
              const msgs = confirmDelete.reduce((s, r) => s + r.msg_count, 0)
              return t("confirmDeleteBody", { msgs: fmtInt(msgs), w: messageWord(msgs) })
            })()}
          </p>
          <div className="rounded-md bg-muted/40 px-3 py-2 text-sm">
            <span className="font-semibold">{t("managerFreeUp", { size: fmtBytes(selBytes) })}</span>
          </div>
          <div className="max-h-32 overflow-auto text-xs text-muted-foreground">
            {confirmDelete.map((r) => (
              <div key={r.id} className="flex justify-between gap-2 py-0.5">
                <span className="truncate">{r.name}</span>
                <span className="shrink-0 tabular-nums">{fmtBytes(r.disk_bytes)}</span>
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(null)}>{t("cancel")}</Button>
            <Button
              variant="destructive"
              size="sm"
              disabled={deleteMut.isPending}
              onClick={() => deleteMut.mutate(confirmDelete.map((r) => r.id))}
            >
              <Trash2 className="size-3.5" />
              {t("confirm")}
            </Button>
          </div>
        </Modal>
      )}

      {/* empty-channels removal confirmation (no disk freed — records only) */}
      {confirmTombs && (
        <Modal onClose={() => setConfirmTombs(null)}>
          <div className="flex items-center gap-2">
            <span className="flex size-9 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
              <Trash2 className="size-4" />
            </span>
            <h2 className="text-base font-semibold">
              {t("confirmTombsTitle", { n: confirmTombs.length, w: chatWord(confirmTombs.length) })}
            </h2>
          </div>
          <p className="text-sm text-muted-foreground">{t("confirmTombsBody")}</p>
          <div className="max-h-32 overflow-auto text-xs text-muted-foreground">
            {confirmTombs.map((r) => (
              <div key={r.id} className="truncate py-0.5" title={r.name}>{r.name}</div>
            ))}
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" onClick={() => setConfirmTombs(null)}>{t("cancel")}</Button>
            <Button
              variant="destructive"
              size="sm"
              disabled={deleteMut.isPending}
              onClick={() => deleteMut.mutate(confirmTombs.map((r) => r.id))}
            >
              <Trash2 className="size-3.5" />
              {t("confirm")}
            </Button>
          </div>
        </Modal>
      )}

      {/* slim modal */}
      {slimFor && <SlimModal chat={slimFor} mediaLabel={mediaLabel} onClose={() => setSlimFor(null)} onApply={(types) => slimMut.mutate({ id: slimFor.id, types })} pending={slimMut.isPending} />}

      {/* empty-trash confirmation */}
      {confirmEmpty && (
        <Modal onClose={() => setConfirmEmpty(false)}>
          <div className="flex items-center gap-2">
            <span className="flex size-9 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
              <AlertTriangle className="size-4" />
            </span>
            <h2 className="text-base font-semibold">{t("emptyTrash")}</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            {t("emptyTrashConfirm", { size: fmtBytes(chatsQ.data?.trash_bytes ?? 0) })}
          </p>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" onClick={() => setConfirmEmpty(false)}>{t("cancel")}</Button>
            <Button variant="destructive" size="sm" disabled={emptyMut.isPending} onClick={() => emptyMut.mutate()}>
              {t("emptyTrash")}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function SlimModal({
  chat,
  mediaLabel,
  onClose,
  onApply,
  pending,
}: {
  chat: BackupChat
  mediaLabel: (k: string) => string
  onClose: () => void
  onApply: (types: string[]) => void
  pending: boolean
}) {
  const { t } = useTranslation()
  const types = Object.keys(chat.media).filter((k) => chat.media[k] > 0).sort((a, b) => chat.media[b] - chat.media[a])
  const [picked, setPicked] = useState<Set<string>>(new Set())
  const pickedBytes = [...picked].reduce((s, k) => s + (chat.media[k] ?? 0), 0)
  const toggle = (k: string) =>
    setPicked((prev) => {
      const next = new Set(prev)
      next.has(k) ? next.delete(k) : next.add(k)
      return next
    })
  return (
    <Modal onClose={onClose}>
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-base font-semibold">{t("slimTitle", { name: chat.name })}</h2>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="size-4" /></button>
      </div>
      <p className="text-sm text-muted-foreground">{t("slimHint")}</p>
      <div className="space-y-1">
        {types.map((k) => {
          const on = picked.has(k)
          return (
            <button
              type="button"
              key={k}
              role="checkbox"
              aria-checked={on}
              onClick={() => toggle(k)}
              className={cn(
                "flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-left transition-colors",
                on ? "bg-primary/10" : "hover:bg-muted/40",
              )}
            >
              <Checkbox checked={on} tabIndex={-1} className="pointer-events-none" />
              <span className="flex-1 text-sm">{mediaLabel(k)}</span>
              <span className="text-sm font-semibold tabular-nums">{fmtBytes(chat.media[k])}</span>
            </button>
          )
        })}
      </div>
      <div className="flex items-center justify-between gap-2 pt-1">
        <span className="text-sm text-muted-foreground">{t("managerFreeUp", { size: fmtBytes(pickedBytes) })}</span>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onClose}>{t("cancel")}</Button>
          <Button variant="destructive" size="sm" disabled={pending || picked.size === 0} onClick={() => onApply([...picked])}>
            <Scissors className="size-3.5" />
            {t("slimApply")}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
