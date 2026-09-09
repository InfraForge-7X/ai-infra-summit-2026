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
 * @param {React.ReactNode} props.children
 * @param {() => void} [props.onClick]
 */
export function Button({ variant = 'ghost', small = false, children, onClick }) {
  const tone = variant === 'primary' ? styles.primary : styles.ghost
  return (
    <button
      type="button"
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
 */
export function Meter({ value, thin = false, color, label }) {
  const pct = Math.max(0, Math.min(1, value)) * 100
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
    </div>
  )
}

/**
 * A metric readout. `value` is already formatted — pass EM_DASH for missing.
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
      <span className={`${styles.tileValue} ${text ? styles.tileValueText : ''}`}>
        <span className={reserve ? 'is-live' : ''} style={reserve ? { '--live-width': `${reserve}ch` } : undefined}>
          {value}
        </span>
        {unit && !missing ? <span className={styles.tileUnit}>{unit}</span> : null}
      </span>
    </div>
  )
}

/**
 * @param {object} props
 * @param {string} props.title
 * @param {string} [props.lede]
 * @param {boolean} [props.accent]  Tint the title with the live accent
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
