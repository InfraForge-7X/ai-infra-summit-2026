"""Test fakes for AFRI-EDGE routing integration."""

from typing import Sequence

from src.api.interfaces import DecisionEngine, InfrastructureStateProvider
from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import ExecutionResult, InfrastructureState, RoutingDecision, WorkloadProfile


class FakeInfrastructureStateProvider(InfrastructureStateProvider):
    """Deterministic state provider used by RoutingService tests."""

    def __init__(self, states: Sequence[InfrastructureState]) -> None:
        self.states = list(states)
        self.requested_targets: list[ExecutionTarget] = []

    def get_current_states(
        self,
        targets: Sequence[ExecutionTarget],
    ) -> Sequence[InfrastructureState]:
        self.requested_targets = list(targets)
        return self.states


class FakeDecisionEngine(DecisionEngine):
    """Deterministic decision engine used by RoutingService tests."""

    def __init__(self, decision: RoutingDecision) -> None:
        self.decision = decision
        self.received_workload: WorkloadProfile | None = None
        self.received_states: Sequence[InfrastructureState] = []

    def decide(
        self,
        workload: WorkloadProfile,
        infrastructure_states: Sequence[InfrastructureState],
    ) -> RoutingDecision:
        self.received_workload = workload
        self.received_states = infrastructure_states
        return self.decision


def make_execution_result(
    task_id: str,
    target: ExecutionTarget,
    status: ExecutionStatus = ExecutionStatus.COMPLETED,
) -> ExecutionResult:
    """Build an execution result when an integration test needs one."""
    return ExecutionResult(
        task_id=task_id,
        target=target,
        status=status,
        execution_time_ms=100.0,
        network_latency_ms=10.0,
        fps=30.0,
    )
