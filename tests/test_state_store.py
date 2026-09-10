"""Unit tests for AFRI-EDGE Metrics & State Layer.

Tests cover:
- State registration and retrieval
- Latest state per target
- Freshness/staleness detection
- Missing target handling
- Thread safety
- Edge cases
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.metrics import InMemoryStateStore, StateStore, TargetState
from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState


def create_infrastructure_state(
    target: ExecutionTarget = ExecutionTarget.LOCAL,
    cpu_usage: float = 50.0,
    gpu_available: bool = True,
    ram_usage: float = 60.0,
    queue: int = 5,
    latency_ms: float = 10.0,
    bandwidth_mbps: float = 100.0,
    packet_loss: float = 0.5,
    timestamp: datetime | None = None,
) -> InfrastructureState:
    """Factory helper for creating test InfrastructureState objects."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return InfrastructureState(
        target=target,
        cpu_usage=cpu_usage,
        gpu_available=gpu_available,
        ram_usage=ram_usage,
        queue=queue,
        latency_ms=latency_ms,
        bandwidth_mbps=bandwidth_mbps,
        packet_loss=packet_loss,
        timestamp=timestamp,
    )


class TestInMemoryStateStoreRegistration:
    """Tests for state registration functionality."""

    def test_register_single_state(self) -> None:
        """Test registering a single infrastructure state."""
        store = InMemoryStateStore()
        state = create_infrastructure_state(target=ExecutionTarget.LOCAL)

        store.register(state)

        assert len(store) == 1
        assert ExecutionTarget.LOCAL in store

    def test_register_multiple_targets(self) -> None:
        """Test registering states for all three targets."""
        store = InMemoryStateStore()

        local_state = create_infrastructure_state(target=ExecutionTarget.LOCAL)
        edge_state = create_infrastructure_state(target=ExecutionTarget.EDGE)
        cloud_state = create_infrastructure_state(target=ExecutionTarget.CLOUD)

        store.register(local_state)
        store.register(edge_state)
        store.register(cloud_state)

        assert len(store) == 3
        assert ExecutionTarget.LOCAL in store
        assert ExecutionTarget.EDGE in store
        assert ExecutionTarget.CLOUD in store

    def test_register_updates_with_newer_timestamp(self) -> None:
        """Test that newer state replaces older state for same target."""
        store = InMemoryStateStore()

        old_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        new_time = datetime.now(timezone.utc)

        old_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            cpu_usage=30.0,
            timestamp=old_time,
        )
        new_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            cpu_usage=70.0,
            timestamp=new_time,
        )

        store.register(old_state)
        store.register(new_state)

        retrieved = store.get_latest(ExecutionTarget.LOCAL)
        assert retrieved is not None
        assert retrieved.cpu_usage == 70.0
        assert retrieved.timestamp == new_time

    def test_register_ignores_older_timestamp(self) -> None:
        """Test that older state does not replace newer state."""
        store = InMemoryStateStore()

        old_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        new_time = datetime.now(timezone.utc)

        new_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            cpu_usage=70.0,
            timestamp=new_time,
        )
        old_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            cpu_usage=30.0,
            timestamp=old_time,
        )

        store.register(new_state)
        store.register(old_state)  # Should be ignored

        retrieved = store.get_latest(ExecutionTarget.LOCAL)
        assert retrieved is not None
        assert retrieved.cpu_usage == 70.0
        assert retrieved.timestamp == new_time


