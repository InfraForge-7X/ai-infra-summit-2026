"""End-to-end tests for the /route endpoint."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_state_adapter, reset_dependencies
from src.main import app
from src.shared import ExecutionTarget, InfrastructureState
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


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset dependencies before each test."""
    reset_dependencies()


def _register_healthy_states() -> None:
    """Register healthy infrastructure states for all targets."""
    adapter = get_state_adapter()
    now = datetime.now(timezone.utc)

    for target in [ExecutionTarget.LOCAL, ExecutionTarget.EDGE, ExecutionTarget.CLOUD]:
        adapter.register_state(
            InfrastructureState(
                target=target,
                cpu_usage=30.0,
                gpu_available=True,
                ram_usage=40.0,
                queue=0,
                latency_ms=20.0 if target == ExecutionTarget.LOCAL else 50.0,
                bandwidth_mbps=100.0,
                packet_loss=0.0,
                timestamp=now,
            )
        )


def test_route_endpoint_validates_shared_workload_contract() -> None:
    """Test that valid workload returns a routing decision."""
    _register_healthy_states()
    client = TestClient(app)

    response = client.post("/route", json=VALID_WORKLOAD)
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

    assert response.status_code == 200
    data = response.json()
    assert "target" in data
    assert "score" in data
    assert "reasons" in data
    assert "ranked_candidates" in data


def test_route_endpoint_rejects_invalid_workload() -> None:
    """Test that invalid workload is rejected with 422."""
    _register_healthy_states()
    client = TestClient(app)

    invalid_workload = {**VALID_WORKLOAD, "input_size": 0}
    response = client.post("/route", json=invalid_workload)
    assert response.status_code == 422


def test_route_endpoint_rejects_unknown_workload_fields() -> None:
    """Test that unknown fields are rejected."""
    _register_healthy_states()
    client = TestClient(app)

    invalid_workload = {**VALID_WORKLOAD, "unexpected": True}
    response = client.post("/route", json=invalid_workload)
    assert response.status_code == 422


def test_route_endpoint_rejects_missing_required_fields() -> None:
    """Test that missing required fields are rejected."""
    _register_healthy_states()
    client = TestClient(app)

    incomplete_workload = {"task_id": "task-001"}
    response = client.post("/route", json=incomplete_workload)
    assert response.status_code == 422


def test_route_endpoint_returns_500_when_no_states_registered() -> None:
    """Test that routing without states returns 500."""
    # Use raise_server_exceptions=False to get the 500 response
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/route", json=VALID_WORKLOAD)
    assert response.status_code == 500
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
