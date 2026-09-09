/**
 * Shared data contracts, mirrored from the merged Pydantic models in
 * `src/shared/models.py` and `src/shared/enums.py` at the repo root.
 *
 * These are JSDoc typedefs, not runtime code — with `checkJs` on in
 * jsconfig.json the editor type-checks against them. Nothing here validates
 * at runtime; when the real API lands, response validation is a separate
 * decision (see the note at the bottom of `api/client.js`).
 *
 * The blueprint PDF (§15) is a draft and disagrees with the merged code in
 * two places: it spells the field `reason[]` (code says `reasons`) and shows
 * uppercase enum values (code is lowercase). The code wins.
 *
 * @see src/shared/models.py
 */

/**
 * @typedef {'real_time_video' | 'video_inference' | 'speech' | 'batch_inference'} WorkloadType
 * `video_inference` is legacy compatibility only — do not use for new profiles.
 */

/** @typedef {'cpu' | 'gpu' | 'any'} ComputeRequirement */
/** @typedef {'standard' | 'sensitive' | 'restricted'} PrivacyLevel */
/** @typedef {'low' | 'medium' | 'high' | 'critical'} Priority */
/** @typedef {'local' | 'edge' | 'cloud'} ExecutionTarget */

/**
 * @typedef {'created' | 'routing' | 'dispatched' | 'running' | 'completed'
 *   | 'result_returned' | 'failed' | 'timeout' | 'cancelled'} ExecutionStatus
 */

/**
 * @typedef {object} WorkloadProfile
 * @property {string} task_id
 * @property {WorkloadType} workload_type
 * @property {string} model
 * @property {number} input_size          Pixels, > 0
 * @property {number} latency_requirement Milliseconds, > 0
 * @property {ComputeRequirement} compute_requirement
 * @property {PrivacyLevel} privacy
 * @property {Priority} priority
 */

/**
 * @typedef {object} InfrastructureState
 * @property {ExecutionTarget} target
 * @property {number} cpu_usage      Percent 0–100
 * @property {boolean} gpu_available
 * @property {number} ram_usage      Percent 0–100
 * @property {number} queue          Tasks queued, >= 0
 * @property {number} latency_ms
 * @property {number} bandwidth_mbps
 * @property {number} packet_loss    Percent 0–100
 * @property {string} timestamp      ISO 8601. Drives freshness — see §8.
 */

/**
 * @typedef {object} RoutingDecision
 * @property {string} task_id
 * @property {ExecutionTarget} target
 * @property {number} score            0–1
 * @property {string[]} reasons        At least one. Length is not fixed.
 *
 * The model sets `extra="forbid"` and carries nothing else — in particular
 * there is no candidate ranking, so the UI cannot show why the other two
 * targets lost. Open question for Tsadok.
 */

/**
 * @typedef {object} ExecutionResult
 * @property {string} task_id
 * @property {ExecutionTarget} target
 * @property {ExecutionStatus} status
 * @property {number} execution_time_ms
 * @property {number} network_latency_ms
 * @property {number | null} fps  Null for non-video workloads. A missing
 *   reading and a zero reading are different facts — render null as an
 *   em dash, never as 0.
 */

export {}
