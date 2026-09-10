"""Core interfaces for AFRI-EDGE."""

from src.core.interfaces.decision_engine import DecisionEngineProtocol
from src.core.interfaces.workload_profiler import WorkloadProfilerProtocol

__all__ = [
    "DecisionEngineProtocol",
    "WorkloadProfilerProtocol",
]