class TestInMemoryStateStoreRetrieval:
    """Tests for state retrieval functionality."""

    def test_get_latest_existing_target(self) -> None:
        """Test retrieving latest state for an existing target."""
        store = InMemoryStateStore()
        state = create_infrastructure_state(
            target=ExecutionTarget.EDGE,
            cpu_usage=45.0,
            ram_usage=55.0,
        )

        store.register(state)
        retrieved = store.get_latest(ExecutionTarget.EDGE)

        assert retrieved is not None
        assert retrieved.target == ExecutionTarget.EDGE
        assert retrieved.cpu_usage == 45.0
        assert retrieved.ram_usage == 55.0

    def test_get_latest_missing_target_returns_none(self) -> None:
        """Test that missing target returns None."""
        store = InMemoryStateStore()

        result = store.get_latest(ExecutionTarget.CLOUD)

        assert result is None

    def test_get_latest_after_registration(self) -> None:
        """Test retrieval returns registered state."""
        store = InMemoryStateStore()
        state = create_infrastructure_state(target=ExecutionTarget.LOCAL)

        assert store.get_latest(ExecutionTarget.LOCAL) is None
        store.register(state)
        assert store.get_latest(ExecutionTarget.LOCAL) is not None

    def test_get_all_latest_empty_store(self) -> None:
        """Test get_all_latest on empty store returns empty sequence."""
        store = InMemoryStateStore()

        result = store.get_all_latest()

        assert len(result) == 0

    def test_get_all_latest_with_states(self) -> None:
        """Test get_all_latest returns all registered states."""
        store = InMemoryStateStore()

        local_state = create_infrastructure_state(target=ExecutionTarget.LOCAL)
        edge_state = create_infrastructure_state(target=ExecutionTarget.EDGE)

        store.register(local_state)
        store.register(edge_state)

        result = store.get_all_latest()

        assert len(result) == 2
        targets = {s.target for s in result}
        assert targets == {ExecutionTarget.LOCAL, ExecutionTarget.EDGE}


class TestInMemoryStateStoreFreshness:
    """Tests for freshness/staleness detection."""

    def test_is_fresh_with_recent_state(self) -> None:
        """Test that recent state is considered fresh."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)
        state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(seconds=30),
        )

        store.register(state)
        is_fresh = store.is_fresh(ExecutionTarget.LOCAL, max_age=timedelta(minutes=1), now=now)

        assert is_fresh is True

    def test_is_fresh_with_stale_state(self) -> None:
        """Test that old state is considered stale."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)
        state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(minutes=5),
        )

        store.register(state)
        is_fresh = store.is_fresh(ExecutionTarget.LOCAL, max_age=timedelta(minutes=1), now=now)

        assert is_fresh is False

    def test_is_fresh_with_missing_target(self) -> None:
        """Test that missing target is not fresh."""
        store = InMemoryStateStore()

        is_fresh = store.is_fresh(ExecutionTarget.CLOUD, max_age=timedelta(minutes=1))

        assert is_fresh is False

    def test_is_fresh_at_boundary(self) -> None:
        """Test freshness at exact max_age boundary."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)
        state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(minutes=1),  # Exactly at boundary
        )

        store.register(state)
        is_fresh = store.is_fresh(ExecutionTarget.LOCAL, max_age=timedelta(minutes=1), now=now)

        assert is_fresh is True  # Boundary is inclusive

    def test_get_state_with_freshness_fresh(self) -> None:
        """Test get_state_with_freshness returns correct freshness info."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)
        timestamp = now - timedelta(seconds=30)
        state = create_infrastructure_state(
            target=ExecutionTarget.EDGE,
            timestamp=timestamp,
        )

        store.register(state)
        result = store.get_state_with_freshness(
            ExecutionTarget.EDGE,
            max_age=timedelta(minutes=1),
            now=now,
        )

        assert result is not None
        assert isinstance(result, TargetState)
        assert result.is_fresh is True
        assert result.state == state
        assert result.target == ExecutionTarget.EDGE
        assert result.age == timedelta(seconds=30)

    def test_get_state_with_freshness_stale(self) -> None:
        """Test get_state_with_freshness correctly identifies stale state."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)
        timestamp = now - timedelta(minutes=10)
        state = create_infrastructure_state(
            target=ExecutionTarget.CLOUD,
            timestamp=timestamp,
        )

        store.register(state)
        result = store.get_state_with_freshness(
            ExecutionTarget.CLOUD,
            max_age=timedelta(minutes=1),
            now=now,
        )

        assert result is not None
        assert result.is_fresh is False
        assert result.age == timedelta(minutes=10)

    def test_get_state_with_freshness_missing(self) -> None:
        """Test get_state_with_freshness returns None for missing target."""
        store = InMemoryStateStore()

        result = store.get_state_with_freshness(
            ExecutionTarget.LOCAL,
            max_age=timedelta(minutes=1),
        )

        assert result is None

    def test_get_fresh_states_all_fresh(self) -> None:
        """Test get_fresh_states when all states are fresh."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)

        states = [
            create_infrastructure_state(
                target=ExecutionTarget.LOCAL,
                timestamp=now - timedelta(seconds=10),
            ),
            create_infrastructure_state(
                target=ExecutionTarget.EDGE,
                timestamp=now - timedelta(seconds=20),
            ),
            create_infrastructure_state(
                target=ExecutionTarget.CLOUD,
                timestamp=now - timedelta(seconds=30),
            ),
        ]

        for state in states:
            store.register(state)

        fresh = store.get_fresh_states(max_age=timedelta(minutes=1), now=now)

        assert len(fresh) == 3

    def test_get_fresh_states_mixed(self) -> None:
        """Test get_fresh_states with mix of fresh and stale states."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)

        fresh_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(seconds=30),
        )
        stale_state = create_infrastructure_state(
            target=ExecutionTarget.EDGE,
            timestamp=now - timedelta(minutes=5),
        )

        store.register(fresh_state)
        store.register(stale_state)

        fresh = store.get_fresh_states(max_age=timedelta(minutes=1), now=now)

        assert len(fresh) == 1
        assert fresh[0].target == ExecutionTarget.LOCAL

    def test_get_fresh_states_none_fresh(self) -> None:
        """Test get_fresh_states when all states are stale."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)

        stale_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(hours=1),
        )

        store.register(stale_state)

        fresh = store.get_fresh_states(max_age=timedelta(minutes=1), now=now)

        assert len(fresh) == 0


