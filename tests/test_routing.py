from fastapi.testclient import TestClient

from src.main import app

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


def test_route_endpoint_validates_shared_workload_contract():
    response = client.post("/route", json=VALID_WORKLOAD)
    assert response.status_code == 501
    assert response.json()["detail"] == "Routing pipeline is not implemented yet"


def test_route_endpoint_rejects_invalid_workload():
    invalid_workload = {**VALID_WORKLOAD, "input_size": 0}
    response = client.post("/route", json=invalid_workload)
    assert response.status_code == 422


def test_route_endpoint_rejects_unknown_workload_fields():
    invalid_workload = {**VALID_WORKLOAD, "unexpected": True}
    response = client.post("/route", json=invalid_workload)
    assert response.status_code == 422


def test_route_endpoint_rejects_missing_required_fields():
    incomplete_workload = {"task_id": "task-001"}
    response = client.post("/route", json=incomplete_workload)
    assert response.status_code == 422
