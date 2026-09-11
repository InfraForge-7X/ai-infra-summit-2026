import { useMemo, useState } from 'react'

import * as api from './api/client.js'
import BaselinePanel from './components/BaselinePanel.jsx'
import DecisionBand from './components/DecisionBand.jsx'
import DecisionDetailDrawer from './components/DecisionDetailDrawer.jsx'
import DemoControlsDrawer from './components/DemoControlsDrawer.jsx'
import EnvironmentsPanel from './components/EnvironmentsPanel.jsx'
import ExecutionPanel from './components/ExecutionPanel.jsx'
import GuideStrip from './components/GuideStrip.jsx'
import Notice from './components/Notice.jsx'
import RoutingHistory from './components/RoutingHistory.jsx'
import TopBar from './components/TopBar.jsx'
import WorkloadBar from './components/WorkloadBar.jsx'
import WorkloadDrawer from './components/WorkloadDrawer.jsx'
import { Button, SectionHeader } from './components/ui/ui.jsx'
import { workload as defaultWorkload } from './mocks/fixtures.js'
import { BASELINE } from './mocks/scenarios.js'
import styles from './App.module.css'

/**
 * AFRI-EDGE routing control.
 *
 * One screen. Navigation would hide the reroute, and the reroute is the
 * product. Drawers are state, not routes — there is no router in this app.
 *
 * `scenarioKey` selects which canned set of API responses is being displayed.
 * It is demo scaffolding: the real dashboard polls and re-renders. What it is
 * NOT is a decision — the target, score and reasons always arrive on a
 * RoutingDecision, and this component never derives them. (DoD item #8.)
 */
export default function App() {
  const [scenarioKey, setScenarioKey] = useState('running')
  const [baseline, setBaseline] = useState(
    /** @type {import('./mocks/scenarios.js').Baseline | null} */ (null),
  )
  const [controlsOpen, setControlsOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [workloadOpen, setWorkloadOpen] = useState(false)
  const [workload, setWorkload] = useState(defaultWorkload)
  // Stamped when we last displayed a real decision, so a 503 can say how old
  // the numbers on screen are. Recorded where the change happens rather than
  // in an effect, which would re-render for nothing.
  const [lastGoodAt, setLastGoodAt] = useState(() =>
    new Date().toLocaleTimeString('en-GB'),
  )

  // Still read through the client seam: when the API is live this becomes a
  // poll of GET /state, /execution/{task_id} and /history.
  const scenario = api.selectScenario(scenarioKey)
  const { decision, execution, states, history, error = null } = scenario

  /** @param {string} key */
  const selectScenario = (key) => {
    const next = api.selectScenario(key)
    if (!next.error && next.decision) {
      setLastGoodAt(new Date().toLocaleTimeString('en-GB'))
    }
    setScenarioKey(key)
  }

  /**
   * A new workload profile is submitted, not routed. The backend decides where
   * it runs; this picks the canned response that decision would produce.
   * @param {import('./mocks/contracts.js').WorkloadProfile} next
   */
  const submitWorkload = (next) => {
    setWorkload(next)
    selectScenario(next.workload_type === 'speech' ? 'speech' : 'running')
  }

  const reroutes = useMemo(
    () => history.filter((event) => event.kind === 'reroute').length,
    [history],
  )

  // A 503 keeps the last known state on screen — the numbers are still there
  // but no longer true, and the user needs to know how stale they are. Every
  // other error clears the board, because nothing was dispatched.
  const showsDashboard = Boolean(decision && execution && (!error || error.showsLastKnownState))

  return (
    <div className={styles.page} data-target={decision?.target ?? 'cloud'}>
      <div className={styles.inner}>
        <TopBar onOpenDemoControls={() => setControlsOpen(true)} />

        {api.USING_MOCK_DATA ? (
          <p className={styles.mockFlag}>
            <strong>Demonstration data</strong> — not measured results. No
            improvement is claimed before measurement.
          </p>
        ) : null}

        <GuideStrip
          heading={scenario.label}
          body={scenario.caption}
          actionLabel="Start workload"
          onAction={() => selectScenario('running')}
        />

        <section className={styles.stack}>
          <div className={styles.stackHead}>
            <SectionHeader
              title={baseline ? 'Baseline recorded' : 'Current workload'}
              lede={
                baseline
                  ? 'Compare the two at the bottom. No improvement is claimed until both runs are measured for real.'
                  : 'The WorkloadProfile sent to the Routing API.'
              }
              gap={7}
            />
            <Button onClick={() => setWorkloadOpen(true)}>Change workload</Button>
          </div>

          <WorkloadBar workload={workload} />

          {error ? (
            <Notice
              tone="bad"
              heading={`${error.status} — ${error.title}`}
              body={error.body}
              actionLabel="Try again"
              onAction={() => selectScenario('running')}
              stamp={
                error.showsLastKnownState && lastGoodAt
                  ? `last update ${lastGoodAt}`
                  : undefined
              }
            />
          ) : null}

          {!error && !decision ? (
            <Notice
              tone={scenarioKey === 'routingFailed' ? 'bad' : 'neutral'}
              heading={
                scenarioKey === 'routingFailed'
                  ? 'Routing failed — no eligible target'
                  : 'No workload running'
              }
              body={
                scenarioKey === 'routingFailed'
                  ? 'Every environment failed a hard constraint, so nothing was dispatched. Relax the workload requirements or restore an environment, then route again.'
                  : 'Start a workload and AFRI-EDGE picks an execution target, then keeps watching conditions and moves the work if something better appears.'
              }
              actionLabel={scenarioKey === 'routingFailed' ? 'Route again' : 'Start workload'}
              onAction={() => selectScenario('running')}
            />
          ) : null}

          {showsDashboard ? (
            <>
              <DecisionBand
                decision={decision}
                status={execution.status}
                onSeeDecision={() => setDetailOpen(true)}
              />
              <EnvironmentsPanel states={states} chosen={decision.target} />

              <div className={styles.split}>
                <ExecutionPanel execution={execution} targetState={states[execution.target]} />
                <RoutingHistory events={history} />
              </div>
            </>
          ) : null}

          <BaselinePanel baseline={baseline} execution={execution} reroutes={reroutes} />
        </section>
      </div>

      <DemoControlsDrawer
        open={controlsOpen}
        onClose={() => setControlsOpen(false)}
        onSelect={selectScenario}
        onChangeWorkload={() => setWorkloadOpen(true)}
        onRunBaseline={() => setBaseline(BASELINE)}
        current={scenarioKey}
      />

      <DecisionDetailDrawer
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        decision={decision}
        workload={workload}
        targetState={states[decision?.target ?? 'cloud']}
        execution={execution}
      />

      <WorkloadDrawer
        open={workloadOpen}
        onClose={() => setWorkloadOpen(false)}
        workload={workload}
        onSubmit={submitWorkload}
      />
    </div>
  )
}
