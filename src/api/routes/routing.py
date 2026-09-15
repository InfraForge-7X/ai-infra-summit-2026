"""HTTP route for AFRI-EDGE workload routing."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.adapters.router import ExecutionRouter, NoAdapterRegisteredError
from src.api.dependencies import get_execution_router, get_routing_service, get_workload_profiler
from src.api.services.routing import RoutingService
from src.core.decision_engine import NoEligibleTargetError
from src.core.workload_profiler import WorkloadProfiler, WorkloadProfilingError
from src.shared.enums import ExecutionTarget
from src.shared.models import RoutingDecision

router = APIRouter(prefix="/route", tags=["routing"])


@router.post("", response_model=RoutingDecision)
async def route_workload(
    request: dict[str, Any],
    current_target: ExecutionTarget | None = None,
    workload_profiler: WorkloadProfiler = Depends(get_workload_profiler),
    routing_service: RoutingService = Depends(get_routing_service),
    execution_router: ExecutionRouter = Depends(get_execution_router),
) -> RoutingDecision:
    """Profile, route, and dispatch an AI workload through AFRI-EDGE."""
    try:
        workload = workload_profiler.profile(request)
    except WorkloadProfilingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        decision = routing_service.route(
            workload,
            current_target=current_target,
        )
    except NoEligibleTargetError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    try:
        execution_router.execute(decision, payload=request)
    except NoAdapterRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return decision
