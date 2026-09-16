/**
 * API client seam — the only place the dashboard talks to the outside world.
 *
 * Two modes, and which one is live is decided by configuration, not by a flag
 * someone can forget to flip:
 *
 *   VITE_API_URL set    → real HTTP against the AFRI-EDGE Routing API
 *   VITE_API_URL unset  → canned fixtures, and the page says so on its face
 *
 * That is deliberate. A boolean toggle in source is one careless commit away
 * from shipping a demo that claims to be live, and §29.7 forbids claiming a
 * result that was not measured. If no API address is configured there is no
 * API, and `USING_MOCK_DATA` is true — there is no third state where the UI
 * believes it is live and is not.
 *
 * Mock data never reaches the live path: the fixtures are imported for the
 * mock branch only, and every live function returns what the server sent or
 * throws. Nothing falls back to a fixture on error, because a fixture rendered
 * after a failed request is a lie with a timestamp on it.
 *
 * @typedef {import('../mocks/contracts.js').RoutingDecision} RoutingDecision
 * @typedef {import('../mocks/contracts.js').InfrastructureState} InfrastructureState
 * @typedef {import('../mocks/contracts.js').ExecutionResult} ExecutionResult
 * @typedef {import('../mocks/contracts.js').ExecutionTarget} ExecutionTarget
 * @typedef {import('../mocks/contracts.js').WorkloadProfile} WorkloadProfile
 * @typedef {import('../mocks/scenarios.js').ApiError} ApiError
 */

import * as fixtures from '../mocks/fixtures.js'
import { SCENARIOS } from '../mocks/scenarios.js'

/** Trailing slash trimmed so `${BASE_URL}/route` cannot become a double slash. */
export const BASE_URL = String(import.meta.env?.VITE_API_URL ?? '').replace(/\/+$/, '')

/** True when nothing on screen came from a server. Surfaced in the UI. */
export const USING_MOCK_DATA = BASE_URL === ''

/**
 * A request that hangs is worse than one that fails: the page keeps showing a
 * stale view with nothing to say anything is wrong. Ten seconds is past any
 * plausible routing decision and well inside a judge's patience.
 */
const TIMEOUT_MS = 10_000

/**
 * Map a failure to the shape the UI already renders (§14, §21).
 *
 * `showsLastKnownState` is the one that matters. A 503 means the decision
 * service is unreachable, so what is on screen is real but old and should be
 * labelled stale rather than blanked — throwing the whole view away because
 * one poll failed discards information the operator still needs. A 422 or a
 * 500 is different: nothing was dispatched, so there is no last known state to
 * keep showing.
 *
 * @param {number} status
 * @param {string} [detail]  Server-supplied explanation, when there is one.
 * @returns {ApiError}
 */
export function toApiError(status, detail) {
  if (status === 422) {
    return {
      status: 422,
      title: 'Workload rejected',
      body:
        detail ||
        'The routing service could not accept this workload. Check the latency requirement and compute requirement, then route again.',
      showsLastKnownState: false,
    }
  }

  if (status === 503) {
    return {
      status: 503,
      title: 'Routing service unavailable',
      body:
        detail ||
        'The decision service or infrastructure state is not reachable. You are seeing the last known state; nothing new has been routed.',
      showsLastKnownState: true,
    }
  }

  return {
    status: 500,
    title: 'Unexpected internal error',
    body:
      detail ||
      'The routing service failed in a way it did not expect. Nothing was dispatched. Try again, and if it persists this is a backend issue rather than a workload one.',
    showsLastKnownState: false,
  }
}

/**
 * Pull a human-readable message out of an error body.
 *
 * The backend is FastAPI, so a validation failure arrives as
 * `{detail: [{loc, msg, type}, ...]}` and a raised HTTPException as
 * `{detail: "..."}`. Both are handled; anything else falls through to the
 * generic wording rather than printing `[object Object]` at a judge.
 *
 * `loc` is kept because on a 422 the useful information is *which field* was
 * rejected. "latency_requirement: input should be greater than 0" is
 * actionable; "validation error" is not.
 *
 * @param {unknown} body
 * @returns {string}
 */
