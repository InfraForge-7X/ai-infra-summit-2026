"""Cloud Target Adapter implementation for AFRI-EDGE.

Executes AI workloads on Cloud execution targets.
"""

import time
from typing import Any

from src.adapters.base import BaseTargetAdapter
from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import ExecutionResult, RoutingDecision


class CloudTargetAdapter(BaseTargetAdapter):
    """Target adapter for executing workloads on Cloud targets.

    Handles compute dispatch to cloud infrastructure.
    """

    def __init__(self, default_network_latency_ms: float = 80.0) -> None:
        """Initialize CloudTargetAdapter with default cloud latency."""
        super().__init__(target=ExecutionTarget.CLOUD)
        self._default_network_latency_ms = default_network_latency_ms

    def execute(
        self,
        decision: RoutingDecision,
        payload: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute workload on a Cloud target.

        Args:
            decision: RoutingDecision specifying the decision details.
            payload: Optional execution payload/parameters.

        Returns:
            ExecutionResult containing execution metrics.
        """
        start_time = time.perf_counter()

        simulated_delay = 0.0
        fps_override = None
        network_latency_ms = self._default_network_latency_ms

        if payload:
            simulated_delay = payload.get("simulated_execution_ms", 0.0) / 1000.0
            fps_override = payload.get("fps")
            if "network_latency_ms" in payload:
                network_latency_ms = float(payload["network_latency_ms"])

        if simulated_delay > 0:
            time.sleep(simulated_delay)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        if payload and "execution_time_ms" in payload:
            elapsed_ms = float(payload["execution_time_ms"])

        return self._create_result(
            task_id=decision.task_id,
            status=ExecutionStatus.COMPLETED,
            execution_time_ms=elapsed_ms,
            network_latency_ms=network_latency_ms,
            fps=fps_override,
        )
