import { CloudIcon, ComputerIcon, FlashIcon } from '@hugeicons/core-free-icons'

import { asScore, STATUS_LABEL, TARGET_CAPTION, TARGET_LABEL } from '../lib/format.js'
import { SWITCHING_MARGIN } from '../mocks/fixtures.js'
import { Button, Icon, Meter } from './ui/ui.jsx'
import styles from './DecisionBand.module.css'

/**
 * Lifecycle tones for the status dot. Running is the healthy steady state;
 * the failure states are the only ones that change colour.
 * @type {Partial<Record<import('../mocks/contracts.js').ExecutionStatus, string>>}
 */
const DOT_TONE = {
  failed: 'fail',
  timeout: 'fail',
  cancelled: 'idle',
  created: 'idle',
  routing: 'idle',
}

/** @type {Record<import('../mocks/contracts.js').ExecutionTarget, any>} */
const TARGET_ICON = {
  local: ComputerIcon,
  edge: FlashIcon,
  cloud: CloudIcon,
}

/**
 * The three cards that answer: where is it running, how confident was the
 * decision, and why. Everything here is read off a RoutingDecision — the
 * frontend computes none of it.
 *
 * `status` is optional because the confirmed POST /route contract returns a
 * RoutingDecision, not an ExecutionResult. Live mode therefore shows a neutral
 * "Decision returned" state until an execution-status contract exists.
 *
 * @param {object} props
 * @param {import('../mocks/contracts.js').RoutingDecision} props.decision
 * @param {import('../mocks/contracts.js').ExecutionStatus} [props.status]
 * @param {() => void} [props.onSeeDecision]
 */
export default function DecisionBand({ decision, status, onSeeDecision }) {
  return (
    <div className={styles.band} key={decision.target}>
      <TargetCard target={decision.target} status={status} />
      <ScoreCard score={decision.score} />
      <ReasonsCard reasons={decision.reasons} onSeeDecision={onSeeDecision} />
    </div>
  )
}

/**
 * @param {object} props
 * @param {import('../mocks/contracts.js').ExecutionTarget} props.target
 * @param {import('../mocks/contracts.js').ExecutionStatus} [props.status]
 */
function TargetCard({ target, status }) {
  const statusLabel = status ? STATUS_LABEL[status] : 'Decision returned'

  return (
    <article className={styles.targetCard}>
      <p className={styles.targetLabel}>Selected target</p>

      <div className={styles.targetBody}>
        <div className={styles.targetName}>
          <span className={styles.glyph}>
            <Icon icon={TARGET_ICON[target]} size={24} color="var(--accent)" />
          </span>
          <span className={styles.name}>{TARGET_LABEL[target]}</span>
        </div>
        <p className={styles.caption}>{TARGET_CAPTION[target]}</p>
      </div>

      <p className={styles.status}>
        <span
          className={`${styles.dot} ${status && DOT_TONE[status] ? styles[DOT_TONE[status]] : ''}`}
          aria-hidden="true"
        />
        {statusLabel}
      </p>
    </article>
  )
}

/** @param {{ score: number }} props */
function ScoreCard({ score }) {
  return (
    <article className={styles.card}>
      <h3 className={styles.cardTitle}>Routing score</h3>

      <p className={styles.score}>
        {asScore(score)}
        <span className={styles.scoreUnit}>/1.00</span>
      </p>

      <Meter
        value={score}
        mark={score + SWITCHING_MARGIN}
        label={`Routing score ${asScore(score)} out of 1`}
      />

      <p className={styles.meterFoot}>
        <span>0</span>
        <span className={styles.margin}>
          <span className={styles.marginTick} aria-hidden="true" />
          switching margin {SWITCHING_MARGIN.toFixed(2)}
        </span>
        <span>1</span>
      </p>

      <p className={styles.scoreNote}>
        Weighted across latency, available resources, network quality and
        reliability, less cost.
      </p>
    </article>
  )
}

/**
 * `reasons` is a variable-length array with a minimum of one.
 *
 * @param {object} props
 * @param {string[]} props.reasons
 * @param {() => void} [props.onSeeDecision]
 */
function ReasonsCard({ reasons, onSeeDecision }) {
  return (
    <article className={styles.card}>
      <h3 className={styles.cardTitle}>Why this target</h3>

      <ul className={styles.reasons}>
        {reasons.map((reason) => (
          <li key={reason} className={styles.reason}>
            <span className={styles.bullet} aria-hidden="true" />
            {reason}
          </li>
        ))}
      </ul>

      <div className={styles.reasonsAction}>
        <Button onClick={onSeeDecision}>See decision</Button>
      </div>
    </article>
  )
}
