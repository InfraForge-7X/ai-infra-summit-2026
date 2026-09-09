from fastapi import APIRouter, HTTPException, status

from src.shared.models import WorkloadProfile

router = APIRouter(prefix="/route", tags=["routing"])


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def route_workload(workload: WorkloadProfile) -> None:
    """Validate a workload and prepare it for the AFRI-EDGE routing pipeline.

    Infrastructure state retrieval and Decision Engine execution will be
    injected once the corresponding services are validated.
    """
    _ = workload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Routing pipeline is not implemented yet",
    )
