"""HTTP route for AFRI-EDGE workload routing."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_routing_service
from src.api.services.routing import RoutingService
from src.shared.models import RoutingDecision, WorkloadProfile

router = APIRouter(prefix="/route", tags=["routing"])


@router.post("", response_model=RoutingDecision)
async def route_workload(
    workload: WorkloadProfile,
    routing_service: RoutingService = Depends(get_routing_service),
) -> RoutingDecision:
    """Route a validated workload through the AFRI-EDGE service layer."""
    return routing_service.route(workload)
