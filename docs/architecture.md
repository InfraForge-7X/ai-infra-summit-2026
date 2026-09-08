# AFRI-EDGE — Documentation Foundation
**InfraForge 7X | AI Infra Summit Hackathon 2026**
**GitHub Issue #10 — Task #9: Documentation Foundation**
**Reference:** AFRI-EDGE Technical Blueprint, Version 1.1

---

## 1. Project Overview

AFRI-EDGE is an **infrastructure-aware, workload-agnostic adaptive runtime**. It dynamically
routes AI workloads across **Local, Edge, and Cloud** environments based on real-time
infrastructure conditions — latency, bandwidth, compute availability, workload requirements,
reliability, and cost.

Real-time video analytics is the primary MVP workload and demonstration scenario, but the
core is designed to remain workload-agnostic so other modalities (e.g. speech) can reuse the
same pipeline without changes to the decision logic.

**Core distinction:** AGENTOS decides *what* to execute. AFRI-EDGE decides *where and how*
to execute it.

---

## 2. Problem We Are Solving

Real-time AI workloads (e.g. video inference) are sensitive to changing infrastructure
conditions. A **static** execution choice (always Local, always Cloud, etc.) can become
inefficient the moment latency, bandwidth, compute availability, workload pressure,
reliability, or cost shifts.

AFRI-EDGE observes these conditions continuously and selects the most appropriate
execution target at any given moment.

---

## 3. AFRI-EDGE Vision (North Star)

AFRI-EDGE dynamically routes real-time video inference workloads across Local, Edge, and
Cloud according to changing infrastructure conditions, while:
- Providing measurable execution metrics
- Outperforming a static routing strategy in relevant scenarios (measured, not assumed)

---

## 4. Core Architecture

```
USER / APPLICATION
        ↓
AGENTOS / Agent Orchestrator
        ↓
Task Decomposition → Workload Profiler
        ↓
AFRI-EDGE Decision Engine
        ↓
   LOCAL | EDGE | CLOUD
        ↓
Execution Router / Adapters
        ↓
   Video AI Inference
        ↓
Execution Result + Metrics
        ↓
Feedback / Re-evaluation → back to Decision Engine
```

This forms a closed feedback loop: **Decide → Route → Execute → Observe → Re-evaluate → Adapt.**

---

## 5. Main Components

| Component | Responsibility |
|---|---|
| AGENTOS Adapter | Translates an AI task into the AFRI-EDGE workload contract |
| Workload Profiler | Produces a deterministic `WorkloadProfile` |
| Infrastructure Monitor | Collects compute and network observations |
| Metrics & State Layer | Normalizes and maintains latest state, tracks freshness |
| Decision Engine | Applies constraints, scoring, ranking, reasons, anti-flapping |
| Execution Router | Dispatches through standardized adapters |
| Local / Edge / Cloud Adapters | Isolate environment-specific execution |
| Feedback Collector | Captures outcomes and observed metrics |
| Dashboard | Exposes decisions, state, metrics, and baseline comparison |

---

## 6. How Local / Edge / Cloud Routing Works

The Decision Engine follows a fixed, deterministic flow:

1. Validate workload
2. Apply hard constraints
3. Determine eligible targets
4. Score eligible targets
5. Rank candidates
6. Select target
7. Generate reasons
8. Apply anti-flapping (prevents oscillation between targets)
9. Return a `RoutingDecision`

**Conceptual scoring formula:**
```
Score(E) = w1*Performance + w2*Resources + w3*Network + w4*Reliability - w5*Cost
```
Weights and switching thresholds are **configurable**, not fixed magic numbers, and are
calibrated through controlled experiments (see Section 10 of the Blueprint).

The engine is deterministic, explainable, and technology-agnostic. A missing or stale
observation makes a target ineligible or reduces its confidence, per policy — it never
silently fails.

**Execution lifecycle:**
```
CREATED → ROUTING → DISPATCHED → RUNNING → COMPLETED → RESULT_RETURNED
```
Failure states: `FAILED`, `TIMEOUT`, `CANCELLED`.

---

## 7. Video Analytics — Primary Use Case

- Primary MVP workload type: `REAL_TIME_VIDEO`
- Reference model: YOLO (as an interchangeable model adapter, not a hard dependency)
- The workload contract (`WorkloadProfile`) is shared and workload-agnostic, so it must
  remain reusable for future modalities (e.g. `SPEECH`) without changing the Decision Engine
- MVP demo scenarios:
  - **Normal conditions** → routes to best eligible target
  - **Edge overloaded** → reroutes to Cloud or another eligible target
  - **Cloud/network degraded** → reroutes to Local/Edge where appropriate
  - **Recovery** → returns to the recovered target only when the stability policy allows

---

## 8. Optional Integrations

### SiMa.ai (Edge / Physical AI)
- Optional execution-provider adapter for the Edge environment
- Architecture remains fully functional **without** SiMa.ai hardware
- When available, routes compatible video/vision workloads to a Physical AI edge target
- Isolated behind the adapter interface — the Decision Engine stays technology-agnostic

### Speechmatics (Optional Speech Capability)
- Optional speech-processing capability, **not** a replacement for video analytics
- Speech workloads enter the same profiling → infrastructure assessment → routing →
  execution → feedback pipeline as video
- Isolated behind its own adapter; demonstrates that the same routing core can handle
  heterogeneous AI workloads

**Sponsor Integration Principle:** Sponsor technologies are capabilities/providers, not
architectural dependencies. The Core decides. Adapters execute. All sponsor adapters must be
optional, replaceable, and isolated from the Decision Engine. The MVP must remain runnable in
a generic simulated Local/Edge/Cloud environment even if sponsor access is unavailable.

---

## 9. Development Workflow

```
Blueprint → GitHub Issue → Owner → Feature Branch → Development
   → Tests → PR → Review → Merge → Integration → Validation
```

- **GitHub** is the technical source of truth.
- **Google Drive** is the collaborative workspace for research, architecture drafts,
  presentation, demo assets, and submission materials.
- **Definition of Done** = Implemented + Tested + Integrated.
- No secrets committed to GitHub — `.env` locally, `.env.example` for the template.
- `main` stays stable; all implementation happens on feature branches.

**Current implementation baseline (as of this Blueprint):**
- Validated on `main`: FastAPI skeleton, health endpoint, tests, Python configuration,
  Dockerfile, Docker Compose, environment template, repo documentation structure.
- The Routing API has an **intentionally non-functional** integration scaffold on
  `feat/routing-decision-api` (**Draft PR #12**), pending the shared contracts and Decision
  Engine.
- Shared Data Models (Task #2) are in progress: **PR #13** open on `feat/shared-data-models`,
  currently under review.

---

## 10. Demo Direction

Planned demo sequence:
1. Run the static baseline (fixed destination)
2. AFRI-EDGE selects the best target under normal conditions
3. Trigger Edge degradation → observe explainable rerouting
4. (Optional) Demonstrate SiMa.ai Edge execution
5. (Optional) Select a Speechmatics speech workload to show modality extensibility
6. Compare measured metrics (latency, FPS, execution time, infra utilization, reliability,
   cost where measurable) against the static baseline

**Important:** No performance-improvement percentage is claimed before measurement — all
comparative claims must come from controlled experiments run under identical scenarios.

---

*This document reflects only what is defined in Blueprint v1.1 and the verified repository
state at the time of this update. No implementation results beyond that state have been
assumed or invented.*
