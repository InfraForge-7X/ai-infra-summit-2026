"""Monitoring state integration layer for AFRI-EDGE.

Bridges the Infrastructure Monitor with the Metrics & State Store layer.
Periodically or on-demand collects infrastructure state snapshots for requested targets
and registers them into the StateStore.
"""

from collections.abc import Sequence
from typing import Any

from src.core.interfaces.infrastructure_monitor import InfrastructureMonitorProtocol
from src.metrics.state_store import StateStore
from src.monitoring.infrastructure_monitor import InfrastructureMonitor
from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState


class InfrastructureStateCollector:
    """Orchestrates collection of infrastructure state snapshots and registration into StateStore.

    Design:
    - Technology-agnostic monitoring bridge.
    - Collects snapshots for requested targets (LOCAL, EDGE, CLOUD).
    - Updates StateStore synchronously or on-demand.
    """

    def __init__(
        self,
        monitor: InfrastructureMonitorProtocol | InfrastructureMonitor | None = None,
        state_store: StateStore | None = None,
    ) -> None:
        """Initialize the collector with monitor and state store dependencies.

        Args:
            monitor: Monitor instance implementing InfrastructureMonitorProtocol.
            state_store: StateStore instance to populate.
        """
        self._monitor = monitor or InfrastructureMonitor()
        self._state_store = state_store

    @property
    def monitor(self) -> InfrastructureMonitorProtocol | InfrastructureMonitor:
        """Return the underlying monitor."""
        return self._monitor

    @property
    def state_store(self) -> StateStore | None:
        """Return the underlying state store."""
        return self._state_store

    def collect_and_register(self, target: ExecutionTarget) -> InfrastructureState:
        """Collect a state snapshot for a single target and register it in StateStore.

        Args:
            target: The ExecutionTarget identity (LOCAL, EDGE, CLOUD).

        Returns:
            InfrastructureState snapshot collected and registered.
        """
        state = self._monitor.collect(target)
        if self._state_store is not None:
            self._state_store.register(state)
        return state

    def collect_all(
        self,
        targets: Sequence[ExecutionTarget] | None = None,
    ) -> list[InfrastructureState]:
        """Collect state snapshots for multiple targets and register them in StateStore.

        Args:
            targets: List of ExecutionTarget identities. Defaults to (LOCAL, EDGE, CLOUD).

        Returns:
            List of InfrastructureState snapshots collected and registered.
        """
        target_list = targets or (
            ExecutionTarget.LOCAL,
            ExecutionTarget.EDGE,
            ExecutionTarget.CLOUD,
        )
        collected_states: list[InfrastructureState] = []
        for target in target_list:
            state = self.collect_and_register(target)
            collected_states.append(state)
        return collected_states
