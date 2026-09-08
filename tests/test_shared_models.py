"""Unit tests for AFRI-EDGE shared data contracts.

Tests cover:
- Valid model instantiation
- Required field validation
- Invalid value rejection
- Enum/type validation
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.shared import (
    ComputeRequirement,
    ExecutionResult,
    ExecutionStatus,
    ExecutionTarget,
    InfrastructureState,
    Priority,
    PrivacyLevel,
    RoutingDecision,
    WorkloadProfile,
    WorkloadType,
)


class TestWorkloadProfile:
    """Tests for WorkloadProfile model."""

    def test_valid_workload_profile(self) -> None:
        """Test creating a valid WorkloadProfile."""
        profile = WorkloadProfile(
            task_id="task-001",
            workload_type=WorkloadType.REAL_TIME_VIDEO,
            model="yolo",
            input_size=1920,
            latency_requirement=100,
            compute_requirement=ComputeRequirement.GPU,
            privacy=PrivacyLevel.STANDARD,
            priority=Priority.HIGH,
        )
        assert profile.task_id == "task-001"
        assert profile.workload_type == WorkloadType.REAL_TIME_VIDEO
        assert profile.model == "yolo"
        assert profile.input_size == 1920
        assert profile.latency_requirement == 100
        assert profile.compute_requirement == ComputeRequirement.GPU
        assert profile.privacy == PrivacyLevel.STANDARD
        assert profile.priority == Priority.HIGH

    def test_valid_workload_profile_with_defaults(self) -> None:
        """Test creating WorkloadProfile with default values."""
        profile = WorkloadProfile(
            task_id="task-002",
            workload_type=WorkloadType.REAL_TIME_VIDEO,
            model="yolo",
            input_size=1080,
            latency_requirement=50,
            compute_requirement=ComputeRequirement.CPU,
        )
        assert profile.privacy == PrivacyLevel.STANDARD
        assert profile.priority == Priority.MEDIUM

    def test_valid_workload_profile_from_string_enums(self) -> None:
        """Test creating WorkloadProfile with string enum values."""
        profile = WorkloadProfile(
            task_id="task-003",
            workload_type="real_time_video",
            model="yolo",
            input_size=1920,
            latency_requirement=100,
            compute_requirement="gpu",
            privacy="standard",
            priority="high",
        )
        assert profile.workload_type == WorkloadType.REAL_TIME_VIDEO
        assert profile.compute_requirement == ComputeRequirement.GPU

    def test_missing_required_task_id(self) -> None:
        """Test that missing task_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                workload_type=WorkloadType.REAL_TIME_VIDEO,
                model="yolo",
                input_size=1920,
                latency_requirement=100,
                compute_requirement=ComputeRequirement.GPU,
            )
        assert "task_id" in str(exc_info.value)

    def test_empty_task_id_rejected(self) -> None:
        """Test that empty task_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                task_id="",
                workload_type=WorkloadType.REAL_TIME_VIDEO,
                model="yolo",
                input_size=1920,
                latency_requirement=100,
                compute_requirement=ComputeRequirement.GPU,
            )
        assert "task_id" in str(exc_info.value)

    def test_invalid_input_size_zero(self) -> None:
        """Test that input_size=0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                task_id="task-001",
                workload_type=WorkloadType.REAL_TIME_VIDEO,
                model="yolo",
                input_size=0,
                latency_requirement=100,
                compute_requirement=ComputeRequirement.GPU,
            )
        assert "input_size" in str(exc_info.value)

    def test_invalid_input_size_negative(self) -> None:
        """Test that negative input_size is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                task_id="task-001",
                workload_type=WorkloadType.REAL_TIME_VIDEO,
                model="yolo",
                input_size=-100,
                latency_requirement=100,
                compute_requirement=ComputeRequirement.GPU,
            )
        assert "input_size" in str(exc_info.value)

    def test_invalid_latency_requirement_zero(self) -> None:
        """Test that latency_requirement=0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                task_id="task-001",
                workload_type=WorkloadType.REAL_TIME_VIDEO,
                model="yolo",
                input_size=1920,
                latency_requirement=0,
                compute_requirement=ComputeRequirement.GPU,
            )
        assert "latency_requirement" in str(exc_info.value)

    def test_invalid_workload_type(self) -> None:
        """Test that invalid workload_type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                task_id="task-001",
                workload_type="invalid_type",
                model="yolo",
                input_size=1920,
                latency_requirement=100,
                compute_requirement=ComputeRequirement.GPU,
            )
        assert "workload_type" in str(exc_info.value)

    def test_invalid_compute_requirement(self) -> None:
        """Test that invalid compute_requirement is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                task_id="task-001",
                workload_type=WorkloadType.REAL_TIME_VIDEO,
                model="yolo",
                input_size=1920,
                latency_requirement=100,
                compute_requirement="tpu",
            )
        assert "compute_requirement" in str(exc_info.value)

    def test_extra_fields_rejected(self) -> None:
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkloadProfile(
                task_id="task-001",
                workload_type=WorkloadType.REAL_TIME_VIDEO,
                model="yolo",
                input_size=1920,
                latency_requirement=100,
                compute_requirement=ComputeRequirement.GPU,
                extra_field="not_allowed",
            )
        assert "extra_field" in str(exc_info.value)


