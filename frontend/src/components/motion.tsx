import type { ReactNode } from "react"
import { motion, useReducedMotion, type Variants } from "motion/react"
import NumberFlow from "@number-flow/react"

import i18n, { fmtInt } from "@/lib/i18n"

// Soft "out" curve top dashboards use (Vercel/Linear) — typed as a 4-tuple so
// motion's Easing type accepts it.
const easeOut: [number, number, number, number] = [0.22, 1, 0.36, 1]

// Entrance: children fade + rise; the parent staggers them, so a grid reads as
// settling into place rather than popping.
const fadeUp: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: easeOut } },
}

const staggerParent: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05 } },
}

/** Grid/row wrapper: its <FadeItem> children animate in with a slight stagger on
 *  mount. Collapses to a plain <div> when the OS asks to reduce motion. */
export function Stagger({ className, children }: { className?: string; children: ReactNode }) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div className={className} variants={staggerParent} initial="hidden" animate="show">
      {children}
    </motion.div>
  )
}

/** One staggered item — use as a direct child of <Stagger>. */
export function FadeItem({ className, children }: { className?: string; children: ReactNode }) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div className={className} variants={fadeUp}>
      {children}
    </motion.div>
  )
}

/** Animated integer counter — rolls to its value on mount and on change, with
 *  grouping matched to fmtInt (Intl ru-RU / en-US). Static fmtInt under reduced
 *  motion. Pass plain integers only — durations / % / decimals keep the string
 *  path, which NumberFlow would otherwise strip of its units. */
export function AnimatedInt({ value, className }: { value: number; className?: string }) {
  const reduce = useReducedMotion()
  if (reduce) return <span className={className}>{fmtInt(value)}</span>
  const locale = i18n.language?.startsWith("ru") ? "ru-RU" : "en-US"
  return <NumberFlow value={value} locales={locale} className={className} />
}
