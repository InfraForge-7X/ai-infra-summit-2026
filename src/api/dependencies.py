"""FastAPI dependency providers for AFRI-EDGE services."""

from src.api.services.routing import RoutingService
from src.api.state_adapter import StateStoreAdapter
from src.core.decision_engine import DecisionEngine

# Module-level singletons for dependency injection
# These are created once and reused across requests
_state_adapter: StateStoreAdapter | None = None
_decision_engine: DecisionEngine | None = None
_routing_service: RoutingService | None = None


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


def reset_dependencies() -> None:
    """Reset all cached dependencies (for testing)."""
    global _state_adapter, _decision_engine, _routing_service
    _state_adapter = None
    _decision_engine = None
    _routing_service = None
