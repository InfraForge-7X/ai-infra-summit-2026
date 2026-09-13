"""Decision Engine implementation.

The Decision Engine is the source of truth for routing decisions.
It evaluates workload requirements against infrastructure state
and produces explainable, deterministic routing decisions.

Pipeline: Hard Constraints → Eligibility → Scoring → Ranking → Selection → Explainability
"""

from collections.abc import Sequence
from datetime import datetime, timezone

from src.shared import (
    ExecutionTarget,
    InfrastructureState,
    RoutingCandidate,
    RoutingDecision,
    WorkloadProfile,
)

from .anti_flapping import AntiFlappingGuard
from .config import DecisionEngineConfig
from .constraints import HardConstraintEvaluator
from .scoring import ScoringEngine


class NoEligibleTargetError(Exception):
    """Raised when no targets pass hard constraints."""

    pass


class DecisionEngine:
    """Orchestrates the routing decision pipeline.

    The Decision Engine evaluates each execution target against workload
    requirements and infrastructure state, producing an explainable
    routing decision with full transparency into the evaluation process.

    Pipeline stages:
    1. Hard Constraints: Check each target for eligibility
    2. Scoring: Compute multi-dimensional scores for eligible targets
    3. Ranking: Sort candidates by score (highest first)
    4. Selection: Choose best eligible target with anti-flapping
    5. Explainability: Generate human-readable reasons
    """

    def __init__(
        self,
        config: DecisionEngineConfig | None = None,
        constraint_evaluator: HardConstraintEvaluator | None = None,
        scoring_engine: ScoringEngine | None = None,
        anti_flapping_guard: AntiFlappingGuard | None = None,
    ) -> None:
        """Initialize the Decision Engine with optional dependencies."""
        self._config = config or DecisionEngineConfig()
        self._constraint_evaluator = constraint_evaluator or HardConstraintEvaluator(
            thresholds=self._config.constraint_thresholds
        )
        self._scoring_engine = scoring_engine or ScoringEngine(
            weights=self._config.scoring_weights
        )
        self._anti_flapping_guard = anti_flapping_guard or AntiFlappingGuard(
            switching_threshold=self._config.switching_threshold
        )

    @property
    def config(self) -> DecisionEngineConfig:
        """Return the engine configuration."""
        return self._config

    def decide(
        self,
        workload: WorkloadProfile,
        infrastructure_states: Sequence[InfrastructureState],
        current_target: ExecutionTarget | None = None,
    ) -> RoutingDecision:
        """Make a routing decision for a workload."""
        if not infrastructure_states:
            raise NoEligibleTargetError("No infrastructure state is available")

        candidates = self._evaluate_candidates(workload, infrastructure_states)
        ranked_candidates = self._rank_candidates(candidates)
        selected = self._select_target(ranked_candidates, current_target)
        reasons = self._generate_reasons(workload, selected, ranked_candidates)

        return RoutingDecision(
            task_id=workload.task_id,
            target=selected.target,
            score=selected.score if selected.score is not None else 0.0,
            reasons=reasons,
            ranked_candidates=ranked_candidates,
        )

    def _evaluate_candidates(
        self,
        workload: WorkloadProfile,
        states: Sequence[InfrastructureState],
    ) -> list[RoutingCandidate]:
        """Evaluate each target for freshness, eligibility, and score."""
        candidates: list[RoutingCandidate] = []
        now = datetime.now(timezone.utc)

        for state in states:
            timestamp = state.timestamp
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            age_seconds = max(0.0, (now - timestamp).total_seconds())
            if age_seconds > self._config.max_state_age_seconds:
                candidates.append(
                    RoutingCandidate(
                        target=state.target,
                        eligible=False,
                        disqualification_reasons=[
                            f"Infrastructure state is stale ({age_seconds:.1f}s old; "
                            f"maximum {self._config.max_state_age_seconds:.1f}s)"
                        ],
                        score=None,
                        score_breakdown={},
                    )
                )
                continue

            eligible, disqualification_reasons = self._constraint_evaluator.evaluate(
                workload, state
            )

            if eligible:
                score, score_breakdown = self._scoring_engine.score(workload, state)
                candidate = RoutingCandidate(
                    target=state.target,
                    eligible=True,
                    disqualification_reasons=[],
                    score=score,
                    score_breakdown=score_breakdown,
                )
            else:
                candidate = RoutingCandidate(
                    target=state.target,
                    eligible=False,
                    disqualification_reasons=disqualification_reasons,
                    score=None,
                    score_breakdown={},
                )

            candidates.append(candidate)

        return candidates

    def _rank_candidates(
        self,
        candidates: list[RoutingCandidate],
    ) -> list[RoutingCandidate]:
        """Rank eligible candidates by score, with ineligible targets last."""

        def sort_key(candidate: RoutingCandidate) -> tuple[int, float]:
            eligibility_rank = 0 if candidate.eligible else 1
            score_rank = -(candidate.score if candidate.score is not None else 0.0)
            return (eligibility_rank, score_rank)

        return sorted(candidates, key=sort_key)

    def _select_target(
        self,
        ranked_candidates: list[RoutingCandidate],
        current_target: ExecutionTarget | None,
    ) -> RoutingCandidate:
        """Select an eligible target with anti-flapping."""
        best_eligible: RoutingCandidate | None = None
        current_candidate: RoutingCandidate | None = None

        for candidate in ranked_candidates:
            if candidate.eligible and best_eligible is None:
                best_eligible = candidate
            if candidate.target == current_target:
                current_candidate = candidate

        if best_eligible is None:
            raise NoEligibleTargetError(
                "No eligible execution target is available"
            )

        current_score = (
            current_candidate.score
            if current_candidate is not None and current_candidate.eligible
            else None
        )

        if self._anti_flapping_guard.should_switch(
            current_target,
            current_score,
            best_eligible,
        ):
            return best_eligible

        if current_candidate is not None and current_candidate.eligible:
            return current_candidate

        return best_eligible

    def _generate_reasons(
        self,
        workload: WorkloadProfile,
        selected: RoutingCandidate,
        ranked_candidates: list[RoutingCandidate],
    ) -> list[str]:
        """Generate human-readable reasons for the decision."""
        reasons: list[str] = []
        target_name = selected.target.value.upper()
        reasons.append(
            f"Selected {target_name} with score {selected.score:.2f}"
        )

        if selected.score_breakdown:
            top_scores = sorted(
                selected.score_breakdown.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:3]
            score_parts = [
                f"{name}: {score:.2f}" for name, score in top_scores
            ]
            reasons.append(f"Top factors: {', '.join(score_parts)}")

        other_eligible = [
            candidate
            for candidate in ranked_candidates
            if candidate.eligible and candidate.target != selected.target
        ]
        if other_eligible:
            runner_up = other_eligible[0]
            if runner_up.score is not None and selected.score is not None:
                diff = selected.score - runner_up.score
                reasons.append(
                    f"Outscored {runner_up.target.value.upper()} by {diff:.2f}"
                )

        ineligible = [
            candidate
            for candidate in ranked_candidates
            if not candidate.eligible
        ]
        if ineligible:
            excluded_names = [
                candidate.target.value.upper() for candidate in ineligible
            ]
            reasons.append(
                f"Excluded: {', '.join(excluded_names)} "
                "(constraints or stale state)"
            )

        return reasons
