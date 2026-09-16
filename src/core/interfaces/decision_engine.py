from typing import Protocol, Sequence

from src.shared.models import InfrastructureState, RoutingDecision, WorkloadProfile


class DecisionEngineProtocol(Protocol):
    def decide(
        self,
        workload: WorkloadProfile,
        infrastructure_state: Sequence[InfrastructureState],
    ) -> RoutingDecision:
        """Return an explainable routing decision for a workload."""
