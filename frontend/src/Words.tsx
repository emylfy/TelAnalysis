import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { AtSign, Cloud, Copy, Library, Quote, Type } from "lucide-react"

import { api, wordcloudUrl, type Sel } from "@/lib/api"
import { fmtInt } from "@/lib/i18n"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { BarsH } from "@/components/charts"
import { RankTable } from "@/components/rank-table"
import { WordCloud } from "@/components/wordcloud"
import { UserCombobox } from "@/components/user-combobox"
import { TabError, TabLoading } from "@/components/loading"
import { Section } from "@/components/section"
import { Collapsible } from "@/components/collapsible"
import { Stat } from "@/components/stat"
import { SentimentBlock } from "@/Sentiment"

// MTLD stabilizes only with a few hundred tokens; below this it reads 0.0 and
// just pads the table with deleted/one-line accounts.
const VOCAB_MIN_TOKENS = 500
const VOCAB_TOP = 20

export function Words({ path, sel }: { path: string; sel: Sel }) {
  const { t } = useTranslation()
  const [n, setN] = useState<2 | 3>(2)
  // word-cloud participant filter ("" = whole chat)
  const [cloudUid, setCloudUid] = useState("")
  const k = [path, sel.chat, sel.from, sel.to]
  const on = !!sel.chat

  const words = useQuery({ queryKey: ["words", ...k], queryFn: () => api.words(path, sel), enabled: on })
  const phrases = useQuery({ queryKey: ["phrases", ...k, n], queryFn: () => api.phrases(path, sel, n), enabled: on })

  const w = words.data
  if (words.isLoading) return <TabLoading />
  if (words.isError) return <TabError onRetry={words.refetch} />
  if (!w) return null

  // Vocabulary richness (MTLD) is noise below a token floor and explodes to
  // hundreds of rows in big groups — sort by verbosity, keep the significant
  // ones, but fall back to everyone for small chats where nobody clears the bar.
  const vocabSorted = [...w.users].sort((a, b) => b.total_tokens - a.total_tokens)
  const vocabSignificant = vocabSorted.filter((u) => u.total_tokens >= VOCAB_MIN_TOKENS)
  const vocabUsers = vocabSignificant.length >= 2 ? vocabSignificant : vocabSorted

  // Per-participant word cloud: pick a user to render only their cloud, "Whole
  // chat" by default. Hidden for <2 participants (saved messages, 1-on-1 bots),
  // where a per-user cloud equals the chat-wide one. `cloudUser` falls back to
  // whole-chat when the selected id isn't in this chat (e.g. after switching).
  const cloudUsers = [...w.users].sort((a, b) => b.msg_count - a.msg_count)
  const cloudUser = cloudUsers.some((u) => u.user_id === cloudUid) ? cloudUid : ""

  return (
    <div className="space-y-8 pt-2">
      <Section
        title={t("wordcloud")}
        hint={t("wordcloudHint")}
        icon={Cloud}
        action={
          cloudUsers.length >= 2 ? (
            <UserCombobox users={cloudUsers} value={cloudUser} onChange={setCloudUid} allLabel={t("wholeChat")} />
          ) : undefined
        }
      >
        <WordCloud src={wordcloudUrl(path, sel.chat, { user: cloudUser || undefined })} alt={t("wordcloud")} />
      </Section>

      {w.chat_top_words.length > 0 && (
        <Section title={t("topWords")} hint={t("topWordsHint")} icon={Type}>
          <RankTable color="var(--chart-1)" max={15} rows={w.chat_top_words.map(([word, c]) => ({ label: word, value: c }))} />
          {w.chat_top_words.length > 15 && (
            <Collapsible label={t("showAll", { n: w.chat_top_words.length })}>
              <PairsTable rows={w.chat_top_words} />
            </Collapsible>
          )}
        </Section>
      )}

      <Section title={t("phrases")} hint={t("phrasesHint")} icon={Quote}>
        <div className="flex items-center rounded-lg border border-border bg-card p-0.5 w-fit">
          {([2, 3] as const).map((v) => (
            <button
              key={v}
              onClick={() => setN(v)}
              className={`rounded-md px-3 py-1 text-sm transition-colors ${
                n === v ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {v === 2 ? t("bigrams") : t("trigrams")}
            </button>
          ))}
        </div>
        {phrases.isLoading ? (
          // Distinguish "still computing" from "no phrases" — for big chats the
          // query lags and a bare empty state read as a false "Нет данных".
          <Skeleton className="h-72 w-full" />
        ) : phrases.data && phrases.data.phrases.length > 0 ? (
          <>
            <Card className="border-border bg-card p-3">
              <BarsH data={phrases.data.phrases.slice(0, 20)} color="var(--chart-4)" />
            </Card>
            {phrases.data.phrases.length > 20 && (
              <Collapsible label={t("showAll", { n: phrases.data.phrases.length })}>
                <PairsTable rows={phrases.data.phrases} />
              </Collapsible>
            )}
          </>
        ) : (
          <div className="text-sm text-muted-foreground">{t("noData")}</div>
        )}
      </Section>

      {vocabUsers.length > 0 && (
        <Section title={t("vocabulary")} hint={t("vocabHint")} icon={Library}>
          {/* MTLD needs enough tokens to be meaningful, so a 509-person chat dumps
              hundreds of rows with MTLD 0.0 — keep only participants past a token
              floor, show the most verbose first, the rest behind a disclosure. */}
          <VocabTable rows={vocabUsers.slice(0, VOCAB_TOP)} />
          {vocabUsers.length > VOCAB_TOP && (
            <Collapsible label={t("showAll", { n: vocabUsers.length })}>
              <Card className="max-h-96 overflow-auto border-border bg-card">
                <VocabTable rows={vocabUsers} flush />
              </Card>
            </Collapsible>
          )}
        </Section>
      )}

      {(w.emails.length > 0 || w.phones.length > 0) && (
        <Section title={t("contacts")} hint={t("contactsHint")} icon={AtSign}>
          <div className="grid grid-cols-2 gap-3 sm:max-w-md">
            <Stat label={t("emailsN")} value={fmtInt(w.emails.length)} />
            <Stat label={t("phonesN")} value={fmtInt(w.phones.length)} />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:max-w-2xl">
            {w.emails.length > 0 && <ContactList label={t("showEmails")} items={w.emails} />}
            {w.phones.length > 0 && <ContactList label={t("showPhones")} items={w.phones} />}
          </div>
        </Section>
      )}

      <SentimentBlock path={path} sel={sel} />
    </div>
  )
}

/** Disclosure with the actual e-mails / phones (not just a count) and a
 *  copy-all button. Data is local to this machine, so showing it is safe. */
function ContactList({ label, items }: { label: string; items: string[] }) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(items.join("\n"))
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable (e.g. non-secure context) — ignore */
    }
  }
  return (
    <Collapsible label={`${label} (${fmtInt(items.length)})`}>
      <Card className="max-h-72 overflow-auto border-border bg-card">
        <div className="sticky top-0 flex items-center justify-end border-b border-border bg-card px-3 py-1.5">
          <button
            type="button"
            onClick={copy}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <Copy className="size-3.5" /> {copied ? t("copied") : t("copy")}
          </button>
        </div>
        <ul className="text-sm">
          {items.map((v, i) => (
            <li key={i} className="select-all border-b border-border/60 px-4 py-1.5 font-mono text-foreground/90 last:border-0">
              {v}
            </li>
          ))}
        </ul>
      </Card>
    </Collapsible>
  )
}

/** Per-user vocabulary-richness table (tokens / unique / MTLD). `flush` drops the
 *  outer Card so it can sit inside the scrollable "Show all" disclosure. */
function VocabTable({ rows, flush = false }: { rows: { user_id: string; name: string; total_tokens: number; unique_tokens: number; mtld: number }[]; flush?: boolean }) {
  const { t } = useTranslation()
  const table = (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
          <th className="px-4 py-2 font-semibold">{t("user")}</th>
          <th className="px-4 py-2 text-right font-semibold">{t("totalTokens")}</th>
          <th className="px-4 py-2 text-right font-semibold">{t("uniqueTokens")}</th>
          <th className="px-4 py-2 text-right font-semibold">{t("mtld")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((u) => (
          <tr key={u.user_id} className="border-b border-border/60 last:border-0">
            <td className="px-4 py-2 font-medium">{u.name}</td>
            <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(u.total_tokens)}</td>
            <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmtInt(u.unique_tokens)}</td>
            <td className="px-4 py-2 text-right tabular-nums">{u.mtld.toFixed(1)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
  return flush ? table : <Card className="overflow-hidden border-border bg-card">{table}</Card>
}

/** Simple [string, number] table — used by the "Show all" disclosures. */
function PairsTable({ rows }: { rows: [string, number][] }) {
  return (
    <Card className="max-h-96 overflow-auto border-border bg-card">
      <table className="w-full text-sm">
        <tbody>
          {rows.map(([w, c], i) => (
            <tr key={i} className="border-b border-border/60 last:border-0">
              <td className="px-4 py-1.5">{w}</td>
              <td className="px-4 py-1.5 text-right tabular-nums text-muted-foreground">{fmtInt(c)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  )
}
