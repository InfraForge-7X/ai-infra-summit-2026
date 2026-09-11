import { asScore, TARGET_LABEL } from '../lib/format.js'
import { Card } from './ui/ui.jsx'
import styles from './RoutingHistory.module.css'

const TARGET_COLOR = {
  local: 'var(--color-local)',
  edge: 'var(--color-edge)',
  cloud: 'var(--color-cloud)',
}

/**
 * Decisions, reroutes, holds and failures in order, newest first.
 *
 * A rail rather than a stack of cards: this is a sequence, and cards would
 * flatten it. Reroutes and failures get a filled marker, so the two moments
 * that matter are findable at a glance.
 *
 * There is no history or event model in `src/shared`. Tsadok confirmed the
 * shape stays local and provisional for now, which the header says out loud.
 *
 * @param {object} props
 * @param {import('../mocks/fixtures.js').RoutingEvent[]} props.events
 */
export default function RoutingHistory({ events }) {
  return (
    <Card className={styles.card}>
      <header className={styles.head}>
        <h2 className={styles.title}>Routing history</h2>
        <p className={styles.meta}>Newest first</p>
        {/* A caveat, not a link. It was accent-coloured, which read as one. */}
        <p className={styles.provisional}>no contract yet</p>
      </header>

      {events.length === 0 ? (
        <p className={styles.empty}>
          Decisions, reroutes, holds and failures land here in order.
        </p>
      ) : (
        <ol className={styles.rail}>
          {events.map((event) => (
            <li
              key={event.id}
              className={[
                styles.event,
                event.kind === 'reroute' || event.kind === 'failure' ? styles.marked : '',
              ].join(' ')}
              style={{ '--event-color': eventColor(event) }}
            >
              <p className={styles.headline}>{headline(event)}</p>
              <p className={styles.detail}>
                <span className={styles.time}>{event.time}</span>
                {detail(event)}
              </p>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

/** @param {import('../mocks/fixtures.js').RoutingEvent} event */
function eventColor(event) {
  if (event.kind === 'failure') return 'var(--color-fail)'
  // A hold keeps its target's colour — it is a decision about that target.
  // Greying it read as disabled, when it is in fact the switching policy
  // working. The hollow marker already says nothing moved.
  return TARGET_COLOR[event.target]
}

/** @param {import('../mocks/fixtures.js').RoutingEvent} event */
function headline(event) {
  const target = <span className={styles.target}>{TARGET_LABEL[event.target]}</span>

  if (event.kind === 'reroute' && event.from) {
    return (
      <>
        {TARGET_LABEL[event.from]} → {target}
      </>
    )
  }
  if (event.kind === 'hold') return <>Held on {target}</>
  if (event.kind === 'failure') return <>Routing failed</>
  return <>Routed to {target}</>
}

/** @param {import('../mocks/fixtures.js').RoutingEvent} event */
function detail(event) {
  if (event.kind === 'failure') return event.reason
  return (
    <>
      <span className={styles.score}>{asScore(event.score)}</span>
      {event.reason}
    </>
  )
}
