"""AFRI-EDGE Target Adapter layer."""

from src.adapters.base import BaseTargetAdapter, TargetAdapter
from src.adapters.cloud_adapter import CloudTargetAdapter
from src.adapters.edge_adapter import EdgeTargetAdapter
from src.adapters.local_adapter import LocalTargetAdapter
from src.adapters.router import ExecutionRouter, NoAdapterRegisteredError

__all__ = [
    "TargetAdapter",
    "BaseTargetAdapter",
    "LocalTargetAdapter",
    "EdgeTargetAdapter",
    "CloudTargetAdapter",
    "ExecutionRouter",
    "NoAdapterRegisteredError",
]
