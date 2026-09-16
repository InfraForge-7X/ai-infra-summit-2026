"""Scoring engine for the Decision Engine.

Computes normalized scores (0-1) for each dimension and produces
a weighted composite score. All scoring logic is deterministic and
its tunable parameters are provided by configuration.
"""

from src.shared import InfrastructureState, WorkloadProfile

from .config import ScoringParameters, ScoringWeights


class ScoringEngine:
    """Computes multi-dimensional scores for eligible targets."""

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        parameters: ScoringParameters | None = None,
    ) -> None:
        """Initialize with configurable weights and scoring parameters."""
        self._weights = weights or ScoringWeights()
        self._parameters = parameters or ScoringParameters()

    def score(
        self,
        workload: WorkloadProfile,
        state: InfrastructureState,
    ) -> tuple[float, dict[str, float]]:
        """Compute composite score and breakdown for a target."""
        breakdown: dict[str, float] = {
            "performance": self._score_performance(workload, state),
            "resources": self._score_resources(state),
            "network": self._score_network(state),
            "reliability": self._score_reliability(state),
            "cost": self._score_cost(state),
        }

        composite = (
            self._weights.performance * breakdown["performance"]
            + self._weights.resources * breakdown["resources"]
            + self._weights.network * breakdown["network"]
            + self._weights.reliability * breakdown["reliability"]
            + self._weights.cost * breakdown["cost"]
        )

        return max(0.0, min(1.0, composite)), breakdown

    def _score_performance(
        self,
        workload: WorkloadProfile,
        state: InfrastructureState,
    ) -> float:
        """Score latency relative to the workload requirement and queue depth."""
        if workload.latency_requirement <= 0:
            return 0.0

        ratio = state.latency_ms / workload.latency_requirement
        score = 1.0 - ratio
        queue_penalty = min(
            state.queue * self._parameters.queue_penalty_per_task,
            self._parameters.max_queue_penalty,
        )
        return max(0.0, min(1.0, score - queue_penalty))

    def _score_resources(self, state: InfrastructureState) -> float:
        """Score CPU/RAM headroom and GPU availability."""
        max_usage = max(state.cpu_usage, state.ram_usage)
        base_score = 1.0 - (max_usage / 100.0)
        gpu_bonus = self._parameters.gpu_bonus if state.gpu_available else 0.0
        return max(0.0, min(1.0, base_score + gpu_bonus))

    def _score_network(self, state: InfrastructureState) -> float:
        """Score bandwidth adequacy and packet loss."""
        bandwidth_score = min(
            state.bandwidth_mbps / self._parameters.bandwidth_reference_mbps,
            1.0,
        )
        loss_factor = 1.0 - (state.packet_loss / 100.0)
        return max(0.0, min(1.0, bandwidth_score * loss_factor))

    def _score_reliability(self, state: InfrastructureState) -> float:
        """Return the MVP reliability placeholder."""
        _ = state
        return 1.0

    def _score_cost(self, state: InfrastructureState) -> float:
        """Return the configured relative cost score for the target."""
        return self._parameters.cost_scores.get(state.target, 0.5)
