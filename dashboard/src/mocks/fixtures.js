/**
 * MOCK DATA — demonstration only, not measured results.
 *
 * These are canned API responses, shaped exactly like the merged contracts in
 * `src/shared`. They are *selected*, never computed.
 *
 * There is deliberately no scoring, no eligibility check and no switching
 * threshold in this file or anywhere else in the frontend. AFRI-EDGE decides;
 * the dashboard displays. Any function here that took infrastructure state and
 * returned a target would be the Decision Engine living in React, and would
 * fail DoD item #8.
 *
 * @typedef {import('./contracts.js').WorkloadProfile} WorkloadProfile
 * @typedef {import('./contracts.js').InfrastructureState} InfrastructureState
 * @typedef {import('./contracts.js').RoutingDecision} RoutingDecision
 * @typedef {import('./contracts.js').ExecutionResult} ExecutionResult
 * @typedef {import('./contracts.js').ExecutionTarget} ExecutionTarget
 */

const now = () => new Date().toISOString()

/** @type {WorkloadProfile} */
export const workload = {
  task_id: 'task-001',
  workload_type: 'real_time_video',
  model: 'yolo',
  input_size: 1920,
  latency_requirement: 100,
  compute_requirement: 'gpu',
  privacy: 'standard',
  priority: 'high',
}

/**
 * One InfrastructureState per target, as GET /state would return them.
 * @returns {Record<ExecutionTarget, InfrastructureState>}
 */
export function infrastructure() {
  const timestamp = now()
  return {
    local: {
      target: 'local',
      cpu_usage: 27.4,
      gpu_available: false,
      ram_usage: 54.1,
      queue: 0,
      latency_ms: 5.2,
      bandwidth_mbps: 940,
      packet_loss: 0,
      timestamp,
    },
    edge: {
      target: 'edge',
      cpu_usage: 27.6,
      gpu_available: true,
      ram_usage: 54.3,
      queue: 2,
      latency_ms: 5.4,
      bandwidth_mbps: 940,
      packet_loss: 0,
      timestamp,
    },
    cloud: {
      target: 'cloud',
      cpu_usage: 27.2,
      gpu_available: false,
      ram_usage: 54.7,
      queue: 0,
      latency_ms: 5.1,
      bandwidth_mbps: 940,
      packet_loss: 0,
      timestamp,
    },
  }
}

/** @type {RoutingDecision} */
export const decision = {
  task_id: 'task-001',
  target: 'cloud',
  score: 0.61,
  reasons: [
    'Latency within requirement',
    'GPU available',
    'Compute headroom available',
    'Network stable',
  ],
}

/** @type {ExecutionResult} */
export const execution = {
  task_id: 'task-001',
  target: 'cloud',
  status: 'running',
  execution_time_ms: 82000,
  network_latency_ms: 73,
  fps: 17,
}

/**
 * Routing history has no contract in `src/shared` yet — no history or event
 * model exists there. This shape is the frontend's own until Tsadok defines
 * one, and the section is labelled as such in the UI.
 *
 * @typedef {object} RoutingEvent
 * @property {string} id
 * @property {string} time              Display time, HH:MM:SS
 * @property {'decision' | 'reroute' | 'hold' | 'failure'} kind
 * @property {ExecutionTarget} target
 * @property {ExecutionTarget} [from]   Present on a reroute
 * @property {number} score
 * @property {string} reason
 */

/** @type {RoutingEvent[]} */
export const history = [
  {
    id: 'ev-4',
    time: '03:20:52',
    kind: 'decision',
    target: 'cloud',
    score: 0.65,
    reason: 'Latency within requirement',
  },
  {
    id: 'ev-3',
    time: '03:20:52',
    kind: 'decision',
    target: 'local',
    score: 0.65,
    reason: 'Latency within requirement',
  },
  {
    id: 'ev-2',
    time: '03:20:52',
    kind: 'reroute',
    from: 'cloud',
    target: 'local',
    score: 0.65,
    reason: 'Latency within requirement',
  },
  {
    id: 'ev-1',
    time: '03:20:52',
    kind: 'decision',
    target: 'cloud',
    score: 0.65,
    reason: 'Latency within requirement',
  },
]

/**
 * The switching margin the Decision Engine applies (§9 anti-flapping). Shown
 * on the score meter so the policy is visible rather than claimed. Displayed
 * only — the frontend never applies it.
 */
export const SWITCHING_MARGIN = 0.08
