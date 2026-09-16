"""Decision Engine for AFRI-EDGE routing decisions.

The Decision Engine selects the best eligible execution target
(LOCAL, EDGE, CLOUD) based on workload requirements and current
infrastructure state.

Pipeline: Hard Constraints → Eligibility → Scoring → Ranking → Selection → Explainability

Example:
    from src.core.decision_engine import DecisionEngine, DecisionEngineConfig

    engine = DecisionEngine()
    decision = engine.decide(workload, infrastructure_states)
    print(decision.target)  # ExecutionTarget.EDGE
    print(decision.reasons)  # ["Selected EDGE with score 0.85", ...]
"""

from .anti_flapping import AntiFlappingGuard
from .config import ConstraintThresholds, DecisionEngineConfig, ScoringWeights
from .constraints import HardConstraintEvaluator
from .engine import DecisionEngine, NoEligibleTargetError
from .scoring import ScoringEngine

__all__ = [
    # Main engine
    "DecisionEngine",
    "NoEligibleTargetError",
    # Configuration
    "DecisionEngineConfig",
    "ScoringWeights",
    "ConstraintThresholds",
    # Components (for testing/customization)
    "HardConstraintEvaluator",
    "ScoringEngine",
    "AntiFlappingGuard",
]
