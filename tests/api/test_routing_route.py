"""HTTP integration tests for the AFRI-EDGE routing endpoint."""

from typing import Any

from fastapi.testclient import TestClient

from src.api.dependencies import get_execution_router, get_routing_service
from src.api.services.routing import RoutingService
from src.main import app
from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import ExecutionResult, RoutingDecision

from tests.api.fakes import FakeDecisionEngine, FakeInfrastructureStateProvider
from tests.api.test_routing_service import make_decision, make_states, make_workload


class SpyExecutionRouter:
    """Test double that records the decision and payload dispatched for execution."""

    def __init__(self) -> None:
        self.received_decision: RoutingDecision | None = None
        self.received_payload: dict[str, Any] | None = None

    def execute(
        self,
        decision: RoutingDecision,
        payload: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        self.received_decision = decision
        self.received_payload = payload
        return ExecutionResult(
            task_id=decision.task_id,
            target=decision.target,
            status=ExecutionStatus.COMPLETED,
            execution_time_ms=1.0,
            network_latency_ms=15.0,
            fps=30.0,
        )


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


def test_route_dispatches_routing_decision_to_execution_router() -> None:
    provider = FakeInfrastructureStateProvider(make_states())
    decision = make_decision()
    engine = FakeDecisionEngine(decision)
    service = RoutingService(provider, engine)
    execution_router = SpyExecutionRouter()
    request = {
        **make_workload().model_dump(mode="json"),
    }

    app.dependency_overrides[get_routing_service] = lambda: service
    app.dependency_overrides[get_execution_router] = lambda: execution_router
    try:
        client = TestClient(app)
        response = client.post("/route", json=request)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert execution_router.received_decision is decision
    assert execution_router.received_payload == request
    assert response.json() == decision.model_dump(mode="json")


def test_route_forwards_current_target() -> None:
    provider = FakeInfrastructureStateProvider(make_states())
    engine = FakeDecisionEngine(make_decision())
    service = RoutingService(provider, engine)

    app.dependency_overrides[get_routing_service] = lambda: service
    try:
        client = TestClient(app)
        response = client.post(
            "/route?current_target=edge",
            json=make_workload().model_dump(mode="json"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert engine.received_current_target == ExecutionTarget.EDGE


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


def test_route_returns_503_when_no_infrastructure_states() -> None:
    """Without infrastructure states, routing should return 503."""
    from src.api.dependencies import reset_dependencies

    reset_dependencies()

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/route", json=make_workload().model_dump(mode="json"))

    assert response.status_code == 503
