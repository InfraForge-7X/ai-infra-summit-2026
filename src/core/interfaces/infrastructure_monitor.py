"""Interface definition for the Infrastructure Monitor.

This protocol defines the contract that any Infrastructure Monitor implementation
must satisfy. It is used by higher-level components (e.g. routing integration,
Metrics & State Layer) without coupling them to a concrete implementation.

The collect() method is the single responsibility of any monitor:
produce a valid InfrastructureState snapshot for a requested execution target.
"""

from typing import Protocol, runtime_checkable

from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState


@runtime_checkable
class InfrastructureMonitorProtocol(Protocol):
    """Protocol defining the interface for infrastructure monitoring.

    Converts a requested execution target into a validated AFRI-EDGE
    InfrastructureState snapshot containing real (or gracefully degraded)
    host and network metrics.

    Any class that implements collect() with the correct signature
    satisfies this protocol, enabling easy replacement or extension
    (e.g. a remote cloud monitor, an edge-specific probe, or a test fake).
    """

    def collect(self, target: ExecutionTarget) -> InfrastructureState:
        """Collect current infrastructure metrics for the given target.

        Args:
            target: The execution target identity to tag this snapshot with.
                    One of ExecutionTarget.LOCAL, EDGE, or CLOUD.

        Returns:
            InfrastructureState: A validated snapshot of current infrastructure
            conditions, timestamped at UTC now. All fields conform to the
            shared InfrastructureState contract.

        Notes:
            Implementations must never raise for unavailable optional metrics
            (GPU, network). They must fall back to safe contract-compatible
            defaults (False / 0.0) instead.
        """
        ...
