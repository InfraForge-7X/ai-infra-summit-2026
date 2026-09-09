"""Shared enums for AFRI-EDGE data contracts.

These enums provide type-safe, validated values for workload and infrastructure attributes.
"""

from enum import Enum


class WorkloadType(str, Enum):
    """Type of AI workload to be processed.

    REAL_TIME_VIDEO is the canonical MVP workload. SPEECH and BATCH_INFERENCE
    are reserved for future workload extensions. VIDEO_INFERENCE is retained
    as a legacy compatibility value for the current test/API surface and should
    not be used for new workload profiles.
    """

    REAL_TIME_VIDEO = "real_time_video"
    VIDEO_INFERENCE = "video_inference"  # Legacy compatibility; use REAL_TIME_VIDEO for new work.
    SPEECH = "speech"
    BATCH_INFERENCE = "batch_inference"


class ComputeRequirement(str, Enum):
    """Compute resource requirement for workload execution."""

    CPU = "cpu"
    GPU = "gpu"
    ANY = "any"


class PrivacyLevel(str, Enum):
    """Privacy level determining where data can be processed."""

    STANDARD = "standard"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


class Priority(str, Enum):
    """Execution priority level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionTarget(str, Enum):
    """Execution environment target."""

    LOCAL = "local"
    EDGE = "edge"
    CLOUD = "cloud"


class ExecutionStatus(str, Enum):
    """Execution lifecycle status.

    Lifecycle: CREATED -> ROUTING -> DISPATCHED -> RUNNING -> COMPLETED -> RESULT_RETURNED
    Failure states: FAILED, TIMEOUT, CANCELLED
    """

    CREATED = "created"
    ROUTING = "routing"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    RESULT_RETURNED = "result_returned"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
