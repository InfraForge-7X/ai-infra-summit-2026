"""AFRI-EDGE shared data contracts.

This module contains the shared Pydantic models used across all AFRI-EDGE components:
Workload Profiler, Infrastructure Monitor, Metrics & State Layer, Decision Engine, and API.
"""

from src.shared.enums import (
    ComputeRequirement,
    ExecutionStatus,
    ExecutionTarget,
    Priority,
    PrivacyLevel,
    WorkloadType,
)
from src.shared.models import (
    ExecutionResult,
    InfrastructureState,
    RoutingCandidate,
    RoutingDecision,
    WorkloadProfile,
)

__all__ = [
    # Enums
    "ComputeRequirement",
    "ExecutionStatus",
    "ExecutionTarget",
    "Priority",
    "PrivacyLevel",
    "WorkloadType",
    # Models
    "ExecutionResult",
    "InfrastructureState",
    "RoutingCandidate",
    "RoutingDecision",
    "WorkloadProfile",
]
