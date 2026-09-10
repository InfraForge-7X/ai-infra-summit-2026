"""Core interfaces for AFRI-EDGE components."""

from src.core.interfaces.decision_engine import DecisionEngineProtocol
from src.core.interfaces.state_provider import StateProviderProtocol

__all__ = [
    "DecisionEngineProtocol",
    "StateProviderProtocol",
]
