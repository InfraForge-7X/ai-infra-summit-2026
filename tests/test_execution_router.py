"""Unit tests for AFRI-EDGE ExecutionRouter (Task #10)."""

import pytest

from src.adapters.cloud_adapter import CloudTargetAdapter
from src.adapters.edge_adapter import EdgeTargetAdapter
from src.adapters.local_adapter import LocalTargetAdapter
from src.adapters.router import ExecutionRouter, NoAdapterRegisteredError
from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import ExecutionResult, RoutingCandidate, RoutingDecision


@pytest.fixture
def sample_decision() -> RoutingDecision:
    """Fixture providing a sample RoutingDecision targeting EDGE."""
    candidate = RoutingCandidate(
        target=ExecutionTarget.EDGE,
        eligible=True,
        score=0.88,
        score_breakdown={"latency": 0.88},
    )
    return RoutingDecision(
        task_id="task-router-456",
        target=ExecutionTarget.EDGE,
        score=0.88,
        reasons=["Selected EDGE with score 0.88"],
        ranked_candidates=[candidate],
    )


def test_router_adapter_registration() -> None:
    """Test registering adapters and inspecting router state."""
    router = ExecutionRouter()
    local_adapter = LocalTargetAdapter()
    edge_adapter = EdgeTargetAdapter()

    assert not router.has_adapter(ExecutionTarget.LOCAL)
    assert not router.has_adapter(ExecutionTarget.EDGE)

    router.register_adapter(local_adapter)
    router.register_adapter(edge_adapter)

    assert router.has_adapter(ExecutionTarget.LOCAL)
    assert router.has_adapter(ExecutionTarget.EDGE)
    assert router.get_adapter(ExecutionTarget.LOCAL) is local_adapter
    assert router.get_adapter(ExecutionTarget.EDGE) is edge_adapter
    assert router.get_adapter(ExecutionTarget.CLOUD) is None


def test_router_execution_dispatch(sample_decision: RoutingDecision) -> None:
    """Test router dispatches decision to the correct target adapter."""
    router = ExecutionRouter(
        adapters=[
            LocalTargetAdapter(),
            EdgeTargetAdapter(),
            CloudTargetAdapter(),
        ]
    )

    result = router.execute(
        sample_decision,
        payload={"execution_time_ms": 35.0, "network_latency_ms": 12.0},
    )

    assert isinstance(result, ExecutionResult)
    assert result.task_id == "task-router-456"
    assert result.target == ExecutionTarget.EDGE
    assert result.status == ExecutionStatus.COMPLETED
    assert result.execution_time_ms == 35.0
    assert result.network_latency_ms == 12.0


def test_router_missing_adapter_raises_error(sample_decision: RoutingDecision) -> None:
    """Test router raises NoAdapterRegisteredError when target adapter is missing."""
    router = ExecutionRouter()  # Empty router

    with pytest.raises(NoAdapterRegisteredError) as exc_info:
        router.execute(sample_decision)

    assert "No target adapter registered for execution target 'edge'" in str(exc_info.value)
