"""Interface definition for the Workload Profiler."""

from typing import Any, Protocol, runtime_checkable

from src.shared.models import WorkloadProfile


@runtime_checkable
class WorkloadProfilerProtocol(Protocol):
    """Protocol defining the interface for AI workload profiling.

    Converts an incoming AI request payload into a validated AFRI-EDGE WorkloadProfile.
    """

    def profile(self, request: Any) -> WorkloadProfile:
        """Profile an AI request and return a validated WorkloadProfile instance.

        Args:
            request: Raw mapping, Pydantic model, or object exposing ``__dict__``.

        Returns:
            WorkloadProfile: Validated shared workload profile instance.

        Raises:
            WorkloadProfilingError: If the request is invalid, missing required fields,
                or fails validation rules.
        """
        ...
