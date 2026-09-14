import Drawer from './Drawer.jsx'
import styles from './DecisionDetailDrawer.module.css'

/**
 * B1 — the exact payloads behind what the dashboard is showing.
 *
 * This drawer used to carry a note saying the contract had no candidate
 * ranking, so the dashboard could not show why the other targets lost. #21
 * added `ranked_candidates` and that note is gone: the ranking is now on the
 * page itself, and what lives here is the part too detailed for it — the
 * per-dimension `score_breakdown` behind each candidate's single number.
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {() => void} props.onClose
 * @param {import('../mocks/contracts.js').RoutingDecision | null} props.decision
 * @param {import('../mocks/contracts.js').WorkloadProfile} props.workload
 * @param {import('../mocks/contracts.js').InfrastructureState} [props.targetState]
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
  // Only candidates that were actually scored have dimensions to show; an
  // ineligible target never got that far.
  const breakdowns = (decision?.ranked_candidates ?? [])
    .filter((candidate) => Object.keys(candidate.score_breakdown ?? {}).length)
    .map((candidate) => [candidate.target, candidate.score_breakdown])

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Decision detail"
      lede="The exact payloads behind what the dashboard is showing."
    >
      <Payload label="RoutingDecision" value={decision ?? { error: 'no eligible target' }} />
      <Payload label="WorkloadProfile sent" value={workload} />
      {/* Absent for the moment between the page loading and the first poll
          returning. A drawer that crashes the app rather than showing one
          fewer payload is a bad trade. */}
      {targetState ? (
        <Payload
          label={`InfrastructureState — ${targetState.target.toUpperCase()}`}
          value={targetState}
        />
      ) : null}
      {execution ? <Payload label="ExecutionResult" value={execution} /> : null}

      {breakdowns.length ? (
        <section className={styles.gap}>
          <p className={styles.gapTitle}>Score breakdown</p>
          <p className={styles.gapBody}>
            The dimensions behind each candidate&rsquo;s single number. The keys
            are the engine&rsquo;s — scoring is configurable, so this renders
            whatever arrives rather than a fixed set.
          </p>
          {breakdowns.map(([target, breakdown]) => (
            <Payload key={target} label={target.toUpperCase()} value={breakdown} />
          ))}
        </section>
      ) : null}
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
