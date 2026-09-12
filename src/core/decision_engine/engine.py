"""Decision Engine implementation.

The Decision Engine is the source of truth for routing decisions.
It evaluates workload requirements against infrastructure state
and produces explainable, deterministic routing decisions.

Pipeline: Hard Constraints → Eligibility → Scoring → Ranking → Selection → Explainability
"""

from collections.abc import Sequence

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
        """Initialize the Decision Engine with optional dependencies.

        Args:
            config: Engine configuration. Uses defaults if not provided.
            constraint_evaluator: Hard constraint evaluator.
            scoring_engine: Scoring engine.
            anti_flapping_guard: Anti-flapping guard.
        """
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
        """Make a routing decision for a workload.

        This is the main entry point implementing the DecisionEngineProtocol.

        Args:
            workload: The workload to route.
            infrastructure_states: Current state of each execution target.
            current_target: Optional current target for anti-flapping.

        Returns:
            A RoutingDecision with the selected target, score, reasons,
            and full ranked candidate list.

        Raises:
            ValueError: If infrastructure_states is empty.
        """
        if not infrastructure_states:
            raise ValueError("At least one infrastructure state is required")

        # Build candidate list with eligibility and scores
        candidates = self._evaluate_candidates(workload, infrastructure_states)

        # Sort by score (highest first), ineligible last
        ranked_candidates = self._rank_candidates(candidates)

        # Select target with anti-flapping consideration
        selected = self._select_target(ranked_candidates, current_target)

        # Generate explainable reasons
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
        """Evaluate each target for eligibility and score.

        Args:
            workload: The workload requirements.
            states: Infrastructure states to evaluate.

        Returns:
            List of RoutingCandidate objects.
        """
        candidates: list[RoutingCandidate] = []

        for state in states:
            # Evaluate hard constraints
            eligible, disqualification_reasons = self._constraint_evaluator.evaluate(
                workload, state
            )

            if eligible:
                # Compute score for eligible targets
                score, score_breakdown = self._scoring_engine.score(workload, state)
                candidate = RoutingCandidate(
                    target=state.target,
                    eligible=True,
                    disqualification_reasons=[],
                    score=score,
                    score_breakdown=score_breakdown,
                )
            else:
                # Ineligible targets have no score
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
        """Rank candidates by score, with ineligible targets last.

        Args:
            candidates: Unordered list of candidates.

        Returns:
            Candidates sorted by score (highest first), ineligible last.
        """

        def sort_key(c: RoutingCandidate) -> tuple[int, float]:
            # Eligible first (0), then ineligible (1)
            # Within eligible, sort by score descending (negate for descending)
            eligibility_rank = 0 if c.eligible else 1
            score_rank = -(c.score if c.score is not None else 0.0)
            return (eligibility_rank, score_rank)

        return sorted(candidates, key=sort_key)

    def _select_target(
        self,
        ranked_candidates: list[RoutingCandidate],
        current_target: ExecutionTarget | None,
    ) -> RoutingCandidate:
        """Select the final target with anti-flapping.

        Args:
            ranked_candidates: Candidates sorted by score.
            current_target: Optional current target.

        Returns:
            The selected candidate.

        Raises:
            NoEligibleTargetError: If no eligible candidates exist.
        """
        # Find best eligible candidate
        best_eligible: RoutingCandidate | None = None
        current_candidate: RoutingCandidate | None = None

        for candidate in ranked_candidates:
            if candidate.eligible and best_eligible is None:
                best_eligible = candidate
            if candidate.target == current_target:
                current_candidate = candidate

        if best_eligible is None:
            # No eligible targets - select least-bad option
            # Return first candidate (which has fewest disqualifications)
            if ranked_candidates:
                return ranked_candidates[0]
            raise NoEligibleTargetError("No targets available for routing")

        # Apply anti-flapping logic
        current_score = (
            current_candidate.score
            if current_candidate is not None and current_candidate.score is not None
            else None
        )

        if self._anti_flapping_guard.should_switch(
            current_target, current_score, best_eligible
        ):
            return best_eligible

        # Stay on current target if it exists and is eligible
        if current_candidate is not None and current_candidate.eligible:
            return current_candidate

        return best_eligible

    def _generate_reasons(
        self,
        workload: WorkloadProfile,
        selected: RoutingCandidate,
        ranked_candidates: list[RoutingCandidate],
    ) -> list[str]:
        """Generate human-readable reasons for the decision.

        Args:
            workload: The workload that was routed.
            selected: The selected candidate.
            ranked_candidates: All evaluated candidates.

        Returns:
            List of reason strings explaining the decision.
        """
        reasons: list[str] = []

        if not selected.eligible:
            reasons.append(
                f"WARNING: Selected {selected.target.value} despite being ineligible "
                f"(no eligible targets available)"
            )
            if selected.disqualification_reasons:
                reasons.append(f"Issues: {', '.join(selected.disqualification_reasons)}")
            return reasons

        # Primary selection reason
        target_name = selected.target.value.upper()
        reasons.append(f"Selected {target_name} with score {selected.score:.2f}")

        # Score breakdown explanation
        if selected.score_breakdown:
            top_scores = sorted(
                selected.score_breakdown.items(), key=lambda x: x[1], reverse=True
            )[:3]
            score_parts = [f"{name}: {score:.2f}" for name, score in top_scores]
            reasons.append(f"Top factors: {', '.join(score_parts)}")

        # Comparison with other eligible candidates
        other_eligible = [
            c for c in ranked_candidates if c.eligible and c.target != selected.target
        ]
        if other_eligible:
            runner_up = other_eligible[0]
            if runner_up.score is not None and selected.score is not None:
                diff = selected.score - runner_up.score
                reasons.append(
                    f"Outscored {runner_up.target.value.upper()} by {diff:.2f}"
                )

        # Note excluded targets
        ineligible = [c for c in ranked_candidates if not c.eligible]
        if ineligible:
            excluded_names = [c.target.value.upper() for c in ineligible]
            reasons.append(f"Excluded: {', '.join(excluded_names)} (constraint violations)")

        return reasons
