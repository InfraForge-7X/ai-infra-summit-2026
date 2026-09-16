"""Application composition for AFRI-EDGE routing services."""

from src.api.interfaces import DecisionEngine, InfrastructureStateProvider
from src.api.services.routing import RoutingService


def create_routing_service(
    state_provider: InfrastructureStateProvider,
    decision_engine: DecisionEngine,
) -> RoutingService:
    """Build the routing service from its infrastructure dependencies."""
    return RoutingService(
        state_provider=state_provider,
        decision_engine=decision_engine,
    )
