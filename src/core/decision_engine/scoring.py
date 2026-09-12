"""Scoring engine for the Decision Engine.

Computes normalized scores (0-1) for each dimension and produces
a weighted composite score. All scoring logic is deterministic.
"""

from src.shared import ExecutionTarget, InfrastructureState, WorkloadProfile

from .config import ScoringWeights


class ScoringEngine:
    """Computes multi-dimensional scores for eligible targets.

    Scoring dimensions:
    - Performance: How well latency meets requirements
    - Resources: CPU/RAM availability and GPU bonus
    - Network: Bandwidth adequacy and packet loss penalty
    - Reliability: Historical uptime (placeholder for MVP)
    - Cost: Operational cost by target type
    """

    # Cost scores by target type (higher = cheaper)
    # LOCAL is free, EDGE has some cost, CLOUD is most expensive
    _COST_SCORES: dict[ExecutionTarget, float] = {
        ExecutionTarget.LOCAL: 1.0,
        ExecutionTarget.EDGE: 0.7,
        ExecutionTarget.CLOUD: 0.4,
    }

    # Bandwidth reference for normalization (Mbps)
    _BANDWIDTH_REFERENCE: float = 100.0

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with configurable weights.

        Args:
            weights: Scoring weights. Uses defaults if not provided.
        """
        self._weights = weights or ScoringWeights()

    def score(
        self,
        workload: WorkloadProfile,
        state: InfrastructureState,
    ) -> tuple[float, dict[str, float]]:
        """Compute composite score and breakdown for a target.

        Args:
            workload: The workload requirements.
            state: Current infrastructure state of the target.

        Returns:
            A tuple of (composite_score, score_breakdown).
            composite_score is the weighted sum (0-1).
            score_breakdown contains per-dimension scores.
        """
        breakdown: dict[str, float] = {}

        # Performance score: How well latency meets requirement
        # Lower latency relative to requirement = higher score
        breakdown["performance"] = self._score_performance(workload, state)

        # Resources score: CPU/RAM availability with GPU bonus
        breakdown["resources"] = self._score_resources(state)

        # Network score: Bandwidth and packet loss
        breakdown["network"] = self._score_network(state)

        # Reliability score: Placeholder for MVP (always 1.0)
        breakdown["reliability"] = self._score_reliability(state)

        # Cost score: Based on target type
        breakdown["cost"] = self._score_cost(state)

        # Compute weighted composite score
        composite = (
            self._weights.performance * breakdown["performance"]
            + self._weights.resources * breakdown["resources"]
            + self._weights.network * breakdown["network"]
            + self._weights.reliability * breakdown["reliability"]
            + self._weights.cost * breakdown["cost"]
        )

        # Clamp to [0, 1] for safety
        composite = max(0.0, min(1.0, composite))

        return composite, breakdown

    def _score_performance(
        self,
        workload: WorkloadProfile,
        state: InfrastructureState,
    ) -> float:
        """Score based on latency relative to requirement.

        Formula: 1 - (latency / requirement), clamped to [0, 1]
        Lower latency = higher score.
        """
        if workload.latency_requirement <= 0:
            return 0.0

        ratio = state.latency_ms / workload.latency_requirement
        # Invert: lower ratio = better
        score = 1.0 - ratio

        # Also factor in queue depth (more queued = slower)
        # Each queued task reduces score slightly
        queue_penalty = min(state.queue * 0.05, 0.3)  # Cap at 30% penalty
        score -= queue_penalty

        return max(0.0, min(1.0, score))

    def _score_resources(self, state: InfrastructureState) -> float:
        """Score based on resource availability.

        Formula: 1 - max(cpu_usage, ram_usage) / 100
        Lower utilization = more headroom = higher score.
        GPU availability adds a bonus.
        """
        max_usage = max(state.cpu_usage, state.ram_usage)
        base_score = 1.0 - (max_usage / 100.0)

        # GPU bonus: having GPU available is valuable
        gpu_bonus = 0.1 if state.gpu_available else 0.0

        return max(0.0, min(1.0, base_score + gpu_bonus))

    def _score_network(self, state: InfrastructureState) -> float:
        """Score based on network quality.

        Combines bandwidth adequacy and packet loss penalty.
        """
        # Bandwidth score: normalize against reference
        bandwidth_score = min(state.bandwidth_mbps / self._BANDWIDTH_REFERENCE, 1.0)

        # Packet loss penalty: each 1% loss reduces score
        loss_factor = 1.0 - (state.packet_loss / 100.0)

        return max(0.0, min(1.0, bandwidth_score * loss_factor))

    def _score_reliability(self, state: InfrastructureState) -> float:
        """Score based on historical reliability.

        Placeholder for MVP: always returns 1.0.
        Future: integrate with metrics/feedback system.
        """
        # TODO: Integrate with historical uptime data
        _ = state  # Unused for now
        return 1.0

    def _score_cost(self, state: InfrastructureState) -> float:
        """Score based on operational cost.

        LOCAL is free (1.0), EDGE has some cost (0.7), CLOUD is expensive (0.4).
        """
        return self._COST_SCORES.get(state.target, 0.5)
