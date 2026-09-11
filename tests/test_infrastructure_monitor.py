"""Unit tests for AFRI-EDGE Infrastructure Monitor (Task #4).

Tests cover:
- collect() produces a valid InfrastructureState for all three targets
- CPU and RAM values are within the valid 0–100 range
- Timestamp is timezone-aware UTC
- Target identity is preserved exactly as supplied
- GPU unavailability degrades gracefully to False (no hardware required)
- Network metric stubs return 0.0 (no ICMP permissions or network required)
- Queue stub returns 0
- Output satisfies InfrastructureMonitorProtocol
- InfrastructureState contract is fully respected (extra="forbid")

All tests use deterministic mocking via _FixedMonitor, which overrides
every private _collect_* method with a fixed value. No psutil calls,
no GPU hardware, no network access, and no subprocess execution are
needed for any test to pass.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.core.interfaces.infrastructure_monitor import InfrastructureMonitorProtocol
from src.monitoring.infrastructure_monitor import InfrastructureMonitor
from src.shared.enums import ExecutionTarget
from src.shared.models import InfrastructureState


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _FixedMonitor(InfrastructureMonitor):
    """Deterministic test double for InfrastructureMonitor.

    Overrides every private _collect_* method so that:
    - No psutil calls are made (no real CPU/RAM sampling)
    - No subprocess is launched (no nvidia-smi)
    - No network access is required
    - All returned values are fixed and predictable

    This is the recommended testing pattern for this codebase:
    constructor-injected or subclass-based fakes rather than mocking
    external libraries (see tests/api/fakes.py for the same convention).
    """

    CPU_USAGE: float = 42.5
    RAM_USAGE: float = 61.0
    GPU_AVAILABLE: bool = True
    QUEUE: int = 0
    LATENCY_MS: float = 0.0
    BANDWIDTH_MBPS: float = 0.0
    PACKET_LOSS: float = 0.0

    def _collect_cpu(self) -> float:
        return self.CPU_USAGE

    def _collect_ram(self) -> float:
        return self.RAM_USAGE

    def _collect_gpu_available(self) -> bool:
        return self.GPU_AVAILABLE

    def _collect_queue(self) -> int:
        return self.QUEUE

    def _collect_latency_ms(self) -> float:
        return self.LATENCY_MS

    def _collect_bandwidth_mbps(self) -> float:
        return self.BANDWIDTH_MBPS

    def _collect_packet_loss(self) -> float:
        return self.PACKET_LOSS


def _make_state(
    target: ExecutionTarget = ExecutionTarget.LOCAL,
    cpu_usage: float = 42.5,
    gpu_available: bool = True,
    ram_usage: float = 61.0,
    queue: int = 0,
    latency_ms: float = 0.0,
    bandwidth_mbps: float = 0.0,
    packet_loss: float = 0.0,
    timestamp: datetime | None = None,
) -> InfrastructureState:
    """Factory helper for building expected InfrastructureState objects.

    Mirrors the create_infrastructure_state() factory pattern used in
    tests/test_state_store.py for consistency with the project conventions.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return InfrastructureState(
        target=target,
        cpu_usage=cpu_usage,
        gpu_available=gpu_available,
        ram_usage=ram_usage,
        queue=queue,
        latency_ms=latency_ms,
        bandwidth_mbps=bandwidth_mbps,
        packet_loss=packet_loss,
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# Test: collect() produces a valid InfrastructureState
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorCollect:
    """Tests that collect() returns a correctly populated InfrastructureState."""

    def test_collect_returns_infrastructure_state_instance(self) -> None:
        """collect() must return an InfrastructureState (not a dict or None)."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert isinstance(result, InfrastructureState)

    def test_collect_cpu_usage_matches_collector(self) -> None:
        """cpu_usage in the snapshot must equal what _collect_cpu() returns."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.cpu_usage == _FixedMonitor.CPU_USAGE

    def test_collect_ram_usage_matches_collector(self) -> None:
        """ram_usage in the snapshot must equal what _collect_ram() returns."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.ram_usage == _FixedMonitor.RAM_USAGE

    def test_collect_gpu_available_matches_collector(self) -> None:
        """gpu_available in the snapshot must equal what _collect_gpu_available() returns."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.gpu_available == _FixedMonitor.GPU_AVAILABLE

    def test_collect_queue_matches_collector(self) -> None:
        """queue in the snapshot must equal what _collect_queue() returns."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.queue == _FixedMonitor.QUEUE

    def test_collect_latency_matches_collector(self) -> None:
        """latency_ms in the snapshot must equal what _collect_latency_ms() returns."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.latency_ms == _FixedMonitor.LATENCY_MS

    def test_collect_bandwidth_matches_collector(self) -> None:
        """bandwidth_mbps must equal what _collect_bandwidth_mbps() returns."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.bandwidth_mbps == _FixedMonitor.BANDWIDTH_MBPS

    def test_collect_packet_loss_matches_collector(self) -> None:
        """packet_loss must equal what _collect_packet_loss() returns."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.packet_loss == _FixedMonitor.PACKET_LOSS

    def test_collect_timestamp_is_datetime(self) -> None:
        """timestamp must be a datetime instance."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert isinstance(result.timestamp, datetime)

    def test_collect_timestamp_is_timezone_aware(self) -> None:
        """timestamp must be timezone-aware (UTC), not a naive datetime."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.timestamp.tzinfo is not None

    def test_collect_timestamp_is_utc(self) -> None:
        """timestamp must be in UTC timezone."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        # UTC offset must be 0
        assert result.timestamp.utcoffset().total_seconds() == 0  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Test: target identity is preserved
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorTargetIdentity:
    """Tests that collect() preserves the requested target in the snapshot."""

    def test_collect_local_target_preserved(self) -> None:
        """LOCAL target must appear in the returned snapshot."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.target == ExecutionTarget.LOCAL

    def test_collect_edge_target_preserved(self) -> None:
        """EDGE target must appear in the returned snapshot."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.EDGE)
        assert result.target == ExecutionTarget.EDGE

    def test_collect_cloud_target_preserved(self) -> None:
        """CLOUD target must appear in the returned snapshot."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.CLOUD)
        assert result.target == ExecutionTarget.CLOUD

    @pytest.mark.parametrize("target", list(ExecutionTarget))
    def test_collect_all_targets_produce_valid_state(
        self, target: ExecutionTarget
    ) -> None:
        """Every ExecutionTarget value must produce a valid InfrastructureState."""
        monitor = _FixedMonitor()
        result = monitor.collect(target)
        assert isinstance(result, InfrastructureState)
        assert result.target == target


# ---------------------------------------------------------------------------
# Test: value ranges satisfy the InfrastructureState contract
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorValueRanges:
    """Tests that collect() produces values within InfrastructureState contract bounds."""

    def test_cpu_usage_within_valid_range(self) -> None:
        """cpu_usage must be in [0, 100]."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert 0.0 <= result.cpu_usage <= 100.0

    def test_ram_usage_within_valid_range(self) -> None:
        """ram_usage must be in [0, 100]."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert 0.0 <= result.ram_usage <= 100.0

    def test_queue_is_non_negative(self) -> None:
        """queue must be >= 0."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.queue >= 0

    def test_latency_ms_is_non_negative(self) -> None:
        """latency_ms must be >= 0."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.latency_ms >= 0.0

    def test_bandwidth_mbps_is_non_negative(self) -> None:
        """bandwidth_mbps must be >= 0."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.bandwidth_mbps >= 0.0

    def test_packet_loss_within_valid_range(self) -> None:
        """packet_loss must be in [0, 100]."""
        monitor = _FixedMonitor()
        result = monitor.collect(ExecutionTarget.LOCAL)
        assert 0.0 <= result.packet_loss <= 100.0


# ---------------------------------------------------------------------------
# Test: GPU graceful degradation
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorGpuFallback:
    """Tests that GPU unavailability degrades to False without raising.

    No GPU hardware, nvidia-smi, or CUDA driver is required for these tests.
    """

    def test_gpu_unavailable_when_nvidia_smi_absent(self) -> None:
        """_collect_gpu_available() must return False when nvidia-smi is not on PATH."""
        monitor = InfrastructureMonitor()
        with patch("src.monitoring.infrastructure_monitor.shutil.which", return_value=None):
            result = monitor._collect_gpu_available()
        assert result is False

    def test_gpu_unavailable_when_nvidia_smi_fails(self) -> None:
        """_collect_gpu_available() must return False when nvidia-smi exits non-zero."""
        monitor = InfrastructureMonitor()
        fake_result = MagicMock()
        fake_result.returncode = 1
        with (
            patch("src.monitoring.infrastructure_monitor.shutil.which", return_value="/usr/bin/nvidia-smi"),
            patch("src.monitoring.infrastructure_monitor.subprocess.run", return_value=fake_result),
        ):
            result = monitor._collect_gpu_available()
        assert result is False

    def test_gpu_unavailable_on_timeout(self) -> None:
        """_collect_gpu_available() must return False when nvidia-smi times out."""
        monitor = InfrastructureMonitor()
        with (
            patch("src.monitoring.infrastructure_monitor.shutil.which", return_value="/usr/bin/nvidia-smi"),
            patch(
                "src.monitoring.infrastructure_monitor.subprocess.run",
                side_effect=__import__("subprocess").TimeoutExpired(cmd="nvidia-smi", timeout=2),
            ),
        ):
            result = monitor._collect_gpu_available()
        assert result is False

    def test_gpu_unavailable_on_os_error(self) -> None:
        """_collect_gpu_available() must return False on unexpected OSError."""
        monitor = InfrastructureMonitor()
        with (
            patch("src.monitoring.infrastructure_monitor.shutil.which", return_value="/usr/bin/nvidia-smi"),
            patch(
                "src.monitoring.infrastructure_monitor.subprocess.run",
                side_effect=OSError("permission denied"),
            ),
        ):
            result = monitor._collect_gpu_available()
        assert result is False

    def test_gpu_available_when_nvidia_smi_succeeds(self) -> None:
        """_collect_gpu_available() returns True when nvidia-smi exits with code 0."""
        monitor = InfrastructureMonitor()
        fake_result = MagicMock()
        fake_result.returncode = 0
        with (
            patch("src.monitoring.infrastructure_monitor.shutil.which", return_value="/usr/bin/nvidia-smi"),
            patch("src.monitoring.infrastructure_monitor.subprocess.run", return_value=fake_result),
        ):
            result = monitor._collect_gpu_available()
        assert result is True

    def test_collect_with_gpu_unavailable_does_not_raise(self) -> None:
        """collect() must not raise even when no GPU is available."""
        monitor = InfrastructureMonitor()
        with (
            patch("src.monitoring.infrastructure_monitor.shutil.which", return_value=None),
            patch("src.monitoring.infrastructure_monitor.psutil.cpu_percent", return_value=30.0),
            patch("src.monitoring.infrastructure_monitor.psutil.virtual_memory") as mock_mem,
        ):
            mock_mem.return_value.percent = 55.0
            result = monitor.collect(ExecutionTarget.LOCAL)
        assert result.gpu_available is False
        assert isinstance(result, InfrastructureState)


# ---------------------------------------------------------------------------
# Test: network metric stubs (0.0 = unavailable / not measured)
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorNetworkStubs:
    """Tests that network metrics return 0.0 (the MVP stub / unavailable sentinel).

    No ICMP permissions, no real network access, and no open ports are needed.
    """

    def test_latency_stub_returns_unavailable_sentinel(self) -> None:
        """_collect_latency_ms() must return 0.0 (unavailable/not measured)."""
        monitor = InfrastructureMonitor()
        assert monitor._collect_latency_ms() == 0.0

    def test_bandwidth_stub_returns_unavailable_sentinel(self) -> None:
        """_collect_bandwidth_mbps() must return 0.0 (unavailable/not measured)."""
        monitor = InfrastructureMonitor()
        assert monitor._collect_bandwidth_mbps() == 0.0

    def test_packet_loss_stub_returns_unavailable_sentinel(self) -> None:
        """_collect_packet_loss() must return 0.0 (unavailable/not measured)."""
        monitor = InfrastructureMonitor()
        assert monitor._collect_packet_loss() == 0.0

    def test_queue_stub_returns_mvp_default(self) -> None:
        """_collect_queue() must return 0 (MVP default, no queue infra)."""
        monitor = InfrastructureMonitor()
        assert monitor._collect_queue() == 0


# ---------------------------------------------------------------------------
# Test: real psutil collectors (patched — no live sampling needed)
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorPsutilCollectors:
    """Tests for _collect_cpu() and _collect_ram() using patched psutil.

    These tests verify that the monitor correctly delegates to psutil
    and passes through the value. No real CPU sampling is performed.
    """

    def test_collect_cpu_delegates_to_psutil(self) -> None:
        """_collect_cpu() must return the value from psutil.cpu_percent."""
        monitor = InfrastructureMonitor()
        with patch("src.monitoring.infrastructure_monitor.psutil.cpu_percent", return_value=73.5):
            cpu = monitor._collect_cpu()
        assert cpu == 73.5

    def test_collect_ram_delegates_to_psutil(self) -> None:
        """_collect_ram() must return psutil.virtual_memory().percent."""
        monitor = InfrastructureMonitor()
        with patch("src.monitoring.infrastructure_monitor.psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 88.2
            ram = monitor._collect_ram()
        assert ram == 88.2

    @pytest.mark.parametrize("cpu_value", [0.0, 0.1, 50.0, 99.9, 100.0])
    def test_collect_cpu_boundary_values(self, cpu_value: float) -> None:
        """cpu_usage must accept all valid boundary values in [0, 100]."""
        monitor = InfrastructureMonitor()
        with patch("src.monitoring.infrastructure_monitor.psutil.cpu_percent", return_value=cpu_value):
            cpu = monitor._collect_cpu()
        assert cpu == cpu_value

    @pytest.mark.parametrize("ram_value", [0.0, 0.1, 50.0, 99.9, 100.0])
    def test_collect_ram_boundary_values(self, ram_value: float) -> None:
        """ram_usage must accept all valid boundary values in [0, 100]."""
        monitor = InfrastructureMonitor()
        with patch("src.monitoring.infrastructure_monitor.psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = ram_value
            ram = monitor._collect_ram()
        assert ram == ram_value


# ---------------------------------------------------------------------------
# Test: InfrastructureMonitorProtocol conformance
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorProtocol:
    """Tests that InfrastructureMonitor satisfies the InfrastructureMonitorProtocol."""

    def test_monitor_satisfies_protocol(self) -> None:
        """InfrastructureMonitor must be recognized as InfrastructureMonitorProtocol."""
        monitor = InfrastructureMonitor()
        assert isinstance(monitor, InfrastructureMonitorProtocol)

    def test_fixed_monitor_satisfies_protocol(self) -> None:
        """_FixedMonitor (test double) must also satisfy the protocol."""
        monitor = _FixedMonitor()
        assert isinstance(monitor, InfrastructureMonitorProtocol)

    def test_protocol_has_collect_method(self) -> None:
        """InfrastructureMonitorProtocol must define a collect() method."""
        assert hasattr(InfrastructureMonitorProtocol, "collect")


# ---------------------------------------------------------------------------
# Test: end-to-end collect() with fully patched psutil
# ---------------------------------------------------------------------------


class TestInfrastructureMonitorEndToEnd:
    """End-to-end tests of collect() with psutil fully patched.

    These tests verify that collect() assembles the InfrastructureState
    correctly from all sub-collectors without any real I/O.
    """

    def _make_patched_monitor(
        self,
        cpu: float = 30.0,
        ram: float = 50.0,
        gpu: bool = False,
    ) -> tuple[InfrastructureMonitor, dict]:
        """Return a real monitor plus a dict of active patches."""
        monitor = InfrastructureMonitor()
        patches: dict = {}
        patches["cpu"] = patch(
            "src.monitoring.infrastructure_monitor.psutil.cpu_percent",
            return_value=cpu,
        )
        patches["mem"] = patch(
            "src.monitoring.infrastructure_monitor.psutil.virtual_memory",
        )
        patches["which"] = patch(
            "src.monitoring.infrastructure_monitor.shutil.which",
            return_value=None,  # no nvidia-smi → gpu_available=False
        )
        return monitor, patches

    def test_collect_assembles_all_fields(self) -> None:
        """collect() must populate every field of InfrastructureState."""
        monitor = InfrastructureMonitor()
        with (
            patch("src.monitoring.infrastructure_monitor.psutil.cpu_percent", return_value=25.0),
            patch("src.monitoring.infrastructure_monitor.psutil.virtual_memory") as mock_mem,
            patch("src.monitoring.infrastructure_monitor.shutil.which", return_value=None),
        ):
            mock_mem.return_value.percent = 40.0
            result = monitor.collect(ExecutionTarget.LOCAL)

        assert result.target == ExecutionTarget.LOCAL
        assert result.cpu_usage == 25.0
        assert result.ram_usage == 40.0
        assert result.gpu_available is False
        assert result.queue == 0
        assert result.latency_ms == 0.0
        assert result.bandwidth_mbps == 0.0
        assert result.packet_loss == 0.0
        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.tzinfo is not None

    @pytest.mark.parametrize("target", list(ExecutionTarget))
    def test_collect_all_targets_end_to_end(self, target: ExecutionTarget) -> None:
        """collect() must succeed for every ExecutionTarget with psutil patched."""
        monitor = InfrastructureMonitor()
        with (
            patch("src.monitoring.infrastructure_monitor.psutil.cpu_percent", return_value=10.0),
            patch("src.monitoring.infrastructure_monitor.psutil.virtual_memory") as mock_mem,
            patch("src.monitoring.infrastructure_monitor.shutil.which", return_value=None),
        ):
            mock_mem.return_value.percent = 20.0
            result = monitor.collect(target)

        assert result.target == target
        assert isinstance(result, InfrastructureState)
