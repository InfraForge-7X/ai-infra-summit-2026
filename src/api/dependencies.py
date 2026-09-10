"""FastAPI dependency providers for AFRI-EDGE services."""

from fastapi import HTTPException, status

from src.api.services.routing import RoutingService


def get_routing_service() -> RoutingService:
    """Return the configured routing service.

    Concrete infrastructure-state and decision-engine implementations are
    injected at application composition time. Until that wiring is available,
    fail explicitly instead of silently using a fake production dependency.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Routing service is not configured",
    )
