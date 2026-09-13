"""End-to-end tests for the /route endpoint."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_state_adapter, reset_dependencies
from src.main import app
from src.shared import ExecutionTarget, InfrastructureState


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

    for target in (
        ExecutionTarget.LOCAL,
        ExecutionTarget.EDGE,
        ExecutionTarget.CLOUD,
    ):
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
    """Test that a valid workload returns a routing decision."""
    _register_healthy_states()

    response = client.post("/route", json=VALID_WORKLOAD)

    assert response.status_code == 200

    data = response.json()
    assert "target" in data
    assert "score" in data
    assert "reasons" in data
    assert "ranked_candidates" in data


def test_route_endpoint_rejects_invalid_workload() -> None:
    """Test that invalid workload is rejected with 422."""
    _register_healthy_states()

    invalid_workload = {
        **VALID_WORKLOAD,
        "input_size": 0,
    }

    response = client.post("/route", json=invalid_workload)

    assert response.status_code == 422


def test_route_endpoint_rejects_unknown_workload_fields() -> None:
    """Test that unknown fields are rejected."""
    _register_healthy_states()

    invalid_workload = {
        **VALID_WORKLOAD,
        "unexpected": True,
    }

    response = client.post("/route", json=invalid_workload)

    assert response.status_code == 422


def test_route_endpoint_rejects_missing_required_fields() -> None:
    """Test that missing required fields are rejected."""
    _register_healthy_states()

    incomplete_workload = {
        "task_id": "task-001",
    }

    response = client.post("/route", json=incomplete_workload)

    assert response.status_code == 422


def test_route_endpoint_returns_503_when_no_states_are_registered() -> None:
    """Test that routing without infrastructure states returns 503."""
    response = client.post("/route", json=VALID_WORKLOAD)

    assert response.status_code == 503
