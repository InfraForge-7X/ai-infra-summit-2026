"""Anti-flapping guard for the Decision Engine.

Prevents rapid switching between targets when score differences are small.
Stabilizes routing decisions to avoid unnecessary target changes.
"""

from src.shared import ExecutionTarget, RoutingCandidate


class AntiFlappingGuard:
    """Guards against rapid target switching (flapping).

    When the current target's score is close to the best candidate's score,
    we prefer to stay on the current target to avoid unnecessary switches.

    The switching_threshold defines the minimum improvement required to switch.
    For example, with threshold=0.15, the new target must score at least 15%
    better than the current target to trigger a switch.
    """

    def __init__(self, switching_threshold: float = 0.15) -> None:
        """Initialize with configurable switching threshold.

        Args:
            switching_threshold: Minimum score improvement (0-1) required
                to switch targets. Default is 0.15 (15%).
        """
        if not (0.0 <= switching_threshold <= 1.0):
            raise ValueError(
                f"switching_threshold must be between 0 and 1, got {switching_threshold}"
            )
        self._threshold = switching_threshold

    @property
    def threshold(self) -> float:
        """Return the configured switching threshold."""
        return self._threshold

    def should_switch(
        self,
        current_target: ExecutionTarget | None,
        current_score: float | None,
        best_candidate: RoutingCandidate,
    ) -> bool:
        """Determine if we should switch to the best candidate.

        Args:
            current_target: The currently selected target, or None if no
                previous selection exists.
            current_score: The score of the current target, or None if
                no previous selection exists.
            best_candidate: The highest-scoring eligible candidate.

        Returns:
            True if we should switch to best_candidate, False if we should
            stay on the current target.
        """
        # No current target: always switch to best
        if current_target is None or current_score is None:
            return True

        # Best candidate is ineligible: cannot switch
        if not best_candidate.eligible or best_candidate.score is None:
            return False

        # Same target: no switch needed
        if best_candidate.target == current_target:
            return False

        # Calculate improvement
        improvement = best_candidate.score - current_score

        # Switch only if improvement exceeds threshold
        return improvement > self._threshold

    def select_target(
        self,
        current_target: ExecutionTarget | None,
        current_score: float | None,
        ranked_candidates: list[RoutingCandidate],
    ) -> RoutingCandidate:
        """Select the final target considering anti-flapping.

        Args:
            current_target: The currently selected target.
            current_score: The score of the current target.
            ranked_candidates: Candidates sorted by score (highest first).

        Returns:
            The selected candidate (may be current target if not switching).

        Raises:
            ValueError: If no eligible candidates exist.
        """
        # Find best eligible candidate
        best_eligible: RoutingCandidate | None = None
        for candidate in ranked_candidates:
            if candidate.eligible and candidate.score is not None:
                best_eligible = candidate
                break

        if best_eligible is None:
            raise ValueError("No eligible candidates available")

        # Check if we should switch
        if self.should_switch(current_target, current_score, best_eligible):
            return best_eligible

        # Stay on current target - find it in candidates
        for candidate in ranked_candidates:
            if candidate.target == current_target:
                return candidate

        # Current target not in candidates (shouldn't happen)
        return best_eligible