class TestInfrastructureState:
    """Tests for InfrastructureState model."""

    def test_valid_infrastructure_state(self) -> None:
        """Test creating a valid InfrastructureState."""
        timestamp = datetime.now(timezone.utc)
        state = InfrastructureState(
            target=ExecutionTarget.EDGE,
            cpu_usage=72.5,
            gpu_available=True,
            ram_usage=61.0,
            queue=2,
            latency_ms=18.5,
            bandwidth_mbps=85.0,
            packet_loss=0.2,
            timestamp=timestamp,
        )
        assert state.target == ExecutionTarget.EDGE
        assert state.cpu_usage == 72.5
        assert state.gpu_available is True
        assert state.ram_usage == 61.0
        assert state.queue == 2
        assert state.latency_ms == 18.5
        assert state.bandwidth_mbps == 85.0
        assert state.packet_loss == 0.2
        assert state.timestamp == timestamp

    def test_valid_infrastructure_state_from_string_target(self) -> None:
        """Test creating InfrastructureState with string target."""
        state = InfrastructureState(
            target="cloud",
            cpu_usage=50.0,
            gpu_available=True,
            ram_usage=40.0,
            queue=0,
            latency_ms=50.0,
            bandwidth_mbps=100.0,
            packet_loss=0.0,
            timestamp=datetime.now(timezone.utc),
        )
        assert state.target == ExecutionTarget.CLOUD

    def test_valid_boundary_values(self) -> None:
        """Test boundary values for percentage fields."""
        state = InfrastructureState(
            target=ExecutionTarget.LOCAL,
            cpu_usage=0.0,
            gpu_available=False,
            ram_usage=100.0,
            queue=0,
            latency_ms=0.0,
            bandwidth_mbps=0.0,
            packet_loss=0.0,
            timestamp=datetime.now(timezone.utc),
        )
        assert state.cpu_usage == 0.0
        assert state.ram_usage == 100.0

    def test_invalid_cpu_usage_over_100(self) -> None:
        """Test that cpu_usage > 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target=ExecutionTarget.EDGE,
                cpu_usage=101.0,
                gpu_available=True,
                ram_usage=50.0,
                queue=0,
                latency_ms=10.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        assert "cpu_usage" in str(exc_info.value)

    def test_invalid_cpu_usage_negative(self) -> None:
        """Test that negative cpu_usage is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target=ExecutionTarget.EDGE,
                cpu_usage=-5.0,
                gpu_available=True,
                ram_usage=50.0,
                queue=0,
                latency_ms=10.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        assert "cpu_usage" in str(exc_info.value)

    def test_invalid_ram_usage_over_100(self) -> None:
        """Test that ram_usage > 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target=ExecutionTarget.EDGE,
                cpu_usage=50.0,
                gpu_available=True,
                ram_usage=150.0,
                queue=0,
                latency_ms=10.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        assert "ram_usage" in str(exc_info.value)

    def test_invalid_packet_loss_over_100(self) -> None:
        """Test that packet_loss > 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target=ExecutionTarget.EDGE,
                cpu_usage=50.0,
                gpu_available=True,
                ram_usage=50.0,
                queue=0,
                latency_ms=10.0,
                bandwidth_mbps=100.0,
                packet_loss=101.0,
                timestamp=datetime.now(timezone.utc),
            )
        assert "packet_loss" in str(exc_info.value)

    def test_invalid_negative_queue(self) -> None:
        """Test that negative queue is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target=ExecutionTarget.EDGE,
                cpu_usage=50.0,
                gpu_available=True,
                ram_usage=50.0,
                queue=-1,
                latency_ms=10.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        assert "queue" in str(exc_info.value)

    def test_invalid_negative_latency(self) -> None:
        """Test that negative latency_ms is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target=ExecutionTarget.EDGE,
                cpu_usage=50.0,
                gpu_available=True,
                ram_usage=50.0,
                queue=0,
                latency_ms=-10.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        assert "latency_ms" in str(exc_info.value)

    def test_invalid_target(self) -> None:
        """Test that invalid target is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target="invalid_target",
                cpu_usage=50.0,
                gpu_available=True,
                ram_usage=50.0,
                queue=0,
                latency_ms=10.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        assert "target" in str(exc_info.value)

    def test_missing_required_timestamp(self) -> None:
        """Test that missing timestamp raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InfrastructureState(
                target=ExecutionTarget.EDGE,
                cpu_usage=50.0,
                gpu_available=True,
                ram_usage=50.0,
                queue=0,
                latency_ms=10.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
            )
        assert "timestamp" in str(exc_info.value)


