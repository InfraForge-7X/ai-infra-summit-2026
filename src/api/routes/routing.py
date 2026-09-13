"""HTTP route for AFRI-EDGE workload routing."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_routing_service
from src.api.services.routing import RoutingService
from src.core.decision_engine import NoEligibleTargetError
from src.shared.enums import ExecutionTarget
from src.shared.models import RoutingDecision, WorkloadProfile

router = APIRouter(prefix="/route", tags=["routing"])


@router.post("", response_model=RoutingDecision)
async def route_workload(
    workload: WorkloadProfile,
    current_target: ExecutionTarget | None = None,
    routing_service: RoutingService = Depends(get_routing_service),
) -> RoutingDecision:
    """Route a validated workload through the AFRI-EDGE service layer."""
    try:
        return routing_service.route(
            workload,
            current_target=current_target,
        )
    except NoEligibleTargetError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
