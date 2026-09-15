# AFRI-EDGE Routing Benchmark & Evidence

## Purpose

This benchmark provides controlled evidence for Task #12: AFRI-EDGE adaptive routing is compared with a static baseline under changing infrastructure conditions.

The benchmark reuses the existing `WorkloadProfile`, `InfrastructureState`, `RoutingDecision`, Decision Engine scoring configuration, and anti-flapping threshold. It does not add benchmark-only routing parameters or change the routing algorithm.

## Common workload

- Type: `REAL_TIME_VIDEO`
- Model: `yolo`
- Input size: `640`
- Latency requirement: `100 ms`
- Compute requirement: `GPU`

## Static baseline

The baseline is intentionally simple and deterministic: **always route to LOCAL**.

This is not presented as an optimal static policy. It is a fixed reference that cannot react to infrastructure changes.

## Controlled scenarios

| Scenario | Infrastructure condition | AFRI-EDGE | Static LOCAL | Evidence |
| --- | --- | --- | --- | --- |
| S1 | Local performant | LOCAL | LOCAL | Adaptive routing preserves the healthy local path. |
| S2 | Local saturated but still eligible | EDGE | LOCAL | Adaptive routing leaves a degraded Local target; static routing does not. |
| S3 | Edge network degraded but still eligible | LOCAL | LOCAL | Adaptive routing avoids the degraded Edge path. |
| S4 | Local changes from healthy to saturated | EDGE | LOCAL | Adaptive routing reroutes after a material infrastructure change. |
| S5 | Cloud is only marginally better than current Edge | EDGE | LOCAL | Anti-flapping keeps the current Edge target because the improvement is below the switching threshold. |

## Expected decision scores

Scores below are calculated from the repository's current default scoring weights and parameters.

| Scenario | LOCAL | EDGE | CLOUD | Selected |
| --- | ---: | ---: | ---: | --- |
| S1 | 0.9440 | 0.8250 | 0.7275 | LOCAL |
| S2 | 0.5600 | 0.8250 | 0.7275 | EDGE |
| S3 | 0.9440 | 0.4692 | 0.7275 | LOCAL |
| S4 | 0.5600 | 0.8250 | 0.7275 | EDGE |
| S5 | 0.6700 | 0.7100 | 0.7275 | EDGE* |

`*` In S5, Cloud has the highest raw score, but the improvement over the current Edge target is only `0.0175`, below the configured `0.15` switching threshold. AFRI-EDGE therefore stays on Edge.

## Scenario details

### S1 — Local performant

- Local: CPU 20%, RAM 30%, GPU available, queue 0, latency 2 ms, bandwidth 1000 Mbps, packet loss 0%.
- Edge: CPU 40%, RAM 50%, GPU available, queue 0, latency 15 ms, bandwidth 200 Mbps, packet loss 0%.
- Cloud: CPU 25%, RAM 35%, GPU available, queue 0, latency 50 ms, bandwidth 500 Mbps, packet loss 0%.

Expected: `LOCAL`.

### S2 — Local saturated

- Local: CPU 90%, RAM 90%, GPU available, queue 5, latency 80 ms, bandwidth 100 Mbps, packet loss 0%.
- Edge: CPU 40%, RAM 50%, GPU available, queue 0, latency 15 ms, bandwidth 200 Mbps, packet loss 0%.
- Cloud: CPU 25%, RAM 35%, GPU available, queue 0, latency 50 ms, bandwidth 500 Mbps, packet loss 0%.

Local remains below the hard 95% CPU/RAM limits, so this scenario demonstrates scoring-based adaptation rather than hard-constraint fallback.

Expected: `EDGE`.

### S3 — Edge degraded

- Local: CPU 20%, RAM 30%, GPU available, queue 0, latency 2 ms, bandwidth 1000 Mbps, packet loss 0%.
- Edge: CPU 40%, RAM 50%, GPU available, queue 0, latency 70 ms, bandwidth 5 Mbps, packet loss 8%.
- Cloud: CPU 25%, RAM 35%, GPU available, queue 0, latency 50 ms, bandwidth 500 Mbps, packet loss 0%.

Edge remains below the 10% packet-loss hard limit and above the 1 Mbps bandwidth minimum, so it stays eligible while receiving a strong network/performance penalty.

Expected: `LOCAL`.

### S4 — Material infrastructure change

The benchmark evaluates the degraded Local state from S2 while explicitly providing `current_target=LOCAL`.

Expected: `LOCAL → EDGE`.

The Edge score exceeds the current Local score by `0.265`, which is greater than the configured `0.15` switching threshold, so anti-flapping permits the switch.

### S5 — Anti-flapping

- Local: CPU 70%, RAM 70%, GPU available, queue 0, latency 60 ms, bandwidth 100 Mbps, packet loss 0%.
- Edge: CPU 60%, RAM 60%, GPU available, queue 0, latency 45 ms, bandwidth 100 Mbps, packet loss 0%.
- Cloud: CPU 25%, RAM 35%, GPU available, queue 0, latency 50 ms, bandwidth 500 Mbps, packet loss 0%.

The benchmark provides `current_target=EDGE`. Cloud scores slightly higher than Edge, but only by `0.0175`, below the `0.15` switching threshold.

Expected: remain on `EDGE`.

## Metrics captured

Each benchmark case verifies the same evidence fields:

- selected target
- routing score
- ranked candidates
- candidate eligibility
- score breakdown: performance, resources, network, reliability, cost
- decision reasons
- static baseline target
- rerouting outcome where applicable
- anti-flapping switch/no-switch outcome where applicable

Execution latency/FPS are intentionally not fabricated here: this benchmark evaluates the routing decision layer. Those metrics belong to execution/adapter evidence when measured by a real workload run.

## Reproduction

Run:

```bash
pytest -q tests/benchmark/test_routing_benchmark.py
```

The benchmark should remain deterministic because all infrastructure states are explicit and the Decision Engine's current scoring configuration is reused unchanged.
