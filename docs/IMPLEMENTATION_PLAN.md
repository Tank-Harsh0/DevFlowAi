# DevFlow AI — Implementation Plan

Version: 1.0
Status: Active

---

## Rules for This Document

- Only mark a task [x] after it has been verified as complete.
- Only work on one phase at a time.
- Do not begin a new phase without explicit approval.
- Record dependencies and blockers in each phase section.

---

## Phase 0 — Planning (Documentation)

Goal: Complete all project documentation before writing any application code.

```
[x] Repository inspection
[x] PRD.md
[x] ARCHITECTURE.md
[x] AGENT_SPEC.md
[x] SUBAGENT_SPEC.md
[x] WORKFLOW.md
[x] AI_RULES.md
[x] IMPLEMENTATION_PLAN.md (this file)
[x] PROJECT_STATE.md
[x] METRICS.md
[x] README.md
[x] .env.example
```

Exit Criteria: All documentation files created and reviewed. No application
code written.

Status: COMPLETE

---

## Phase 1 — Foundation

Goal: Set up the project structure, tooling, and a minimal runnable skeleton.

Do not begin until Phase 0 is reviewed and approved.

```
[ ] Create Python project structure (app/, tests/, devflow/)
[ ] Create requirements.txt with justified dependencies only
[ ] Create pyproject.toml or setup.cfg for the project
[ ] Create basic configuration module (config.py reading from .env)
[ ] Create session output directory management
[ ] Create logging setup (writes to session.log)
[ ] Verify Python 3.11+ is available
[ ] Verify pytest is available
[ ] Create a minimal smoke test that imports the project without errors
```

Dependencies:
- IBM Bob 2.0 SDK version and import mechanism must be confirmed before
  adding it as a dependency.
  Status: Implementation Dependency — Requires Validation

Justification for each expected dependency:
- fastapi: Sample project runtime (not DevFlow AI itself; in sample-project/)
- motor: MongoDB async driver (sample project only)
- pytest: Test runner detection and execution
- httpx: Async HTTP client for pytest tests against FastAPI
- python-dotenv: Load .env for local development

Note: DevFlow AI's own dependencies will be determined once the IBM Bob 2.0
SDK interface is confirmed.

Exit Criteria: Project imports without errors. Session logging works.
Smoke test passes.

Status: NOT STARTED

---

## Phase 2 — Orchestrator Skeleton

Goal: Implement the main orchestrator agent shell with workflow state
management. No subagents yet.

Do not begin until Phase 1 is complete and verified.

```
[ ] Implement workflow state machine (tracks current stage)
[ ] Implement Repository Inspector (reads files, builds project_context.json)
[ ] Implement Task Planner (produces execution_plan.json)
[ ] Implement session output directory creation
[ ] Implement audit log writing (session.log)
[ ] Write integration test: point at sample-project/; verify project_context.json
    is produced correctly
```

Implementation Dependency: IBM Bob 2.0 agent creation and tool registration
API must be validated before implementing the orchestrator agent wrapper.

Exit Criteria: Repository Inspector correctly reads the sample project and
produces a valid project_context.json. Integration test passes.

Status: NOT STARTED

---

## Phase 3 — Subagents

Goal: Implement the four analysis subagents. Each returns findings in the
defined schema.

Do not begin until Phase 2 is complete and verified.

```
[ ] Implement Code Review Agent
[ ] Write unit test: Code Review Agent detects at least 3 known issues
    in the sample project
[ ] Implement Test Analysis Agent
[ ] Write unit test: Test Analysis Agent identifies at least 2 known gaps
[ ] Implement Security Agent (with mandatory disclaimer)
[ ] Write unit test: Security Agent flags the hardcoded connection string
[ ] Implement Documentation Agent
[ ] Write unit test: Documentation Agent flags the missing README sections
[ ] Implement Finding schema validation (validates each agent output)
```

Implementation Dependency: Subagent dispatch mechanism in IBM Bob 2.0 must
be confirmed. If subagents are plain Python functions rather than true agents,
document this in PROJECT_STATE.md.

