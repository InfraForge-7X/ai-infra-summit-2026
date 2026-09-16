import { Button } from './ui/ui.jsx'
import styles from './Notice.module.css'

/**
 * Empty, pending and failure states.
 *
 * NOT DESIGNED. None of the failure states exist in the Figma frames, so this
 * is built from the Notice pattern in the design spec using the token
 * `--color-fail`, which is itself carried over from the HTML prototype.
 * Flagged in the PR as awaiting design.
 *
 * Copy rules, from the spec's copy deck: errors say what to do next and never
 * apologise; an empty screen is an invitation to act.
 *
 * @param {object} props
 * @param {string} props.heading
 * @param {string} props.body
 * @param {'neutral' | 'bad'} [props.tone]
 * @param {string} [props.actionLabel]
 * @param {() => void} [props.onAction]
 * @param {string} [props.stamp]  e.g. last-known-state time on a 503
 */
export default function Notice({
  heading,
  body,
  tone = 'neutral',
  actionLabel,
  onAction,
  stamp,
}) {
  return (
    <section className={`${styles.notice} ${tone === 'bad' ? styles.bad : ''}`} role={tone === 'bad' ? 'alert' : undefined}>
      <h2 className={styles.heading}>{heading}</h2>
      <p className={styles.body}>{body}</p>

      {actionLabel || stamp ? (
        <div className={styles.actions}>
          {actionLabel ? (
            <Button variant="primary" onClick={onAction}>
              {actionLabel}
            </Button>
          ) : null}
          {stamp ? <span className={styles.stamp}>{stamp}</span> : null}
        </div>
      ) : null}
    </section>
  )
}
