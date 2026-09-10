"""Tests for AFRI-EDGE application composition."""

from src.api.container import create_routing_service
from src.api.services.routing import RoutingService

from tests.api.fakes import FakeDecisionEngine, FakeInfrastructureStateProvider
from tests.api.test_routing_service import make_decision, make_states, make_workload


def test_create_routing_service_injects_dependencies() -> None:
    provider = FakeInfrastructureStateProvider(make_states())
    engine = FakeDecisionEngine(make_decision())

    service = create_routing_service(
        state_provider=provider,
        decision_engine=engine,
    )

    assert isinstance(service, RoutingService)
    result = service.route(make_workload())

    assert result is engine.decision
    assert engine.received_workload is not None
    assert list(engine.received_states) == provider.states
