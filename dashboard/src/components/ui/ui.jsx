/**
 * Primitives shared across the dashboard. One module, one stylesheet, so the
 * design-system layer stays in a single place a reviewer can read end to end.
 *
 * Every one of these maps to a component in the Figma spec (§5 of the design
 * spec) and consumes tokens only.
 */

import { HugeiconsIcon } from '@hugeicons/react'

import { EM_DASH } from '../../lib/format.js'
import styles from './ui.module.css'

/**
 * @param {object} props
 * @param {import('@hugeicons/react').IconSvgElement} props.icon
 * @param {number} [props.size]
 * @param {number} [props.strokeWidth]
 * @param {string} [props.color]
 */
export function Icon({ icon, size = 24, strokeWidth = 1.6, color = 'currentColor' }) {
  return <HugeiconsIcon icon={icon} size={size} strokeWidth={strokeWidth} color={color} />
}

/**
 * @param {object} props
 * @param {'primary' | 'ghost'} [props.variant]
 * @param {boolean} [props.small]
 * @param {'button' | 'submit'} [props.type]  Defaults to button, so a Button
 *   inside a form does not submit it by accident.
 * @param {React.ReactNode} props.children
 * @param {() => void} [props.onClick]
 */
export function Button({ variant = 'ghost', small = false, type = 'button', children, onClick }) {
  const tone = variant === 'primary' ? styles.primary : styles.ghost
  return (
    <button
      type={type}
      onClick={onClick}
      className={[styles.button, tone, small ? styles.small : ''].join(' ')}
    >
      {children}
    </button>
  )
}

/**
 * Label + value pill, used for the WorkloadProfile summary.
 * @param {object} props
 * @param {string} props.label
 * @param {string | number} props.value
 */
export function Chip({ label, value }) {
  return (
    <span className={styles.chip}>
      <span className={styles.chipLabel}>{label}</span>
      <span className={styles.chipValue}>{value}</span>
    </span>
  )
}

/**
 * @param {object} props
 * @param {React.ReactNode} props.children
 * @param {string} [props.className]
 */
export function Card({ children, className = '' }) {
  return <section className={`${styles.card} ${className}`}>{children}</section>
}

/**
 * Only two kinds exist. Eligibility is the Decision Engine's judgement and is
 * not returned on any contract, so the dashboard cannot show "ineligible".
 * @param {object} props
 * @param {'live' | 'stale'} props.kind
 */
export function Tag({ kind }) {
  return (
    <span className={`${styles.tag} ${kind === 'stale' ? styles.tagStale : ''}`}>
      {kind === 'stale' ? 'Stale' : 'Live'}
    </span>
  )
}

/**
 * @param {object} props
 * @param {number} props.value     0–1
 * @param {boolean} [props.thin]   Thin variant for environment CPU / RAM bars
 * @param {string} [props.color]   Defaults to the live accent
 * @param {string} props.label     Accessible name
 * @param {number} [props.mark]    0–1. Draws a tick on the track — used for the
 *   switching margin, which is the design spec's one non-negotiable detail:
 *   it turns "we have anti-flapping" into something on screen. The engine
 *   applies the policy; this only draws where it sits.
 */
export function Meter({ value, thin = false, color, label, mark }) {
  const pct = Math.max(0, Math.min(1, value)) * 100
  const markPct = mark === undefined ? null : Math.max(0, Math.min(1, mark)) * 100
  return (
    <div
      className={`${styles.track} ${thin ? styles.trackThin : ''}`}
      role="meter"
      aria-label={label}
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className={styles.fill} style={{ inlineSize: `${pct}%`, '--fill-color': color }} />
      {markPct === null ? null : (
        <span className={styles.mark} style={{ insetInlineStart: `${markPct}%` }} aria-hidden="true" />
      )}
    </div>
  )
}

/**
 * A metric readout. `value` is already formatted — pass EM_DASH for missing.
 *
 * Units always arrive through `unit`, never baked into `value`, so every tile
 * renders them the same way. Mixing the two gave "73 ms" at full size next to
 * "27" with a small grey "%" hanging off it.
 *
 * @param {object} props
 * @param {string} props.label
 * @param {string} props.value
 * @param {string} [props.unit]
 * @param {boolean} [props.text]  Render at text size rather than display size
 * @param {number} [props.reserve] Digits to reserve, for values that tick live
 */
export function MetricTile({ label, value, unit, text = false, reserve }) {
  const missing = value === EM_DASH
  return (
    <div className={styles.tile}>
      <span className={styles.tileLabel}>{label}</span>
      {/* The reserved width goes on the group, so a ticking number cannot
          shove its own unit sideways. */}
      <span
        className={`${styles.tileValue} ${text ? styles.tileValueText : ''} ${reserve ? 'is-live' : ''}`}
        style={reserve ? { '--live-width': `${reserve}ch` } : undefined}
      >
        <span>{value}</span>
        {unit && !missing ? <span className={styles.tileUnit}>{unit}</span> : null}
      </span>
    </div>
  )
}

/**
 * Execution status. A word, not a quantity — so it gets text weight and a
 * lifecycle dot rather than the 24px treatment a measurement earns.
 *
 * @param {object} props
 * @param {string} props.label
 * @param {string} props.value
 * @param {'ok' | 'fail' | 'idle'} props.tone
 */
export function StatusTile({ label, value, tone }) {
  const toneClass =
    tone === 'fail' ? styles.tileStatusDotFail : tone === 'idle' ? styles.tileStatusDotIdle : ''
  return (
    <div className={styles.tile}>
      <span className={styles.tileLabel}>{label}</span>
      <span className={styles.tileStatus}>
        <span className={`${styles.tileStatusDot} ${toneClass}`} aria-hidden="true" />
        {value}
      </span>
    </div>
  )
}

/**
 * @param {object} props
 * @param {string} props.title
 * @param {string} [props.lede]
 * @param {boolean} [props.accent]  Reserved for headings that name the current
 *   target. Section titles are neutral — accent carries the decision, not
 *   the hierarchy.
 * @param {number} [props.gap]
 */
export function SectionHeader({ title, lede, accent = false, gap }) {
  return (
    <header className={styles.sectionHeader} style={gap ? { gap: `${gap}px` } : undefined}>
      <h2 className={`${styles.sectionTitle} ${accent ? styles.sectionTitleAccent : ''}`}>
        {title}
      </h2>
      {lede ? <p className={styles.sectionLede}>{lede}</p> : null}
    </header>
  )
}
