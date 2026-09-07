# InfraForge 7X

> Forging the infrastructure behind intelligent systems.

**InfraForge 7X** is building **AFRI-EDGE**, an infrastructure-aware, workload-agnostic adaptive runtime for intelligent AI execution across Local, Edge, and Cloud environments.

## AI Infra Summit Hackathon 2026

This repository is the central engineering workspace for the team.

### Current MVP

**Primary use case:** Intelligent real-time video analytics.

**Core principle:**

> AGENTOS decides what to execute. AFRI-EDGE decides where and how to execute it.

The MVP evaluates workload requirements and real-time infrastructure conditions, selects an eligible execution target, routes the workload, observes execution, and can re-evaluate when conditions change.

### Competitive Extensions

- **SiMa.ai** — optional Edge / Physical AI execution adapter for compatible vision workloads.
- **Speechmatics** — optional speech capability demonstrating that the same routing core can handle another AI modality.

Sponsor technologies are adapters/capabilities, not hard-coded dependencies. The generic AFRI-EDGE MVP remains runnable without sponsor hardware or APIs.

### Architecture

```text
AI Request
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
Feedback & Re-evaluation
```

### Repository Structure

```text
.
├── README.md
├── docs/
├── research/
├── ideas/
├── decisions/
├── team/
├── src/
│   ├── core/
│   ├── adapters/
│   ├── monitoring/
│   └── api/
├── dashboard/
├── tests/
├── deployment/
└── docker-compose.yml
```

### Development

The initial runtime uses **Python 3.11 + FastAPI** and is containerized with Docker/Docker Compose.

The first vertical slice is the routing flow:

`POST /route → Workload Profile → Infrastructure State → Decision Engine → Routing Decision`

### Engineering Workflow

`Issue → Feature Branch → Development → Tests → Pull Request → Review → Merge → Integration → Validation`

**Definition of Done:** Implemented + Tested + Integrated.
