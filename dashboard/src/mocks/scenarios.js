/**
 * MOCK SCENARIOS — demonstration only.
 *
 * Each demo control SELECTS one of these. Nothing here is computed: there is
 * no scoring function, no eligibility test and no switching threshold. If a
 * function in this file took infrastructure state and returned a target, that
 * would be the Decision Engine running in the browser, which DoD item #8
 * forbids and which Tsadok confirmed we should keep out.
 *
 * Every scenario is a complete snapshot of what the four read endpoints would
 * return at that moment, so `App` swaps one object and the whole page follows.
 *
 * @typedef {import('./contracts.js').RoutingDecision} RoutingDecision
 * @typedef {import('./contracts.js').ExecutionResult} ExecutionResult
 * @typedef {import('./contracts.js').InfrastructureState} InfrastructureState
 * @typedef {import('./contracts.js').ExecutionTarget} ExecutionTarget
 * @typedef {import('./fixtures.js').RoutingEvent} RoutingEvent
 */

import { history as baseHistory, infrastructure } from './fixtures.js'

/**
 * @typedef {object} ApiError
 * @property {422 | 500 | 503} status
 * @property {string} title
 * @property {string} body
 * @property {boolean} showsLastKnownState  True when the page below stays
 *   visible but is no longer current.
 */

/**
 * @typedef {object} Baseline
 * @property {ExecutionTarget} target
 * @property {number | null} fps
 * @property {number} network_latency_ms
 * @property {number} reroutes
 * @property {number} failed_frames
 */

/**
 * @typedef {object} Scenario
 * @property {string} label            Shown in the guide strip
 * @property {string} caption          What just happened, in one sentence
 * @property {RoutingDecision | null} decision
 * @property {ExecutionResult | null} execution
 * @property {Record<ExecutionTarget, InfrastructureState>} states
 * @property {RoutingEvent[]} history
 * @property {ApiError | null} [error]
 * @property {Baseline | null} [baseline]
 * @property {ExecutionTarget | null} [staleTarget]
 * @property {boolean} [held]
 */

/** @param {number} secondsAgo */
function staleStates(target, secondsAgo = 14) {
  const states = infrastructure()
  states[target] = {
    ...states[target],
    timestamp: new Date(Date.now() - secondsAgo * 1000).toISOString(),
  }
  return states
}

/** @param {Partial<RoutingDecision>} overrides @returns {RoutingDecision} */
const decisionOf = (overrides) => ({
  task_id: 'task-001',
  target: 'cloud',
  score: 0.61,
  reasons: ['Latency within requirement'],
  ...overrides,
})

/** @param {Partial<ExecutionResult>} overrides @returns {ExecutionResult} */
const executionOf = (overrides) => ({
  task_id: 'task-001',
  target: 'cloud',
  status: 'running',
  execution_time_ms: 82000,
  network_latency_ms: 73,
  fps: 17,
  ...overrides,
})

