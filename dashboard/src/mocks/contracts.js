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
 * Verified against origin/main at 24514ab (decision engine, #21) — the commit
 * that added `ranked_candidates`. Every model here sets `extra="forbid"`, so a
 * field the UI invents is a 422 on the way in and a silently ignored key on
 * the way out. Nothing below is speculative: if it is in this file, it is in
 * models.py.
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
 * One target as the Decision Engine evaluated it.
 *
 * `score` is null when `eligible` is false — an ineligible target was never
 * scored, which is a different fact from scoring zero, and the UI must render
 * it as an em dash. A target fails eligibility on a HARD constraint, and
 * `disqualification_reasons` says which; it is empty when eligible.
 *
 * `score_breakdown` is per-dimension (performance, cost, and whatever else the
 * engine is configured with). The keys are the engine's to choose — the UI
 * reads whatever arrives rather than assuming a fixed set, because the
 * pipeline is explicitly "configurable scoring" and a hard-coded list here
 * would silently drop a dimension the day someone adds one.
 *
 * @typedef {object} RoutingCandidate
 * @property {ExecutionTarget} target
 * @property {boolean} eligible
 * @property {string[]} disqualification_reasons  Empty when eligible.
 * @property {number | null} score                0–1, null when ineligible.
 * @property {Record<string, number>} score_breakdown  Each value 0–1.
 */

/**
 * @typedef {object} RoutingDecision
 * @property {string} task_id
 * @property {ExecutionTarget} target
 * @property {number} score            0–1
 * @property {string[]} reasons        At least one. Length is not fixed.
 * @property {RoutingCandidate[]} ranked_candidates  Every target the engine
 *   looked at, highest score first, INCLUDING the ineligible ones. Never
 *   empty. The chosen target appears here too — it is not held out.
 *
 * The ranking is what lets the dashboard show why the other targets lost
 * rather than only announcing the winner. It is also the clearest evidence
 * that the engine, not the frontend, did the deciding: the UI renders an
 * order the backend already computed and never sorts or scores anything.
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
