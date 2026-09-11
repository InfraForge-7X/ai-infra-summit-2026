"""Core interfaces for AFRI-EDGE components."""

from src.core.interfaces.decision_engine import DecisionEngineProtocol
from src.core.interfaces.state_provider import StateProviderProtocol
from src.core.interfaces.workload_profiler import WorkloadProfilerProtocol

__all__ = [
    "DecisionEngineProtocol",
    "StateProviderProtocol",
    "WorkloadProfilerProtocol",
]