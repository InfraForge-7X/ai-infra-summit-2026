"""Tests for AFRI-EDGE execution routing."""

from src.adapters.edge_adapter import EdgeTargetAdapter
from src.adapters.router import ExecutionRouter
from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import RoutingCandidate, RoutingDecision


def make_decision() -> RoutingDecision:
    return RoutingDecision(
        task_id="task-execution-001",
        target=ExecutionTarget.EDGE,
        score=0.9,
        reasons=["edge selected for low latency"],
        ranked_candidates=[
            RoutingCandidate(
                target=ExecutionTarget.EDGE,
                eligible=True,
                score=0.9,
                score_breakdown={"performance": 0.9},
            )
        ],
    )


def test_execution_router_dispatches_to_selected_target() -> None:
    router = ExecutionRouter([EdgeTargetAdapter()])
    result = router.execute(make_decision(), payload={"execution_time_ms": 12.0, "fps": 30.0})

    assert result.task_id == "task-execution-001"
    assert result.target == ExecutionTarget.EDGE
    assert result.status == ExecutionStatus.COMPLETED
    assert result.execution_time_ms == 12.0
    assert result.fps == 30.0
