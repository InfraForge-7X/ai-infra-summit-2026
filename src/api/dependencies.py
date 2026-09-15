"""FastAPI dependency providers for AFRI-EDGE services."""

from src.adapters.cloud_adapter import CloudTargetAdapter
from src.adapters.edge_adapter import EdgeTargetAdapter
from src.adapters.local_adapter import LocalTargetAdapter
from src.adapters.router import ExecutionRouter
from src.api.services.routing import RoutingService
from src.api.state_adapter import StateStoreAdapter
from src.core.decision_engine import DecisionEngine
from src.core.workload_profiler import WorkloadProfiler
from src.monitoring.infrastructure_monitor import InfrastructureMonitor
from src.monitoring.state_integration import InfrastructureStateCollector

# Module-level singletons for dependency injection
# These are created once and reused across requests
_state_adapter: StateStoreAdapter | None = None
_decision_engine: DecisionEngine | None = None
_routing_service: RoutingService | None = None
_workload_profiler: WorkloadProfiler | None = None
_infrastructure_monitor: InfrastructureMonitor | None = None
_state_collector: InfrastructureStateCollector | None = None
_execution_router: ExecutionRouter | None = None


def _get_state_adapter() -> StateStoreAdapter:
    """Return the singleton state adapter."""
    global _state_adapter
    if _state_adapter is None:
        _state_adapter = StateStoreAdapter()
    return _state_adapter


def _get_decision_engine() -> DecisionEngine:
    """Return the singleton decision engine."""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine


def _get_workload_profiler() -> WorkloadProfiler:
    """Return the singleton workload profiler."""
    global _workload_profiler
    if _workload_profiler is None:
        _workload_profiler = WorkloadProfiler()
    return _workload_profiler


def get_infrastructure_monitor() -> InfrastructureMonitor:
    """Return the singleton infrastructure monitor."""
    global _infrastructure_monitor
    if _infrastructure_monitor is None:
        _infrastructure_monitor = InfrastructureMonitor()
    return _infrastructure_monitor


def get_state_collector() -> InfrastructureStateCollector:
    """Return the configured infrastructure state collector."""
    global _state_collector
    if _state_collector is None:
        adapter = _get_state_adapter()
        _state_collector = InfrastructureStateCollector(
            monitor=get_infrastructure_monitor(),
            state_store=adapter.store,
        )
    return _state_collector


def get_execution_router() -> ExecutionRouter:
    """Return the configured execution router with default target adapters."""
    global _execution_router
    if _execution_router is None:
        router = ExecutionRouter()
        router.register_adapter(LocalTargetAdapter())
        router.register_adapter(EdgeTargetAdapter())
        router.register_adapter(CloudTargetAdapter())
        _execution_router = router
    return _execution_router


def get_routing_service() -> RoutingService:
    """Return the configured routing service.

    Creates and caches a RoutingService with real implementations
    of the state provider and decision engine.
    """
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService(
            state_provider=_get_state_adapter(),
            decision_engine=_get_decision_engine(),
        )
    return _routing_service


def get_state_adapter() -> StateStoreAdapter:
    """Return the state adapter for registering infrastructure states.

    This is exposed for the state ingestion endpoint to register new states.
    """
    return _get_state_adapter()


def get_workload_profiler() -> WorkloadProfiler:
    """Return the workload profiler for AI request profiling."""
    return _get_workload_profiler()


def reset_dependencies() -> None:
    """Reset all cached dependencies (for testing)."""
    global _state_adapter, _decision_engine, _routing_service, _workload_profiler, _infrastructure_monitor, _state_collector, _execution_router
    _state_adapter = None
    _decision_engine = None
    _routing_service = None
    _workload_profiler = None
    _infrastructure_monitor = None
    _state_collector = None
    _execution_router = None
