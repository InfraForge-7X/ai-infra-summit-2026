"""State provider protocol for Decision Engine consumption.

This protocol defines the interface that the Decision Engine uses to retrieve
infrastructure state without depending on the internal implementation details
of the state storage layer.
"""

from datetime import timedelta
from typing import Protocol, Sequence

from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState


class StateProviderProtocol(Protocol):
    """Protocol for retrieving infrastructure state.

    The Decision Engine depends on this protocol rather than concrete
    implementations, enabling easy replacement of storage backends.
    """

    def get_latest_state(self, target: ExecutionTarget) -> InfrastructureState | None:
        """Retrieve the most recent state for a specific target.

        Args:
            target: The execution target (LOCAL, EDGE, CLOUD).

        Returns:
            The latest InfrastructureState for the target, or None if no state exists.
        """
        ...

    def get_all_latest_states(self) -> Sequence[InfrastructureState]:
        """Retrieve the latest state for all known targets.

        Returns:
            A sequence of the most recent InfrastructureState for each target
            that has registered state. Empty sequence if no states exist.
        """
        ...

    def is_state_fresh(
        self,
        target: ExecutionTarget,
        max_age: timedelta,
    ) -> bool:
        """Check if the state for a target is fresh (within max_age).

        Args:
            target: The execution target to check.
            max_age: Maximum acceptable age for the state.

        Returns:
            True if state exists and is within max_age, False otherwise.
        """
        ...

    def get_fresh_states(
        self,
        max_age: timedelta,
    ) -> Sequence[InfrastructureState]:
        """Retrieve only fresh states for all targets.

        Args:
            max_age: Maximum acceptable age for states.

        Returns:
            A sequence of InfrastructureState objects that are within max_age.
            States that are stale or missing are excluded.
        """
        ...
