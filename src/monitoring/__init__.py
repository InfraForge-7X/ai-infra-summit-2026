"""Infrastructure monitoring module for AFRI-EDGE.

This module collects real-time infrastructure conditions (CPU, RAM, GPU,
network) and produces validated InfrastructureState snapshots for use by
the Metrics & State Layer and the Decision Engine.
"""

from src.monitoring.infrastructure_monitor import InfrastructureMonitor

__all__ = ["InfrastructureMonitor"]
