"""Controlled routing benchmark for AFRI-EDGE versus a static baseline.

The benchmark intentionally exercises the existing Decision Engine without
changing routing logic or introducing benchmark-only routing parameters.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from src.core.decision_engine import DecisionEngine
from src.shared import (
    ComputeRequirement,
    ExecutionTarget,
    InfrastructureState,
    WorkloadProfile,
    WorkloadType,
)


def create_state(
    target: ExecutionTarget,
    cpu_usage: float = 30.0,
    gpu_available: bool = True,
    ram_usage: float = 40.0,
    queue: int = 0,
    latency_ms: float = 10.0,
    bandwidth_mbps: float = 100.0,
    packet_loss: float = 0.0,
    timestamp: datetime | None = None,
) -> InfrastructureState:
    """Create a deterministic infrastructure state for benchmark scenarios."""
    return InfrastructureState(
        target=target,
        cpu_usage=cpu_usage,
        gpu_available=gpu_available,
        ram_usage=ram_usage,
        queue=queue,
        latency_ms=latency_ms,
        bandwidth_mbps=bandwidth_mbps,
        packet_loss=packet_loss,
        timestamp=timestamp or datetime.now(timezone.utc),
    )


@dataclass(frozen=True)
class BenchmarkScenario:
    """A deterministic routing scenario and its expected evidence."""

    name: str
    states: tuple[InfrastructureState, ...]
    expected_target: ExecutionTarget
    static_target: ExecutionTarget = ExecutionTarget.LOCAL
    current_target: ExecutionTarget | None = None
    expected_switch: bool | None = None


@pytest.fixture
def benchmark_workload() -> WorkloadProfile:
    """Representative real-time video workload used by every scenario."""
    return WorkloadProfile(
        task_id="benchmark-video-001",
        workload_type=WorkloadType.REAL_TIME_VIDEO,
        model="yolo",
        input_size=640,
        latency_requirement=100,
        compute_requirement=ComputeRequirement.GPU,
    )


def scenario_1() -> BenchmarkScenario:
    """Healthy Local should remain the preferred target."""
    return BenchmarkScenario(
        name="S1_local_performant",
        states=(
            create_state(ExecutionTarget.LOCAL, cpu_usage=20, ram_usage=30, latency_ms=2, bandwidth_mbps=1000),
            create_state(ExecutionTarget.EDGE, cpu_usage=40, ram_usage=50, latency_ms=15, bandwidth_mbps=200),
            create_state(ExecutionTarget.CLOUD, cpu_usage=25, ram_usage=35, latency_ms=50, bandwidth_mbps=500),
        ),
        expected_target=ExecutionTarget.LOCAL,
    )


def scenario_2() -> BenchmarkScenario:
    """Local saturation should make Edge preferable while Local stays eligible."""
    return BenchmarkScenario(
        name="S2_local_saturated",
        states=(
            create_state(ExecutionTarget.LOCAL, cpu_usage=90, ram_usage=90, queue=5, latency_ms=80, bandwidth_mbps=100),
            create_state(ExecutionTarget.EDGE, cpu_usage=40, ram_usage=50, latency_ms=15, bandwidth_mbps=200),
            create_state(ExecutionTarget.CLOUD, cpu_usage=25, ram_usage=35, latency_ms=50, bandwidth_mbps=500),
        ),
        expected_target=ExecutionTarget.EDGE,
    )


def scenario_3() -> BenchmarkScenario:
    """Edge network degradation should make Local preferable."""
    return BenchmarkScenario(
        name="S3_edge_degraded",
        states=(
            create_state(ExecutionTarget.LOCAL, cpu_usage=20, ram_usage=30, latency_ms=2, bandwidth_mbps=1000),
            create_state(ExecutionTarget.EDGE, cpu_usage=40, ram_usage=50, latency_ms=70, bandwidth_mbps=5, packet_loss=8),
            create_state(ExecutionTarget.CLOUD, cpu_usage=25, ram_usage=35, latency_ms=50, bandwidth_mbps=500),
        ),
        expected_target=ExecutionTarget.LOCAL,
    )


def scenario_4() -> BenchmarkScenario:
    """A material infrastructure change should trigger rerouting."""
    return BenchmarkScenario(
        name="S4_infrastructure_change",
        states=(
            create_state(ExecutionTarget.LOCAL, cpu_usage=90, ram_usage=90, queue=5, latency_ms=80, bandwidth_mbps=100),
            create_state(ExecutionTarget.EDGE, cpu_usage=40, ram_usage=50, latency_ms=15, bandwidth_mbps=200),
            create_state(ExecutionTarget.CLOUD, cpu_usage=25, ram_usage=35, latency_ms=50, bandwidth_mbps=500),
        ),
        expected_target=ExecutionTarget.EDGE,
        current_target=ExecutionTarget.LOCAL,
        expected_switch=True,
    )


def scenario_5() -> BenchmarkScenario:
    """A small score improvement must not cause unnecessary switching."""
    return BenchmarkScenario(
        name="S5_anti_flapping",
        states=(
            create_state(ExecutionTarget.LOCAL, cpu_usage=70, ram_usage=70, latency_ms=60, bandwidth_mbps=100),
            create_state(ExecutionTarget.EDGE, cpu_usage=60, ram_usage=60, latency_ms=45, bandwidth_mbps=100),
            create_state(ExecutionTarget.CLOUD, cpu_usage=25, ram_usage=35, latency_ms=50, bandwidth_mbps=500),
        ),
        expected_target=ExecutionTarget.EDGE,
        current_target=ExecutionTarget.EDGE,
        expected_switch=False,
    )


SCENARIOS = (scenario_1, scenario_2, scenario_3, scenario_4, scenario_5)


@pytest.mark.parametrize("scenario_factory", SCENARIOS, ids=lambda factory: factory().name)
def test_adaptive_routing_matches_benchmark_expectation(
    benchmark_workload: WorkloadProfile,
    scenario_factory,
) -> None:
    """Each controlled scenario produces its documented adaptive decision."""
    scenario = scenario_factory()
    decision = DecisionEngine().decide(
        benchmark_workload,
        scenario.states,
        current_target=scenario.current_target,
    )

    assert decision.target == scenario.expected_target
    assert len(decision.ranked_candidates) == 3
    assert all(candidate.eligible for candidate in decision.ranked_candidates)


@pytest.mark.parametrize("scenario_factory", SCENARIOS, ids=lambda factory: factory().name)
def test_static_baseline_is_explicit_and_comparable(
    benchmark_workload: WorkloadProfile,
    scenario_factory,
) -> None:
    """The benchmark compares every scenario against the same static policy."""
    scenario = scenario_factory()
    decision = DecisionEngine().decide(benchmark_workload, scenario.states)

    adaptive_target = decision.target
    static_target = scenario.static_target

    assert static_target == ExecutionTarget.LOCAL
    assert adaptive_target == scenario.expected_target

    if scenario.name in {"S2_local_saturated", "S4_infrastructure_change"}:
        assert adaptive_target != static_target


@pytest.mark.parametrize("scenario_factory", [scenario_4], ids=["S4_rerouting"])
def test_material_change_triggers_rerouting(
    benchmark_workload: WorkloadProfile,
    scenario_factory,
) -> None:
    """Scenario 4 must switch away from Local after its degradation."""
    scenario = scenario_factory()
    decision = DecisionEngine().decide(
        benchmark_workload,
        scenario.states,
        current_target=scenario.current_target,
    )

    assert scenario.expected_switch is True
    assert decision.target == ExecutionTarget.EDGE
    local = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.LOCAL)
    edge = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.EDGE)
    assert local.score is not None and edge.score is not None
    assert edge.score - local.score > DecisionEngine().config.switching_threshold


@pytest.mark.parametrize("scenario_factory", [scenario_5], ids=["S5_anti_flapping"])
def test_small_improvement_does_not_switch(
    benchmark_workload: WorkloadProfile,
    scenario_factory,
) -> None:
    """Scenario 5 must stay on Edge when Cloud is only marginally better."""
    scenario = scenario_factory()
    decision = DecisionEngine().decide(
        benchmark_workload,
        scenario.states,
        current_target=scenario.current_target,
    )

    assert scenario.expected_switch is False
    assert decision.target == ExecutionTarget.EDGE
    edge = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.EDGE)
    cloud = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.CLOUD)
    assert edge.score is not None and cloud.score is not None
    assert cloud.score > edge.score
    assert cloud.score - edge.score < DecisionEngine().config.switching_threshold


def test_benchmark_captures_comparable_metrics(
    benchmark_workload: WorkloadProfile,
) -> None:
    """Every scenario exposes the same decision metrics for evidence."""
    engine = DecisionEngine()

    for scenario_factory in SCENARIOS:
        scenario = scenario_factory()
        decision = engine.decide(
            benchmark_workload,
            scenario.states,
            current_target=scenario.current_target,
        )
        assert decision.task_id == benchmark_workload.task_id
        assert 0.0 <= decision.score <= 1.0
        assert decision.reasons
        assert len(decision.ranked_candidates) == 3
        for candidate in decision.ranked_candidates:
            assert candidate.eligible
            assert candidate.score is not None
            assert set(candidate.score_breakdown) == {
                "performance",
                "resources",
                "network",
                "reliability",
                "cost",
            }
