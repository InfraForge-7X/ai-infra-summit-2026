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
      // The default workload requires a GPU and CLOUD is the target the engine
      // picks, so CLOUD having no GPU made the headline decision contradict the
      // evidence directly under it. LOCAL is the one without a GPU, which is
      // also what makes it the honest example of an ineligible candidate.
      gpu_available: true,
      ram_usage: 54.7,
      queue: 0,
      latency_ms: 5.1,
      bandwidth_mbps: 940,
      packet_loss: 0,
      timestamp,
    },
  }
}

/**
 * Build a ranked candidate list from rows written out by hand.
 *
 * This maps an array to objects. It does NOT sort, score, or test eligibility:
 * the order out is the order in, exactly as the engine would have sent it.
 * Sorting here would be the ranking logic walking into the frontend by the
 * back door — the one thing DoD item #8 forbids.
 *
 * An ineligible target carries `score: null`, never 0. It was never scored,
 * which is a different fact from scoring badly, and the contract says so.
 *
 * @param {[ExecutionTarget, number | null, Record<string, number>, string[]?][]} rows
 * @returns {import('./contracts.js').RoutingCandidate[]}
 */
export const rank = (rows) =>
  rows.map(([target, score, score_breakdown, disqualification_reasons = []]) => ({
    target,
    eligible: score !== null,
    disqualification_reasons,
    score,
    score_breakdown,
  }))

/**
 * The default ranking: CLOUD wins, EDGE is a close second, LOCAL never gets
 * scored because it fails a hard constraint. Those three states — winner,
 * viable alternative, disqualified — are the whole point of showing a ranking,
 * so the default fixture exercises all three rather than three near-identical
 * rows.
 *
 * Breakdown keys are the engine's to choose (#21 is explicitly configurable
 * scoring), so the UI renders whatever keys arrive instead of assuming this
 * set. These are the dimensions §9 names.
 */
export const candidates = rank([
  ['cloud', 0.61, { latency: 0.72, resources: 0.68, network: 0.74, reliability: 0.66, cost: 0.31 }],
  ['edge', 0.54, { latency: 0.81, resources: 0.42, network: 0.63, reliability: 0.58, cost: 0.55 }],
  ['local', null, {}, ['GPU required by the workload is not available on this target']],
])

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
  ranked_candidates: candidates,
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
    time: '03:20:31',
    kind: 'decision',
    target: 'local',
    score: 0.71,
    reason: 'Restricted privacy requires on-device execution',
  },
  {
    id: 'ev-2',
    time: '03:20:07',
    kind: 'reroute',
    from: 'cloud',
    target: 'local',
    score: 0.68,
    reason: 'Cloud latency exceeded the requirement',
  },
  {
    id: 'ev-1',
    time: '03:19:44',
    kind: 'decision',
    target: 'cloud',
    score: 0.59,
    reason: 'GPU available',
  },
]

/**
 * The switching margin the Decision Engine applies (§9 anti-flapping). Shown
 * on the score meter so the policy is visible rather than claimed. Displayed
 * only — the frontend never applies it.
 */
export const SWITCHING_MARGIN = 0.08

/**
 * Optional execution-provider adapters (§29.3, §29.5).
 *
 * SiMa.ai is an optional Edge provider: the architecture is functional without
 * it and the Decision Engine stays technology-agnostic, so this is a label on
 * a card and never a branch in routing. A target absent from this map simply
 * shows no tag.
 *
 * @type {Partial<Record<ExecutionTarget, string>>}
 */
export const ADAPTERS = { edge: 'SiMa.ai' }
