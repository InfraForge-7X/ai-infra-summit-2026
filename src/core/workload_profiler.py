"""Workload Profiler implementation for AFRI-EDGE.

Transforms incoming AI workload requests into validated shared WorkloadProfile instances.
Focuses on REAL_TIME_VIDEO as the canonical MVP workload while maintaining determinism
and extensibility for future workload types (SPEECH, BATCH_INFERENCE).
"""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from src.shared.enums import (
    ComputeRequirement,
    Priority,
    PrivacyLevel,
    WorkloadType,
)
from src.shared.models import WorkloadProfile


class WorkloadProfilingError(ValueError):
    """Exception raised when workload profiling fails validation."""

    pass


class WorkloadProfiler:
    """Deterministic profiler for converting AI requests into validated WorkloadProfile instances."""

    def profile(self, request: Any) -> WorkloadProfile:
        """Profile an AI request and construct a validated WorkloadProfile.

        Args:
            request: Request data provided as a mapping, Pydantic BaseModel, or object
                exposing ``__dict__``. Pydantic models must preserve extra fields
                (for example with ``extra='allow'``) if those fields need to be
                validated by the profiler.

        Returns:
            WorkloadProfile: Validated shared workload profile model.

        Raises:
            WorkloadProfilingError: If required fields are missing, invalid, empty, or incompatible.
        """
        if request is None:
            raise WorkloadProfilingError("Request payload cannot be None")

        if isinstance(request, BaseModel):
            payload = request.model_dump()
            extra = getattr(request, "__pydantic_extra__", None)
            if extra:
                payload.update(extra)
        elif isinstance(request, Mapping):
            payload = dict(request)
        elif hasattr(request, "__dict__"):
            payload = dict(request.__dict__)
        else:
            raise WorkloadProfilingError(f"Unsupported request payload type: {type(request).__name__}")

        # Validate task_id early
        if "task_id" not in payload:
            raise WorkloadProfilingError("Missing required field: 'task_id'")
        task_id = payload.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise WorkloadProfilingError("Field 'task_id' must be a non-empty string")

        # Validate model early
        if "model" not in payload:
            raise WorkloadProfilingError("Missing required field: 'model'")
        model = payload.get("model")
        if not isinstance(model, str) or not model.strip():
            raise WorkloadProfilingError("Field 'model' must be a non-empty string")

        # Validate workload_type early
        if "workload_type" not in payload:
            raise WorkloadProfilingError("Missing required field: 'workload_type'")

        workload_type = payload.get("workload_type")
        if isinstance(workload_type, str):
            try:
                workload_type = WorkloadType(workload_type)
            except ValueError:
                valid_types = [wt.value for wt in WorkloadType]
                raise WorkloadProfilingError(
                    f"Invalid workload_type '{workload_type}'. Must be one of: {valid_types}"
                )
        elif not isinstance(workload_type, WorkloadType):
            raise WorkloadProfilingError(f"Invalid workload_type '{workload_type}'. Expected WorkloadType enum or string.")

        payload["workload_type"] = workload_type

        # Validate input_size
        if "input_size" not in payload:
            raise WorkloadProfilingError("Missing required field: 'input_size'")
        input_size = payload.get("input_size")
        if not isinstance(input_size, int) or isinstance(input_size, bool) or input_size <= 0:
            raise WorkloadProfilingError("Field 'input_size' must be a positive integer (> 0)")

        # Validate latency_requirement
        if "latency_requirement" not in payload:
            raise WorkloadProfilingError("Missing required field: 'latency_requirement'")
        latency = payload.get("latency_requirement")
        if not isinstance(latency, int) or isinstance(latency, bool) or latency <= 0:
            raise WorkloadProfilingError("Field 'latency_requirement' must be a positive integer (> 0)")

        # Validate compute_requirement
        if "compute_requirement" not in payload:
            raise WorkloadProfilingError("Missing required field: 'compute_requirement'")
        compute_req = payload.get("compute_requirement")
        if isinstance(compute_req, str):
            try:
                compute_req = ComputeRequirement(compute_req)
            except ValueError:
                valid_computes = [cr.value for cr in ComputeRequirement]
                raise WorkloadProfilingError(
                    f"Invalid compute_requirement '{compute_req}'. Must be one of: {valid_computes}"
                )
        elif not isinstance(compute_req, ComputeRequirement):
            raise WorkloadProfilingError(f"Invalid compute_requirement '{compute_req}'.")
        payload["compute_requirement"] = compute_req

        # Validate optional privacy if provided
        if "privacy" in payload and payload["privacy"] is not None:
            privacy = payload["privacy"]
            if isinstance(privacy, str):
                try:
                    payload["privacy"] = PrivacyLevel(privacy)
                except ValueError:
                    valid_privacies = [p.value for p in PrivacyLevel]
                    raise WorkloadProfilingError(
                        f"Invalid privacy value '{privacy}'. Must be one of: {valid_privacies}"
                    )
            elif not isinstance(privacy, PrivacyLevel):
                raise WorkloadProfilingError(f"Invalid privacy value '{privacy}'.")

        # Validate optional priority if provided
        if "priority" in payload and payload["priority"] is not None:
            priority = payload["priority"]
            if isinstance(priority, str):
                try:
                    payload["priority"] = Priority(priority)
                except ValueError:
                    valid_priorities = [p.value for p in Priority]
                    raise WorkloadProfilingError(
                        f"Invalid priority value '{priority}'. Must be one of: {valid_priorities}"
                    )
            elif not isinstance(priority, Priority):
                raise WorkloadProfilingError(f"Invalid priority value '{priority}'.")

        # Construct WorkloadProfile model using Pydantic contract
        try:
            profile = WorkloadProfile(**payload)
            return profile
        except ValidationError as e:
            raise WorkloadProfilingError(f"Validation error creating WorkloadProfile: {e}") from e
