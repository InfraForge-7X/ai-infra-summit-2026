import { useState } from 'react'

import { Button } from './ui/ui.jsx'
import Select from './ui/Select.jsx'
import Drawer from './Drawer.jsx'
import styles from './WorkloadDrawer.module.css'

/**
 * B2 — the WorkloadProfile form.
 *
 * Field names and enum values come from `src/shared/models.py` and
 * `src/shared/enums.py` exactly, so what this sends is what POST /route
 * accepts. `video_inference` is deliberately absent from the options: the enum
 * marks it legacy compatibility only.
 *
 * Selecting a speech workload is step 5 of the demo sequence in §29.6, and it
 * is also the honest test of the nullable `fps` path — speech has no frames,
 * so the metric reads as an em dash rather than zero.
 *
 * The form does not route anything. It submits a profile; the backend decides.
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {() => void} props.onClose
 * @param {import('../mocks/contracts.js').WorkloadProfile} props.workload
 * @param {(next: import('../mocks/contracts.js').WorkloadProfile) => void} props.onSubmit
 */
export default function WorkloadDrawer({ open, onClose, workload, onSubmit }) {
  const [draft, setDraft] = useState(workload)

  /** @param {string} field */
  const set = (field) => (event) => {
    const raw = event.target.value
    const numeric = field === 'input_size' || field === 'latency_requirement'
    setDraft({ ...draft, [field]: numeric ? Number(raw) : raw })
  }

  /** @param {string} field */
  const choose = (field) => (next) => setDraft({ ...draft, [field]: next })

  const asOptions = (values) => values.map((value) => ({ value }))

  const submit = (event) => {
    event.preventDefault()
    onSubmit(draft)
    onClose()
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Workload"
      lede="Sent to POST /route as a WorkloadProfile. Fields and values match src/shared."
    >
      <form className={styles.form} onSubmit={submit}>
        <Field wide label="Task ID" id="task_id">
          <input
            id="task_id"
            className={styles.input}
            value={draft.task_id}
            onChange={set('task_id')}
            required
          />
        </Field>

        <Field label="Workload type" id="workload_type">
          {/* `video_inference` is absent on purpose — the enum marks it legacy
              compatibility, not a value for new profiles. */}
          <Select
            id="workload_type"
            label="Workload type"
            value={draft.workload_type}
            options={asOptions(['real_time_video', 'speech', 'batch_inference'])}
            onChange={choose('workload_type')}
          />
        </Field>

        <Field label="Model" id="model">
          <input id="model" className={styles.input} value={draft.model} onChange={set('model')} required />
        </Field>

        <Field label="Input size (px)" id="input_size">
          <input
            id="input_size"
            type="number"
            min="1"
            className={styles.input}
            value={draft.input_size}
            onChange={set('input_size')}
          />
        </Field>

        <Field label="Latency requirement (ms)" id="latency_requirement">
          <input
            id="latency_requirement"
            type="number"
            min="1"
            className={styles.input}
            value={draft.latency_requirement}
            onChange={set('latency_requirement')}
          />
        </Field>

        <Field label="Compute requirement" id="compute_requirement">
          <Select
            id="compute_requirement"
            label="Compute requirement"
            value={draft.compute_requirement}
            options={asOptions(['cpu', 'gpu', 'any'])}
            onChange={choose('compute_requirement')}
          />
        </Field>

        <Field label="Privacy" id="privacy">
          <Select
            id="privacy"
            label="Privacy"
            value={draft.privacy}
            options={asOptions(['standard', 'sensitive', 'restricted'])}
            onChange={choose('privacy')}
          />
        </Field>

        <Field wide label="Priority" id="priority">
          <Select
            id="priority"
            label="Priority"
            value={draft.priority}
            options={asOptions(['low', 'medium', 'high', 'critical'])}
            onChange={choose('priority')}
          />
        </Field>

        <p className={styles.hint}>
          Try <strong>speech</strong> — it has no frames, so frames per second
          reads as an em dash rather than zero. A missing reading and a zero
          reading are different facts.
        </p>

        <div className={styles.actions}>
          <Button variant="primary" type="submit">
            Route this workload
          </Button>
          <Button onClick={onClose}>Cancel</Button>
        </div>
      </form>
    </Drawer>
  )
}

/**
 * @param {object} props
 * @param {string} props.label
 * @param {string} props.id
 * @param {boolean} [props.wide]
 * @param {React.ReactNode} props.children
 */
function Field({ label, id, wide = false, children }) {
  return (
    <div className={`${styles.field} ${wide ? styles.wide : ''}`}>
      <label className={styles.label} htmlFor={id}>
        {label}
      </label>
      {children}
    </div>
  )
}
