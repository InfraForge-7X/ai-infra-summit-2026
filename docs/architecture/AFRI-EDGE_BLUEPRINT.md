# AFRI-EDGE — Competitive Architecture Baseline

**AI Infra Summit Hackathon 2026 — InfraForge 7X**

## Product Positioning

**AFRI-EDGE is intelligent infrastructure orchestration for real-time AI.**

The core product is the infrastructure intelligence that decides **where and how AI workloads should execute** across Local, Edge, and Cloud as infrastructure conditions change.

> AGENTOS decides what to execute. AFRI-EDGE decides where and how to execute it.

## Core Architecture

```text
User / Application
       ↓
AGENTOS / Orchestrator
       ↓
Workload Profile
       ↓
AFRI-EDGE Decision Engine
       ↓
Local / Edge / Cloud
       ↓
Execution Router + Adapters
       ↓
AI Workload Execution
       ↓
Result + Metrics
       ↓
Feedback / Re-evaluation
```

## Workload Strategy

The AFRI-EDGE core is **workload-agnostic**. The primary MVP workload is **real-time video analytics**.

Additional workloads can reuse the same profiling, state, routing, execution and feedback interfaces without changing the core Decision Engine.

Current planned modality coverage:

- **Video** — primary MVP and main demonstration workload.
- **Speech** — optional secondary capability using a Speechmatics adapter.
- Future modalities remain out of MVP scope unless they can be added without destabilizing the core.

## Infrastructure Strategy

The Decision Engine evaluates workload requirements against infrastructure state, applies hard constraints, scores eligible targets, explains the selected target, and applies anti-flapping before routing.

Conceptual score:

`Score(E) = w1*Performance + w2*Resources + w3*Network + w4*Reliability - w5*Cost`

Weights and switching thresholds are configurable and must be calibrated through controlled experiments. No performance improvement claim is valid before measurement.

## Adapter Architecture

> **The Core decides. Adapters execute.**

```text
                     AFRI-EDGE CORE
                          │
             ┌────────────┴────────────┐
             │     Decision Engine    │
             └────────────┬────────────┘
                          ↓
                  Execution Router
                          │
       ┌──────────────────┼──────────────────┐
       ↓                  ↓                  ↓
 Local Adapter      Edge Adapters      Cloud Adapter
                         │
                         └── SiMa.ai Adapter (optional)

 Speech workloads may use:
                         └── Speechmatics Adapter (optional)
```

Sponsor technologies are **optional providers/adapters**, not hard-coded dependencies. The generic Local/Edge/Cloud MVP must remain runnable without sponsor hardware or APIs.

## SiMa.ai Integration

SiMa.ai is treated as an optional **Edge / Physical AI execution adapter** for compatible vision workloads.

Goals:

- demonstrate real-time vision inference on an Edge/Physical AI target where access permits;
- allow AFRI-EDGE to route a compatible video workload to that target;
- keep provider-specific logic outside the Decision Engine;
- preserve a generic Edge adapter as fallback when SiMa.ai hardware/access is unavailable.

SiMa.ai integration strengthens the Physical AI / Edge AI demonstration but does not redefine AFRI-EDGE.

## Speechmatics Integration

Speechmatics is an optional speech capability, not a replacement for video analytics.

A user may select a speech/voice workload. The workload enters the same high-level pipeline:

`Speech input → Workload Profile → Infrastructure State → Decision → Local/Edge/Cloud → Speech execution → Feedback`

Speechmatics-specific logic belongs in an adapter. The routing core remains technology-agnostic.

## Competitive Demonstration Strategy

1. Run a **static-routing baseline**.
2. Run AFRI-EDGE with the same video workload.
3. Show the Edge environment degrading.
4. Show AFRI-EDGE making an explainable rerouting decision.
5. Demonstrate optional SiMa.ai Edge execution when available.
6. Switch to an optional Speechmatics workload to demonstrate modality extensibility.
7. Compare measured outcomes in the dashboard.

Primary evidence:

- latency;
- FPS where applicable;
- execution time;
- CPU/GPU/RAM utilization;
- network latency/bandwidth/data transferred;
- reliability/failures/timeouts;
- cost estimates where measurable.

## Scope Guardrails

Priority order:

**Core AFRI-EDGE → Video Analytics → SiMa.ai Edge adapter → Speechmatics optional capability**

Do not introduce unnecessary Kubernetes, large model catalogs, custom model training, reinforcement learning, complex persistence, or multi-cloud management into the MVP.

## Engineering Principle

Sponsor integrations must increase competitive value **without destabilizing the core build**.

The project remains successful if the generic AFRI-EDGE routing system works, even when a sponsor-specific integration is unavailable.
