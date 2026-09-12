"""Configuration for the Decision Engine.

All weights, thresholds, and tunable parameters are defined here.
No magic numbers should be scattered in the implementation.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringWeights:
    """Configurable weights for multi-dimensional scoring.

    All weights should sum to 1.0 for normalized composite scores.
    Each weight represents the relative importance of that dimension.
    """

    performance: float = 0.30  # Latency relative to requirement, queue depth
    resources: float = 0.25  # CPU, RAM utilization, GPU availability
    network: float = 0.20  # Bandwidth adequacy, packet loss
    reliability: float = 0.15  # Historical uptime (placeholder for MVP)
    cost: float = 0.10  # Operational cost by target type

    def __post_init__(self) -> None:
        """Validate weights sum to 1.0 within tolerance."""
        total = self.performance + self.resources + self.network + self.reliability + self.cost
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Scoring weights must sum to 1.0, got {total:.2f}")

        for name, value in [
            ("performance", self.performance),
            ("resources", self.resources),
            ("network", self.network),
            ("reliability", self.reliability),
            ("cost", self.cost),
        ]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Weight '{name}' must be between 0 and 1, got {value}")


@dataclass(frozen=True)
class ConstraintThresholds:
    """Thresholds for hard constraint evaluation.

    These define when a target becomes ineligible.
    """

    max_cpu_usage: float = 95.0  # Exclude if CPU usage exceeds this
    max_ram_usage: float = 95.0  # Exclude if RAM usage exceeds this
    max_packet_loss: float = 10.0  # Exclude if packet loss exceeds this
    min_bandwidth_mbps: float = 1.0  # Exclude if bandwidth below this


@dataclass(frozen=True)
class DecisionEngineConfig:
    """Top-level configuration for the Decision Engine.

    Attributes:
        scoring_weights: Weights for each scoring dimension.
        constraint_thresholds: Thresholds for hard constraints.
        switching_threshold: Minimum score improvement (0-1) required to switch
            targets. Prevents flapping between similar-scoring targets.
        max_state_age_seconds: Maximum age of infrastructure state before
            it's considered stale.
    """

    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)
    constraint_thresholds: ConstraintThresholds = field(default_factory=ConstraintThresholds)
    switching_threshold: float = 0.15  # 15% improvement required to switch
    max_state_age_seconds: float = 30.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not (0.0 <= self.switching_threshold <= 1.0):
            raise ValueError(
                f"switching_threshold must be between 0 and 1, got {self.switching_threshold}"
            )
        if self.max_state_age_seconds <= 0:
            raise ValueError(
                f"max_state_age_seconds must be positive, got {self.max_state_age_seconds}"
            )
