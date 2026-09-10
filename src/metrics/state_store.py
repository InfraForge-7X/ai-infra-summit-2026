"""State storage layer for AFRI-EDGE Metrics & State.

This module implements the state store that maintains infrastructure snapshots
and provides the latest valid state per execution target to the Decision Engine.

Design principles:
- In-memory implementation for MVP (no Redis/Kafka/database)
- Clean separation via StateStore protocol
- Explicit handling of stale/missing state
- Thread-safe operations for concurrent access
- Easily replaceable by persistent storage later
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Sequence

from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState


@dataclass(frozen=True)
class TargetState:
    """Wrapper for target state with freshness metadata.

    This provides additional context about the state beyond the raw
    InfrastructureState, including whether it's considered fresh.
    """

    state: InfrastructureState
    is_fresh: bool
    age: timedelta

    @property
    def target(self) -> ExecutionTarget:
        """Convenience accessor for the target."""
        return self.state.target


class StateStore(ABC):
    """Abstract base class for state storage implementations.

    This defines the contract that all state stores must implement,
    allowing easy swapping between in-memory, Redis, or database backends.
    """

    @abstractmethod
    def register(self, state: InfrastructureState) -> None:
        """Register a new infrastructure state snapshot.

        This updates the stored state for the target identified in the snapshot.
        If state already exists for this target, it will be replaced if the
        new state has a more recent timestamp.

        Args:
            state: The infrastructure state snapshot to register.
        """
        ...

    @abstractmethod
    def get_latest(self, target: ExecutionTarget) -> InfrastructureState | None:
        """Retrieve the most recent state for a specific target.

        Args:
            target: The execution target (LOCAL, EDGE, CLOUD).

        Returns:
            The latest InfrastructureState for the target, or None if no state exists.
        """
        ...

    @abstractmethod
    def get_all_latest(self) -> Sequence[InfrastructureState]:
        """Retrieve the latest state for all known targets.

        Returns:
            A sequence of the most recent InfrastructureState for each target.
            Empty sequence if no states exist.
        """
        ...

    @abstractmethod
    def get_state_with_freshness(
        self,
        target: ExecutionTarget,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> TargetState | None:
        """Retrieve state with freshness information.

        Args:
            target: The execution target to retrieve.
            max_age: Maximum acceptable age for fresh state.
            now: Reference time for age calculation. Defaults to UTC now.

        Returns:
            TargetState with freshness info, or None if no state exists.
        """
        ...

    @abstractmethod
    def is_fresh(
        self,
        target: ExecutionTarget,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> bool:
        """Check if the state for a target is fresh.

        Args:
            target: The execution target to check.
            max_age: Maximum acceptable age for the state.
            now: Reference time for age calculation. Defaults to UTC now.

        Returns:
            True if state exists and is within max_age, False otherwise.
        """
        ...

    @abstractmethod
    def get_fresh_states(
        self,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> Sequence[InfrastructureState]:
        """Retrieve only fresh states for all targets.

        Args:
            max_age: Maximum acceptable age for states.
            now: Reference time for age calculation. Defaults to UTC now.

        Returns:
            A sequence of InfrastructureState objects within max_age.
        """
        ...

    @abstractmethod
    def get_missing_targets(self) -> Sequence[ExecutionTarget]:
        """Identify targets that have no registered state.

        Returns:
            A sequence of ExecutionTarget values that have no state.
        """
        ...

    @abstractmethod
    def get_stale_targets(
        self,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> Sequence[ExecutionTarget]:
        """Identify targets with stale state.

        Args:
            max_age: Maximum acceptable age for fresh state.
            now: Reference time for age calculation. Defaults to UTC now.

        Returns:
            A sequence of ExecutionTarget values with stale state.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all stored state.

        Primarily useful for testing.
        """
        ...

    @abstractmethod
    def clear_target(self, target: ExecutionTarget) -> bool:
        """Clear state for a specific target.

        Args:
            target: The target to clear.

        Returns:
            True if state was cleared, False if no state existed.
        """
        ...


class InMemoryStateStore(StateStore):
    """In-memory implementation of state storage.

    This implementation stores state in a dictionary, keyed by ExecutionTarget.
    It is thread-safe via RLock and suitable for MVP usage.

    Attributes:
        _states: Dictionary mapping targets to their latest state.
        _lock: Reentrant lock for thread safety.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory state store."""
        self._states: dict[ExecutionTarget, InfrastructureState] = {}
        self._lock = RLock()

    def register(self, state: InfrastructureState) -> None:
        """Register a new infrastructure state snapshot.

        Thread-safe. Only updates if the new state is more recent than existing.
        """
        with self._lock:
            existing = self._states.get(state.target)
            if existing is None or state.timestamp > existing.timestamp:
                self._states[state.target] = state

    def get_latest(self, target: ExecutionTarget) -> InfrastructureState | None:
        """Retrieve the most recent state for a specific target."""
        with self._lock:
            return self._states.get(target)

    def get_all_latest(self) -> Sequence[InfrastructureState]:
        """Retrieve the latest state for all known targets."""
        with self._lock:
            return list(self._states.values())

    def get_state_with_freshness(
        self,
        target: ExecutionTarget,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> TargetState | None:
        """Retrieve state with freshness information."""
        with self._lock:
            state = self._states.get(target)
            if state is None:
                return None

            reference_time = now if now is not None else datetime.now(timezone.utc)
            # Ensure timestamp is timezone-aware for comparison
            state_timestamp = state.timestamp
            if state_timestamp.tzinfo is None:
                state_timestamp = state_timestamp.replace(tzinfo=timezone.utc)

            age = reference_time - state_timestamp
            is_fresh = age <= max_age

            return TargetState(state=state, is_fresh=is_fresh, age=age)

    def is_fresh(
        self,
        target: ExecutionTarget,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> bool:
        """Check if the state for a target is fresh."""
        target_state = self.get_state_with_freshness(target, max_age, now)
        return target_state is not None and target_state.is_fresh

    def get_fresh_states(
        self,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> Sequence[InfrastructureState]:
        """Retrieve only fresh states for all targets."""
        with self._lock:
            reference_time = now if now is not None else datetime.now(timezone.utc)
            fresh_states: list[InfrastructureState] = []

            for state in self._states.values():
                state_timestamp = state.timestamp
                if state_timestamp.tzinfo is None:
                    state_timestamp = state_timestamp.replace(tzinfo=timezone.utc)

                age = reference_time - state_timestamp
                if age <= max_age:
                    fresh_states.append(state)

            return fresh_states

    def get_missing_targets(self) -> Sequence[ExecutionTarget]:
        """Identify targets that have no registered state."""
        with self._lock:
            all_targets = set(ExecutionTarget)
            registered_targets = set(self._states.keys())
            return list(all_targets - registered_targets)

    def get_stale_targets(
        self,
        max_age: timedelta,
        now: datetime | None = None,
    ) -> Sequence[ExecutionTarget]:
        """Identify targets with stale state."""
        with self._lock:
            reference_time = now if now is not None else datetime.now(timezone.utc)
            stale_targets: list[ExecutionTarget] = []

            for target, state in self._states.items():
                state_timestamp = state.timestamp
                if state_timestamp.tzinfo is None:
                    state_timestamp = state_timestamp.replace(tzinfo=timezone.utc)

                age = reference_time - state_timestamp
                if age > max_age:
                    stale_targets.append(target)

            return stale_targets

    def clear(self) -> None:
        """Clear all stored state."""
        with self._lock:
            self._states.clear()

    def clear_target(self, target: ExecutionTarget) -> bool:
        """Clear state for a specific target."""
        with self._lock:
            if target in self._states:
                del self._states[target]
                return True
            return False

    def __len__(self) -> int:
        """Return the number of targets with registered state."""
        with self._lock:
            return len(self._states)

    def __contains__(self, target: ExecutionTarget) -> bool:
        """Check if a target has registered state."""
        with self._lock:
            return target in self._states