class TestInMemoryStateStoreMissingAndStale:
    """Tests for missing and stale target detection."""

    def test_get_missing_targets_all_missing(self) -> None:
        """Test that all targets are reported missing when store is empty."""
        store = InMemoryStateStore()

        missing = store.get_missing_targets()

        assert len(missing) == 3
        assert set(missing) == {ExecutionTarget.LOCAL, ExecutionTarget.EDGE, ExecutionTarget.CLOUD}

    def test_get_missing_targets_some_present(self) -> None:
        """Test missing targets when some are registered."""
        store = InMemoryStateStore()
        store.register(create_infrastructure_state(target=ExecutionTarget.LOCAL))

        missing = store.get_missing_targets()

        assert len(missing) == 2
        assert ExecutionTarget.LOCAL not in missing
        assert ExecutionTarget.EDGE in missing
        assert ExecutionTarget.CLOUD in missing

    def test_get_missing_targets_none_missing(self) -> None:
        """Test missing targets when all are registered."""
        store = InMemoryStateStore()
        store.register(create_infrastructure_state(target=ExecutionTarget.LOCAL))
        store.register(create_infrastructure_state(target=ExecutionTarget.EDGE))
        store.register(create_infrastructure_state(target=ExecutionTarget.CLOUD))

        missing = store.get_missing_targets()

        assert len(missing) == 0

    def test_get_stale_targets_empty_store(self) -> None:
        """Test stale targets on empty store returns empty list."""
        store = InMemoryStateStore()

        stale = store.get_stale_targets(max_age=timedelta(minutes=1))

        assert len(stale) == 0

    def test_get_stale_targets_all_fresh(self) -> None:
        """Test stale targets when all states are fresh."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)

        store.register(create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(seconds=10),
        ))
        store.register(create_infrastructure_state(
            target=ExecutionTarget.EDGE,
            timestamp=now - timedelta(seconds=20),
        ))

        stale = store.get_stale_targets(max_age=timedelta(minutes=1), now=now)

        assert len(stale) == 0

    def test_get_stale_targets_some_stale(self) -> None:
        """Test stale targets with mix of fresh and stale."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)

        store.register(create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(seconds=30),  # Fresh
        ))
        store.register(create_infrastructure_state(
            target=ExecutionTarget.EDGE,
            timestamp=now - timedelta(minutes=5),  # Stale
        ))
        store.register(create_infrastructure_state(
            target=ExecutionTarget.CLOUD,
            timestamp=now - timedelta(minutes=10),  # Stale
        ))

        stale = store.get_stale_targets(max_age=timedelta(minutes=1), now=now)

        assert len(stale) == 2
        assert ExecutionTarget.LOCAL not in stale
        assert ExecutionTarget.EDGE in stale
        assert ExecutionTarget.CLOUD in stale


