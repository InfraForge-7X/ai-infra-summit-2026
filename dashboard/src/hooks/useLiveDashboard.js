import { useCallback, useEffect, useRef, useState } from 'react'

import * as api from '../api/client.js'

/**
 * Three seconds.
 *
 * Fast enough that a reroute appears while a judge is still looking at the
 * screen, slow enough that three read endpoints per tick is not a load test.
 * §8 marks a reading stale at eight seconds, so this gives two chances to
 * refresh before anything goes grey.
 */
const POLL_MS = 3000

/**
 * The live data path: polls the AFRI-EDGE API and hands `App` the same shape a
 * canned scenario has, so one component renders both without knowing which it
 * is looking at.
 *
 * Returns `null` in mock mode, and that is load-bearing. With no API address
 * configured this hook starts no timers and issues no requests at all — a demo
 * machine with no backend must not be quietly hammering localhost every few
 * seconds and swallowing the failures.
 *
 * What it does NOT do is decide anything. It fetches, it stores, it hands over.
 * The target, the score, the reasons and the candidate order all arrive
 * decided; nothing here sorts, scores or picks. (DoD item #8.)
 *
 * @returns {null | {
 *   label: string,
 *   caption: string,
 *   decision: import('../mocks/contracts.js').RoutingDecision | null,
 *   execution: import('../mocks/contracts.js').ExecutionResult | null,
 *   states: Record<string, import('../mocks/contracts.js').InfrastructureState>,
 *   history: import('../mocks/fixtures.js').RoutingEvent[],
 *   error: import('../mocks/scenarios.js').ApiError | null,
 *   loading: boolean,
 *   route: (profile: import('../mocks/contracts.js').WorkloadProfile) => Promise<void>,
 * }}
 */
export function useLiveDashboard() {
  const isLive = !api.USING_MOCK_DATA

  const [decision, setDecision] = useState(null)
  const [execution, setExecution] = useState(null)
  const [states, setStates] = useState(/** @type {any} */ ({}))
  const [history, setHistory] = useState(/** @type {any[]} */ ([]))
  // Two error slots, not one.
  //
  // Reads and routing fail independently and a success in one must not erase a
  // failure in the other. With a single slot, a POST /route that came back 503
  // was wiped by the next successful poll three seconds later — the operator
  // saw the failure flash and vanish, and the dashboard went back to looking
  // healthy while nothing had been dispatched.
  const [readError, setReadError] = useState(/** @type {any} */ (null))
  const [routeError, setRouteError] = useState(/** @type {any} */ (null))
  const [loading, setLoading] = useState(isLive)

  // The task currently on screen, kept in a ref so the polling effect does not
  // have to restart every time a new decision lands. Restarting the interval on
  // each poll result is how a 3s poll quietly becomes a much faster one.
  const taskId = useRef(/** @type {string | null} */ (null))

  /**
   * One pass over the read endpoints.
   *
   * Infrastructure state and history are fetched every time; execution only
   * once something has been routed, because `/execution/{task_id}` has no
   * meaningful answer before that.
   */
  const poll = useCallback(async () => {
    try {
      const [nextStates, nextHistory] = await Promise.all([
        api.getInfrastructureState(),
        api.getHistory(),
      ])
      setStates(nextStates)
      setHistory(nextHistory)

      if (taskId.current) {
        setExecution(await api.getExecution(taskId.current))
      }

      // Only a successful pass clears it, and only the read failure. Clearing
      // optimistically at the start of a poll makes a persistent outage flicker
      // between "broken" and "fine" at the poll interval.
      setReadError(null)
    } catch (failure) {
      setReadError(failure)
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * POST /route, then pick up the execution it produced.
   *
   * A 422 here is the interesting one: the workload was rejected, so the
   * previous decision must go. Leaving it on screen would show a decision that
   * does not correspond to the profile displayed above it.
   *
   * @param {import('../mocks/contracts.js').WorkloadProfile} profile
   */
  const route = useCallback(async (profile) => {
    setLoading(true)
    try {
      const next = await api.route(profile)
      taskId.current = next.task_id
      setDecision(next)
      setExecution(await api.getExecution(next.task_id))
      setRouteError(null)
    } catch (failure) {
      setRouteError(failure)
      if (!failure?.showsLastKnownState) {
        setDecision(null)
        setExecution(null)
        taskId.current = null
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!isLive) return undefined

    // The first pass is scheduled rather than called inline. `poll` is async,
    // so its setState calls already land in a callback, but calling it in the
    // effect body reads as a synchronous cascade to both React's lint rule and
    // to anyone reviewing this. A zero timeout says what is actually happening:
    // subscribe now, update when the data arrives.
    const first = setTimeout(poll, 0)
    const timer = setInterval(poll, POLL_MS)

    return () => {
      clearTimeout(first)
      clearInterval(timer)
    }
  }, [isLive, poll])

  if (!isLive) return null

  return {
    label: decision ? `Running on ${decision.target.toUpperCase()}` : 'No workload running',
    caption: decision
      ? 'Target, score and reasons come from the Routing API. The frontend only displays them.'
      : 'Start a workload and AFRI-EDGE picks an execution target.',
    decision,
    execution,
    states,
    history,
    // A routing failure wins when both are present: it is about the action the
    // operator just took, and it is the one that means nothing was dispatched.
    error: routeError ?? readError,
    loading,
    route,
  }
}
