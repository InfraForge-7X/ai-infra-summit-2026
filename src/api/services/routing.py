"""Routing service orchestration for AFRI-EDGE."""

from typing import Sequence

from src.api.interfaces import DecisionEngine, InfrastructureStateProvider
from src.shared.enums import ExecutionTarget
from src.shared.models import RoutingDecision, WorkloadProfile


class RoutingService:
    """Orchestrate state retrieval and routing decision without owning either."""

    def __init__(
        self,
        state_provider: InfrastructureStateProvider,
        decision_engine: DecisionEngine,
    ) -> None:
        self._state_provider = state_provider
        self._decision_engine = decision_engine

    def route(
        self,
        workload: WorkloadProfile,
        current_target: ExecutionTarget | None = None,
    ) -> RoutingDecision:
        """Retrieve current infrastructure state and delegate the decision."""
        targets: Sequence[ExecutionTarget] = (
            ExecutionTarget.LOCAL,
            ExecutionTarget.EDGE,
            ExecutionTarget.CLOUD,
        )

        infrastructure_states = self._state_provider.get_current_states(targets)

        return self._decision_engine.decide(
            workload=workload,
            infrastructure_states=infrastructure_states,
            current_target=current_target,
        )
