# Workload Profiler — Technical Documentation

## Overview

The **Workload Profiler** is a core component of the AFRI-EDGE runtime. Its responsibility is to transform raw, incoming AI workload requests (from AGENTOS, application orchestrators, or external APIs) into validated, standardized `WorkloadProfile` data contracts.

The Workload Profiler acts as the entry validation boundary before workloads enter the Decision Engine or Routing Pipeline.

---

## MVP Focus & Scope

- **Primary Modality**: Real-time Video Analytics (`WorkloadType.REAL_TIME_VIDEO`).
- **Extensibility**: Designed to easily extend to future AI modalities (`SPEECH`, `BATCH_INFERENCE`).
- **Decoupled Architecture**: Strictly independent of the Decision Engine, Infrastructure Monitor, and Routing API logic.

---

## Data Model & Interfaces

### Input Request Format
The profiler accepts:
- Python `Mapping` implementations containing request payload fields (including `dict` and other mapping types).
- Pydantic `BaseModel` objects. Extra fields are forwarded when the input model preserves them (for example with `extra="allow"`).
- Python objects with attribute dictionaries (`__dict__`).

### Workload Profile Fields
| Field Name | Type | Description | Required | Validation Rules | Default Value |
|---|---|---|---|---|---|
| `task_id` | `str` | Unique task identifier | Yes | `min_length=1`, non-empty string | None |
| `workload_type` | `WorkloadType` | Type of AI workload | Yes | Valid `WorkloadType` enum/string | None |
| `model` | `str` | AI model identifier (e.g. `'yolov8n'`) | Yes | `min_length=1`, non-empty string | None |
| `input_size` | `int` | Input frame size in pixels | Yes | Strictly positive (`gt=0`), non-boolean | None |
| `latency_requirement` | `int` | Maximum acceptable latency (ms) | Yes | Strictly positive (`gt=0`), non-boolean | None |
| `compute_requirement` | `ComputeRequirement` | Preferred compute resource (`cpu`, `gpu`, `any`) | Yes | Valid `ComputeRequirement` enum/string | None |
| `privacy` | `PrivacyLevel` | Data privacy level (`standard`, `sensitive`, `restricted`) | No | Valid `PrivacyLevel` enum/string | `PrivacyLevel.STANDARD` |
| `priority` | `Priority` | Execution priority (`low`, `medium`, `high`, `critical`) | No | Valid `Priority` enum/string | `Priority.MEDIUM` |

---

## Validation & Error Handling

### Validation Rules
1. **Missing Required Fields**: Any missing required field raises a `WorkloadProfilingError`.
2. **Empty Strings**: `task_id` and `model` must not be empty or whitespace-only strings.
3. **Non-Positive Integers**: `input_size` and `latency_requirement` must be integers `> 0`. Boolean values (`True`/`False`) are rejected.
4. **Enum Validation**: String values for enums (`workload_type`, `compute_requirement`, `privacy`, `priority`) are automatically mapped to valid `src.shared.enums` values or rejected.
5. **Extra Fields**: Unexpected extra fields are rejected by the shared `WorkloadProfile` Pydantic configuration (`extra="forbid"`).
6. **Pydantic Input Preservation**: When a Pydantic input model is configured to preserve extra fields (for example `extra="allow"`), those extras are forwarded to the shared model so the same `extra="forbid"` boundary can reject them.

### Exception Class
- **`WorkloadProfilingError`**: Subclass of `ValueError` raised when any validation check fails during profiling.

---

## Workload Type Support

- **`WorkloadType.REAL_TIME_VIDEO` (`"real_time_video"`)**: Canonical MVP workload type for real-time video analytics.
- **`WorkloadType.VIDEO_INFERENCE` (`"video_inference"`)**: Supported for backward compatibility with legacy API contracts without modifying shared contract definitions.

---

## Usage Example

### Python Code Example
```python
from src.core.workload_profiler import WorkloadProfiler

profiler = WorkloadProfiler()

# Raw incoming request payload
raw_request = {
    "task_id": "video-stream-cam-01",
    "workload_type": "real_time_video",
    "model": "yolov8n",
    "input_size": 1080,
    "latency_requirement": 33,
    "compute_requirement": "gpu",
}

# Transform and validate into shared WorkloadProfile
profile = profiler.profile(raw_request)

print(profile.task_id)             # "video-stream-cam-01"
print(profile.workload_type)       # WorkloadType.REAL_TIME_VIDEO
print(profile.privacy)             # PrivacyLevel.STANDARD (default applied)
print(profile.priority)             # Priority.MEDIUM (default applied)
```

---

## Testing Summary

The test suite in `tests/test_workload_profiler.py` covers:
- Interface protocol conformance (`WorkloadProfilerProtocol`).
- Complete valid request profiling.
- Minimal valid requests applying default values (`privacy=STANDARD`, `priority=MEDIUM`).
- Canonical `REAL_TIME_VIDEO` workloads and legacy `VIDEO_INFERENCE` compatibility.
- Parameterized tests for missing required fields.
- Parameterized tests for invalid `input_size` (zero, negative, string, boolean).
- Parameterized tests for invalid `latency_requirement` (zero, negative, string, boolean).
- Parameterized tests for invalid enum values (`workload_type`, `compute_requirement`, `privacy`, `priority`).
- Parameterized tests for empty/whitespace `task_id` and `model`.
- Extra unexpected fields rejection.
- Generic mapping inputs.
- Pydantic request model payload inputs, including preserved extra-field rejection.
- `None` input handling.

---

## Architectural Decisions

1. **Strict Decoupling**: The profiler performs profiling and validation only. Routing decisions, infrastructure scoring, and network dispatch logic belong exclusively to downstream services.
2. **Zero Modification to Shared Contracts**: All shared Pydantic data models (`WorkloadProfile`) and enums in `src/shared/` were preserved intact without modifications.
3. **Deterministic & Lightweight**: Built strictly on top of standard library features and `pydantic>=2.0` without external databases, queues, or heavy dependencies.
