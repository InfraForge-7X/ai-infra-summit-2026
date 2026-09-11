import { asInt, TARGET_LABEL } from '../lib/format.js'
import { Card, SectionHeader } from './ui/ui.jsx'
import styles from './BaselinePanel.module.css'

/**
 * §19 — static baseline against adaptive routing, same workload and conditions.
 *
 * Both states are designed: empty in 5798:2, populated in 5808:17345.
 *
 * Laid out as one table rather than two stacked boxes. Side-by-side lists make
 * the reader hold a number in their head and hunt for its partner; a row puts
 * both values on the same line, which is where the comparison actually happens.
 * It is also genuinely tabular data, so a real <table> gives screen readers the
 * row and column association for free.
 *
 * §29.7 forbids claiming an improvement before measurement, so this reports two
 * sets of numbers and draws no conclusion — no percentage, no delta column, no
 * arrows. The reader compares; the dashboard does not argue.
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
        />
        <p className={styles.empty}>
          Run the static baseline to compare a fixed destination against adaptive
          routing under the same conditions. No improvement is claimed until both
          runs are measured.
        </p>
      </Card>
    )
  }

  const rows = [
    {
      label: 'Frames per second',
      unit: '',
      staticValue: asInt(baseline.fps),
      adaptiveValue: asInt(execution?.fps),
    },
    {
      label: 'Network latency',
      unit: 'ms',
      staticValue: asInt(baseline.network_latency_ms),
      adaptiveValue: asInt(execution?.network_latency_ms),
    },
    {
      label: 'Reroutes',
      unit: '',
      staticValue: asInt(baseline.reroutes),
      adaptiveValue: asInt(reroutes),
    },
    {
      label: 'Failed frames',
      unit: '',
      staticValue: asInt(baseline.failed_frames),
      adaptiveValue: asInt(0),
    },
  ]

  return (
    <Card>
      <SectionHeader
        title="Static baseline vs adaptive"
        lede="Identical workload and conditions"
      />

      <div className={styles.scroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col" className={styles.metricHead}>
                Metric
              </th>
              <th scope="col" className={styles.runHead}>
                Static
                <span className={styles.runNote}>
                  pinned to {TARGET_LABEL[baseline.target]}
                </span>
              </th>
              <th scope="col" className={`${styles.runHead} ${styles.adaptive}`}>
                Adaptive
                <span className={styles.runNote}>AFRI-EDGE</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th scope="row" className={styles.metric}>
                  {row.label}
                </th>
                <Value value={row.staticValue} unit={row.unit} />
                <Value value={row.adaptiveValue} unit={row.unit} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className={styles.note}>
        Demonstration values only. Real figures come from the controlled scenarios
        in §10 and §19 of the blueprint.
      </p>
    </Card>
  )
}

/** @param {{ value: string, unit: string }} props */
function Value({ value, unit }) {
  return (
    <td className={styles.value}>
      {value}
      {unit ? <span className={styles.unit}>{unit}</span> : null}
    </td>
  )
}
