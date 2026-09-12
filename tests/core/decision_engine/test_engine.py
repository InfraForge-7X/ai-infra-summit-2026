"""Tests for DecisionEngine integration."""

import pytest

from src.core.decision_engine import (
    DecisionEngine,
    DecisionEngineConfig,
    NoEligibleTargetError,
    ScoringWeights,
)
from src.shared import (
    ComputeRequirement,
    ExecutionTarget,
    InfrastructureState,
    PrivacyLevel,
    RoutingCandidate,
    RoutingDecision,
    WorkloadProfile,
)

from .conftest import create_state


class TestDecisionEngineInit:
    """Tests for DecisionEngine initialization."""

    def test_default_initialization(self) -> None:
        """Should initialize with default config."""
        engine = DecisionEngine()
        assert engine.config is not None
        assert engine.config.switching_threshold == 0.15

    def test_custom_config(self) -> None:
        """Should accept custom config."""
        config = DecisionEngineConfig(switching_threshold=0.25)
        engine = DecisionEngine(config=config)
        assert engine.config.switching_threshold == 0.25


class TestBasicDecisions:
    """Tests for basic routing decisions."""

    def test_returns_routing_decision(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Should return a valid RoutingDecision."""
        engine = DecisionEngine()

        decision = engine.decide(base_workload, all_healthy_states)

        assert isinstance(decision, RoutingDecision)
        assert decision.task_id == base_workload.task_id
        assert decision.target in ExecutionTarget
        assert 0.0 <= decision.score <= 1.0
        assert len(decision.reasons) >= 1
        assert len(decision.ranked_candidates) == len(all_healthy_states)

    def test_selects_highest_scoring_target(
        self,
        base_workload: WorkloadProfile,
    ) -> None:
        """Should select the highest scoring eligible target."""
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL, cpu_usage=90.0, latency_ms=5.0),
            create_state(ExecutionTarget.EDGE, cpu_usage=30.0, latency_ms=20.0),
            create_state(ExecutionTarget.CLOUD, cpu_usage=80.0, latency_ms=60.0),
        ]

        decision = engine.decide(base_workload, states)

        # EDGE should win: moderate CPU, good latency
        assert decision.target == ExecutionTarget.EDGE

    def test_ranked_candidates_ordered_by_score(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Ranked candidates should be ordered by score descending."""
        engine = DecisionEngine()

        decision = engine.decide(base_workload, all_healthy_states)

        eligible_scores = [
            c.score for c in decision.ranked_candidates if c.eligible and c.score
        ]
        assert eligible_scores == sorted(eligible_scores, reverse=True)


class TestEligibilityFiltering:
    """Tests for hard constraint filtering."""

    def test_excludes_ineligible_from_selection(
        self,
        base_workload: WorkloadProfile,
    ) -> None:
        """Ineligible targets should not be selected."""
        engine = DecisionEngine()
        states = [
            create_state(
                ExecutionTarget.LOCAL,
                gpu_available=False,  # Fails GPU requirement
            ),
            create_state(
                ExecutionTarget.EDGE,
                gpu_available=True,
                latency_ms=20.0,
            ),
            create_state(
                ExecutionTarget.CLOUD,
                latency_ms=150.0,  # Fails latency requirement
            ),
        ]

        decision = engine.decide(base_workload, states)

        assert decision.target == ExecutionTarget.EDGE
        # Check that LOCAL and CLOUD are marked ineligible
        local_candidate = next(
            c for c in decision.ranked_candidates if c.target == ExecutionTarget.LOCAL
        )
        cloud_candidate = next(
            c for c in decision.ranked_candidates if c.target == ExecutionTarget.CLOUD
        )
        assert local_candidate.eligible is False
        assert cloud_candidate.eligible is False

    def test_ineligible_candidates_have_no_score(
        self,
        base_workload: WorkloadProfile,
    ) -> None:
        """Ineligible candidates should have None score."""
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL, gpu_available=False),
            create_state(ExecutionTarget.EDGE, gpu_available=True),
        ]

        decision = engine.decide(base_workload, states)

        local_candidate = next(
            c for c in decision.ranked_candidates if c.target == ExecutionTarget.LOCAL
        )
        assert local_candidate.score is None
        assert len(local_candidate.disqualification_reasons) > 0

    def test_privacy_restricted_excludes_non_local(
        self,
        restricted_workload: WorkloadProfile,
    ) -> None:
        """RESTRICTED privacy should exclude EDGE and CLOUD."""
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL),
            create_state(ExecutionTarget.EDGE),
            create_state(ExecutionTarget.CLOUD),
        ]

        decision = engine.decide(restricted_workload, states)

        assert decision.target == ExecutionTarget.LOCAL
        edge_candidate = next(
            c for c in decision.ranked_candidates if c.target == ExecutionTarget.EDGE
        )
        cloud_candidate = next(
            c for c in decision.ranked_candidates if c.target == ExecutionTarget.CLOUD
        )
        assert edge_candidate.eligible is False
        assert cloud_candidate.eligible is False


