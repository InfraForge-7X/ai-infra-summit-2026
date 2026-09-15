import { useCallback, useRef, useState } from 'react'

import * as api from '../api/client.js'

/**
 * Live dashboard data path.
 *
 * The backend contract currently confirmed in the repository is POST /route.
 * This hook therefore only calls that endpoint in live mode. It does not poll
 * speculative /state, /execution/{task_id}, or /history endpoints.
 *
 * What it does NOT do is decide anything. The target, score, reasons and
 * candidate order all arrive from RoutingDecision; the dashboard only renders
 * them.
 *
 * @returns {null | {
 *   label: string,
 *   caption: string,
 *   decision: import('../mocks/contracts.js').RoutingDecision | null,
 *   execution: null,
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
  const [routeError, setRouteError] = useState(null)
  const [loading, setLoading] = useState(isLive)

  // Kept for future execution telemetry once a confirmed backend contract
  // exists. They intentionally remain empty in live mode rather than being
  // populated with invented or stale data.
  const states = /** @type {Record<string, any>} */ ({})
  const history = /** @type {any[]} */ ([])
  const execution = null
  const taskId = useRef(null)

  /**
   * POST /route — the confirmed AFRI-EDGE API contract.
   *
   * The response is the RoutingDecision itself. No second request is made here:
   * there is currently no confirmed execution endpoint in the backend.
   *
   * @param {import('../mocks/contracts.js').WorkloadProfile} profile
   */
  const route = useCallback(async (profile) => {
    setLoading(true)
    try {
      const next = await api.route(profile)
      taskId.current = next.task_id
      setDecision(next)
      setRouteError(null)
    } catch (failure) {
      setRouteError(failure)
      if (!failure?.showsLastKnownState) {
        setDecision(null)
        taskId.current = null
      }
    } finally {
      setLoading(false)
    }
  }, [])

  if (!isLive) return null

  return {
    label: decision ? `Routing decision — ${decision.target.toUpperCase()}` : 'No routing decision yet',
    caption: decision
      ? 'Target, score, reasons and candidate ranking come directly from the AFRI-EDGE Routing API.'
      : 'Submit a workload to POST /route and AFRI-EDGE will choose the execution target.',
    decision,
    execution,
    states,
    history,
    error: routeError,
    loading,
    route,
  }
}
