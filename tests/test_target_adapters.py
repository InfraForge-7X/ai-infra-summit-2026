"""Unit tests for AFRI-EDGE Target Adapters (Task #10)."""

import pytest

from src.adapters.base import TargetAdapter
from src.adapters.cloud_adapter import CloudTargetAdapter
from src.adapters.edge_adapter import EdgeTargetAdapter
from src.adapters.local_adapter import LocalTargetAdapter
from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import ExecutionResult, RoutingCandidate, RoutingDecision


@pytest.fixture
def sample_routing_decision() -> RoutingDecision:
    """Fixture providing a sample RoutingDecision."""
    candidate = RoutingCandidate(
        target=ExecutionTarget.LOCAL,
        eligible=True,
        score=0.95,
        score_breakdown={"performance": 0.95},
    )
    return RoutingDecision(
        task_id="task-test-123",
        target=ExecutionTarget.LOCAL,
        score=0.95,
        reasons=["Selected LOCAL with score 0.95"],
        ranked_candidates=[candidate],
    )


def test_target_adapter_protocol_conformance() -> None:
    """Verify adapters satisfy the TargetAdapter runtime protocol."""
    local_adapter = LocalTargetAdapter()
    edge_adapter = EdgeTargetAdapter()
    cloud_adapter = CloudTargetAdapter()

    assert isinstance(local_adapter, TargetAdapter)
    assert isinstance(edge_adapter, TargetAdapter)
    assert isinstance(cloud_adapter, TargetAdapter)


def test_local_target_adapter_execution(sample_routing_decision: RoutingDecision) -> None:
    """Test LocalTargetAdapter execution returning valid ExecutionResult."""
    adapter = LocalTargetAdapter()
    assert adapter.target == ExecutionTarget.LOCAL

    result = adapter.execute(
        sample_routing_decision,
        payload={"execution_time_ms": 12.5, "fps": 30.0},
    )

    assert isinstance(result, ExecutionResult)
    assert result.task_id == "task-test-123"
    assert result.target == ExecutionTarget.LOCAL
    assert result.status == ExecutionStatus.COMPLETED
    assert result.execution_time_ms == 12.5
    assert result.network_latency_ms == 0.0
    assert result.fps == 30.0


def test_edge_target_adapter_execution(sample_routing_decision: RoutingDecision) -> None:
    """Test EdgeTargetAdapter execution with network latency."""
    adapter = EdgeTargetAdapter(default_network_latency_ms=18.0)
    assert adapter.target == ExecutionTarget.EDGE

    edge_decision = sample_routing_decision.model_copy(update={"target": ExecutionTarget.EDGE})
    result = adapter.execute(
        edge_decision,
        payload={"execution_time_ms": 25.0, "network_latency_ms": 15.0, "fps": 60.0},
    )

    assert isinstance(result, ExecutionResult)
    assert result.task_id == "task-test-123"
    assert result.target == ExecutionTarget.EDGE
    assert result.status == ExecutionStatus.COMPLETED
    assert result.execution_time_ms == 25.0
    assert result.network_latency_ms == 15.0
    assert result.fps == 60.0


def test_cloud_target_adapter_execution(sample_routing_decision: RoutingDecision) -> None:
    """Test CloudTargetAdapter execution with default cloud latency."""
    adapter = CloudTargetAdapter(default_network_latency_ms=75.0)
    assert adapter.target == ExecutionTarget.CLOUD

    cloud_decision = sample_routing_decision.model_copy(update={"target": ExecutionTarget.CLOUD})
    result = adapter.execute(cloud_decision)

    assert isinstance(result, ExecutionResult)
    assert result.task_id == "task-test-123"
    assert result.target == ExecutionTarget.CLOUD
    assert result.status == ExecutionStatus.COMPLETED
    assert result.execution_time_ms >= 0.0
    assert result.network_latency_ms == 75.0