class TestInMemoryStateStoreClear:
    """Tests for clearing state."""

    def test_clear_all(self) -> None:
        """Test clearing all state from store."""
        store = InMemoryStateStore()
        store.register(create_infrastructure_state(target=ExecutionTarget.LOCAL))
        store.register(create_infrastructure_state(target=ExecutionTarget.EDGE))
        store.register(create_infrastructure_state(target=ExecutionTarget.CLOUD))

        assert len(store) == 3
        store.clear()
        assert len(store) == 0

    def test_clear_target_existing(self) -> None:
        """Test clearing state for a specific target."""
        store = InMemoryStateStore()
        store.register(create_infrastructure_state(target=ExecutionTarget.LOCAL))
        store.register(create_infrastructure_state(target=ExecutionTarget.EDGE))

        result = store.clear_target(ExecutionTarget.LOCAL)

        assert result is True
        assert len(store) == 1
        assert ExecutionTarget.LOCAL not in store
        assert ExecutionTarget.EDGE in store

    def test_clear_target_nonexistent(self) -> None:
        """Test clearing state for a non-existent target returns False."""
        store = InMemoryStateStore()

        result = store.clear_target(ExecutionTarget.CLOUD)

        assert result is False


class TestInMemoryStateStoreTimezoneHandling:
    """Tests for timezone-aware and naive datetime handling."""

    def test_handles_timezone_aware_timestamp(self) -> None:
        """Test that timezone-aware timestamps work correctly."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)
        state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(seconds=30),
        )

        store.register(state)
        is_fresh = store.is_fresh(ExecutionTarget.LOCAL, max_age=timedelta(minutes=1), now=now)

        assert is_fresh is True

    def test_handles_timezone_naive_timestamp(self) -> None:
        """Test that timezone-naive timestamps are treated as UTC."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)
        naive_timestamp = datetime.now() - timedelta(seconds=30)  # Naive datetime
        state = InfrastructureState(
            target=ExecutionTarget.LOCAL,
            cpu_usage=50.0,
            gpu_available=True,
            ram_usage=60.0,
            queue=5,
            latency_ms=10.0,
            bandwidth_mbps=100.0,
            packet_loss=0.5,
            timestamp=naive_timestamp,
        )

        store.register(state)
        # Should not raise, assumes UTC
        result = store.get_state_with_freshness(
            ExecutionTarget.LOCAL,
            max_age=timedelta(minutes=1),
            now=now,
        )

        assert result is not None


class TestStateStoreContainerOperations:
    """Tests for container-like operations (__len__, __contains__)."""

    def test_len_empty(self) -> None:
        """Test len on empty store."""
        store = InMemoryStateStore()
        assert len(store) == 0

    def test_len_with_states(self) -> None:
        """Test len with registered states."""
        store = InMemoryStateStore()
        store.register(create_infrastructure_state(target=ExecutionTarget.LOCAL))
        store.register(create_infrastructure_state(target=ExecutionTarget.EDGE))

        assert len(store) == 2

    def test_contains_present(self) -> None:
        """Test __contains__ for present target."""
        store = InMemoryStateStore()
        store.register(create_infrastructure_state(target=ExecutionTarget.LOCAL))

        assert ExecutionTarget.LOCAL in store

    def test_contains_absent(self) -> None:
        """Test __contains__ for absent target."""
        store = InMemoryStateStore()

        assert ExecutionTarget.CLOUD not in store


