import { asInt, STATUS_LABEL } from '../lib/format.js'
import { Card, MetricTile, SectionHeader } from './ui/ui.jsx'
import styles from './ExecutionPanel.module.css'

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
        <MetricTile
          label="Execution time"
          value={asInt(execution.execution_time_ms)}
          unit="ms"
          reserve={6}
        />
        <MetricTile label="CPU on target" value={asInt(targetState.cpu_usage)} unit="%" reserve={3} />
        <MetricTile label="RAM on target" value={asInt(targetState.ram_usage)} unit="%" reserve={3} />
        <MetricTile label="Status" value={STATUS_LABEL[execution.status]} text />
      </div>
    </Card>
  )
}
