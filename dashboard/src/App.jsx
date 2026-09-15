import { useMemo, useState } from 'react'

import * as api from './api/client.js'
import BaselinePanel from './components/BaselinePanel.jsx'
import CandidateRanking from './components/CandidateRanking.jsx'
import DecisionBand from './components/DecisionBand.jsx'
import DecisionDetailDrawer from './components/DecisionDetailDrawer.jsx'
import DemoControlsDrawer from './components/DemoControlsDrawer.jsx'
import GuideStrip from './components/GuideStrip.jsx'
import Notice from './components/Notice.jsx'
import TopBar from './components/TopBar.jsx'
import WorkloadBar from './components/WorkloadBar.jsx'
import WorkloadDrawer from './components/WorkloadDrawer.jsx'
import { Button, SectionHeader } from './components/ui/ui.jsx'
import { useLiveDashboard } from './hooks/useLiveDashboard.js'
import { workload as defaultWorkload } from './mocks/fixtures.js'
import { BASELINE } from './mocks/scenarios.js'
import styles from './App.module.css'

/**
 * AFRI-EDGE routing control.
 *
 * The live path renders only data backed by the confirmed POST /route contract.
 * Mock mode can still render the complete demo snapshot. The frontend never
 * invents execution, infrastructure or history data when those backend
 * contracts are not available.
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
  const [lastGoodAt, setLastGoodAt] = useState(() =>
    new Date().toLocaleTimeString('en-GB'),
  )

  const live = useLiveDashboard()
  const scenario = live ?? api.selectScenario(scenarioKey)
  const { decision, execution, states, history, error = null } = scenario

  /** @param {string} key */
  const selectScenario = (key) => {
    if (live) {
      live.route(workload)
      return
    }

    const next = api.selectScenario(key)
    if (!next.error && next.decision) {
      setLastGoodAt(new Date().toLocaleTimeString('en-GB'))
    }
    setScenarioKey(key)
  }

  /**
   * Submit a WorkloadProfile. In live mode this becomes POST /route; in mock
   * mode it selects the corresponding canned scenario.
   * @param {import('./mocks/contracts.js').WorkloadProfile} next
   */
  const submitWorkload = (next) => {
    setWorkload(next)
    if (live) {
      live.route(next)
      return
    }
    selectScenario(next.workload_type === 'speech' ? 'speech' : 'running')
  }

  const reroutes = useMemo(
    () => history.filter((event) => event.kind === 'reroute').length,
    [history],
  )

  // In live mode, a successful POST /route is enough to show the decision.
  // Execution/state/history panels stay mock-only until their backend contracts
  // actually exist.
  const showsDecision = Boolean(decision && (!error || error.showsLastKnownState))
  const isLive = Boolean(live)

  return (
    <div className={styles.page} data-target={decision?.target ?? 'cloud'}>
      <div className={styles.inner}>
        <TopBar onOpenDemoControls={live ? undefined : () => setControlsOpen(true)} />

        {api.USING_MOCK_DATA ? (
          <p className={styles.mockFlag}>
            <strong>Demonstration data</strong> — not measured results. No
            improvement is claimed before measurement.
          </p>
        ) : null}

        <GuideStrip
          heading={scenario.label}
          body={scenario.caption}
          actionLabel="Route workload"
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
              actionLabel="Route again"
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
              tone="neutral"
              heading={isLive ? 'Ready to route' : 'No workload running'}
              body={
                isLive
                  ? 'Submit the workload to the real AFRI-EDGE Routing API. The target, score and candidate ranking will come directly from the Decision Engine.'
                  : 'Start a workload and AFRI-EDGE picks an execution target, then keeps watching conditions and moves the work if something better appears.'
              }
              actionLabel="Route workload"
              onAction={() => selectScenario('running')}
            />
          ) : null}

          {showsDecision ? (
            <>
              <DecisionBand
                decision={decision}
                status={execution?.status}
                onSeeDecision={() => setDetailOpen(true)}
              />
              <CandidateRanking
                candidates={decision.ranked_candidates}
                selected={decision.target}
              />

              {isLive ? (
                <Notice
                  tone="neutral"
                  heading="Routing decision confirmed"
                  body="This view is backed by POST /route. Infrastructure telemetry, execution status and routing history will appear here when their backend contracts are available."
                />
              ) : null}
            </>
          ) : null}

          {!isLive && decision && execution ? (
            <BaselinePanel baseline={baseline} execution={execution} reroutes={reroutes} />
          ) : null}
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
