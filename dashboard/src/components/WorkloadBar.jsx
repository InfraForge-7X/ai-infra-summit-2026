import { WORKLOAD_LABEL } from '../lib/format.js'
import { Chip } from './ui/ui.jsx'
import styles from './WorkloadBar.module.css'

/**
 * The WorkloadProfile currently being routed, as chips.
 *
 * Field names track `src/shared/models.py` exactly. `workload_type` is
 * translated for display only — the value itself stays lowercase.
 *
 * @param {object} props
 * @param {import('../mocks/contracts.js').WorkloadProfile} props.workload
 */
export default function WorkloadBar({ workload }) {
  return (
    <div className={styles.chips}>
      <Chip label="Workload task" value={workload.task_id.replace(/^task-/, '')} />
      <Chip label={WORKLOAD_LABEL[workload.workload_type]} value={workload.model} />
      <Chip label="Input" value={`${workload.input_size}px`} />
      <Chip
        label={`Needs ${workload.compute_requirement.toUpperCase()}`}
        value={`under ${workload.latency_requirement}`}
      />
      <Chip label="Privacy" value={workload.privacy} />
      <Chip label="Priority" value={workload.priority} />
    </div>
  )
}
