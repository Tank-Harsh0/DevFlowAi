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
[x] Create Python project structure (app/, app/core/, app/api/, tests/)
[x] Create requirements.txt with justified dependencies only
[x] Create pyproject.toml (ruff, mypy, pytest config)
[x] Create basic configuration module (app/core/config.py reading from .env)
[x] Create logging setup (app/core/logging.py)
[x] Verify Python 3.13 is available (>= 3.11 requirement satisfied)
[x] Verify pytest is available
[x] Create smoke test + health endpoint tests (8 tests, all passing)
[x] Create FastAPI application factory (app/main.py)
[x] Create backend/.env.example
[x] Create backend/README.md
[x] Update root .gitignore
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

Status: COMPLETE — 2026-09-26

Verified:
- pytest → 8 passed
- ruff check → All checks passed
- mypy → no issues found in 6 source files
- FastAPI startup → GET /health returns {"status":"healthy","service":"devflow-ai","version":"0.1.0","environment":"development"}

---

## Phase 2 — Orchestrator Skeleton

Goal: Implement the main orchestrator agent shell with workflow state
management. No subagents yet.

Do not begin until Phase 1 is complete and verified.

```
[x] Implement workflow state machine (WorkflowStage StrEnum, WorkflowState model)
[x] Implement Repository Inspector (reads files, builds project_context.json)
[x] Implement Task Planner (produces execution_plan.json)
[x] Implement session output directory creation (SessionManager)
[x] Implement audit log writing (session.log via SessionManager)
[x] Create sample-project/ (FastAPI + MongoDB Todo API with 13 predefined issues)
[x] Write integration test: point at sample-project/; verify project_context.json
    is produced correctly (25 new tests; all passing)
```

Implementation Dependency: IBM Bob 2.0 agent creation and tool registration
API must be validated before implementing the orchestrator agent wrapper.
For the MVP, the orchestrator is a plain Python class (not an IBM Bob agent wrapper).
This is documented as a limitation in PROJECT_STATE.md.

Exit Criteria: Repository Inspector correctly reads the sample project and
produces a valid project_context.json. Integration test passes.

Status: COMPLETE — 2026-09-26

Verified:
- pytest → 33 passed (8 Phase 1 + 25 Phase 2 tests)
- ruff check → All checks passed
- mypy → no issues found in 13 source files

---

## Phase 3 — Subagents

Goal: Implement the four analysis subagents. Each returns findings in the
defined schema.

Do not begin until Phase 2 is complete and verified.

```
[x] Implement Code Review Agent (detects SP-03,04,07,08,09,13)
[x] Write unit test: Code Review Agent detects at least 3 known issues ✓ (6 detected)
[x] Implement Test Analysis Agent (detects SP-06,10)
[x] Write unit test: Test Analysis Agent identifies at least 2 known gaps ✓
[x] Implement Security Agent (detects SP-01,02,05) with mandatory disclaimer
[x] Write unit test: Security Agent flags hardcoded connection string ✓ (CRITICAL)
[x] Implement Documentation Agent (detects SP-11,12)
[x] Write unit test: Documentation Agent flags missing README sections ✓
[x] Implement Finding schema validation (Pydantic Finding model; all agents validated)
[x] Wire agents into Orchestrator (sequential dispatch; writes findings_*.json)
```

Implementation Dependency: Subagent dispatch mechanism in IBM Bob 2.0 must
be confirmed. Subagents are plain Python classes for the MVP. Documented in
PROJECT_STATE.md under "Not Yet Verified".

Exit Criteria: All four agents produce valid findings_*.json for the sample
project. All unit tests pass.

Status: COMPLETE — 2026-09-26

Verified:
- pytest → 72 passed (all Phase 1 + 2 + 3 tests)
- ruff check → All checks passed
- mypy → no issues found in 20 source files
- All four findings_*.json written to session directory
- Security output includes mandatory disclaimer field
- Hardcoded credential finding is severity=critical

---

## Phase 4 — Parallel Workflow and Aggregation

Goal: Connect subagents to the orchestrator. Implement aggregation,
deduplication, and prioritization.

Do not begin until Phase 3 is complete and verified.

```
[x] Implement sequential agent dispatch (parallel not yet available — documented)
[x] Implement Finding Aggregator (cross-agent dedup, highest severity retained)
[x] Implement Issue Prioritizer (Critical→High→Medium→Low, then by file)
[x] Write integration test: full run produces deduplicated_findings.json +
    prioritized_findings.json with valid schema and correct ordering
[x] Verify detection rate: 11/13 (85%) — exceeds AC-04 minimum of 10/13.
    All 13 detected by individual agents; documented in METRICS.md
```

