import { asDuration, asInt, STATUS_LABEL } from '../lib/format.js'
import { Card, MetricTile, SectionHeader, StatusTile } from './ui/ui.jsx'
import styles from './ExecutionPanel.module.css'

/**
 * Lifecycle tone for the status dot — the same three states the target card
 * uses, so one status reads the same way in both places.
 * @type {Record<string, 'ok' | 'fail' | 'idle'>}
 */
const STATUS_TONE = {
  running: 'ok',
  dispatched: 'ok',
  completed: 'ok',
  result_returned: 'ok',
  failed: 'fail',
  timeout: 'fail',
  cancelled: 'idle',
  created: 'idle',
  routing: 'idle',
}

/**
 * Execution metrics on the current target.
 *
 * `fps` is nullable in the contract — a speech workload has no frames — and
 * `asInt` renders null as an em dash. A missing reading and a zero reading
 * are different facts.
 *
 * @param {object} props
 * @param {import('../mocks/contracts.js').ExecutionResult} props.execution
 * @param {import('../mocks/contracts.js').InfrastructureState} props.targetState
 */
export default function ExecutionPanel({ execution, targetState }) {
  return (
    <Card className={styles.card}>
      <SectionHeader title="Execution" lede="On the current target" />

      <div className={styles.tiles}>
        <MetricTile label="Frames per second" value={asInt(execution.fps)} reserve={3} />
        <MetricTile
          label="Network latency"
          value={asInt(execution.network_latency_ms)}
          unit="ms"
          reserve={4}
        />
        <MetricTile label="Execution time" value={asDuration(execution.execution_time_ms)} reserve={6} />
        <MetricTile label="CPU on target" value={asInt(targetState.cpu_usage)} unit="%" reserve={3} />
        <MetricTile label="RAM on target" value={asInt(targetState.ram_usage)} unit="%" reserve={3} />
        <StatusTile
          label="Status"
          value={STATUS_LABEL[execution.status]}
          tone={STATUS_TONE[execution.status] ?? 'idle'}
        />
      </div>
    </Card>
  )
}