class TestRoutingDecision:
    """Tests for RoutingDecision model."""

    def test_valid_routing_decision(self) -> None:
        """Test creating a valid RoutingDecision."""
        decision = RoutingDecision(
            task_id="task-001",
            target=ExecutionTarget.EDGE,
            score=0.85,
            reasons=["Low latency", "GPU available", "Sufficient bandwidth"],
        )
        assert decision.task_id == "task-001"
        assert decision.target == ExecutionTarget.EDGE
        assert decision.score == 0.85
        assert len(decision.reasons) == 3

    def test_valid_routing_decision_single_reason(self) -> None:
        """Test creating RoutingDecision with single reason."""
        decision = RoutingDecision(
            task_id="task-002",
            target=ExecutionTarget.CLOUD,
            score=0.95,
            reasons=["Only eligible target"],
        )
        assert len(decision.reasons) == 1

    def test_valid_routing_decision_boundary_scores(self) -> None:
        """Test boundary values for score."""
        decision_min = RoutingDecision(
            task_id="task-001",
            target=ExecutionTarget.LOCAL,
            score=0.0,
            reasons=["Minimum score"],
        )
        decision_max = RoutingDecision(
            task_id="task-002",
            target=ExecutionTarget.CLOUD,
            score=1.0,
            reasons=["Maximum score"],
        )
        assert decision_min.score == 0.0
        assert decision_max.score == 1.0

    def test_invalid_score_over_1(self) -> None:
        """Test that score > 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                score=1.5,
                reasons=["Invalid score"],
            )
        assert "score" in str(exc_info.value)

    def test_invalid_score_negative(self) -> None:
        """Test that negative score is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                score=-0.5,
                reasons=["Invalid score"],
            )
        assert "score" in str(exc_info.value)

    def test_empty_reasons_rejected(self) -> None:
        """Test that empty reasons list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                score=0.5,
                reasons=[],
            )
        assert "reasons" in str(exc_info.value)

    def test_empty_string_reason_rejected(self) -> None:
        """Test that empty string in reasons is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                score=0.5,
                reasons=["Valid reason", ""],
            )
        assert "reasons" in str(exc_info.value)

    def test_whitespace_only_reason_rejected(self) -> None:
        """Test that whitespace-only reason is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                score=0.5,
                reasons=["Valid reason", "   "],
            )
        assert "reasons" in str(exc_info.value)

    def test_missing_task_id(self) -> None:
        """Test that missing task_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                target=ExecutionTarget.EDGE,
                score=0.5,
                reasons=["A reason"],
            )
        assert "task_id" in str(exc_info.value)


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_valid_execution_result(self) -> None:
        """Test creating a valid ExecutionResult."""
        result = ExecutionResult(
            task_id="task-001",
            target=ExecutionTarget.EDGE,
            status=ExecutionStatus.COMPLETED,
            execution_time_ms=45.0,
            network_latency_ms=12.0,
            fps=30.5,
        )
        assert result.task_id == "task-001"
        assert result.target == ExecutionTarget.EDGE
        assert result.status == ExecutionStatus.COMPLETED
        assert result.execution_time_ms == 45.0
        assert result.network_latency_ms == 12.0
        assert result.fps == 30.5

    def test_valid_execution_result_without_fps(self) -> None:
        """Test creating ExecutionResult without FPS (non-video workload)."""
        result = ExecutionResult(
            task_id="task-001",
            target=ExecutionTarget.CLOUD,
            status=ExecutionStatus.COMPLETED,
            execution_time_ms=100.0,
            network_latency_ms=50.0,
        )
        assert result.fps is None

    def test_valid_execution_result_failed_status(self) -> None:
        """Test creating ExecutionResult with FAILED status."""
        result = ExecutionResult(
            task_id="task-001",
            target=ExecutionTarget.LOCAL,
            status=ExecutionStatus.FAILED,
            execution_time_ms=10.0,
            network_latency_ms=0.0,
        )
        assert result.status == ExecutionStatus.FAILED

    def test_valid_execution_result_timeout_status(self) -> None:
        """Test creating ExecutionResult with TIMEOUT status."""
        result = ExecutionResult(
            task_id="task-001",
            target=ExecutionTarget.CLOUD,
            status=ExecutionStatus.TIMEOUT,
            execution_time_ms=5000.0,
            network_latency_ms=200.0,
        )
        assert result.status == ExecutionStatus.TIMEOUT

    def test_valid_execution_result_from_string_enums(self) -> None:
        """Test creating ExecutionResult with string enum values."""
        result = ExecutionResult(
            task_id="task-001",
            target="edge",
            status="completed",
            execution_time_ms=45.0,
            network_latency_ms=12.0,
            fps=30.0,
        )
        assert result.target == ExecutionTarget.EDGE
        assert result.status == ExecutionStatus.COMPLETED

    def test_invalid_negative_execution_time(self) -> None:
        """Test that negative execution_time_ms is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                status=ExecutionStatus.COMPLETED,
                execution_time_ms=-10.0,
                network_latency_ms=5.0,
            )
        assert "execution_time_ms" in str(exc_info.value)

    def test_invalid_negative_network_latency(self) -> None:
        """Test that negative network_latency_ms is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                status=ExecutionStatus.COMPLETED,
                execution_time_ms=10.0,
                network_latency_ms=-5.0,
            )
        assert "network_latency_ms" in str(exc_info.value)

    def test_invalid_negative_fps(self) -> None:
        """Test that negative fps is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                status=ExecutionStatus.COMPLETED,
                execution_time_ms=45.0,
                network_latency_ms=12.0,
                fps=-30.0,
            )
        assert "fps" in str(exc_info.value)

    def test_invalid_status(self) -> None:
        """Test that invalid status is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionResult(
                task_id="task-001",
                target=ExecutionTarget.EDGE,
                status="invalid_status",
                execution_time_ms=45.0,
                network_latency_ms=12.0,
            )
        assert "status" in str(exc_info.value)

    def test_all_execution_statuses(self) -> None:
        """Test that all ExecutionStatus values are valid."""
        for status in ExecutionStatus:
            result = ExecutionResult(
                task_id="task-001",
                target=ExecutionTarget.LOCAL,
                status=status,
                execution_time_ms=10.0,
                network_latency_ms=0.0,
            )
            assert result.status == status


