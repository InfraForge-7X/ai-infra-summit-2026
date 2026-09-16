"""Tests for AntiFlappingGuard."""

import pytest

from src.core.decision_engine import AntiFlappingGuard
from src.shared import ExecutionTarget, RoutingCandidate


def make_candidate(
    target: ExecutionTarget,
    eligible: bool = True,
    score: float | None = 0.8,
) -> RoutingCandidate:
    """Helper to create a RoutingCandidate."""
    return RoutingCandidate(
        target=target,
        eligible=eligible,
        score=score if eligible else None,
        score_breakdown={"performance": 0.8} if eligible else {},
        disqualification_reasons=[] if eligible else ["Test failure"],
    )


class TestAntiFlappingGuardInit:
    """Tests for AntiFlappingGuard initialization."""

    def test_default_threshold(self) -> None:
        """Default threshold should be 0.15."""
        guard = AntiFlappingGuard()
        assert guard.threshold == 0.15

    def test_custom_threshold(self) -> None:
        """Custom threshold should be accepted."""
        guard = AntiFlappingGuard(switching_threshold=0.25)
        assert guard.threshold == 0.25

    def test_invalid_threshold_rejected(self) -> None:
        """Threshold outside [0, 1] should be rejected."""
        with pytest.raises(ValueError):
            AntiFlappingGuard(switching_threshold=1.5)

        with pytest.raises(ValueError):
            AntiFlappingGuard(switching_threshold=-0.1)


class TestShouldSwitch:
    """Tests for should_switch decision logic."""

    def test_no_current_target_always_switches(self) -> None:
        """Without current target, should always switch to best."""
        guard = AntiFlappingGuard()
        best = make_candidate(ExecutionTarget.EDGE, score=0.8)

        result = guard.should_switch(None, None, best)

        assert result is True

    def test_same_target_no_switch(self) -> None:
        """Same target should never trigger switch."""
        guard = AntiFlappingGuard()
        best = make_candidate(ExecutionTarget.EDGE, score=0.9)

        result = guard.should_switch(ExecutionTarget.EDGE, 0.8, best)

        assert result is False

    def test_small_improvement_no_switch(self) -> None:
        """Improvement below threshold should not trigger switch."""
        guard = AntiFlappingGuard(switching_threshold=0.15)
        best = make_candidate(ExecutionTarget.CLOUD, score=0.85)

        # 0.85 - 0.80 = 0.05, less than 0.15 threshold
        result = guard.should_switch(ExecutionTarget.EDGE, 0.80, best)

        assert result is False

    def test_large_improvement_triggers_switch(self) -> None:
        """Improvement above threshold should trigger switch."""
        guard = AntiFlappingGuard(switching_threshold=0.15)
        best = make_candidate(ExecutionTarget.CLOUD, score=0.95)

        # 0.95 - 0.75 = 0.20, greater than 0.15 threshold
        result = guard.should_switch(ExecutionTarget.EDGE, 0.75, best)

        assert result is True

    def test_improvement_at_threshold_no_switch(self) -> None:
        """Improvement exactly at threshold should not trigger switch."""
        # Use 0.25 threshold and 0.5/0.75 scores (exact binary fractions)
        guard = AntiFlappingGuard(switching_threshold=0.25)
        best = make_candidate(ExecutionTarget.CLOUD, score=0.75)

        # 0.75 - 0.50 = 0.25, exactly at threshold
        result = guard.should_switch(ExecutionTarget.EDGE, 0.50, best)

        assert result is False  # Must exceed, not equal

    def test_ineligible_best_no_switch(self) -> None:
        """Ineligible best candidate should not trigger switch."""
        guard = AntiFlappingGuard()
        best = make_candidate(ExecutionTarget.CLOUD, eligible=False)

        result = guard.should_switch(ExecutionTarget.EDGE, 0.75, best)

        assert result is False


class TestSelectTarget:
    """Tests for select_target with anti-flapping."""

    def test_selects_best_eligible_when_no_current(self) -> None:
        """Without current target, should select best eligible."""
        guard = AntiFlappingGuard()
        candidates = [
            make_candidate(ExecutionTarget.EDGE, score=0.9),
            make_candidate(ExecutionTarget.CLOUD, score=0.8),
            make_candidate(ExecutionTarget.LOCAL, score=0.7),
        ]

        result = guard.select_target(None, None, candidates)

        assert result.target == ExecutionTarget.EDGE

    def test_stays_on_current_when_improvement_small(self) -> None:
        """Should stay on current when improvement is small."""
        guard = AntiFlappingGuard(switching_threshold=0.15)
        candidates = [
            make_candidate(ExecutionTarget.CLOUD, score=0.85),
            make_candidate(ExecutionTarget.EDGE, score=0.80),
            make_candidate(ExecutionTarget.LOCAL, score=0.75),
        ]

        # Current is EDGE at 0.80, CLOUD is 0.85 (only 0.05 better)
        result = guard.select_target(ExecutionTarget.EDGE, 0.80, candidates)

        assert result.target == ExecutionTarget.EDGE

    def test_switches_when_improvement_large(self) -> None:
        """Should switch when improvement exceeds threshold."""
        guard = AntiFlappingGuard(switching_threshold=0.15)
        candidates = [
            make_candidate(ExecutionTarget.CLOUD, score=0.95),
            make_candidate(ExecutionTarget.EDGE, score=0.75),
            make_candidate(ExecutionTarget.LOCAL, score=0.70),
        ]

        # Current is EDGE at 0.75, CLOUD is 0.95 (0.20 better)
        result = guard.select_target(ExecutionTarget.EDGE, 0.75, candidates)

        assert result.target == ExecutionTarget.CLOUD

    def test_raises_when_no_eligible_candidates(self) -> None:
        """Should raise when no eligible candidates exist."""
        guard = AntiFlappingGuard()
        candidates = [
            make_candidate(ExecutionTarget.EDGE, eligible=False),
            make_candidate(ExecutionTarget.CLOUD, eligible=False),
        ]

        with pytest.raises(ValueError, match="No eligible"):
            guard.select_target(None, None, candidates)

    def test_switches_when_current_not_in_candidates(self) -> None:
        """Should switch to best when current target not in candidates."""
        guard = AntiFlappingGuard()
        candidates = [
            make_candidate(ExecutionTarget.EDGE, score=0.9),
            make_candidate(ExecutionTarget.CLOUD, score=0.8),
        ]

        # Current is LOCAL but not in candidates
        result = guard.select_target(ExecutionTarget.LOCAL, 0.85, candidates)

        assert result.target == ExecutionTarget.EDGE
