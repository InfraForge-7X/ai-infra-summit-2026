import { asScore, TARGET_LABEL } from '../lib/format.js'
import { Card } from './ui/ui.jsx'
import styles from './RoutingHistory.module.css'

const TARGET_COLOR = {
  local: 'var(--color-local)',
  edge: 'var(--color-edge)',
  cloud: 'var(--color-cloud)',
}

/**
 * Decisions, reroutes and holds in order, newest first.
 *
 * A rail rather than a stack of cards: this is a sequence, and cards would
 * flatten it. Reroutes get a filled marker so a move is findable at a glance.
 *
 * There is no history or event model in `src/shared` — this shape is the
 * frontend's own until Tsadok defines one, which the header says out loud.
 *
 * @param {object} props
 * @param {import('../mocks/fixtures.js').RoutingEvent[]} props.events
 */
export default function RoutingHistory({ events }) {
  return (
    <Card className={styles.card}>
      <header className={styles.head}>
        <h2 className={styles.title}>Routing history</h2>
        <p className={styles.note}>Newest first · no contract yet</p>
      </header>

      {events.length === 0 ? (
        <p className={styles.empty}>
          Decisions, reroutes and failures land here in order.
        </p>
      ) : (
        <ol className={styles.rail}>
          {events.map((event) => (
            <li
              key={event.id}
              className={`${styles.event} ${event.kind === 'reroute' ? styles.marked : ''}`}
              style={{ '--event-color': TARGET_COLOR[event.target] }}
            >
              <p className={styles.time}>{event.time}</p>
              <p className={styles.headline}>
                {event.from ? (
                  <>
                    {TARGET_LABEL[event.from]} →{' '}
                    <span className={styles.target}>{TARGET_LABEL[event.target]}</span>
                  </>
                ) : (
                  <>
                    Routed to <span className={styles.target}>{TARGET_LABEL[event.target]}</span>
                  </>
                )}
              </p>
              <p className={styles.detail}>
                Score {asScore(event.score)} · {event.reason}
              </p>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}
