"""Shared Pydantic models for AFRI-EDGE data contracts.

These models are used across all AFRI-EDGE components:
- Workload Profiler
- Infrastructure Monitor
- Metrics & State Layer
- Decision Engine
- API

All models are framework-agnostic and reusable.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from src.shared.enums import (
    ComputeRequirement,
    ExecutionStatus,
    ExecutionTarget,
    Priority,
    PrivacyLevel,
    WorkloadType,
)


class WorkloadProfile(BaseModel):
    """Workload profile created by the Workload Profiler.

    Represents a deterministic profile of an AI workload with its requirements
    for routing decisions.

    Example:
        {
            "task_id": "task-001",
            "workload_type": "video_inference",
            "model": "yolo",
            "input_size": 1920,
            "latency_requirement": 100,
            "compute_requirement": "gpu",
            "privacy": "standard",
            "priority": "high"
        }
    """

    task_id: Annotated[
        str,
        Field(min_length=1, description="Unique identifier for the task"),
    ]
    workload_type: Annotated[
        WorkloadType,
        Field(description="Type of AI workload"),
    ]
    model: Annotated[
        str,
        Field(min_length=1, description="Model identifier (e.g., 'yolo')"),
    ]
    input_size: Annotated[
        int,
        Field(gt=0, description="Input size in pixels (e.g., 1920 for 1080p)"),
    ]
    latency_requirement: Annotated[
        int,
        Field(gt=0, description="Maximum acceptable latency in milliseconds"),
    ]
    compute_requirement: Annotated[
        ComputeRequirement,
        Field(description="Required compute resource type"),
    ]
    privacy: Annotated[
        PrivacyLevel,
        Field(default=PrivacyLevel.STANDARD, description="Privacy level for data handling"),
    ]
    priority: Annotated[
        Priority,
        Field(default=Priority.MEDIUM, description="Execution priority"),
    ]

    model_config = {"frozen": False, "extra": "forbid"}


class InfrastructureState(BaseModel):
    """Infrastructure state collected by the Infrastructure Monitor.

    Represents the current state of a compute target including compute resources,
    network conditions, and operational metadata.

    Example:
        {
            "target": "edge",
            "cpu_usage": 72,
            "gpu_available": true,
            "ram_usage": 61,
            "queue": 2,
            "latency_ms": 18,
            "bandwidth_mbps": 85,
            "packet_loss": 0.2,
            "timestamp": "2026-09-08T10:00:00Z"
        }
    """

    target: Annotated[
        ExecutionTarget,
        Field(description="Execution target this state represents"),
    ]
    cpu_usage: Annotated[
        float,
        Field(ge=0, le=100, description="CPU usage percentage (0-100)"),
    ]
    gpu_available: Annotated[
        bool,
        Field(description="Whether GPU is available for compute"),
    ]
    ram_usage: Annotated[
        float,
        Field(ge=0, le=100, description="RAM usage percentage (0-100)"),
    ]
    queue: Annotated[
        int,
        Field(ge=0, description="Number of tasks in queue"),
    ]
    latency_ms: Annotated[
        float,
        Field(ge=0, description="Network latency in milliseconds"),
    ]
    bandwidth_mbps: Annotated[
        float,
        Field(ge=0, description="Available bandwidth in Mbps"),
    ]
    packet_loss: Annotated[
        float,
        Field(ge=0, le=100, description="Packet loss percentage (0-100)"),
    ]
    timestamp: Annotated[
        datetime,
        Field(description="Timestamp of this state observation"),
    ]

    model_config = {"frozen": False, "extra": "forbid"}

    @field_validator("cpu_usage", "ram_usage", "packet_loss")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Ensure percentage values are within valid range."""
        if not 0 <= v <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v


class RoutingDecision(BaseModel):
    """Routing decision produced by the Decision Engine.

    Contains the selected target, computed score, and explanatory reasons
    for the routing decision.

    Example:
        {
            "task_id": "task-001",
            "target": "edge",
            "score": 0.85,
            "reasons": ["Low latency", "GPU available", "Sufficient bandwidth"]
        }
    """

    task_id: Annotated[
        str,
        Field(min_length=1, description="Task ID this decision applies to"),
    ]
    target: Annotated[
        ExecutionTarget,
        Field(description="Selected execution target"),
    ]
    score: Annotated[
        float,
        Field(ge=0, le=1, description="Computed score for this decision (0-1)"),
    ]
    reasons: Annotated[
        list[str],
        Field(min_length=1, description="Explanatory reasons for the decision"),
    ]

    model_config = {"frozen": False, "extra": "forbid"}

    @field_validator("reasons")
    @classmethod
    def validate_reasons_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure reasons list is not empty and contains valid strings."""
        if not v:
            raise ValueError("At least one reason must be provided")
        if any(not reason.strip() for reason in v):
            raise ValueError("Reasons cannot be empty strings")
        return v


class ExecutionResult(BaseModel):
    """Execution result captured by the Feedback Collector.

    Contains execution metadata including timing, status, and performance metrics.

    Example:
        {
            "task_id": "task-001",
            "target": "edge",
            "status": "completed",
            "execution_time_ms": 45,
            "network_latency_ms": 12,
            "fps": 30.5
        }
    """

    task_id: Annotated[
        str,
        Field(min_length=1, description="Task ID this result belongs to"),
    ]
    target: Annotated[
        ExecutionTarget,
        Field(description="Target where execution occurred"),
    ]
    status: Annotated[
        ExecutionStatus,
        Field(description="Final execution status"),
    ]
    execution_time_ms: Annotated[
        float,
        Field(ge=0, description="Total execution time in milliseconds"),
    ]
    network_latency_ms: Annotated[
        float,
        Field(ge=0, description="Network latency observed during execution"),
    ]
    fps: Annotated[
        float | None,
        Field(default=None, ge=0, description="Frames per second (for video workloads)"),
    ]

    model_config = {"frozen": False, "extra": "forbid"}
