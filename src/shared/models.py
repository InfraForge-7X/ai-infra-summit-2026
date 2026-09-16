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
    """Workload profile created by the Workload Profiler."""

    task_id: Annotated[str, Field(min_length=1, description="Unique identifier for the task")]
    workload_type: Annotated[WorkloadType, Field(description="Type of AI workload")]
    model: Annotated[str, Field(min_length=1, description="Model identifier (e.g., 'yolo')")]
    input_size: Annotated[int, Field(gt=0, description="Input size in pixels")]
    latency_requirement: Annotated[int, Field(gt=0, description="Maximum acceptable latency in milliseconds")]
    compute_requirement: Annotated[ComputeRequirement, Field(description="Required compute resource type")]
    privacy: Annotated[PrivacyLevel, Field(default=PrivacyLevel.STANDARD, description="Privacy level for data handling")]
    priority: Annotated[Priority, Field(default=Priority.MEDIUM, description="Execution priority")]

    model_config = {"frozen": False, "extra": "forbid"}


class InfrastructureState(BaseModel):
    """Infrastructure state collected by the Infrastructure Monitor."""

    target: Annotated[ExecutionTarget, Field(description="Execution target this state represents")]
    cpu_usage: Annotated[float, Field(ge=0, le=100, description="CPU usage percentage (0-100)")]
    gpu_available: Annotated[bool, Field(description="Whether GPU is available for compute")]
    ram_usage: Annotated[float, Field(ge=0, le=100, description="RAM usage percentage (0-100)")]
    queue: Annotated[int, Field(ge=0, description="Number of tasks in queue")]
    latency_ms: Annotated[float, Field(ge=0, description="Network latency in milliseconds")]
    bandwidth_mbps: Annotated[float, Field(ge=0, description="Available bandwidth in Mbps")]
    packet_loss: Annotated[float, Field(ge=0, le=100, description="Packet loss percentage (0-100)")]
    timestamp: Annotated[datetime, Field(description="Timestamp of this state observation")]

    model_config = {"frozen": False, "extra": "forbid"}

    @field_validator("cpu_usage", "ram_usage", "packet_loss")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Ensure percentage values are within valid range."""
        if not 0 <= v <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v


class RoutingCandidate(BaseModel):
    """A candidate target evaluated by the Decision Engine.

    Represents a single execution target with its eligibility status,
    score breakdown, and explanatory reasons. Used to provide full
    transparency into the routing decision process.
    """

    target: Annotated[ExecutionTarget, Field(description="Execution target being evaluated")]
    eligible: Annotated[bool, Field(description="Whether this target passed hard constraints")]
    disqualification_reasons: Annotated[
        list[str],
        Field(default_factory=list, description="Reasons why target is ineligible (empty if eligible)"),
    ]
    score: Annotated[
        float | None,
        Field(default=None, ge=0, le=1, description="Composite score (0-1), None if ineligible"),
    ]
    score_breakdown: Annotated[
        dict[str, float],
        Field(default_factory=dict, description="Per-dimension scores (e.g., performance, cost)"),
    ]

    model_config = {"frozen": False, "extra": "forbid"}

    @field_validator("score_breakdown")
    @classmethod
    def validate_score_breakdown_values(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure all score breakdown values are within valid range."""
        for key, value in v.items():
            if not 0 <= value <= 1:
                raise ValueError(f"Score breakdown '{key}' must be between 0 and 1, got {value}")
        return v


class RoutingDecision(BaseModel):
    """Routing decision produced by the Decision Engine.

    Contains the selected target, its score, human-readable reasons,
    and the full list of ranked candidates for Dashboard visualization.
    The Decision Engine is the source of truth — the frontend only
    visualizes its output without computing any intelligence.
    """

    task_id: Annotated[str, Field(min_length=1, description="Task ID this decision applies to")]
    target: Annotated[ExecutionTarget, Field(description="Selected execution target")]
    score: Annotated[float, Field(ge=0, le=1, description="Composite score of selected target (0-1)")]
    reasons: Annotated[list[str], Field(min_length=1, description="Human-readable reasons for the decision")]
    ranked_candidates: Annotated[
        list[RoutingCandidate],
        Field(description="All candidates ranked by score (highest first), including ineligible"),
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

    @field_validator("ranked_candidates")
    @classmethod
    def validate_ranked_candidates(cls, v: list["RoutingCandidate"]) -> list["RoutingCandidate"]:
        """Ensure ranked candidates list is not empty."""
        if not v:
            raise ValueError("At least one candidate must be provided")
        return v


class ExecutionResult(BaseModel):
    """Execution result captured by the Feedback Collector."""

    task_id: Annotated[str, Field(min_length=1, description="Task ID this result belongs to")]
    target: Annotated[ExecutionTarget, Field(description="Target where execution occurred")]
    status: Annotated[ExecutionStatus, Field(description="Final execution status")]
    execution_time_ms: Annotated[float, Field(ge=0, description="Total execution time in milliseconds")]
    network_latency_ms: Annotated[float, Field(ge=0, description="Network latency observed during execution")]
    fps: Annotated[float | None, Field(default=None, ge=0, description="Frames per second for video workloads")]

    model_config = {"frozen": False, "extra": "forbid"}