export function detailFrom(body) {
  const detail = /** @type {any} */ (body)?.detail
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return ''

  return detail
    .map((item) => {
      const field = Array.isArray(item?.loc)
        ? item.loc.filter((part) => part !== 'body').join('.')
        : ''
      const message = typeof item?.msg === 'string' ? item.msg : ''
      return field && message ? `${field}: ${message}` : message
    })
    .filter(Boolean)
    .join('. ')
}

/**
 * One HTTP call, with the timeout and the error mapping applied in one place.
 *
 * Throws an `ApiError` on anything that is not a 2xx, including a network
 * failure or a timeout — both treated as 503, because from the dashboard's
 * point of view a service that cannot be reached and a service that says it is
 * unavailable are the same fact.
 *
 * @param {string} path
 * @param {RequestInit} [init]
 * @returns {Promise<any>}
 */
async function request(path, init) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    // Network down, DNS failure, CORS refusal, or our own abort. None of them
    // distinguish themselves usefully here, and all mean the same thing to the
    // operator: the service cannot be reached right now.
    throw toApiError(503)
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw toApiError(response.status, detailFrom(body))
  }

  return response.json()
}

/**
 * POST /route — the endpoint §14 defines.
 *
 * Returns a `RoutingDecision`, which since #21 carries `ranked_candidates`:
 * every target the engine evaluated, already ordered. The dashboard renders
 * that order and never sorts it.
 *
 * @param {WorkloadProfile} profile
 * @returns {Promise<RoutingDecision>}
 */
export async function route(profile) {
  if (USING_MOCK_DATA) return fixtures.decision
  return request('/route', { method: 'POST', body: JSON.stringify(profile) })
}

/**
 * GET /state — still an ASSUMPTION, not a confirmed contract.
 *
 * §14 defines only POST /route. Polled REST is the assumption (§16 says REST
 * first); the path and response shape are unconfirmed. The normalisation below
 * is the only thing that changes if it turns out to be a list rather than a
 * map, which is why it lives here and not in a component.
 *
 * @returns {Promise<Record<ExecutionTarget, InfrastructureState>>}
 */
export async function getInfrastructureState() {
  if (USING_MOCK_DATA) return fixtures.infrastructure()

  const payload = await request('/state')
  if (!Array.isArray(payload)) return payload

  // A list of InfrastructureState, keyed by the `target` each one already
  // carries. Grouping by a field the server set is a lookup, not a decision.
  return Object.fromEntries(payload.map((state) => [state.target, state]))
}

/**
 * GET /execution/{task_id} (assumed — see above)
 * @param {string} taskId
 * @returns {Promise<ExecutionResult>}
 */
export async function getExecution(taskId) {
  if (USING_MOCK_DATA) return fixtures.execution
  return request(`/execution/${encodeURIComponent(taskId)}`)
}

/**
 * GET /history (assumed, and no model exists in `src/shared` yet)
 * @returns {Promise<import('../mocks/fixtures.js').RoutingEvent[]>}
 */
export async function getHistory() {
  if (USING_MOCK_DATA) return fixtures.history
  return request('/history')
}

/**
 * Demo scaffolding: a complete canned snapshot of what the endpoints above
 * would return at one moment. The demo controls pick which.
 *
 * This is the one export that disappears when the API lands — the page will
 * poll instead. It selects; it does not decide. No scoring, eligibility or
 * threshold logic runs here or anywhere else in the frontend.
 *
 * @param {string} key
 * @returns {import('../mocks/scenarios.js').Scenario}
 */
export function selectScenario(key) {
  return SCENARIOS[key] ?? SCENARIOS.running
}

/**
 * Still open: JSON crosses this boundary untyped, so the JSDoc types above are
 * a promise nothing checks at runtime. If we want real safety, parse responses
 * with a schema validator here — one place, not scattered through components.
 * Worth doing only if the contract keeps moving; it has been stable since #13.
 */
