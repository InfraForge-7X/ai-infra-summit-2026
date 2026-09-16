"""Base interface and abstract class for AFRI-EDGE Target Adapters.

Target Adapters bridge the Decision Engine's RoutingDecision output with the actual
workload execution environment (Local host, Edge device, Cloud service).

Design principles:
- Technology-agnostic interface
- Standardized execution contract returning ExecutionResult
- Easily extensible for future sponsor hardware/cloud adapters
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from src.shared.enums import ExecutionStatus, ExecutionTarget
from src.shared.models import ExecutionResult, RoutingDecision


@runtime_checkable
class TargetAdapter(Protocol):
    """Protocol defining the contract for execution target adapters.

    The Core decides. Adapters execute.
    """

    @property
    def target(self) -> ExecutionTarget:
        """The execution target this adapter handles."""
        ...

    def execute(
        self,
        decision: RoutingDecision,
        payload: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute a workload according to the routing decision.

        Args:
            decision: The RoutingDecision produced by the Decision Engine.
            payload: Optional workload payload / parameters.

        Returns:
            ExecutionResult detailing the status and performance metrics of execution.
        """
        ...


class BaseTargetAdapter(ABC):
    """Abstract base class for TargetAdapter implementations.

    Provides common functionality for formatting ExecutionResult objects
    and tracking target identities.
    """

    def __init__(self, target: ExecutionTarget) -> None:
        """Initialize the target adapter with its target identity."""
        self._target = target

    @property
    def target(self) -> ExecutionTarget:
        """Return the target identity."""
        return self._target

    @abstractmethod
    def execute(
        self,
        decision: RoutingDecision,
        payload: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute a workload according to the routing decision."""
        ...

    def _create_result(
        self,
        task_id: str,
        status: ExecutionStatus = ExecutionStatus.COMPLETED,
        execution_time_ms: float = 0.0,
        network_latency_ms: float = 0.0,
        fps: float | None = None,
    ) -> ExecutionResult:
        """Construct a validated ExecutionResult object."""
        return ExecutionResult(
            task_id=task_id,
            target=self._target,
            status=status,
            execution_time_ms=execution_time_ms,
            network_latency_ms=network_latency_ms,
            fps=fps,
        )