Exit Criteria: All four agents produce valid findings_*.json for the sample
project. All unit tests pass.

Status: NOT STARTED

---

## Phase 4 — Parallel Workflow and Aggregation

Goal: Connect subagents to the orchestrator. Implement aggregation,
deduplication, and prioritization.

Do not begin until Phase 3 is complete and verified.

```
[ ] Implement parallel (or sequential fallback) agent dispatch
[ ] Implement Finding Aggregator
[ ] Implement Issue Prioritizer
[ ] Write integration test: full analysis run on sample project produces
    deduplicated_findings.json and prioritized_findings.json
[ ] Verify that all 13 predefined issues are detected (or document which
    ones are not and why)
```

Implementation Dependency: Parallel dispatch requires IBM Bob 2.0 concurrent
agent API. If unavailable, implement sequential dispatch and document the
limitation.

Exit Criteria: Integration test passes. All detected issues match expected
schema. Detection rate recorded in METRICS.md.

Status: NOT STARTED

---

## Phase 5 — Remediation

Goal: Implement fix planning, human approval, and code modification.

Do not begin until Phase 4 is complete and verified.

```
[ ] Implement Fix Planner (generates fix_plan.json)
[ ] Implement Human Approval Gate (CLI prompts; records decisions)
[ ] Implement Code Modifier (applies changes with backup and syntax check)
[ ] Write integration test: approve one safe fix; verify file is modified
    correctly and backup exists
[ ] Write integration test: reject a fix; verify file is unchanged
[ ] Write integration test: apply a fix that introduces a syntax error;
    verify revert from backup
```

Exit Criteria: All three integration tests pass. fix_application_log.json
is produced with correct entries.

Status: NOT STARTED

---

## Phase 6 — Verification

Goal: Implement test generation, test execution, failure analysis, and
the iteration loop.

Do not begin until Phase 5 is complete and verified.

```
[ ] Implement Test Generator (produces tests/test_devflow_generated.py)
[ ] Write integration test: generator produces at least 6 test functions
    for the sample project issues
[ ] Implement Test Runner (runs pytest; parses output)
[ ] Write integration test: Test Runner executes and produces
    test_results_post_fix.json
[ ] Implement Failure Analyzer
[ ] Implement iteration logic (maximum 2 total post-fix runs)
[ ] Run full end-to-end on sample project; record test pass rate
```

Exit Criteria: Full pipeline runs. test_results_post_fix.json produced.
Post-fix test pass rate recorded in METRICS.md.

Status: NOT STARTED

---

## Phase 7 — Reporting and Demo

Goal: Implement the final report generator and prepare the demo.

Do not begin until Phase 6 is complete and verified.

```
[ ] Implement Report Generator (produces final_report.md)
[ ] Verify report contains all required sections per PRD FR-60
[ ] Record actual productivity metrics in METRICS.md
[ ] Record actual baseline (human manual workflow time)
[ ] Compute time saved (measured, not estimated)
[ ] Prepare demo script following WORKFLOW.md Stage sequence
[ ] Run full end-to-end demo on sample project
[ ] Record demo run results
[ ] Update PROJECT_STATE.md to Phase 7 Complete
```

Exit Criteria: final_report.md is produced. All acceptance criteria in
PRD Section 32 are verified. Demo runs without errors.

Status: NOT STARTED

---

## Sample Project Setup

The sample FastAPI + MongoDB Todo API lives in:
  sample-project/

This is the target repository for the prototype. It must be set up with the
predefined issues listed in PRD Section 19 (to be created in Phase 1).

The sample project is not DevFlow AI itself. It is the project that DevFlow
AI analyzes.

---

## Known Risks and Blockers

| Risk | Phase Affected | Mitigation |
|---|---|---|
| IBM Bob 2.0 SDK not yet validated | 1, 2, 3, 4 | Validate SDK in Phase 1 before proceeding |
| Parallel agent API not available | 4 | Implement sequential fallback |
| Sample project issues too easy to detect | 3, 4 | Calibrate during Phase 3 testing |
| MongoDB not available in test environment | 1 | Use mongomock or testcontainers for testing |
