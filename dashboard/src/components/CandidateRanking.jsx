import { asScore, TARGET_LABEL } from '../lib/format.js'
import { Card, Meter, SectionHeader, Tag } from './ui/ui.jsx'
import styles from './CandidateRanking.module.css'

/**
 * `RoutingDecision.ranked_candidates` — every target the engine evaluated,
 * in the order it sent them.
 *
 * This is the strongest evidence on the page that the frontend is not doing
 * the deciding. The list arrives ranked; this component renders that order and
 * never sorts, scores or filters it. If it called `.sort()` on the way in, the
 * ordering would have moved into React, which DoD item #8 forbids.
 *
 * Three states per row, and they are genuinely different:
 *
 *   selected    the target the decision names
 *   eligible    scored, ranked, not chosen — a real alternative
 *   ineligible  never scored, because it failed a hard constraint
 *
 * An ineligible candidate carries `score: null`, not 0. Rendering it as 0 would
 * say "scored worst", when the fact is "was never in the running", and the
 * reason it was excluded is the more useful thing to show anyway.
 *
 * @param {object} props
 * @param {import('../mocks/contracts.js').RoutingCandidate[]} props.candidates
 * @param {import('../mocks/contracts.js').ExecutionTarget} props.selected
 */
export default function CandidateRanking({ candidates, selected }) {
  if (!candidates?.length) return null

  return (
    <Card>
      <SectionHeader
        title="How the targets ranked"
        lede="Every target the Decision Engine evaluated, in the order it returned them"
      />

      <ol className={styles.list}>
        {candidates.map((candidate, index) => (
          <Row
            key={candidate.target}
            candidate={candidate}
            position={index + 1}
            isSelected={candidate.target === selected}
          />
        ))}
      </ol>

      <p className={styles.note}>
        Ranked by the engine. The dashboard displays this order and does not
        compute it.
      </p>
    </Card>
  )
}

/** Each target keeps the colour it carries everywhere else on the page. */
const TARGET_COLOR = {
  local: 'var(--color-local)',
  edge: 'var(--color-edge)',
  cloud: 'var(--color-cloud)',
}

/**
 * @param {object} props
 * @param {import('../mocks/contracts.js').RoutingCandidate} props.candidate
 * @param {number} props.position
 * @param {boolean} props.isSelected
 */
function Row({ candidate, position, isSelected }) {
  const { target, eligible, score, disqualification_reasons: disqualified } = candidate

  return (
    <li className={`${styles.row} ${isSelected ? styles.selected : ''}`}>
      <span className={styles.position} aria-hidden="true">
        {position}
      </span>

      <div className={styles.body}>
        <div className={styles.head}>
          <span className={styles.target} data-target={target}>
            {TARGET_LABEL[target]}
          </span>

          {/* The winner is named, not merely implied by being first — the top
              row is not always the selected one. Anti-flapping (§9) can hold a
              workload on a target that ranks second, and that gap between
              "highest score" and "where it is running" is the policy being
              visible rather than claimed. */}
          {isSelected ? <Tag kind="selected" /> : null}

          {!eligible ? <span className={styles.excluded}>Not eligible</span> : null}

          <span className={`${styles.score} ${eligible ? '' : styles.scoreMissing}`}>
            {asScore(score)}
          </span>
        </div>

        {eligible ? (
          <Meter
            value={score ?? 0}
            label={`${TARGET_LABEL[target]} scored ${asScore(score)} out of 1`}
            color={TARGET_COLOR[target]}
            thin
          />
        ) : (
          <p className={styles.why}>
            {disqualified.length ? disqualified.join('. ') : 'Failed a hard constraint.'}
          </p>
        )}
      </div>
    </li>
  )
}
