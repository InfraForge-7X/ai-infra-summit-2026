"""Unit tests for AFRI-EDGE Workload Profiler (Task #3)."""

from typing import Any

import pytest
from pydantic import BaseModel

from src.core.interfaces.workload_profiler import WorkloadProfilerProtocol
from src.core.workload_profiler import WorkloadProfiler, WorkloadProfilingError
from src.shared.enums import (
    ComputeRequirement,
    Priority,
    PrivacyLevel,
    WorkloadType,
)
from src.shared.models import WorkloadProfile


def test_workload_profiler_implements_protocol() -> None:
    """Verify WorkloadProfiler conforms to WorkloadProfilerProtocol."""
    profiler = WorkloadProfiler()
    assert isinstance(profiler, WorkloadProfilerProtocol)


def test_valid_complete_request() -> None:
    """Test 1: Valid complete request with all fields explicitly specified."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-video-101",
        "workload_type": "real_time_video",
        "model": "yolov8n",
        "input_size": 1920,
        "latency_requirement": 30,
        "compute_requirement": "gpu",
        "privacy": "sensitive",
        "priority": "high",
    }

    profile = profiler.profile(request_data)

    assert isinstance(profile, WorkloadProfile)
    assert profile.task_id == "task-video-101"
    assert profile.workload_type == WorkloadType.REAL_TIME_VIDEO
    assert profile.model == "yolov8n"
    assert profile.input_size == 1920
    assert profile.latency_requirement == 30
    assert profile.compute_requirement == ComputeRequirement.GPU
    assert profile.privacy == PrivacyLevel.SENSITIVE
    assert profile.priority == Priority.HIGH


def test_minimal_valid_request_uses_shared_defaults() -> None:
    """Test 2: Minimal valid request uses default privacy and priority from shared model."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-minimal-001",
        "workload_type": WorkloadType.REAL_TIME_VIDEO,
        "model": "yolov8s",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": ComputeRequirement.ANY,
    }

    profile = profiler.profile(request_data)

    assert isinstance(profile, WorkloadProfile)
    assert profile.task_id == "task-minimal-001"
    assert profile.privacy == PrivacyLevel.STANDARD
    assert profile.priority == Priority.MEDIUM


def test_valid_real_time_video_request() -> None:
    """Test 3: Valid REAL_TIME_VIDEO request (canonical MVP workload)."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-rtv-4k",
        "workload_type": "real_time_video",
        "model": "yolov8x",
        "input_size": 3840,
        "latency_requirement": 16,
        "compute_requirement": "gpu",
    }

    profile = profiler.profile(request_data)

    assert profile.workload_type == WorkloadType.REAL_TIME_VIDEO
    assert profile.input_size == 3840
    assert profile.latency_requirement == 16


def test_legacy_video_inference_workload_type_supported() -> None:
    """Test legacy VIDEO_INFERENCE compatibility enum value."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-legacy-001",
        "workload_type": "video_inference",
        "model": "resnet50",
        "input_size": 640,
        "latency_requirement": 100,
        "compute_requirement": "cpu",
    }

    profile = profiler.profile(request_data)

    assert profile.workload_type == WorkloadType.VIDEO_INFERENCE


@pytest.mark.parametrize(
    "missing_field",
    [
        "task_id",
        "workload_type",
        "model",
        "input_size",
        "latency_requirement",
        "compute_requirement",
    ],
)
def test_missing_required_fields_raises_error(missing_field: str) -> None:
    """Test 4: Missing any required field causes validation failure."""
    profiler = WorkloadProfiler()
    base_request: dict[str, Any] = {
        "task_id": "task-missing-test",
        "workload_type": "real_time_video",
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": "gpu",
    }

    del base_request[missing_field]

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(base_request)

    assert missing_field in str(exc_info.value)


@pytest.mark.parametrize("invalid_size", [0, -1, -1080, "invalid", True, False])
def test_invalid_input_size_raises_error(invalid_size: Any) -> None:
    """Test 5: Invalid or non-positive input_size is rejected."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-size-err",
        "workload_type": "real_time_video",
        "model": "yolov8",
        "input_size": invalid_size,
        "latency_requirement": 50,
        "compute_requirement": "gpu",
    }

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(request_data)

    assert "input_size" in str(exc_info.value)


@pytest.mark.parametrize("invalid_latency", [0, -1, -50, "fast", True, False])
def test_invalid_latency_requirement_raises_error(invalid_latency: Any) -> None:
    """Test 6: Invalid or non-positive latency_requirement is rejected."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-lat-err",
        "workload_type": "real_time_video",
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": invalid_latency,
        "compute_requirement": "gpu",
    }

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(request_data)

    assert "latency_requirement" in str(exc_info.value)


