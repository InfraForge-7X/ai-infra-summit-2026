"""Tests for RoutingService orchestration."""

from datetime import datetime, timezone

from src.api.services.routing import RoutingService
from src.shared.enums import (
    ComputeRequirement,
    ExecutionTarget,
    PrivacyLevel,
    Priority,
    WorkloadType,
)
from src.shared.models import InfrastructureState, RoutingDecision, WorkloadProfile

from tests.api.fakes import FakeDecisionEngine, FakeInfrastructureStateProvider


def make_workload() -> WorkloadProfile:
    return WorkloadProfile(
        task_id="task-001",
        workload_type=WorkloadType.REAL_TIME_VIDEO,
        model="yolo",
        input_size=640,
        latency_requirement=100,
        compute_requirement=ComputeRequirement.GPU,
        privacy=PrivacyLevel.STANDARD,
        priority=Priority.HIGH,
    )


def make_states() -> list[InfrastructureState]:
    timestamp = datetime.now(timezone.utc)
    return [
        InfrastructureState(
            target=ExecutionTarget.LOCAL,
            cpu_usage=30,
            gpu_available=True,
            ram_usage=40,
            queue=0,
            latency_ms=2,
            bandwidth_mbps=100,
            packet_loss=0,
            timestamp=timestamp,
        ),
        InfrastructureState(
            target=ExecutionTarget.EDGE,
            cpu_usage=50,
            gpu_available=True,
            ram_usage=50,
            queue=1,
            latency_ms=8,
            bandwidth_mbps=200,
            packet_loss=0,
            timestamp=timestamp,
        ),
        InfrastructureState(
            target=ExecutionTarget.CLOUD,
            cpu_usage=20,
            gpu_available=True,
            ram_usage=30,
            queue=0,
            latency_ms=40,
            bandwidth_mbps=500,
            packet_loss=0,
            timestamp=timestamp,
        ),
    ]


def make_decision() -> RoutingDecision:
    return RoutingDecision(
        task_id="task-001",
        target=ExecutionTarget.EDGE,
        score=0.82,
        reasons=["edge latency is acceptable", "GPU is available"],
    )


def test_route_requests_all_execution_targets() -> None:
    states = make_states()
    provider = FakeInfrastructureStateProvider(states)
    engine = FakeDecisionEngine(make_decision())
    service = RoutingService(provider, engine)

    service.route(make_workload())

    assert provider.requested_targets == [
        ExecutionTarget.LOCAL,
        ExecutionTarget.EDGE,
        ExecutionTarget.CLOUD,
    ]


def test_route_forwards_workload_and_states_to_decision_engine() -> None:
    workload = make_workload()
    states = make_states()
    provider = FakeInfrastructureStateProvider(states)
    engine = FakeDecisionEngine(make_decision())
    service = RoutingService(provider, engine)

    service.route(workload)

    assert engine.received_workload is workload
    assert list(engine.received_states) == states


def test_route_returns_decision_engine_result_unchanged() -> None:
    decision = make_decision()
    provider = FakeInfrastructureStateProvider(make_states())
    engine = FakeDecisionEngine(decision)
    service = RoutingService(provider, engine)

    result = service.route(make_workload())

    assert result is decision
