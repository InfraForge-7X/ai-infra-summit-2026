"""HTTP integration tests for the AFRI-EDGE routing endpoint."""

from fastapi.testclient import TestClient

from src.api.dependencies import get_routing_service
from src.api.services.routing import RoutingService
from src.main import app

from tests.api.fakes import FakeDecisionEngine, FakeInfrastructureStateProvider
from tests.api.test_routing_service import make_decision, make_states, make_workload


def test_route_returns_routing_decision_from_injected_service() -> None:
    provider = FakeInfrastructureStateProvider(make_states())
    engine = FakeDecisionEngine(make_decision())
    service = RoutingService(provider, engine)

    app.dependency_overrides[get_routing_service] = lambda: service
    try:
        client = TestClient(app)
        response = client.post("/route", json=make_workload().model_dump(mode="json"))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == make_decision().model_dump(mode="json")
    assert engine.received_workload == make_workload()
    assert list(engine.received_states) == provider.states


def test_route_rejects_invalid_workload() -> None:
    provider = FakeInfrastructureStateProvider(make_states())
    engine = FakeDecisionEngine(make_decision())
    service = RoutingService(provider, engine)

    app.dependency_overrides[get_routing_service] = lambda: service
    try:
        client = TestClient(app)
        response = client.post(
            "/route",
            json={
                **make_workload().model_dump(mode="json"),
                "input_size": 0,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert engine.received_workload is None


def test_route_returns_service_unavailable_when_not_configured() -> None:
    client = TestClient(app)

    response = client.post("/route", json=make_workload().model_dump(mode="json"))

    assert response.status_code == 503
    assert response.json() == {"detail": "Routing service is not configured"}
