"""Integration tests for Infrastructure State Integration pipeline (Task #10).

Verifies the flow:
InfrastructureMonitor -> InfrastructureStateCollector -> StateStore -> DecisionEngine
"""

from datetime import datetime, timezone

from src.core.decision_engine import DecisionEngine
from src.metrics.state_store import InMemoryStateStore
from src.monitoring.infrastructure_monitor import InfrastructureMonitor
from src.monitoring.state_integration import InfrastructureStateCollector
from src.shared.enums import ComputeRequirement, ExecutionTarget, Priority, PrivacyLevel, WorkloadType
from src.shared.models import InfrastructureState, WorkloadProfile


def test_state_collector_end_to_end_integration() -> None:
    """Test full pipeline: InfrastructureMonitor -> Collector -> StateStore -> DecisionEngine."""
    monitor = InfrastructureMonitor()
    store = InMemoryStateStore()
    collector = InfrastructureStateCollector(monitor=monitor, state_store=store)

    # Register custom probes for EDGE and CLOUD targets to simulate diverse network conditions
    now = datetime.now(timezone.utc)

    def edge_probe(target: ExecutionTarget) -> InfrastructureState:
        return InfrastructureState(
            target=target,
            cpu_usage=25.0,
            gpu_available=True,
            ram_usage=40.0,
            queue=0,
            latency_ms=10.0,
            bandwidth_mbps=100.0,
            packet_loss=0.0,
            timestamp=now,
        )

    def cloud_probe(target: ExecutionTarget) -> InfrastructureState:
        return InfrastructureState(
            target=target,
            cpu_usage=15.0,
            gpu_available=True,
            ram_usage=30.0,
            queue=0,
            latency_ms=80.0,
            bandwidth_mbps=500.0,
            packet_loss=0.0,
            timestamp=now,
        )

    monitor.register_target_probe(ExecutionTarget.EDGE, edge_probe)
    monitor.register_target_probe(ExecutionTarget.CLOUD, cloud_probe)

    # Collect and register states across all targets
    collected = collector.collect_all()
    assert len(collected) == 3
    assert len(store) == 3

    # Retrieve all latest states from StateStore for Decision Engine
    states = store.get_all_latest_states()
    assert len(states) == 3

    # Define a workload requiring GPU and low latency
    workload = WorkloadProfile(
        task_id="task-integration-789",
        workload_type=WorkloadType.REAL_TIME_VIDEO,
        model="yolov8",
        input_size=640,
        latency_requirement=30,
        compute_requirement=ComputeRequirement.GPU,
        privacy=PrivacyLevel.STANDARD,
        priority=Priority.HIGH,
    )

    # Run DecisionEngine with stored states
    engine = DecisionEngine()
    decision = engine.decide(workload=workload, infrastructure_states=states)

    assert decision.task_id == "task-integration-789"
    assert decision.target in (ExecutionTarget.LOCAL, ExecutionTarget.EDGE, ExecutionTarget.CLOUD)
    assert decision.score > 0.0
    assert len(decision.reasons) > 0
    assert len(decision.ranked_candidates) == 3
