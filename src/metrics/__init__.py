"""Metrics & State Layer for AFRI-EDGE.

This module provides the state management layer that:
- Receives infrastructure snapshots from the Infrastructure Monitor
- Maintains the latest valid state for each execution target (Local/Edge/Cloud)
- Tracks freshness and handles stale/missing state
- Exposes a clean interface for the Decision Engine

The implementation is in-memory for the MVP but designed to be easily
replaceable by persistent storage later.
"""

from src.metrics.state_store import InMemoryStateStore, StateStore, TargetState

__all__ = [
    "InMemoryStateStore",
    "StateStore",
    "TargetState",
]
