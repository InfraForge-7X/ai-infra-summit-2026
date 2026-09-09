import { Button } from './ui/ui.jsx'
import styles from './GuideStrip.module.css'

/**
 * Demo scaffolding: says what just happened and offers the next step.
 *
 * This is not part of the product. It exists so a judge — or a reviewer with
 * no backend — can follow the demo sequence without narration. Deleting this
 * component and its one line in App leaves the dashboard intact.
 *
 * @param {object} props
 * @param {string} props.heading
 * @param {string} props.body
 * @param {string} props.actionLabel
 * @param {() => void} [props.onAction]
 */
export default function GuideStrip({ heading, body, actionLabel, onAction }) {
  return (
    <section className={styles.strip}>
      <div className={styles.copy}>
        <p className={styles.heading}>{heading}</p>
        <p className={styles.body}>{body}</p>
      </div>
      <Button variant="primary" onClick={onAction}>
        {actionLabel}
      </Button>
    </section>
  )
}
