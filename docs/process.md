# AFRI-EDGE — Documentation Foundation (Part 2: Process & Governance)
**InfraForge 7X | AI Infra Summit Hackathon 2026**
**GitHub Issue #10 — Task #9: Documentation Foundation**
**Reference:** AFRI-EDGE Technical Blueprint, Version 1.1

> This document covers team process, workflow, sponsor governance, demo direction, and
> scope boundaries. For architecture, components, and routing logic, see the companion
> document (Part 1).

---

## 1. Team Execution Map

| Task | Owner | Support |
|---|---|---|
| #1 Project Structure | Tsadok | Muhammad |
| #2 Shared Data Models | Hoàng | — |
| #3 Workload Profiler | Muhammad | Hoàng |
| #4 Infrastructure Monitor | Muhammad | Tsadok |
| #5 Metrics & State | Hoàng | Muhammad |
| #6 Decision Engine | Hoàng | Tsadok |
| #7 Routing API | Tsadok | Hoàng |
| #8 Dashboard | Tsadok + Jeremiah | Muhammad if needed |
| #9 Documentation | Madiha | Whole team |

**Engineering principles:**
- One primary owner per component; contributors may assist.
- `main` stays stable — all feature work happens on branches.
- Architecture changes require alignment between Hoàng + Tsadok; major decisions are team decisions.
- Definition of Done = **Implemented + Tested + Integrated.**
- No secrets in GitHub — `.env` locally, `.env.example` committed as the template.

---

## 2. Sprint 1 Dependency Chain

```
Task #1 Foundation [VALIDATED]
        ↓
Task #2 Shared Data Models
        ↓
   Task #3 ─┬─ Task #4
             ↓
     Task #5 Metrics & State
             ↓
     Task #6 Decision Engine
             ↓
     Task #7 Routing API
             ↓
     Task #8 Dashboard

Task #9 Documentation → runs in parallel, wherever dependencies allow
```

---

## 3. Development Workflow

```
Blueprint → GitHub Issue → Owner → Feature Branch → Development
   → Tests → PR → Review → Merge → Integration → Validation
```
- **GitHub** = technical source of truth.
- **Google Drive** = collaborative workspace (research, architecture drafts, presentation,
  demo assets, submission materials).
- Sponsor-specific capabilities are designed as **optional adapters** — they must never
  become hard-coded core dependencies.

---

## 4. Sponsor Integration Governance

**Principle:** Sponsor technologies are capabilities/providers, not architectural dependencies.

- The Core decides. Adapters execute.
- All sponsor adapters (SiMa.ai, Speechmatics) must be **optional, replaceable, and isolated**
  from the Decision Engine.
- The MVP must remain fully runnable in a generic simulated Local/Edge/Cloud environment
  even with zero sponsor access.
- **Priority order if time/access is constrained:**
  `Core AFRI-EDGE → Video Analytics → SiMa.ai Edge adapter → Speechmatics optional capability`
- If sponsor hardware/API access becomes a blocker, the generic adapter path is the fallback
  — never a reason to delay the core MVP.

---

## 5. Demo Direction (Competitive Demonstration Sequence)

1. Run static baseline (fixed destination)
2. AFRI-EDGE selects the best target under normal conditions
3. Trigger Edge degradation → show explainable rerouting
4. *(Optional)* Demonstrate SiMa.ai Edge execution
5. *(Optional)* Select a Speechmatics speech workload → show modality extensibility
6. Compare measured metrics against the static baseline

**Rule:** the demo must make adaptation *visible* — same workload, changing conditions,
observable decision, executed result, compared outcome. No claimed result is shown that
wasn't actually measured.

---

## 6. Benchmark & Evidence Policy

- No performance-improvement percentage is claimed before testing.
- Comparison metrics: latency, FPS (where applicable), execution time, infrastructure
  utilization, network conditions, reliability/failures, cost estimates (where measurable).
- Results must come from controlled experiments and be reproducible enough to support the
  final presentation.
- Calibration loop: `Define scenarios → Run static baseline → Run adaptive routing →
  Measure metrics → Adjust parameters → Repeat → Select stable configuration → Validate
  on unseen scenarios.`

---

## 7. Scope Guardrails — Explicitly Out of Scope for MVP

- Reinforcement learning
- Custom model training
- Kubernetes orchestration
- Complex multi-cloud management
- Large-scale distributed persistence
- Enterprise IAM/security architecture
- Large model zoo
- Unvalidated optimization claims

Sponsor integrations specifically must **not** expand the MVP into a large multi-provider
platform — this is a hard guardrail, not a soft preference.

---

## 8. Current Status (verified against GitHub, not just Blueprint plan)

- Validated on `main`: FastAPI skeleton, health endpoint, tests, Python configuration,
  Dockerfile, Docker Compose, environment template, repo documentation structure.
- Routing API scaffold on `feat/routing-decision-api` (**Draft PR #12**) is **intentionally
  non-functional** pending shared contracts (#2) and Decision Engine (#6).
- **Task #2 — Shared Data Models:** In progress. PR #13 open on `feat/shared-data-models`,
  currently under review.
- **Task #6 — Decision Engine:** Not started. Still blocked on Tasks #2, #3, and #5 per the
  dependency chain in Section 2.

---

*This document is based on Blueprint v1.1 and the verified repository state at the time of
this update. Status and implementation claims are not inferred beyond GitHub evidence.*
