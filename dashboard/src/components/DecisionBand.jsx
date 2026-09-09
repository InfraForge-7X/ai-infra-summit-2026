import { CloudIcon, ComputerIcon, FlashIcon } from '@hugeicons/core-free-icons'

import { asScore, STATUS_LABEL, TARGET_CAPTION, TARGET_LABEL } from '../lib/format.js'
import { SWITCHING_MARGIN } from '../mocks/fixtures.js'
import { Button, Icon, Meter } from './ui/ui.jsx'
import styles from './DecisionBand.module.css'

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
 * @param {object} props
 * @param {import('../mocks/contracts.js').RoutingDecision} props.decision
 * @param {import('../mocks/contracts.js').ExecutionStatus} props.status
 * @param {() => void} [props.onSeeDecision]
 */
export default function DecisionBand({ decision, status, onSeeDecision }) {
  return (
    <div className={styles.band}>
      <TargetCard target={decision.target} status={status} />
      <ScoreCard score={decision.score} />
      <ReasonsCard reasons={decision.reasons} onSeeDecision={onSeeDecision} />
    </div>
  )
}

/**
 * @param {object} props
 * @param {import('../mocks/contracts.js').ExecutionTarget} props.target
 * @param {import('../mocks/contracts.js').ExecutionStatus} props.status
 */
function TargetCard({ target, status }) {
  return (
    <article className={styles.targetCard}>
      <p className={styles.targetLabel}>Running on</p>

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
        <span className={styles.dot} aria-hidden="true" />
        {STATUS_LABEL[status]}
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

      <Meter value={score} label={`Routing score ${asScore(score)} out of 1`} />

      <p className={styles.meterFoot}>
        <span>0</span>
        {/* The switching margin is the anti-flapping policy from §9, shown so
            it is visible rather than claimed. Displayed only — never applied. */}
        <span>switching margin {SWITCHING_MARGIN.toFixed(2)}</span>
        <span>1</span>
      </p>
    </article>
  )
}

/**
 * `reasons` is a variable-length array with a minimum of one. Do not assume
 * four — the layout has to hold for one.
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
