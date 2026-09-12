"""Tests for DecisionEngine integration."""

from datetime import datetime, timedelta, timezone

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
    def test_default_initialization(self) -> None:
        engine = DecisionEngine()
        assert engine.config is not None
        assert engine.config.switching_threshold == 0.15

    def test_custom_config(self) -> None:
        config = DecisionEngineConfig(switching_threshold=0.25)
        engine = DecisionEngine(config=config)
        assert engine.config.switching_threshold == 0.25


class TestBasicDecisions:
    def test_returns_routing_decision(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        engine = DecisionEngine()
        decision = engine.decide(base_workload, all_healthy_states)
        assert isinstance(decision, RoutingDecision)
        assert decision.task_id == base_workload.task_id
        assert decision.target in ExecutionTarget
        assert 0.0 <= decision.score <= 1.0
        assert len(decision.reasons) >= 1
        assert len(decision.ranked_candidates) == len(all_healthy_states)

    def test_selects_highest_scoring_target(self, base_workload: WorkloadProfile) -> None:
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL, cpu_usage=90.0, latency_ms=5.0),
            create_state(ExecutionTarget.EDGE, cpu_usage=30.0, latency_ms=20.0),
            create_state(ExecutionTarget.CLOUD, cpu_usage=80.0, latency_ms=60.0),
        ]
        decision = engine.decide(base_workload, states)
        assert decision.target == ExecutionTarget.EDGE

    def test_ranked_candidates_ordered_by_score(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        engine = DecisionEngine()
        decision = engine.decide(base_workload, all_healthy_states)
        eligible_scores = [
            c.score for c in decision.ranked_candidates if c.eligible and c.score is not None
        ]
        assert eligible_scores == sorted(eligible_scores, reverse=True)


class TestEligibilityFiltering:
    def test_excludes_ineligible_from_selection(self, base_workload: WorkloadProfile) -> None:
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL, gpu_available=False),
            create_state(ExecutionTarget.EDGE, gpu_available=True, latency_ms=20.0),
            create_state(ExecutionTarget.CLOUD, latency_ms=150.0),
        ]
        decision = engine.decide(base_workload, states)
        assert decision.target == ExecutionTarget.EDGE
        local_candidate = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.LOCAL)
        cloud_candidate = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.CLOUD)
        assert local_candidate.eligible is False
        assert cloud_candidate.eligible is False

    def test_ineligible_candidates_have_no_score(self, base_workload: WorkloadProfile) -> None:
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL, gpu_available=False),
            create_state(ExecutionTarget.EDGE, gpu_available=True),
        ]
        decision = engine.decide(base_workload, states)
        local_candidate = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.LOCAL)
        assert local_candidate.score is None
        assert len(local_candidate.disqualification_reasons) > 0

    def test_privacy_restricted_excludes_non_local(
        self, restricted_workload: WorkloadProfile
    ) -> None:
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL),
            create_state(ExecutionTarget.EDGE),
            create_state(ExecutionTarget.CLOUD),
        ]
        decision = engine.decide(restricted_workload, states)
        assert decision.target == ExecutionTarget.LOCAL
        edge_candidate = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.EDGE)
        cloud_candidate = next(c for c in decision.ranked_candidates if c.target == ExecutionTarget.CLOUD)
        assert edge_candidate.eligible is False
        assert cloud_candidate.eligible is False

    def test_stale_state_is_ineligible(self, base_workload: WorkloadProfile) -> None:
        config = DecisionEngineConfig(max_state_age_seconds=30.0)
        engine = DecisionEngine(config=config)
        stale = create_state(
            ExecutionTarget.LOCAL,
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=31),
        )
        fresh = create_state(ExecutionTarget.EDGE)

        decision = engine.decide(base_workload, [stale, fresh])

        assert decision.target == ExecutionTarget.EDGE
        stale_candidate = next(
            c for c in decision.ranked_candidates if c.target == ExecutionTarget.LOCAL
        )
        assert stale_candidate.eligible is False
        assert any("stale" in reason.lower() for reason in stale_candidate.disqualification_reasons)


