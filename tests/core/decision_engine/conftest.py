"""Shared fixtures for Decision Engine tests."""

from datetime import datetime, timezone

import pytest

from src.shared import (
    ComputeRequirement,
    ExecutionTarget,
    InfrastructureState,
    Priority,
    PrivacyLevel,
    WorkloadProfile,
    WorkloadType,
)


@pytest.fixture
def base_workload() -> WorkloadProfile:
    """Create a standard workload for testing."""
    return WorkloadProfile(
        task_id="test-task-001",
        workload_type=WorkloadType.REAL_TIME_VIDEO,
        model="yolo",
        input_size=640,
        latency_requirement=100,  # 100ms
        compute_requirement=ComputeRequirement.GPU,
        privacy=PrivacyLevel.STANDARD,
        priority=Priority.HIGH,
    )


@pytest.fixture
def cpu_only_workload() -> WorkloadProfile:
    """Create a CPU-only workload."""
    return WorkloadProfile(
        task_id="test-task-002",
        workload_type=WorkloadType.BATCH_INFERENCE,
        model="bert",
        input_size=512,
        latency_requirement=500,
        compute_requirement=ComputeRequirement.CPU,
        privacy=PrivacyLevel.STANDARD,
        priority=Priority.MEDIUM,
    )


@pytest.fixture
def restricted_workload() -> WorkloadProfile:
    """Create a privacy-restricted workload."""
    return WorkloadProfile(
        task_id="test-task-003",
        workload_type=WorkloadType.SPEECH,
        model="whisper",
        input_size=16000,
        latency_requirement=200,
        compute_requirement=ComputeRequirement.ANY,
        privacy=PrivacyLevel.RESTRICTED,
        priority=Priority.HIGH,
    )


def create_state(
    target: ExecutionTarget,
    cpu_usage: float = 30.0,
    gpu_available: bool = True,
    ram_usage: float = 40.0,
    queue: int = 0,
    latency_ms: float = 10.0,
    bandwidth_mbps: float = 100.0,
    packet_loss: float = 0.0,
    timestamp: datetime | None = None,
) -> InfrastructureState:
    """Factory for creating infrastructure states."""
    return InfrastructureState(
        target=target,
        cpu_usage=cpu_usage,
        gpu_available=gpu_available,
        ram_usage=ram_usage,
        queue=queue,
        latency_ms=latency_ms,
        bandwidth_mbps=bandwidth_mbps,
        packet_loss=packet_loss,
        timestamp=timestamp or datetime.now(timezone.utc),
    )


@pytest.fixture
def healthy_local_state() -> InfrastructureState:
    """Create a healthy LOCAL state."""
    return create_state(
        target=ExecutionTarget.LOCAL,
        cpu_usage=20.0,
        gpu_available=True,
        ram_usage=30.0,
        latency_ms=2.0,
        bandwidth_mbps=1000.0,
    )


@pytest.fixture
def healthy_edge_state() -> InfrastructureState:
    """Create a healthy EDGE state."""
    return create_state(
        target=ExecutionTarget.EDGE,
        cpu_usage=40.0,
        gpu_available=True,
        ram_usage=50.0,
        latency_ms=15.0,
        bandwidth_mbps=200.0,
    )


@pytest.fixture
def healthy_cloud_state() -> InfrastructureState:
    """Create a healthy CLOUD state."""
    return create_state(
        target=ExecutionTarget.CLOUD,
        cpu_usage=25.0,
        gpu_available=True,
        ram_usage=35.0,
        latency_ms=50.0,
        bandwidth_mbps=500.0,
    )


@pytest.fixture
def all_healthy_states(
    healthy_local_state: InfrastructureState,
    healthy_edge_state: InfrastructureState,
    healthy_cloud_state: InfrastructureState,
) -> list[InfrastructureState]:
    """Create states for all targets in healthy condition."""
    return [healthy_local_state, healthy_edge_state, healthy_cloud_state]