@pytest.mark.parametrize("invalid_wt", ["invalid_workload", "audio", 123, None])
def test_invalid_workload_type_raises_error(invalid_wt: Any) -> None:
    """Test 7: Invalid workload_type is rejected."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-wt-err",
        "workload_type": invalid_wt,
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": "gpu",
    }

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(request_data)

    assert "workload_type" in str(exc_info.value)


@pytest.mark.parametrize("invalid_cr", ["tpu", "quantum", 99, None])
def test_invalid_compute_requirement_raises_error(invalid_cr: Any) -> None:
    """Test 8: Invalid compute_requirement is rejected."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-cr-err",
        "workload_type": "real_time_video",
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": invalid_cr,
    }

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(request_data)

    assert "compute_requirement" in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_privacy,invalid_priority",
    [
        ("ultra_secret", "medium"),
        ("standard", "ultra_high"),
        (123, "high"),
        ("sensitive", 456),
    ],
)
def test_invalid_privacy_or_priority_raises_error(invalid_privacy: Any, invalid_priority: Any) -> None:
    """Test 9: Invalid privacy or priority enum values are rejected."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-enum-err",
        "workload_type": "real_time_video",
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": "gpu",
        "privacy": invalid_privacy,
        "priority": invalid_priority,
    }

    with pytest.raises(WorkloadProfilingError):
        profiler.profile(request_data)


@pytest.mark.parametrize("bad_task_id", ["", "   ", None, 12345])
def test_empty_or_invalid_task_id_raises_error(bad_task_id: Any) -> None:
    """Test 10: Empty or non-string task_id is rejected."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": bad_task_id,
        "workload_type": "real_time_video",
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": "gpu",
    }

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(request_data)

    assert "task_id" in str(exc_info.value)


@pytest.mark.parametrize("bad_model", ["", "   ", None, 999])
def test_empty_or_invalid_model_raises_error(bad_model: Any) -> None:
    """Test 11: Empty or non-string model name is rejected."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-model-err",
        "workload_type": "real_time_video",
        "model": bad_model,
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": "gpu",
    }

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(request_data)

    assert "model" in str(exc_info.value)


def test_unexpected_extra_fields_rejected() -> None:
    """Test 12: Unexpected extra fields are rejected as per shared WorkloadProfile model extra='forbid'."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-extra-001",
        "workload_type": "real_time_video",
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": "gpu",
        "unknown_extra_param": "should_be_forbidden",
    }

    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(request_data)

    assert "Validation error" in str(exc_info.value)


def test_returns_shared_workload_profile_instance() -> None:
    """Test 13: Returned object is strictly an instance of src.shared.models.WorkloadProfile."""
    profiler = WorkloadProfiler()
    request_data: dict[str, Any] = {
        "task_id": "task-type-check",
        "workload_type": WorkloadType.REAL_TIME_VIDEO,
        "model": "yolov8",
        "input_size": 1080,
        "latency_requirement": 50,
        "compute_requirement": ComputeRequirement.GPU,
    }

    profile = profiler.profile(request_data)

    assert type(profile) is WorkloadProfile
    assert isinstance(profile, WorkloadProfile)


class SamplePydanticRequest(BaseModel):
    task_id: str
    workload_type: str
    model: str
    input_size: int
    latency_requirement: int
    compute_requirement: str


def test_profile_pydantic_model_input() -> None:
    """Test profiler handles Pydantic model object as input payload."""
    profiler = WorkloadProfiler()
    req_model = SamplePydanticRequest(
        task_id="task-pydantic-01",
        workload_type="real_time_video",
        model="yolov8",
        input_size=1920,
        latency_requirement=33,
        compute_requirement="gpu",
    )

    profile = profiler.profile(req_model)

    assert profile.task_id == "task-pydantic-01"
    assert profile.workload_type == WorkloadType.REAL_TIME_VIDEO


def test_profile_none_input_raises_error() -> None:
    """Test profile(None) raises WorkloadProfilingError."""
    profiler = WorkloadProfiler()
    with pytest.raises(WorkloadProfilingError) as exc_info:
        profiler.profile(None)
    assert "cannot be None" in str(exc_info.value)