class TestStateStoreAbstractBase:
    """Tests verifying abstract base class behavior."""

    def test_inmemory_is_statestore(self) -> None:
        """Test that InMemoryStateStore is a StateStore."""
        store = InMemoryStateStore()
        assert isinstance(store, StateStore)


class TestTargetStateDataclass:
    """Tests for TargetState wrapper."""

    def test_target_state_properties(self) -> None:
        """Test TargetState exposes correct properties."""
        state = create_infrastructure_state(target=ExecutionTarget.EDGE)
        target_state = TargetState(
            state=state,
            is_fresh=True,
            age=timedelta(seconds=30),
        )

        assert target_state.state == state
        assert target_state.is_fresh is True
        assert target_state.age == timedelta(seconds=30)
        assert target_state.target == ExecutionTarget.EDGE

    def test_target_state_immutable(self) -> None:
        """Test that TargetState is immutable (frozen dataclass)."""
        state = create_infrastructure_state(target=ExecutionTarget.LOCAL)
        target_state = TargetState(
            state=state,
            is_fresh=True,
            age=timedelta(seconds=30),
        )

        with pytest.raises(AttributeError):
            target_state.is_fresh = False  # type: ignore[misc]


class TestDecisionEngineIntegration:
    """Tests verifying the state store works for Decision Engine consumption."""

    def test_get_all_states_for_decision_engine(self) -> None:
        """Test that Decision Engine can get all states for routing decision."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)

        # Register states for all targets
        local_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            cpu_usage=80.0,
            latency_ms=5.0,
            timestamp=now,
        )
        edge_state = create_infrastructure_state(
            target=ExecutionTarget.EDGE,
            cpu_usage=40.0,
            latency_ms=20.0,
            timestamp=now,
        )
        cloud_state = create_infrastructure_state(
            target=ExecutionTarget.CLOUD,
            cpu_usage=20.0,
            latency_ms=100.0,
            timestamp=now,
        )

        store.register(local_state)
        store.register(edge_state)
        store.register(cloud_state)

        # Decision Engine would call this
        states = store.get_all_latest()

        assert len(states) == 3
        # Verify we can access all state properties needed for decision
        for state in states:
            assert state.target in {ExecutionTarget.LOCAL, ExecutionTarget.EDGE, ExecutionTarget.CLOUD}
            assert 0 <= state.cpu_usage <= 100
            assert state.latency_ms >= 0

    def test_get_fresh_states_for_decision_engine(self) -> None:
        """Test that Decision Engine can filter out stale states."""
        store = InMemoryStateStore()
        now = datetime.now(timezone.utc)

        # Fresh state
        fresh_state = create_infrastructure_state(
            target=ExecutionTarget.LOCAL,
            timestamp=now - timedelta(seconds=10),
        )
        # Stale state - should be excluded from routing decision
        stale_state = create_infrastructure_state(
            target=ExecutionTarget.EDGE,
            timestamp=now - timedelta(hours=1),
        )

        store.register(fresh_state)
        store.register(stale_state)

        # Decision Engine would filter for fresh states only
        fresh_states = store.get_fresh_states(max_age=timedelta(minutes=5), now=now)

        assert len(fresh_states) == 1
        assert fresh_states[0].target == ExecutionTarget.LOCAL

    def test_handle_missing_target_gracefully(self) -> None:
        """Test that Decision Engine can handle missing targets."""
        store = InMemoryStateStore()
        store.register(create_infrastructure_state(target=ExecutionTarget.LOCAL))

        # Decision Engine checks for missing targets
        missing = store.get_missing_targets()

        assert ExecutionTarget.EDGE in missing
        assert ExecutionTarget.CLOUD in missing
        # Decision Engine might log warning or exclude these from routing options
