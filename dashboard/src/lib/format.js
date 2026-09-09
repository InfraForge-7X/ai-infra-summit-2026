/**
 * Display formatters.
 *
 * The only rule with teeth: a missing value is an em dash, never a zero.
 * `fps` is nullable in the contract and a speech workload returns null, so
 * every numeric readout goes through here rather than through Math.round.
 */

export const EM_DASH = '—'

/**
 * @param {number | null | undefined} value
 * @param {(n: number) => string} render
 * @returns {string}
 */
function guard(value, render) {
  if (value === null || value === undefined || Number.isNaN(value)) return EM_DASH
  return render(value)
}

/** @param {number | null | undefined} value */
export const asInt = (value) => guard(value, (n) => String(Math.round(n)))

/** @param {number | null | undefined} value */
export const asPercent = (value) => guard(value, (n) => `${Math.round(n)}%`)

/** @param {number | null | undefined} value */
export const asOneDecimal = (value) => guard(value, (n) => (Math.round(n * 10) / 10).toFixed(1))

/** @param {number | null | undefined} value */
export const asScore = (value) => guard(value, (n) => n.toFixed(2))

/**
 * Human freshness for an InfrastructureState timestamp.
 * @param {string} iso
 * @param {number} [now]
 */
export function timeAgo(iso, now = Date.now()) {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return EM_DASH
  const seconds = Math.round((now - then) / 1000)
  if (seconds < 1) return 'updated just now'
  if (seconds < 60) return `updated ${seconds}s ago`
  return `updated ${Math.round(seconds / 60)}m ago`
}

/**
 * §8 tracks freshness; a target whose state is older than the window is
 * stale. Eligibility is the Decision Engine's judgement and is not returned
 * on any contract, so the dashboard can only ever say live or stale.
 *
 * @param {string} iso
 * @param {number} [now]
 * @param {number} [windowMs]
 */
export function isStale(iso, now = Date.now(), windowMs = 8000) {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return true
  return now - then > windowMs
}

/** @type {Record<import('./contracts.js').ExecutionTarget, string>} */
export const TARGET_LABEL = { local: 'LOCAL', edge: 'EDGE', cloud: 'CLOUD' }

/** @type {Record<import('./contracts.js').ExecutionTarget, string>} */
export const TARGET_CAPTION = {
  local: 'On device execution',
  edge: 'Edge node execution',
  cloud: 'Cloud execution',
}

/** @type {Record<import('./contracts.js').ExecutionStatus, string>} */
export const STATUS_LABEL = {
  created: 'Created',
  routing: 'Choosing a target',
  dispatched: 'Dispatched',
  running: 'Executing',
  completed: 'Completed',
  result_returned: 'Result returned',
  failed: 'Failed',
  timeout: 'Timed out',
  cancelled: 'Cancelled',
}

/** @type {Record<import('./contracts.js').WorkloadType, string>} */
export const WORKLOAD_LABEL = {
  real_time_video: 'Real-time video',
  video_inference: 'Video inference (legacy)',
  speech: 'Speech',
  batch_inference: 'Batch inference',
}
