import {
  asInt,
  asLatency,
  asOneDecimal,
  asPercent,
  isStale,
  TARGET_LABEL,
  timeAgo,
} from '../lib/format.js'
import { ADAPTERS } from '../mocks/fixtures.js'
import { Meter, SectionHeader, Tag } from './ui/ui.jsx'
import styles from './EnvironmentsPanel.module.css'

/** Architecture order, left to right. Position carries meaning as well as colour. */
const ORDER = /** @type {const} */ (['local', 'edge', 'cloud'])

const TARGET_COLOR = {
  local: 'var(--color-local)',
  edge: 'var(--color-edge)',
  cloud: 'var(--color-cloud)',
}

/**
 * One card per execution target: current state and how fresh the reading is.
 *
 * @param {object} props
 * @param {Record<import('../mocks/contracts.js').ExecutionTarget,
 *   import('../mocks/contracts.js').InfrastructureState>} props.states
 * @param {import('../mocks/contracts.js').ExecutionTarget} props.chosen
 */
export default function EnvironmentsPanel({ states, chosen }) {
  return (
    <section className={styles.panel}>
      <div className={styles.head}>
        <SectionHeader
          title="Environments"
          lede="State per target, and how fresh each reading is"
          gap={7}
        />
      </div>

      <div className={styles.grid}>
        {ORDER.map((target) => (
          <EnvironmentCard
            key={target}
            state={states[target]}
            chosen={target === chosen}
            adapter={ADAPTERS[target]}
          />
        ))}
      </div>
    </section>
  )
}

/**
 * @param {object} props
 * @param {import('../mocks/contracts.js').InfrastructureState} props.state
 * @param {boolean} props.chosen
 * @param {string} [props.adapter]  Optional execution provider, e.g. SiMa.ai
 */
function EnvironmentCard({ state, chosen, adapter }) {
  const stale = isStale(state.timestamp)
  const color = TARGET_COLOR[state.target]

  return (
    <article className={`${styles.card} ${chosen ? styles.chosen : ''}`}>
      <div className={styles.cardHead}>
        <div className={styles.identity}>
          <p className={styles.name}>
            {TARGET_LABEL[state.target]}
            {/* Sponsor adapters are capabilities, not dependencies (§29.5).
                The label says where execution would happen; it changes no
                routing behaviour. */}
            {adapter ? <span className={styles.adapter}>via {adapter}</span> : null}
          </p>
          <p className={styles.fresh}>{timeAgo(state.timestamp)}</p>
        </div>
        {/* Only live and stale exist. Ineligibility is the engine's judgement
            and is not carried on InfrastructureState. */}
        {chosen ? <Tag kind="live" /> : null}
        {!chosen && stale ? <Tag kind="stale" /> : null}
      </div>

      <dl className={styles.rows}>
        <BarRow label="CPU" value={asPercent(state.cpu_usage)} ratio={state.cpu_usage / 100} color={color} />
        <BarRow label="RAM" value={asPercent(state.ram_usage)} ratio={state.ram_usage / 100} color={color} />
        <Row label="GPU" value={state.gpu_available ? 'available' : 'none'} muted={!state.gpu_available} />
        <Row label="Latency" value={asLatency(state.latency_ms)} />
        <Row label="Bandwidth" value={`${asInt(state.bandwidth_mbps)} Mbps`} />
        <Row label="Packet loss" value={`${asOneDecimal(state.packet_loss)}%`} />
        <Row label="Queue" value={asInt(state.queue)} />
      </dl>
    </article>
  )
}

/** @param {{ label: string, value: string, muted?: boolean }} props */
function Row({ label, value, muted = false }) {
  return (
    <div className={styles.row}>
      <dt className={styles.rowLabel}>{label}</dt>
      <dd className={`${styles.rowValue} ${muted ? styles.rowValueMuted : ''}`}>{value}</dd>
    </div>
  )
}

/** @param {{ label: string, value: string, ratio: number, color: string }} props */
function BarRow({ label, value, ratio, color }) {
  return (
    <div className={styles.barRow}>
      <div className={styles.row}>
        <dt className={styles.rowLabel}>{label}</dt>
        <dd className={styles.rowValue}>{value}</dd>
      </div>
      <Meter thin value={ratio} color={color} label={`${label} usage`} />
    </div>
  )
}
