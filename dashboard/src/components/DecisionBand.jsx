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
 * @param {object} props
 * @param {import('../mocks/contracts.js').RoutingDecision} props.decision
 * @param {import('../mocks/contracts.js').ExecutionStatus} props.status
 * @param {() => void} [props.onSeeDecision]
 */
export default function DecisionBand({ decision, status, onSeeDecision }) {
  return (
    /*
     * The design spec allows exactly one moment of motion: the reroute. Keying
     * the band on the target remounts it when — and only when — the work moves,
     * so the wash animation runs on that change and on nothing else. A scenario
     * that keeps the same target (a 503, say) does not re-key, so it does not
     * flash. No effect, no timer, no state.
     */
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
        {/* The dot encodes lifecycle, not target — so its colour is fixed and
            it carries a ring to stay legible on any of the three cards. */}
        <span
          className={`${styles.dot} ${DOT_TONE[status] ? styles[DOT_TONE[status]] : ''}`}
          aria-hidden="true"
        />
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

      {/* The tick sits at the score plus the switching margin: the bar a rival
          target has to clear before AFRI-EDGE will move the work. The engine
          applies that policy; the dashboard only draws where it falls. */}
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

      {/* The card's lower half was empty. What the number is made of is worth
          more there than whitespace — and §9 names the factors, so this is
          description, not a claim about weights. */}
      <p className={styles.scoreNote}>
        Weighted across latency, available resources, network quality and
        reliability, less cost.
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
