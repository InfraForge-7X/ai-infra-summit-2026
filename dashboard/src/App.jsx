import { useEffect, useState } from 'react'

import * as api from './api/client.js'
import DecisionBand from './components/DecisionBand.jsx'
import EnvironmentsPanel from './components/EnvironmentsPanel.jsx'
import ExecutionPanel from './components/ExecutionPanel.jsx'
import GuideStrip from './components/GuideStrip.jsx'
import RoutingHistory from './components/RoutingHistory.jsx'
import TopBar from './components/TopBar.jsx'
import WorkloadBar from './components/WorkloadBar.jsx'
import { workload } from './mocks/fixtures.js'
import { Button, SectionHeader } from './components/ui/ui.jsx'
import styles from './App.module.css'

/**
 * AFRI-EDGE routing control.
 *
 * One screen. Navigation would hide the reroute, and the reroute is the
 * product. Drawers are state, not routes — there is no router in this app.
 *
 * The execution target on `data-target` comes from the RoutingDecision and
 * nothing else. This component never scores, ranks or chooses; it renders
 * what the Routing API decided. (DoD item #8.)
 */
export default function App() {
  const [decision, setDecision] = useState(/** @type {any} */ (null))
  const [states, setStates] = useState(/** @type {any} */ (null))
  const [execution, setExecution] = useState(/** @type {any} */ (null))
  const [history, setHistory] = useState(/** @type {any[]} */ ([]))

  useEffect(() => {
    let cancelled = false

    async function load() {
      const [nextDecision, nextStates, nextExecution, nextHistory] = await Promise.all([
        api.route(workload),
        api.getInfrastructureState(),
        api.getExecution(workload.task_id),
        api.getHistory(),
      ])
      if (cancelled) return
      setDecision(nextDecision)
      setStates(nextStates)
      setExecution(nextExecution)
      setHistory(nextHistory)
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  if (!decision || !states || !execution) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <TopBar />
          <p className={styles.loading}>Choosing a target…</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page} data-target={decision.target}>
      <div className={styles.inner}>
        <TopBar />

        {api.USING_MOCK_DATA ? (
          <p className={styles.mockFlag}>
            <strong>Demonstration data</strong> — not measured results. No
            improvement is claimed before measurement.
          </p>
        ) : null}

        <GuideStrip
          heading="Running on EDGE"
          body="Use the button on the right to step through the demo, or open demo controls for every state."
          actionLabel="Start workload"
        />

        <section className={styles.stack}>
          <div className={styles.stackHead}>
            <SectionHeader
              title="Base line recorded"
              lede="Compare the two at the bottom. No improvement is claimed until both runs are measured for real."
              gap={7}
            />
            <Button>Change workload</Button>
          </div>

          <WorkloadBar workload={workload} />

          <DecisionBand decision={decision} status={execution.status} />

          <EnvironmentsPanel states={states} chosen={decision.target} />

          <div className={styles.split}>
            <ExecutionPanel execution={execution} targetState={states[execution.target]} />
            <RoutingHistory events={history} />
          </div>
        </section>
      </div>
    </div>
  )
}