class TestAntiFlapping:
    def test_stays_on_current_when_improvement_small(self, base_workload: WorkloadProfile) -> None:
        config = DecisionEngineConfig(switching_threshold=0.15)
        engine = DecisionEngine(config=config)
        states = [
            create_state(ExecutionTarget.LOCAL, cpu_usage=35.0, latency_ms=5.0),
            create_state(ExecutionTarget.EDGE, cpu_usage=30.0, latency_ms=15.0),
        ]
        decision1 = engine.decide(base_workload, states)
        decision2 = engine.decide(base_workload, states, current_target=decision1.target)
        assert decision2.target == decision1.target

    def test_switches_when_improvement_large(self, base_workload: WorkloadProfile) -> None:
        config = DecisionEngineConfig(switching_threshold=0.15)
        engine = DecisionEngine(config=config)
        states = [
            create_state(ExecutionTarget.LOCAL, cpu_usage=90.0, latency_ms=80.0, gpu_available=True),
            create_state(ExecutionTarget.EDGE, cpu_usage=20.0, latency_ms=15.0, gpu_available=True),
        ]
        decision = engine.decide(base_workload, states, current_target=ExecutionTarget.LOCAL)
        assert decision.target == ExecutionTarget.EDGE


class TestDegradedScenarios:
    def test_empty_states_raises_error(self, base_workload: WorkloadProfile) -> None:
        engine = DecisionEngine()
        with pytest.raises(ValueError, match="At least one"):
            engine.decide(base_workload, [])

    def test_all_ineligible_raises_no_eligible_target(self, base_workload: WorkloadProfile) -> None:
        engine = DecisionEngine()
        states = [
            create_state(ExecutionTarget.LOCAL, gpu_available=False),
            create_state(ExecutionTarget.EDGE, gpu_available=False),
            create_state(ExecutionTarget.CLOUD, gpu_available=False),
        ]
        with pytest.raises(NoEligibleTargetError, match="No eligible"):
            engine.decide(base_workload, states)

    def test_single_state_works(self, base_workload: WorkloadProfile) -> None:
        engine = DecisionEngine()
        decision = engine.decide(base_workload, [create_state(ExecutionTarget.EDGE)])
        assert decision.target == ExecutionTarget.EDGE
        assert len(decision.ranked_candidates) == 1


class TestExplainability:
    def test_reasons_non_empty(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        decision = DecisionEngine().decide(base_workload, all_healthy_states)
        assert len(decision.reasons) >= 1
        assert all(len(r.strip()) > 0 for r in decision.reasons)

    def test_reasons_include_selected_target(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        decision = DecisionEngine().decide(base_workload, all_healthy_states)
        target_name = decision.target.value.upper()
        assert any(target_name in r for r in decision.reasons)

    def test_reasons_include_score(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        decision = DecisionEngine().decide(base_workload, all_healthy_states)
        assert any("score" in r.lower() or "0." in r for r in decision.reasons)

    def test_score_breakdown_populated(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        decision = DecisionEngine().decide(base_workload, all_healthy_states)
        for candidate in decision.ranked_candidates:
            if candidate.eligible:
                assert len(candidate.score_breakdown) == 5
                expected_keys = {"performance", "resources", "network", "reliability", "cost"}
                assert set(candidate.score_breakdown.keys()) == expected_keys


class TestDeterminism:
    def test_same_inputs_same_output(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        engine = DecisionEngine()
        decision1 = engine.decide(base_workload, all_healthy_states)
        decision2 = engine.decide(base_workload, all_healthy_states)
        assert decision1.target == decision2.target
        assert decision1.score == decision2.score
        assert decision1.reasons == decision2.reasons

    def test_different_engines_same_config_same_output(
        self, base_workload: WorkloadProfile, all_healthy_states: list[InfrastructureState]
    ) -> None:
        config = DecisionEngineConfig()
        decision1 = DecisionEngine(config=config).decide(base_workload, all_healthy_states)
        decision2 = DecisionEngine(config=config).decide(base_workload, all_healthy_states)
        assert decision1.target == decision2.target
        assert decision1.score == decision2.score
