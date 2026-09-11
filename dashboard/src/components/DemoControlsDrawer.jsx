import Drawer from './Drawer.jsx'
import styles from './DemoControlsDrawer.module.css'

/**
 * Demo scaffolding — NOT part of the product.
 *
 * In the real system conditions change because Tsadok saturates a container or
 * throttles the network. During the demo, and during review when there is no
 * backend at all, something has to stand in for that. These controls do.
 *
 * Each button selects a canned scenario. None of them computes a routing
 * decision — they choose which pre-baked API response the page is showing.
 *
 * Removable by design: delete this component and its one line in App, and the
 * dashboard is intact. That is why it lives in a drawer rather than a bar.
 *
 * Figma node 5808:16715. Two copy slips in the design are corrected here: the
 * Conditions group is duplicated in the frame, and both it and "Change
 * Workload" carry the Workload group's description.
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {() => void} props.onClose
 * @param {(scenarioKey: string) => void} props.onSelect
 * @param {() => void} props.onRunBaseline
 * @param {string} props.current
 */
export default function DemoControlsDrawer({
  open,
  onClose,
  onSelect,
  onRunBaseline,
  current,
}) {
  /** @param {string} key */
  const choose = (key) => () => {
    onSelect(key)
    onClose()
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Demo controls"
      lede="Prototype scaffolding, not part of the product. These stand in for changes the backend will cause for real."
    >
      <Group title="Workload" hint="Start or replace what is being routed">
        <Control
          primary
          label="Start workload"
          hint="Route the current workload from scratch"
          onClick={choose('running')}
          active={current === 'running'}
        />
        <Control
          label="Reroute under pressure"
          hint="Edge saturates, the work moves and the interface changes colour"
          onClick={choose('rerouted')}
          active={current === 'rerouted'}
        />
      </Group>

      <Group title="Conditions" hint="Change infrastructure and watch routing respond">
        <Control
          label="Hold instead of move"
          hint="A better target exists but the gain is under the switching threshold"
          onClick={choose('held')}
          active={current === 'held'}
        />
        <Control
          label="Stop edge reporting"
          hint="State goes stale, so the reading is no longer trusted"
          onClick={choose('stale')}
          active={current === 'stale'}
        />
        <Control
          label="Recover everything"
          hint="Back to normal conditions"
          onClick={choose('running')}
          active={false}
        />
      </Group>

      <Group title="Failures" hint="Every failure path has its own state">
        <Control
          label="No eligible target"
          hint="Explicit routing failure, nothing dispatched"
          onClick={choose('routingFailed')}
          active={current === 'routingFailed'}
        />
        <Control
          label="Execution timeout"
          hint="Recorded as a failure, then re-evaluated"
          onClick={choose('timeout')}
          active={current === 'timeout'}
        />
        <div className={styles.pair}>
          <Control
            label="API 503"
            hint="Service unreachable"
            onClick={choose('error503')}
            active={current === 'error503'}
          />
          <Control
            label="API 422"
            hint="Workload rejected"
            onClick={choose('error422')}
            active={current === 'error422'}
          />
        </div>
        <Control
          label="API 500"
          hint="Unexpected internal error"
          onClick={choose('error500')}
          active={current === 'error500'}
        />
      </Group>

      <Group title="Comparison" hint="Adaptive routing against a fixed destination">
        <Control
          label="Run static baseline"
          hint="Pin the workload to one target for the run"
          onClick={() => {
            onRunBaseline()
            onClose()
          }}
        />
        <Control
          label="Reset everything"
          hint="Back to an empty dashboard"
          onClick={choose('idle')}
          active={current === 'idle'}
        />
      </Group>
    </Drawer>
  )
}

/**
 * @param {object} props
 * @param {string} props.title
 * @param {string} props.hint
 * @param {React.ReactNode} props.children
 */
function Group({ title, hint, children }) {
  return (
    <section className={styles.group}>
      <header className={styles.groupHead}>
        <p className={styles.groupTitle}>{title}</p>
        <p className={styles.groupHint}>{hint}</p>
      </header>
      <div className={styles.controls}>{children}</div>
    </section>
  )
}

/**
 * Every control carries a second line. "Stop edge reporting" on its own tells
 * a reviewer nothing, which is what made the earlier control bar unreadable.
 *
 * @param {object} props
 * @param {string} props.label
 * @param {string} props.hint
 * @param {() => void} props.onClick
 * @param {boolean} [props.primary]
 * @param {boolean} [props.active]
 */
function Control({ label, hint, onClick, primary = false, active = false }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[styles.control, primary ? styles.primary : '', active ? styles.active : ''].join(' ')}
    >
      <span className={styles.controlLabel}>{label}</span>
      <span className={styles.controlHint}>{hint}</span>
    </button>
  )
}
