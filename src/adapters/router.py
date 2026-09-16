"""Execution Router for AFRI-EDGE Target Adapters.

Maintains a registry of ExecutionTarget -> TargetAdapter mappings, receives
RoutingDecision outputs from the Decision Engine, dispatches execution to
the appropriate target adapter, and returns ExecutionResult telemetry.
"""

from typing import Any

from src.adapters.base import TargetAdapter
from src.shared.enums import ExecutionTarget
from src.shared.models import ExecutionResult, RoutingDecision


class NoAdapterRegisteredError(Exception):
    """Raised when no adapter is registered for a requested ExecutionTarget."""

    pass


class ExecutionRouter:
    """Dispatches execution decisions to registered TargetAdapters.

    Design:
    - Target-agnostic router.
    - Allows dynamic registration of generic or sponsor-specific adapters.
    - Preserves clean boundary: Core decides -> ExecutionRouter dispatches -> Adapter executes.
    """

    def __init__(
        self,
        adapters: list[TargetAdapter] | None = None,
    ) -> None:
        """Initialize the router with optional pre-registered adapters."""
        self._adapters: dict[ExecutionTarget, TargetAdapter] = {}
        if adapters:
            for adapter in adapters:
                self.register_adapter(adapter)

    def register_adapter(
        self,
        adapter: TargetAdapter,
        target: ExecutionTarget | None = None,
    ) -> None:
        """Register a TargetAdapter for an ExecutionTarget.

        Args:
            adapter: The TargetAdapter instance.
            target: Optional target override; if not provided, uses adapter.target.
        """
        target_key = target or adapter.target
        self._adapters[target_key] = adapter

    def get_adapter(self, target: ExecutionTarget) -> TargetAdapter | None:
        """Retrieve the registered adapter for a target.

        Args:
            target: The execution target to look up.

        Returns:
            The registered TargetAdapter, or None if not registered.
        """
        return self._adapters.get(target)

    def has_adapter(self, target: ExecutionTarget) -> bool:
        """Check whether an adapter is registered for a target."""
        return target in self._adapters

    def execute(
        self,
        decision: RoutingDecision,
        payload: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Dispatch a RoutingDecision to the appropriate TargetAdapter.

        Args:
            decision: RoutingDecision from the Decision Engine.
            payload: Optional workload execution payload.

        Returns:
            ExecutionResult: Telemetry returned by the executing adapter.

        Raises:
            NoAdapterRegisteredError: If no adapter is registered for decision.target.
        """
        target = decision.target
        adapter = self.get_adapter(target)
        if adapter is None:
            raise NoAdapterRegisteredError(
                f"No target adapter registered for execution target '{target.value}'"
            )

        return adapter.execute(decision, payload=payload)
