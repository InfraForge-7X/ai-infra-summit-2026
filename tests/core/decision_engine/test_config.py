"""Tests for Decision Engine configuration."""

import pytest

from src.core.decision_engine import (
    ConstraintThresholds,
    DecisionEngineConfig,
    ScoringWeights,
)


class TestScoringWeights:
    """Tests for ScoringWeights configuration."""

    def test_default_weights_sum_to_one(self) -> None:
        """Default weights should sum to 1.0."""
        weights = ScoringWeights()
        total = (
            weights.performance
            + weights.resources
            + weights.network
            + weights.reliability
            + weights.cost
        )
        assert abs(total - 1.0) < 0.01

    def test_custom_weights_valid(self) -> None:
        """Custom weights that sum to 1.0 should be accepted."""
        weights = ScoringWeights(
            performance=0.4,
            resources=0.3,
            network=0.15,
            reliability=0.1,
            cost=0.05,
        )
        assert weights.performance == 0.4
        assert weights.cost == 0.05

    def test_weights_not_summing_to_one_rejected(self) -> None:
        """Weights not summing to 1.0 should be rejected."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            ScoringWeights(
                performance=0.5,
                resources=0.5,
                network=0.5,
                reliability=0.5,
                cost=0.5,
            )

    def test_negative_weight_rejected(self) -> None:
        """Negative weights should be rejected."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            ScoringWeights(
                performance=-0.1,
                resources=0.4,
                network=0.3,
                reliability=0.2,
                cost=0.2,
            )

    def test_weight_over_one_rejected(self) -> None:
        """Weights over 1.0 should be rejected."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            ScoringWeights(
                performance=1.5,
                resources=-0.2,
                network=-0.1,
                reliability=-0.1,
                cost=-0.1,
            )


class TestConstraintThresholds:
    """Tests for ConstraintThresholds configuration."""

    def test_default_thresholds(self) -> None:
        """Default thresholds should be sensible."""
        thresholds = ConstraintThresholds()
        assert thresholds.max_cpu_usage == 95.0
        assert thresholds.max_ram_usage == 95.0
        assert thresholds.max_packet_loss == 10.0
        assert thresholds.min_bandwidth_mbps == 1.0

    def test_custom_thresholds(self) -> None:
        """Custom thresholds should be accepted."""
        thresholds = ConstraintThresholds(
            max_cpu_usage=80.0,
            max_ram_usage=85.0,
            max_packet_loss=5.0,
            min_bandwidth_mbps=10.0,
        )
        assert thresholds.max_cpu_usage == 80.0
        assert thresholds.min_bandwidth_mbps == 10.0


class TestDecisionEngineConfig:
    """Tests for DecisionEngineConfig."""

    def test_default_config(self) -> None:
        """Default config should be valid."""
        config = DecisionEngineConfig()
        assert config.switching_threshold == 0.15
        assert config.max_state_age_seconds == 30.0
        assert isinstance(config.scoring_weights, ScoringWeights)
        assert isinstance(config.constraint_thresholds, ConstraintThresholds)

    def test_custom_config(self) -> None:
        """Custom config should be accepted."""
        config = DecisionEngineConfig(
            switching_threshold=0.20,
            max_state_age_seconds=60.0,
        )
        assert config.switching_threshold == 0.20
        assert config.max_state_age_seconds == 60.0

    def test_invalid_switching_threshold_rejected(self) -> None:
        """Switching threshold outside [0, 1] should be rejected."""
        with pytest.raises(ValueError, match="switching_threshold"):
            DecisionEngineConfig(switching_threshold=1.5)

        with pytest.raises(ValueError, match="switching_threshold"):
            DecisionEngineConfig(switching_threshold=-0.1)

    def test_invalid_max_state_age_rejected(self) -> None:
        """Non-positive max_state_age should be rejected."""
        with pytest.raises(ValueError, match="max_state_age_seconds"):
            DecisionEngineConfig(max_state_age_seconds=0)

        with pytest.raises(ValueError, match="max_state_age_seconds"):
            DecisionEngineConfig(max_state_age_seconds=-10)

    def test_config_is_immutable(self) -> None:
        """Config should be frozen (immutable)."""
        config = DecisionEngineConfig()
        with pytest.raises(AttributeError):
            config.switching_threshold = 0.5  # type: ignore[misc]