class TestAntiFlapping:
    """Tests for anti-flapping behavior."""

    def test_stays_on_current_when_improvement_small(
        self,
        base_workload: WorkloadProfile,
    ) -> None:
        """Should stay on current target when improvement is small."""
        config = DecisionEngineConfig(switching_threshold=0.15)
        engine = DecisionEngine(config=config)

        # EDGE slightly better than LOCAL
        states = [
            create_state(ExecutionTarget.LOCAL, cpu_usage=35.0, latency_ms=5.0),
            create_state(ExecutionTarget.EDGE, cpu_usage=30.0, latency_ms=15.0),
        ]

        # First decision: no current target
        decision1 = engine.decide(base_workload, states)
        first_target = decision1.target

        # Second decision: with current target
        decision2 = engine.decide(
            base_workload, states, current_target=first_target
        )

        # Should stay on first target unless improvement is large
        assert decision2.target == first_target

    def test_switches_when_improvement_large(
        self,
        base_workload: WorkloadProfile,
    ) -> None:
        """Should switch when improvement exceeds threshold."""
        config = DecisionEngineConfig(switching_threshold=0.15)
        engine = DecisionEngine(config=config)

        # EDGE much better than LOCAL
        states_local_worse = [
            create_state(
                ExecutionTarget.LOCAL,
                cpu_usage=90.0,
                latency_ms=80.0,
                gpu_available=True,
            ),
            create_state(
                ExecutionTarget.EDGE,
                cpu_usage=20.0,
                latency_ms=15.0,
                gpu_available=True,
            ),
        ]

        decision = engine.decide(
            base_workload,
            states_local_worse,
            current_target=ExecutionTarget.LOCAL,
        )

        assert decision.target == ExecutionTarget.EDGE


class TestDegradedScenarios:
    """Tests for degraded/edge case scenarios."""

    def test_empty_states_raises_error(self, base_workload: WorkloadProfile) -> None:
        """Should raise error when no states provided."""
        engine = DecisionEngine()

        with pytest.raises(ValueError, match="At least one"):
            engine.decide(base_workload, [])

    def test_all_ineligible_selects_first(
        self,
        base_workload: WorkloadProfile,
    ) -> None:
        """When all targets ineligible, should select first with warning."""
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL, gpu_available=False),
            create_state(ExecutionTarget.EDGE, gpu_available=False),
            create_state(ExecutionTarget.CLOUD, gpu_available=False),
        ]

        decision = engine.decide(base_workload, states)

        # Should still return a decision (graceful degradation)
        assert decision.target in ExecutionTarget
        assert any("WARNING" in r or "ineligible" in r.lower() for r in decision.reasons)

    def test_single_state_works(self, base_workload: WorkloadProfile) -> None:
        """Should work with a single infrastructure state."""
        engine = DecisionEngine()
        states = [create_state(ExecutionTarget.EDGE)]

        decision = engine.decide(base_workload, states)

        assert decision.target == ExecutionTarget.EDGE
        assert len(decision.ranked_candidates) == 1


class TestExplainability:
    """Tests for decision explainability."""

    def test_reasons_non_empty(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Reasons should never be empty."""
        engine = DecisionEngine()

        decision = engine.decide(base_workload, all_healthy_states)

        assert len(decision.reasons) >= 1
        assert all(len(r.strip()) > 0 for r in decision.reasons)

    def test_reasons_include_selected_target(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Reasons should mention the selected target."""
        engine = DecisionEngine()

        decision = engine.decide(base_workload, all_healthy_states)

        target_name = decision.target.value.upper()
        assert any(target_name in r for r in decision.reasons)

    def test_reasons_include_score(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Reasons should include the score."""
        engine = DecisionEngine()

        decision = engine.decide(base_workload, all_healthy_states)

        # Should mention score somewhere
        assert any("score" in r.lower() or "0." in r for r in decision.reasons)

    def test_score_breakdown_populated(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Score breakdown should be populated for eligible candidates."""
        engine = DecisionEngine()

        decision = engine.decide(base_workload, all_healthy_states)

        for candidate in decision.ranked_candidates:
            if candidate.eligible:
                assert len(candidate.score_breakdown) == 5
                expected_keys = {"performance", "resources", "network", "reliability", "cost"}
                assert set(candidate.score_breakdown.keys()) == expected_keys


class TestDeterminism:
    """Tests for decision determinism."""

    def test_same_inputs_same_output(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Same inputs should always produce the same decision."""
        engine = DecisionEngine()

        decision1 = engine.decide(base_workload, all_healthy_states)
        decision2 = engine.decide(base_workload, all_healthy_states)

        assert decision1.target == decision2.target
        assert decision1.score == decision2.score
        assert decision1.reasons == decision2.reasons

    def test_different_engines_same_config_same_output(
        self,
        base_workload: WorkloadProfile,
        all_healthy_states: list[InfrastructureState],
    ) -> None:
        """Different engine instances with same config should produce same output."""
        config = DecisionEngineConfig()
        engine1 = DecisionEngine(config=config)
        engine2 = DecisionEngine(config=config)

        decision1 = engine1.decide(base_workload, all_healthy_states)
        decision2 = engine2.decide(base_workload, all_healthy_states)

        assert decision1.target == decision2.target
        assert decision1.score == decision2.score