/** @type {Record<string, Scenario>} */
export const SCENARIOS = {
  running: {
    label: 'Running on CLOUD',
    caption:
      'Target, score and reasons come from the Routing API. The frontend only displays them.',
    decision: decisionOf({
      reasons: [
        'Latency within requirement',
        'GPU available',
        'Compute headroom available',
        'Network stable',
      ],
    }),
    execution: executionOf({}),
    states: infrastructure(),
    history: baseHistory,
  },

  rerouted: {
    label: 'Rerouted to LOCAL',
    caption:
      'Conditions changed, so the workload moved. The accent colour follows the target.',
    decision: decisionOf({
      target: 'local',
      score: 0.74,
      reasons: ['Edge compute saturated', 'Low network latency', 'Compute headroom available'],
    }),
    execution: executionOf({ target: 'local', network_latency_ms: 5, fps: 31 }),
    states: infrastructure(),
    history: [
      {
        id: 'ev-reroute',
        time: '03:21:04',
        kind: 'reroute',
        from: 'cloud',
        target: 'local',
        score: 0.74,
        reason: 'Edge compute saturated',
      },
      ...baseHistory,
    ],
  },

  // §9 anti-flapping. A better target exists but the gain is under the
  // switching margin, so nothing moved. Most teams will not show this.
  held: {
    label: 'Held on CLOUD',
    caption:
      'A better target exists, but the gain is under the switching threshold — so the workload did not move. That is the anti-flapping policy working.',
    held: true,
    decision: decisionOf({
      score: 0.63,
      reasons: ['Gain below switching threshold — holding current target'],
    }),
    execution: executionOf({}),
    states: infrastructure(),
    history: [
      {
        id: 'ev-hold',
        time: '03:21:10',
        kind: 'hold',
        target: 'cloud',
        score: 0.63,
        reason: 'Gain below switching threshold',
      },
      ...baseHistory,
    ],
  },

  stale: {
    label: 'EDGE stopped reporting',
    caption:
      'The reading is old, so the card is marked stale. Whether that makes the target ineligible is the engine’s judgement, and no contract carries it.',
    staleTarget: 'edge',
    decision: decisionOf({ reasons: ['Latency within requirement', 'Network stable'] }),
    execution: executionOf({}),
    states: staleStates('edge'),
    history: baseHistory,
  },

  // §21: no eligible target is an explicit outcome, not a crash.
  routingFailed: {
    label: 'Routing failed',
    caption: 'Nothing was dispatched. This is a recorded outcome, not an error page.',
    decision: null,
    execution: null,
    states: infrastructure(),
    history: [
      {
        id: 'ev-fail',
        time: '03:21:18',
        kind: 'failure',
        target: 'cloud',
        score: 0,
        reason: 'Every environment failed a hard constraint',
      },
      ...baseHistory,
    ],
  },

  timeout: {
    label: 'Execution timed out',
    caption: 'The failure is recorded, then AFRI-EDGE re-evaluates and tries another target.',
    decision: decisionOf({}),
    execution: executionOf({ status: 'timeout', execution_time_ms: 30000, fps: null }),
    states: infrastructure(),
    history: [
      {
        id: 'ev-timeout',
        time: '03:21:26',
        kind: 'failure',
        target: 'cloud',
        score: 0.61,
        reason: 'Execution timed out — re-evaluating',
      },
      ...baseHistory,
    ],
  },

  error503: {
    label: 'Routing service unreachable',
    caption: 'A 503 tells you the view is stale rather than pretending everything is fine.',
    error: {
      status: 503,
      title: 'Routing service unavailable',
      body: 'The decision service or infrastructure state is not reachable. You are seeing the last known state; nothing new has been routed.',
      showsLastKnownState: true,
    },
    decision: decisionOf({}),
    execution: executionOf({}),
    states: infrastructure(),
    history: baseHistory,
  },

  error422: {
    label: 'Workload rejected',
    caption: 'A 422 names what to fix instead of showing a generic error.',
    error: {
      status: 422,
      title: 'Workload rejected',
      body: 'The routing service could not accept this workload. Check the latency requirement and compute requirement, then route again.',
      showsLastKnownState: false,
    },
    decision: null,
    execution: null,
    states: infrastructure(),
    history: baseHistory,
  },

  error500: {
    label: 'Unexpected error',
    caption: 'A 500 is neither stale data nor bad input — there is nothing to fix from here.',
    error: {
      status: 500,
      title: 'Unexpected internal error',
      body: 'The routing service failed in a way it did not expect. Nothing was dispatched. Try again, and if it persists this is a backend issue rather than a workload one.',
      showsLastKnownState: false,
    },
    decision: null,
    execution: null,
    states: infrastructure(),
    history: baseHistory,
  },

  idle: {
    label: 'No workload running',
    caption: 'Start a workload and AFRI-EDGE picks an execution target.',
    decision: null,
    execution: null,
    states: infrastructure(),
    history: [],
  },
}

/**
 * §19 baseline: a fixed destination, run under the same conditions.
 * Demonstration values. §29.7 forbids claiming an improvement before
 * measurement, and the panel says so on its face.
 *
 * @type {Baseline}
 */
export const BASELINE = {
  target: 'cloud',
  fps: 14,
  network_latency_ms: 940,
  reroutes: 0,
  failed_frames: 2,
}
