"""Tests for ScoringEngine."""

import pytest

from src.core.decision_engine import ScoringEngine, ScoringWeights
from src.shared import ExecutionTarget, InfrastructureState, WorkloadProfile

from .conftest import create_state


class TestPerformanceScoring:
    """Tests for performance dimension scoring."""

    def test_low_latency_scores_high(self, base_workload: WorkloadProfile) -> None:
        """Low latency relative to requirement should score high."""
        engine = ScoringEngine()
        state = create_state(ExecutionTarget.LOCAL, latency_ms=10.0, queue=0)

        score, breakdown = engine.score(base_workload, state)

        # Latency is 10ms vs 100ms requirement = 90% headroom
        assert breakdown["performance"] > 0.8

    def test_high_latency_scores_low(self, base_workload: WorkloadProfile) -> None:
        """High latency relative to requirement should score low."""
        engine = ScoringEngine()
        state = create_state(ExecutionTarget.CLOUD, latency_ms=90.0, queue=0)

        score, breakdown = engine.score(base_workload, state)

        # Latency is 90ms vs 100ms requirement = only 10% headroom
        assert breakdown["performance"] < 0.2

    def test_queue_depth_reduces_performance_score(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Higher queue depth should reduce performance score."""
        engine = ScoringEngine()
        state_empty_queue = create_state(ExecutionTarget.EDGE, latency_ms=20.0, queue=0)
        state_full_queue = create_state(ExecutionTarget.EDGE, latency_ms=20.0, queue=5)

        _, breakdown_empty = engine.score(base_workload, state_empty_queue)
        _, breakdown_full = engine.score(base_workload, state_full_queue)

        assert breakdown_full["performance"] < breakdown_empty["performance"]


class TestResourceScoring:
    """Tests for resource dimension scoring."""

    def test_low_utilization_scores_high(self, base_workload: WorkloadProfile) -> None:
        """Low CPU/RAM utilization should score high."""
        engine = ScoringEngine()
        state = create_state(
            ExecutionTarget.LOCAL,
            cpu_usage=20.0,
            ram_usage=30.0,
            gpu_available=True,
        )

        score, breakdown = engine.score(base_workload, state)

        # max(20, 30) = 30, so 1 - 0.3 = 0.7, plus GPU bonus
        assert breakdown["resources"] >= 0.7

    def test_high_utilization_scores_low(self, base_workload: WorkloadProfile) -> None:
        """High CPU/RAM utilization should score low."""
        engine = ScoringEngine()
        state = create_state(
            ExecutionTarget.LOCAL,
            cpu_usage=90.0,
            ram_usage=85.0,
            gpu_available=False,
        )

        score, breakdown = engine.score(base_workload, state)

        # max(90, 85) = 90, so 1 - 0.9 = 0.1
        assert breakdown["resources"] < 0.2

    def test_gpu_available_adds_bonus(self, base_workload: WorkloadProfile) -> None:
        """GPU availability should add bonus to resource score."""
        engine = ScoringEngine()
        state_with_gpu = create_state(
            ExecutionTarget.EDGE,
            cpu_usage=50.0,
            ram_usage=50.0,
            gpu_available=True,
        )
        state_without_gpu = create_state(
            ExecutionTarget.EDGE,
            cpu_usage=50.0,
            ram_usage=50.0,
            gpu_available=False,
        )

        _, breakdown_with = engine.score(base_workload, state_with_gpu)
        _, breakdown_without = engine.score(base_workload, state_without_gpu)

        assert breakdown_with["resources"] > breakdown_without["resources"]


class TestNetworkScoring:
    """Tests for network dimension scoring."""

    def test_high_bandwidth_low_loss_scores_high(
        self, base_workload: WorkloadProfile
    ) -> None:
        """High bandwidth and low packet loss should score high."""
        engine = ScoringEngine()
        state = create_state(
            ExecutionTarget.EDGE,
            bandwidth_mbps=200.0,
            packet_loss=0.0,
        )

        score, breakdown = engine.score(base_workload, state)

        assert breakdown["network"] >= 0.9

    def test_low_bandwidth_scores_low(self, base_workload: WorkloadProfile) -> None:
        """Low bandwidth should score low."""
        engine = ScoringEngine()
        state = create_state(
            ExecutionTarget.EDGE,
            bandwidth_mbps=10.0,
            packet_loss=0.0,
        )

        score, breakdown = engine.score(base_workload, state)

        # 10/100 = 0.1
        assert breakdown["network"] < 0.2

    def test_packet_loss_reduces_network_score(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Packet loss should reduce network score."""
        engine = ScoringEngine()
        state_no_loss = create_state(
            ExecutionTarget.EDGE,
            bandwidth_mbps=100.0,
            packet_loss=0.0,
        )
        state_with_loss = create_state(
            ExecutionTarget.EDGE,
            bandwidth_mbps=100.0,
            packet_loss=5.0,
        )

        _, breakdown_no_loss = engine.score(base_workload, state_no_loss)
        _, breakdown_with_loss = engine.score(base_workload, state_with_loss)

        assert breakdown_with_loss["network"] < breakdown_no_loss["network"]


class TestCostScoring:
    """Tests for cost dimension scoring."""

    def test_local_has_highest_cost_score(self, base_workload: WorkloadProfile) -> None:
        """LOCAL should have highest cost score (cheapest)."""
        engine = ScoringEngine()

        _, local_breakdown = engine.score(
            base_workload, create_state(ExecutionTarget.LOCAL)
        )
        _, edge_breakdown = engine.score(
            base_workload, create_state(ExecutionTarget.EDGE)
        )
        _, cloud_breakdown = engine.score(
            base_workload, create_state(ExecutionTarget.CLOUD)
        )

        assert local_breakdown["cost"] > edge_breakdown["cost"]
        assert edge_breakdown["cost"] > cloud_breakdown["cost"]

    def test_cost_scores_match_expected_values(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Cost scores should match configured values."""
        engine = ScoringEngine()

        _, local = engine.score(base_workload, create_state(ExecutionTarget.LOCAL))
        _, edge = engine.score(base_workload, create_state(ExecutionTarget.EDGE))
        _, cloud = engine.score(base_workload, create_state(ExecutionTarget.CLOUD))

        assert local["cost"] == 1.0
        assert edge["cost"] == 0.7
        assert cloud["cost"] == 0.4


class TestCompositeScoring:
    """Tests for weighted composite score calculation."""

    def test_composite_score_in_valid_range(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Composite score should always be between 0 and 1."""
        engine = ScoringEngine()

        for target in ExecutionTarget:
            state = create_state(target)
            score, _ = engine.score(base_workload, state)
            assert 0.0 <= score <= 1.0

    def test_composite_score_respects_weights(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Composite score should be weighted average of dimensions."""
        weights = ScoringWeights(
            performance=0.5,
            resources=0.2,
            network=0.15,
            reliability=0.1,
            cost=0.05,
        )
        engine = ScoringEngine(weights=weights)
        state = create_state(ExecutionTarget.EDGE)

        score, breakdown = engine.score(base_workload, state)

        # Calculate expected composite
        expected = (
            0.5 * breakdown["performance"]
            + 0.2 * breakdown["resources"]
            + 0.15 * breakdown["network"]
            + 0.1 * breakdown["reliability"]
            + 0.05 * breakdown["cost"]
        )
        assert abs(score - expected) < 0.01

    def test_score_breakdown_contains_all_dimensions(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Score breakdown should contain all five dimensions."""
        engine = ScoringEngine()
        state = create_state(ExecutionTarget.EDGE)

        _, breakdown = engine.score(base_workload, state)

        expected_keys = {"performance", "resources", "network", "reliability", "cost"}
        assert set(breakdown.keys()) == expected_keys

    def test_all_breakdown_values_in_valid_range(
        self, base_workload: WorkloadProfile
    ) -> None:
        """All breakdown values should be between 0 and 1."""
        engine = ScoringEngine()

        for target in ExecutionTarget:
            state = create_state(target)
            _, breakdown = engine.score(base_workload, state)

            for dimension, value in breakdown.items():
                assert 0.0 <= value <= 1.0, f"{dimension} = {value} out of range"


class TestScoringDeterminism:
    """Tests for scoring determinism."""

    def test_same_inputs_produce_same_score(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Identical inputs should always produce identical scores."""
        engine = ScoringEngine()
        state = create_state(ExecutionTarget.EDGE, cpu_usage=45.0, latency_ms=25.0)

        score1, breakdown1 = engine.score(base_workload, state)
        score2, breakdown2 = engine.score(base_workload, state)

        assert score1 == score2
        assert breakdown1 == breakdown2
