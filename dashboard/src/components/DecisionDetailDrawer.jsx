import Drawer from './Drawer.jsx'
import styles from './DecisionDetailDrawer.module.css'

/**
 * B1 — the exact payloads behind what the dashboard is showing.
 *
 * The original design for this drawer had a candidate ranking table: all three
 * targets, their scores, and why each was rejected. That data does not exist.
 * `RoutingDecision` sets extra="forbid" and carries only task_id, target,
 * score and reasons. Tsadok's call is to leave the contract alone until
 * Hoàng's Decision Engine shows what ranking information is worth exposing,
 * and to revisit during integration.
 *
 * So this drawer shows the raw contracts instead, and says plainly what is
 * missing rather than implying the engine did not weigh alternatives.
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {() => void} props.onClose
 * @param {import('../mocks/contracts.js').RoutingDecision | null} props.decision
 * @param {import('../mocks/contracts.js').WorkloadProfile} props.workload
 * @param {import('../mocks/contracts.js').InfrastructureState} props.targetState
 * @param {import('../mocks/contracts.js').ExecutionResult | null} props.execution
 */
export default function DecisionDetailDrawer({
  open,
  onClose,
  decision,
  workload,
  targetState,
  execution,
}) {
  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Decision detail"
      lede="The exact payloads behind what the dashboard is showing."
    >
      <Payload label="RoutingDecision" value={decision ?? { error: 'no eligible target' }} />
      <Payload label="WorkloadProfile sent" value={workload} />
      <Payload label={`InfrastructureState — ${targetState.target.toUpperCase()}`} value={targetState} />
      {execution ? <Payload label="ExecutionResult" value={execution} /> : null}

      <section className={styles.gap}>
        <p className={styles.gapTitle}>No candidate ranking</p>
        <p className={styles.gapBody}>
          The contract carries only the winning target, its score and its
          reasons — so the dashboard cannot show why LOCAL and CLOUD lost. That
          comparison is what would prove the engine weighed alternatives.
          Deferred to the integration phase, once the Decision Engine shows what
          is worth exposing.
        </p>
      </section>
    </Drawer>
  )
}

/** @param {{ label: string, value: unknown }} props */
function Payload({ label, value }) {
  return (
    <section className={styles.payload}>
      <h3 className={styles.payloadLabel}>{label}</h3>
      <pre className={styles.code}>{JSON.stringify(value, null, 2)}</pre>
    </section>
  )
}
