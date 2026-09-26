# DevFlow AI

**AI-Powered Developer Workflow Orchestration Platform**

Built on IBM Bob 2.0 for the IBM Developer Workflow Automation Challenge.

---

## What Is DevFlow AI?

DevFlow AI replaces the manual developer workflow for code review, debugging,
test analysis, security review, and documentation verification. It uses an AI
orchestrator that delegates work to specialized subagents running in parallel,
aggregates their findings, plans and applies safe fixes with human approval,
generates and runs tests, and produces a final measurable report.

---

## Prototype Scope

The first prototype targets a sample **FastAPI + MongoDB Todo API** repository.

It demonstrates the complete workflow from repository understanding to final
verification on a bounded, realistic codebase.

---

## Project Structure

```
DevFlow-AI/
├── docs/                   Project documentation
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── AGENT_SPEC.md
│   ├── SUBAGENT_SPEC.md
│   ├── WORKFLOW.md
│   ├── AI_RULES.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PROJECT_STATE.md
│   └── METRICS.md
├── app/                    DevFlow AI application (Phase 1+)
├── tests/                  Test suite (Phase 1+)
├── sample-project/         FastAPI + MongoDB Todo API prototype target
├── .env.example
└── README.md
```

---

## Development Status

**Current Phase:** Phase 0 — Planning

See [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md) for live status.

---

## Documentation

| Document | Purpose |
|---|---|
| [PRD.md](docs/PRD.md) | Product requirements and goals |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [AGENT_SPEC.md](docs/AGENT_SPEC.md) | Orchestrator specification |
| [SUBAGENT_SPEC.md](docs/SUBAGENT_SPEC.md) | Subagent specifications |
| [WORKFLOW.md](docs/WORKFLOW.md) | Step-by-step workflow |
| [AI_RULES.md](docs/AI_RULES.md) | Development rules |
| [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Implementation phases |
| [METRICS.md](docs/METRICS.md) | Success metrics |

---

## Challenge Alignment

| Requirement | Implementation |
|---|---|
| Improve developer workflow | Code review, debug, test, verify pipeline |
| Agent mode | Main orchestrator agent |
| Parallel tasks | 4 independent analysis agents |
| Subagents | Code Review, Test Analysis, Security, Documentation |
| Document understanding | README, architecture, API spec parsing |
| Working prototype | FastAPI + MongoDB Todo API |
| Productivity improvement | Before/after time and effort measurement |

---

> This project is under active development.
> Do not treat any component as production-ready.
