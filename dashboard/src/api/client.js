/**
 * API client seam.
 *
 * Every component reads through this module. Today it returns fixtures; when
 * the Routing API is ready, the bodies below become fetch calls and nothing
 * else in the app changes.
 *
 * Read endpoints are an ASSUMPTION, not a contract. §14 of the blueprint
 * defines only POST /route. We assumed polled REST — GET /state,
 * GET /execution/{task_id}, GET /history — because §16 says REST first.
 * Tsadok has not confirmed it. Flagged in the PR.
 *
 * @typedef {import('../mocks/contracts.js').RoutingDecision} RoutingDecision
 * @typedef {import('../mocks/contracts.js').InfrastructureState} InfrastructureState
 * @typedef {import('../mocks/contracts.js').ExecutionResult} ExecutionResult
 * @typedef {import('../mocks/contracts.js').ExecutionTarget} ExecutionTarget
 * @typedef {import('../mocks/contracts.js').WorkloadProfile} WorkloadProfile
 */

import * as fixtures from '../mocks/fixtures.js'
import { SCENARIOS } from '../mocks/scenarios.js'

/** Every response from this module is mock data. Surfaced in the UI. */
export const USING_MOCK_DATA = true

/**
 * POST /route — the only endpoint the blueprint defines.
 * @param {WorkloadProfile} _profile
 * @returns {Promise<RoutingDecision>}
 */
export async function route(_profile) {
  return fixtures.decision
}

/**
 * GET /state (assumed)
 * @returns {Promise<Record<ExecutionTarget, InfrastructureState>>}
 */
export async function getInfrastructureState() {
  return fixtures.infrastructure()
}

/**
 * GET /execution/{task_id} (assumed)
 * @param {string} _taskId
 * @returns {Promise<ExecutionResult>}
 */
export async function getExecution(_taskId) {
  return fixtures.execution
}

/**
 * GET /history (assumed, and no model exists in src/shared yet)
 * @returns {Promise<import('../mocks/fixtures.js').RoutingEvent[]>}
 */
export async function getHistory() {
  return fixtures.history
}

/**
 * Demo scaffolding: returns a complete canned snapshot of what the four
 * endpoints above would return at one moment. The demo controls pick which.
 *
 * This is the one function that disappears when the API lands — the page will
 * poll the endpoints instead. It selects; it does not decide. No scoring,
 * eligibility or threshold logic runs here or anywhere else in the frontend.
 *
 * @param {string} key
 * @returns {import('../mocks/scenarios.js').Scenario}
 */
export function selectScenario(key) {
  return SCENARIOS[key] ?? SCENARIOS.running
}

/**
 * When this talks to a real server, JSON crosses the boundary untyped and the
 * JSDoc types above become a promise nothing checks. If we want real safety
 * there, parse responses with a schema validator at this seam — one place,
 * not scattered through components.
 */
