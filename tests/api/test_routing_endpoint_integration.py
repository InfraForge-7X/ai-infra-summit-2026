"""Integration tests for the AFRI-EDGE routing HTTP endpoint."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_routing_service
from src.api.routes.routing import router
from src.api.services.routing import RoutingService
from src.shared.enums import ExecutionTarget

from tests.api.fakes import FakeDecisionEngine, FakeInfrastructureStateProvider
from tests.api.test_routing_service import make_decision, make_states, make_workload


def make_client() -> tuple[TestClient, RoutingService]:
    provider = FakeInfrastructureStateProvider(make_states())
    engine = FakeDecisionEngine(make_decision())
    service = RoutingService(provider, engine)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_routing_service] = lambda: service

    return TestClient(app), service


def test_route_endpoint_returns_routing_decision() -> None:
    client, _ = make_client()
    response = client.post("/route", json=make_workload().model_dump())

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "task-001",
        "target": ExecutionTarget.EDGE.value,
        "score": 0.82,
        "reasons": ["edge latency is acceptable", "GPU is available"],
    }


def test_route_endpoint_rejects_invalid_workload() -> None:
    client, _ = make_client()
    payload = make_workload().model_dump()
    payload["input_size"] = 0

    response = client.post("/route", json=payload)

    assert response.status_code == 422


def test_route_endpoint_uses_injected_routing_service() -> None:
    client, service = make_client()
    response = client.post("/route", json=make_workload().model_dump())

    assert response.status_code == 200
    assert service._decision_engine.received_workload is not None
    assert service._decision_engine.received_workload.task_id == "task-001"
