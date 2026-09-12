"""Interfaces used to integrate the Routing API with core AFRI-EDGE services."""

from typing import Protocol, Sequence

from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState, RoutingDecision, WorkloadProfile


class InfrastructureStateProvider(Protocol):
    """Provide the latest infrastructure state for requested execution targets."""

    def get_current_states(
        self,
        targets: Sequence[ExecutionTarget],
    ) -> Sequence[InfrastructureState]:
        """Return the latest available state for each requested target."""
        ...


class DecisionEngine(Protocol):
    """Select the best execution target for a workload."""

    def decide(
        self,
        workload: WorkloadProfile,
        infrastructure_states: Sequence[InfrastructureState],
        current_target: ExecutionTarget | None = None,
    ) -> RoutingDecision:
        """Return an explainable routing decision with optional anti-flapping context."""
        ...
