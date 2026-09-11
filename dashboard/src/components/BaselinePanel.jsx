import { asInt, TARGET_LABEL } from '../lib/format.js'
import { Card, SectionHeader } from './ui/ui.jsx'
import styles from './BaselinePanel.module.css'

/**
 * §19 — static baseline against adaptive routing, same workload and conditions.
 *
 * Both states are designed: empty in 5798:2, populated in 5808:17345.
 *
 * §29.7 forbids claiming an improvement before measurement, so this panel
 * reports two sets of numbers and draws no conclusion. No percentage, no
 * "2x faster", no green arrow.
 *
 * @param {object} props
 * @param {import('../mocks/scenarios.js').Baseline | null} props.baseline
 * @param {import('../mocks/contracts.js').ExecutionResult | null} props.execution
 * @param {number} props.reroutes
 */
export default function BaselinePanel({ baseline, execution, reroutes }) {
  if (!baseline) {
    return (
      <Card>
        <SectionHeader
          title="Static baseline"
          lede="Same workload, fixed destination, no re-evaluation"
          accent
        />
        <p className={styles.empty}>
          Run the static baseline to compare a fixed destination against adaptive
          routing under the same conditions. No improvement is claimed until both
          runs are measured.
        </p>
      </Card>
    )
  }

  return (
    <Card>
      <SectionHeader
        title="Static baseline vs adaptive"
        lede="Identical workload and conditions"
        accent
      />

      <div className={styles.columns}>
        <div className={styles.column}>
          <h3 className={styles.columnTitle}>
            Static — pinned to {TARGET_LABEL[baseline.target].toLowerCase()}
          </h3>
          <Row label="Frames per second" value={asInt(baseline.fps)} />
          <Row label="Network latency" value={`${asInt(baseline.network_latency_ms)} ms`} />
          <Row label="Reroutes" value={asInt(baseline.reroutes)} />
          <Row label="Failed frames" value={asInt(baseline.failed_frames)} />
        </div>

        <div className={styles.column}>
          <h3 className={`${styles.columnTitle} ${styles.adaptive}`}>Adaptive — AFRI-EDGE</h3>
          <Row label="Frames per second" value={asInt(execution?.fps)} />
          <Row label="Network latency" value={`${asInt(execution?.network_latency_ms)} ms`} />
          <Row label="Reroutes" value={asInt(reroutes)} />
          <Row label="Failed frames" value={asInt(0)} />
        </div>
      </div>

      <p className={styles.note}>
        Demonstration values only. Real figures come from the controlled scenarios
        in §10 and §19 of the blueprint.
      </p>
    </Card>
  )
}

/** @param {{ label: string, value: string }} props */
function Row({ label, value }) {
  return (
    <div className={styles.row}>
      <span className={styles.rowLabel}>{label}</span>
      <span className={styles.rowValue}>{value}</span>
    </div>
  )
}
