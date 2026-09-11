"""Infrastructure Monitor implementation for AFRI-EDGE.

Collects real host system metrics and produces validated InfrastructureState
snapshots compatible with the shared AFRI-EDGE data contract.

Design principles:
- CPU and RAM are always collected via psutil (cross-platform, reliable).
- GPU availability is optional: detected via nvidia-smi; returns False when
  the binary is absent, times out, or fails. No GPU hardware is required.
- Network metrics (latency, bandwidth, packet loss) are optional stubs in the
  MVP. They return 0.0, which is the contract-compatible sentinel meaning
  "unavailable / not measured". Future implementations can override individual
  _collect_* methods without changing the public API or the shared contract.
- Queue depth returns 0 for the MVP. There is no queue infrastructure yet.
- The requested target identity is always preserved in the snapshot.
  This implementation collects LOCAL host metrics only. Callers must use
  target-appropriate collector subclasses (or adapters) for EDGE/CLOUD.
- All private _collect_* methods are deliberately small and overrideable
  to enable deterministic testing without touching psutil or the network.
"""

import shutil
import subprocess
from datetime import datetime, timezone

import psutil

from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState

# ---------------------------------------------------------------------------
# Sentinel values
# ---------------------------------------------------------------------------
# These are contract-compatible defaults returned when an optional metric
# cannot be measured. A value of 0.0 means "unavailable / not measured"
# and is safe for all ge=0 fields in InfrastructureState. Consumers of
# InfrastructureState should treat 0.0 latency/bandwidth/packet_loss as
# "metric not available" rather than "perfectly healthy network".

_UNAVAILABLE_FLOAT: float = 0.0
_UNAVAILABLE_QUEUE: int = 0


class InfrastructureMonitor:
    """Collects host system metrics and formats them as InfrastructureState.

    This is the MVP implementation. It collects real CPU and RAM readings
    from the local host via psutil. All other metrics (GPU, network) are
    either probed with safe fallbacks or stubbed with contract-safe defaults.

    The target parameter in collect() identifies *which* execution environment
    the snapshot represents, not where the monitor is running. For the MVP,
    all snapshots reflect local host conditions. Future implementations can
    subclass or replace individual _collect_* methods to probe remote targets.

    Usage:
        monitor = InfrastructureMonitor()
        state = monitor.collect(ExecutionTarget.LOCAL)
        # state is a valid InfrastructureState ready for StateStore.register()
    """

    def collect(self, target: ExecutionTarget) -> InfrastructureState:
        """Collect a current infrastructure snapshot for the given target.

        Args:
            target: The execution target identity to stamp on the snapshot.
                    The target is preserved as-is; it does not change which
                    host metrics are read in the MVP.

        Returns:
            InfrastructureState: Validated snapshot. All optional metrics
            (GPU, network) gracefully fall back to safe defaults when
            unavailable. Never raises.
        """
        return InfrastructureState(
            target=target,
            cpu_usage=self._collect_cpu(),
            gpu_available=self._collect_gpu_available(),
            ram_usage=self._collect_ram(),
            queue=self._collect_queue(),
            latency_ms=self._collect_latency_ms(),
            bandwidth_mbps=self._collect_bandwidth_mbps(),
            packet_loss=self._collect_packet_loss(),
            timestamp=self._collect_timestamp(),
        )

    # ------------------------------------------------------------------
    # Reliable host metrics — always collected
    # ------------------------------------------------------------------

    def _collect_cpu(self) -> float:
        """Return current CPU utilisation as a percentage (0–100).

        Uses psutil.cpu_percent with a short blocking interval to ensure
        the first call returns a meaningful reading (interval=None returns
        0.0 on the very first invocation after process startup).
        """
        return psutil.cpu_percent(interval=0.1)

    def _collect_ram(self) -> float:
        """Return current RAM utilisation as a percentage (0–100).

        Uses psutil.virtual_memory().percent which is always available
        across Linux, macOS, and Windows.
        """
        return psutil.virtual_memory().percent

    def _collect_timestamp(self) -> datetime:
        """Return the current UTC time for the snapshot.

        Always timezone-aware (UTC). InfrastructureState stores naive
        datetimes as UTC by convention, but this implementation provides
        an explicit timezone for clarity and correctness.
        """
        return datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Optional metric — GPU availability
    # ------------------------------------------------------------------

    def _collect_gpu_available(self) -> bool:
        """Probe whether a CUDA-capable GPU is accessible via nvidia-smi.

        Returns True only when nvidia-smi is present on PATH and exits
        with code 0. Falls back to False for any of:
          - nvidia-smi not found (FileNotFoundError / shutil.which miss)
          - probe times out (2 s ceiling)
          - unexpected OS-level error

        This does not use a Python GPU library (e.g. pynvml) to avoid
        an additional dependency. shutil.which provides a fast pre-check
        before spawning the subprocess.
        """
        if shutil.which("nvidia-smi") is None:
            # nvidia-smi not on PATH — no CUDA GPU available
            return False
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            # Probe timed out or OS refused execution — treat as unavailable
            return False

    # ------------------------------------------------------------------
    # Optional metrics — network (MVP stubs)
    # ------------------------------------------------------------------
    # These return 0.0 for the MVP. 0.0 is the contract-compatible sentinel
    # meaning "unavailable / not measured" for all ge=0 float fields.
    # Override these methods in a subclass to add real network probes
    # (e.g. ICMP ping, TCP round-trip, iperf3) without changing the API.
    # ------------------------------------------------------------------

    def _collect_latency_ms(self) -> float:
        """Return network latency to the target in milliseconds.

        MVP stub — returns 0.0 (unavailable / not measured).
        Real implementations: ICMP ping, TCP SYN probe, or HTTP round-trip.
        """
        return _UNAVAILABLE_FLOAT

    def _collect_bandwidth_mbps(self) -> float:
        """Return available network bandwidth in Mbps.

        MVP stub — returns 0.0 (unavailable / not measured).
        Real implementations: psutil.net_io_counters() delta over an
        interval, or an iperf3-based probe.
        """
        return _UNAVAILABLE_FLOAT

    def _collect_packet_loss(self) -> float:
        """Return packet loss as a percentage (0–100).

        MVP stub — returns 0.0 (unavailable / not measured).
        Real implementations: parse ping statistics or use a UDP probe.
        """
        return _UNAVAILABLE_FLOAT

    # ------------------------------------------------------------------
    # Optional metric — queue depth (MVP default)
    # ------------------------------------------------------------------

    def _collect_queue(self) -> int:
        """Return the number of tasks currently queued for this target.

        MVP default — returns 0. There is no queue infrastructure yet.
        Future implementations can read from a local task queue, Redis,
        or a target-specific API without changing the public collect() API.
        """
        return _UNAVAILABLE_QUEUE
