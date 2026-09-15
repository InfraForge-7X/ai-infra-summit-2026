"""Local Target Adapter implementation for AFRI-EDGE.

Executes AI workloads on the local host environment.
"""

import time
from typing import Any

from src.adapters.base import BaseTargetAdapter
from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import ExecutionResult, RoutingDecision


class LocalTargetAdapter(BaseTargetAdapter):
    """Target adapter for executing workloads locally.

    Handles local compute execution for Local host targets.
    In MVP mode, simulates or executes real CPU/GPU workload logic.
    """

    def __init__(self) -> None:
        """Initialize LocalTargetAdapter."""
        super().__init__(target=ExecutionTarget.LOCAL)

    def execute(
        self,
        decision: RoutingDecision,
        payload: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute workload on the local host.

        Args:
            decision: RoutingDecision specifying the decision details.
            payload: Optional execution payload/parameters (e.g. simulated processing time, frames).

        Returns:
            ExecutionResult containing execution metrics.
        """
        start_time = time.perf_counter()

        # Handle optional payload arguments for simulated or real execution
        simulated_delay = 0.0
        fps_override = None
        if payload:
            simulated_delay = payload.get("simulated_execution_ms", 0.0) / 1000.0
            fps_override = payload.get("fps")

        if simulated_delay > 0:
            time.sleep(simulated_delay)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        # If payload supplied explicit execution_time_ms, use it (useful for deterministic tests)
        if payload and "execution_time_ms" in payload:
            elapsed_ms = float(payload["execution_time_ms"])

        # Local execution has zero network latency
        network_latency_ms = 0.0

        return self._create_result(
            task_id=decision.task_id,
            status=ExecutionStatus.COMPLETED,
            execution_time_ms=elapsed_ms,
            network_latency_ms=network_latency_ms,
            fps=fps_override,
        )