class TestEnumValues:
    """Tests for enum completeness and string conversion."""

    def test_workload_types(self) -> None:
        """Test all WorkloadType values."""
        assert WorkloadType.REAL_TIME_VIDEO.value == "real_time_video"
        assert WorkloadType.SPEECH.value == "speech"
        assert WorkloadType.BATCH_INFERENCE.value == "batch_inference"

    def test_compute_requirements(self) -> None:
        """Test all ComputeRequirement values."""
        assert ComputeRequirement.CPU.value == "cpu"
        assert ComputeRequirement.GPU.value == "gpu"
        assert ComputeRequirement.ANY.value == "any"

    def test_privacy_levels(self) -> None:
        """Test all PrivacyLevel values."""
        assert PrivacyLevel.STANDARD.value == "standard"
        assert PrivacyLevel.SENSITIVE.value == "sensitive"
        assert PrivacyLevel.RESTRICTED.value == "restricted"

    def test_priorities(self) -> None:
        """Test all Priority values."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.CRITICAL.value == "critical"

    def test_execution_targets(self) -> None:
        """Test all ExecutionTarget values."""
        assert ExecutionTarget.LOCAL.value == "local"
        assert ExecutionTarget.EDGE.value == "edge"
        assert ExecutionTarget.CLOUD.value == "cloud"

    def test_execution_statuses(self) -> None:
        """Test all ExecutionStatus values."""
        expected_statuses = [
            "created",
            "routing",
            "dispatched",
            "running",
            "completed",
            "result_returned",
            "failed",
            "timeout",
            "cancelled",
        ]
        actual_statuses = [s.value for s in ExecutionStatus]
        assert sorted(actual_statuses) == sorted(expected_statuses)
