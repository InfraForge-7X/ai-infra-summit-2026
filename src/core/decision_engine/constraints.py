"""Hard constraint evaluation for the Decision Engine.

Hard constraints determine eligibility. An ineligible target cannot win
regardless of its score. Constraints are evaluated before scoring.
"""

from src.shared import (
    ComputeRequirement,
    ExecutionTarget,
    InfrastructureState,
    PrivacyLevel,
    WorkloadProfile,
)

from .config import ConstraintThresholds


class HardConstraintEvaluator:
    """Evaluates hard constraints to determine target eligibility.

    Hard constraints include:
    - Latency: Network latency must not exceed workload requirement
    - Compute: GPU must be available if workload requires GPU
    - Privacy: RESTRICTED privacy requires LOCAL execution only
    - Availability: CPU/RAM usage must be below saturation thresholds
    - Network: Packet loss and bandwidth must be acceptable
    """

    def __init__(self, thresholds: ConstraintThresholds | None = None) -> None:
        """Initialize with configurable thresholds.

        Args:
            thresholds: Constraint thresholds. Uses defaults if not provided.
        """
        self._thresholds = thresholds or ConstraintThresholds()

    def evaluate(
        self,
        workload: WorkloadProfile,
        state: InfrastructureState,
    ) -> tuple[bool, list[str]]:
        """Evaluate all hard constraints for a target.

        Args:
            workload: The workload requirements to satisfy.
            state: Current infrastructure state of the target.

        Returns:
            A tuple of (eligible, disqualification_reasons).
            eligible is True if all constraints pass.
            disqualification_reasons lists why constraints failed (empty if eligible).
        """
        reasons: list[str] = []

        # Check latency constraint
        if state.latency_ms > workload.latency_requirement:
            reasons.append(
                f"Latency {state.latency_ms:.0f}ms exceeds requirement {workload.latency_requirement}ms"
            )

        # Check compute constraint (GPU requirement)
        if workload.compute_requirement == ComputeRequirement.GPU and not state.gpu_available:
            reasons.append("GPU required but not available")

        # Check privacy constraint (RESTRICTED must stay LOCAL)
        if workload.privacy == PrivacyLevel.RESTRICTED and state.target != ExecutionTarget.LOCAL:
            reasons.append(f"RESTRICTED privacy requires LOCAL execution, not {state.target.value}")

        # Check resource availability (CPU saturation)
        if state.cpu_usage > self._thresholds.max_cpu_usage:
            reasons.append(
                f"CPU usage {state.cpu_usage:.0f}% exceeds threshold {self._thresholds.max_cpu_usage:.0f}%"
            )

        # Check resource availability (RAM saturation)
        if state.ram_usage > self._thresholds.max_ram_usage:
            reasons.append(
                f"RAM usage {state.ram_usage:.0f}% exceeds threshold {self._thresholds.max_ram_usage:.0f}%"
            )

        # Check network quality (packet loss)
        if state.packet_loss > self._thresholds.max_packet_loss:
            reasons.append(
                f"Packet loss {state.packet_loss:.1f}% exceeds threshold {self._thresholds.max_packet_loss:.1f}%"
            )

        # Check network quality (bandwidth)
        if state.bandwidth_mbps < self._thresholds.min_bandwidth_mbps:
            reasons.append(
                f"Bandwidth {state.bandwidth_mbps:.1f}Mbps below minimum {self._thresholds.min_bandwidth_mbps:.1f}Mbps"
            )

        eligible = len(reasons) == 0
        return eligible, reasons
