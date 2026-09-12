from fastapi.testclient import TestClient

from src.api.dependencies import get_routing_service
from src.api.services.routing import RoutingService
from src.main import app

from tests.api.fakes import FakeDecisionEngine, FakeInfrastructureStateProvider
from tests.api.test_routing_service import make_decision, make_states

client = TestClient(app)

VALID_WORKLOAD = {
    "task_id": "task-001",
    "workload_type": "real_time_video",
    "model": "yolo",
    "input_size": 1920,
    "latency_requirement": 100,
    "compute_requirement": "gpu",
    "privacy": "standard",
    "priority": "high",
}


def _create_fake_routing_service() -> RoutingService:
    provider = FakeInfrastructureStateProvider(make_states())
    engine = FakeDecisionEngine(make_decision())
    return RoutingService(provider, engine)


def test_route_endpoint_unconfigured_returns_503() -> None:
    response = client.post("/route", json=VALID_WORKLOAD)
    assert response.status_code == 503
    assert response.json()["detail"] == "Routing service is not configured"


def test_route_endpoint_validates_shared_workload_contract() -> None:
    service = _create_fake_routing_service()
    app.dependency_overrides[get_routing_service] = lambda: service
    try:
        response = client.post("/route", json=VALID_WORKLOAD)
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_route_endpoint_rejects_invalid_workload() -> None:
    service = _create_fake_routing_service()
    app.dependency_overrides[get_routing_service] = lambda: service
    try:
        invalid_workload = {**VALID_WORKLOAD, "input_size": 0}
        response = client.post("/route", json=invalid_workload)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_route_endpoint_rejects_unknown_workload_fields() -> None:
    service = _create_fake_routing_service()
    app.dependency_overrides[get_routing_service] = lambda: service
    try:
        invalid_workload = {**VALID_WORKLOAD, "unexpected": True}
        response = client.post("/route", json=invalid_workload)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_route_endpoint_rejects_missing_required_fields() -> None:
    service = _create_fake_routing_service()
    app.dependency_overrides[get_routing_service] = lambda: service
    try:
        incomplete_workload = {"task_id": "task-001"}
        response = client.post("/route", json=incomplete_workload)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
