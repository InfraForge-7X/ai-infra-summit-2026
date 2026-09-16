"""Tests for HardConstraintEvaluator."""

import pytest

from src.core.decision_engine import ConstraintThresholds, HardConstraintEvaluator
from src.shared import (
    ComputeRequirement,
    ExecutionTarget,
    InfrastructureState,
    PrivacyLevel,
    WorkloadProfile,
)

from .conftest import create_state


class TestLatencyConstraint:
    """Tests for latency constraint evaluation."""

    def test_latency_within_requirement_passes(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Target with latency under requirement should pass."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.EDGE, latency_ms=50.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is True
        assert len(reasons) == 0

    def test_latency_exceeds_requirement_fails(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Target with latency over requirement should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.CLOUD, latency_ms=150.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert any("Latency" in r for r in reasons)
        assert any("150" in r and "100" in r for r in reasons)

    def test_latency_exactly_at_requirement_passes(
        self, base_workload: WorkloadProfile
    ) -> None:
        """Target with latency exactly at requirement should pass."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.EDGE, latency_ms=100.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is True


class TestComputeConstraint:
    """Tests for compute (GPU) constraint evaluation."""

    def test_gpu_required_and_available_passes(
        self, base_workload: WorkloadProfile
    ) -> None:
        """GPU workload with GPU available should pass."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.EDGE, gpu_available=True)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is True

    def test_gpu_required_but_unavailable_fails(
        self, base_workload: WorkloadProfile
    ) -> None:
        """GPU workload without GPU should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.LOCAL, gpu_available=False)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert any("GPU required but not available" in r for r in reasons)

    def test_cpu_workload_without_gpu_passes(
        self, cpu_only_workload: WorkloadProfile
    ) -> None:
        """CPU workload without GPU available should pass."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.LOCAL, gpu_available=False)

        eligible, reasons = evaluator.evaluate(cpu_only_workload, state)

        assert eligible is True


class TestPrivacyConstraint:
    """Tests for privacy constraint evaluation."""

    def test_restricted_on_local_passes(
        self, restricted_workload: WorkloadProfile
    ) -> None:
        """RESTRICTED workload on LOCAL should pass."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.LOCAL)

        eligible, reasons = evaluator.evaluate(restricted_workload, state)

        assert eligible is True

    def test_restricted_on_edge_fails(
        self, restricted_workload: WorkloadProfile
    ) -> None:
        """RESTRICTED workload on EDGE should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.EDGE)

        eligible, reasons = evaluator.evaluate(restricted_workload, state)

        assert eligible is False
        assert any("RESTRICTED privacy requires LOCAL" in r for r in reasons)

    def test_restricted_on_cloud_fails(
        self, restricted_workload: WorkloadProfile
    ) -> None:
        """RESTRICTED workload on CLOUD should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.CLOUD)

        eligible, reasons = evaluator.evaluate(restricted_workload, state)

        assert eligible is False
        assert any("RESTRICTED privacy requires LOCAL" in r for r in reasons)

    def test_standard_privacy_on_any_target_passes(
        self, base_workload: WorkloadProfile
    ) -> None:
        """STANDARD privacy should pass on any target."""
        evaluator = HardConstraintEvaluator()

        for target in ExecutionTarget:
            state = create_state(target)
            eligible, reasons = evaluator.evaluate(base_workload, state)
            assert eligible is True, f"Failed for {target}"


class TestResourceConstraint:
    """Tests for resource availability constraints."""

    def test_cpu_under_threshold_passes(self, base_workload: WorkloadProfile) -> None:
        """CPU usage under threshold should pass."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.LOCAL, cpu_usage=80.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is True

    def test_cpu_over_threshold_fails(self, base_workload: WorkloadProfile) -> None:
        """CPU usage over threshold should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.LOCAL, cpu_usage=96.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert any("CPU usage" in r for r in reasons)

    def test_ram_over_threshold_fails(self, base_workload: WorkloadProfile) -> None:
        """RAM usage over threshold should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.LOCAL, ram_usage=98.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert any("RAM usage" in r for r in reasons)

    def test_custom_thresholds_applied(self, base_workload: WorkloadProfile) -> None:
        """Custom thresholds should be respected."""
        thresholds = ConstraintThresholds(max_cpu_usage=50.0)
        evaluator = HardConstraintEvaluator(thresholds=thresholds)
        state = create_state(ExecutionTarget.LOCAL, cpu_usage=60.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert any("50%" in r for r in reasons)


class TestNetworkConstraint:
    """Tests for network quality constraints."""

    def test_low_packet_loss_passes(self, base_workload: WorkloadProfile) -> None:
        """Low packet loss should pass."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.EDGE, packet_loss=2.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is True

    def test_high_packet_loss_fails(self, base_workload: WorkloadProfile) -> None:
        """High packet loss should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.EDGE, packet_loss=15.0)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert any("Packet loss" in r for r in reasons)

    def test_insufficient_bandwidth_fails(self, base_workload: WorkloadProfile) -> None:
        """Insufficient bandwidth should fail."""
        evaluator = HardConstraintEvaluator()
        state = create_state(ExecutionTarget.EDGE, bandwidth_mbps=0.5)

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert any("Bandwidth" in r for r in reasons)


class TestMultipleConstraintViolations:
    """Tests for scenarios with multiple constraint violations."""

    def test_multiple_violations_all_reported(
        self, base_workload: WorkloadProfile
    ) -> None:
        """All violated constraints should be reported."""
        evaluator = HardConstraintEvaluator()
        state = create_state(
            ExecutionTarget.CLOUD,
            latency_ms=200.0,  # Exceeds 100ms requirement
            gpu_available=False,  # GPU required
            cpu_usage=98.0,  # Over threshold
        )

        eligible, reasons = evaluator.evaluate(base_workload, state)

        assert eligible is False
        assert len(reasons) >= 3
        assert any("Latency" in r for r in reasons)
        assert any("GPU" in r for r in reasons)
        assert any("CPU" in r for r in reasons)
