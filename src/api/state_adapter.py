"""Adapter to connect StateStore to the API's InfrastructureStateProvider interface.

This bridges the metrics layer's StateStore with the API layer's expected interface.
"""

from collections.abc import Sequence

from src.metrics import InMemoryStateStore, StateStore
from src.shared import ExecutionTarget, InfrastructureState


class StateStoreAdapter:
    """Adapts a StateStore to the InfrastructureStateProvider protocol.

    The API layer expects an InfrastructureStateProvider with get_current_states().
    This adapter wraps a StateStore and provides that interface.
    """

    def __init__(self, store: StateStore | None = None) -> None:
        """Initialize with an optional StateStore.

        Args:
            store: The state store to wrap. Creates InMemoryStateStore if not provided.
        """
        self._store = store or InMemoryStateStore()

    @property
    def store(self) -> StateStore:
        """Return the underlying state store for direct access."""
        return self._store

    def get_current_states(
        self,
        targets: Sequence[ExecutionTarget],
    ) -> Sequence[InfrastructureState]:
        """Return the latest available state for each requested target.

        Args:
            targets: The execution targets to get states for.

        Returns:
            A sequence of InfrastructureState objects. Only targets with
            registered state are included; missing targets are omitted.
        """
        states: list[InfrastructureState] = []

        for target in targets:
            state = self._store.get_latest_state(target)
            if state is not None:
                states.append(state)

        return states

    def register_state(self, state: InfrastructureState) -> None:
        """Register a new infrastructure state (convenience method).

        Args:
            state: The state to register.
        """
        self._store.register(state)