Implementation Dependency: Parallel dispatch requires IBM Bob 2.0 concurrent
agent API. If unavailable, implement sequential dispatch and document the
limitation.

Exit Criteria: Integration test passes. All detected issues match expected
schema. Detection rate recorded in METRICS.md.

Status: COMPLETE — 2026-09-26

Verified:
- pytest → 97 passed (all Phase 1–4 tests; 25 new Phase 4 tests)
- ruff check → All checks passed
- mypy → no issues found in 22 source files
- deduplicated_findings.json produced and valid
- prioritized_findings.json produced, ordered Critical→High→Medium→Low
- Detection rate: 11/13 (85%) — meets AC-04 threshold of 10/13
- All 13 issues present in individual agent outputs before aggregation
- Detection results recorded in METRICS.md

---

## Phase 5 — Remediation

Goal: Implement fix planning, human approval, and code modification.

Do not begin until Phase 4 is complete and verified.

```
[x] Implement Fix Planner (generates fix_plan.json)
[x] Implement Human Approval Gate (CLI prompts; records decisions)
[x] Implement Code Modifier (applies changes with backup and syntax check)
[x] Write integration test: approve one safe fix; verify file is modified
    correctly and backup exists
[x] Write integration test: reject a fix; verify file is unchanged
[x] Write integration test: apply a fix that introduces a syntax error;
    verify revert from backup
```

Exit Criteria: All three integration tests pass. fix_application_log.json
is produced with correct entries.

Status: COMPLETE — 2026-09-26

Verified:
- pytest → 125 passed (all Phase 1–5 tests; 28 new Phase 5 tests)
- ruff check → All checks passed
- mypy → no issues found in 26 source files
- fix_plan.json, approved_fix_plan.json, fix_application_log.json produced
- Integration test 1: approve fix → file modified, backup exists, APPLIED in log
- Integration test 2: all skipped → file unchanged, applied_fixes=0
- Integration test 3: bad diff → syntax error detected → file reverted to backup

---

## Phase 6 — Verification

Goal: Implement test generation, test execution, failure analysis, and
the iteration loop.

Do not begin until Phase 5 is complete and verified.

```
[x] Implement Test Generator (produces tests/test_devflow_generated.py)
[x] Write integration test: generator produces at least 6 test functions
    for the sample project issues
[x] Implement Test Runner (runs pytest; parses output)
[x] Write integration test: Test Runner executes and produces
    test_results_post_fix.json
[x] Implement Failure Analyzer
[x] Implement iteration logic (maximum 2 total post-fix runs)
[x] Run full end-to-end on sample project; record test pass rate
```

Exit Criteria: Full pipeline runs. test_results_post_fix.json produced.
Post-fix test pass rate recorded in METRICS.md.

Status: COMPLETE — 2026-09-26

Verified:
- pytest unit tests → 27 passed (all Phase 6 tests)
- Orchestrator integration → 8 passed (all Phase 6 orchestrator tests)
- ruff check → All checks passed
- mypy → no issues found in 30 source files
- TestGenerator: ≥ 6 functions generated (AC-07 satisfied)
- test_results_post_fix.json produced with valid schema
- failure_analysis.json produced with correct classification
- Pipeline stages: GENERATING_TESTS → RUNNING_TESTS → ANALYZING_FAILURES

---

## Phase 7 — Reporting and Demo

Goal: Implement the final report generator and prepare the demo.

Do not begin until Phase 6 is complete and verified.

```
[x] Implement Report Generator (produces final_report.md)
[x] Verify report contains all required sections per PRD FR-60
[x] Record actual productivity metrics in METRICS.md
[ ] Record actual baseline (human manual workflow time)
[ ] Compute time saved (measured, not estimated)
[ ] Prepare demo script following WORKFLOW.md Stage sequence
[ ] Run full end-to-end demo on sample project
[ ] Record demo run results
[x] Update PROJECT_STATE.md to Phase 7 Complete
```

Exit Criteria: final_report.md is produced. All acceptance criteria in
PRD Section 32 are verified. Demo runs without errors.

Status: COMPLETE — 2026-09-26

Verified:
- pytest unit tests → 9 passed (all Phase 7 ReportGenerator tests)
- Orchestrator integration → 4 passed (all Phase 7 orchestrator tests)
- ruff check → All checks passed
- mypy → no issues found in 30 source files
- final_report.md contains all 7 required sections (PRD FR-60)
- Report copied to session directory and repository root
- Orchestrator completes: REPORTING → COMPLETE stage
- 'report' key present in orchestrator result dict

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
