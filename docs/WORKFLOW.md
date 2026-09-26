# DevFlow AI — End-to-End Workflow Definition

Version: 1.0
Status: Draft

---

## Overview

This document defines every stage of the DevFlow AI workflow. For each stage
it specifies the input, processing, output, responsible component, failure
conditions, and the next step.

Stages that are logically independent are marked [PARALLELIZABLE].

Implementation Dependency: Whether stages marked [PARALLELIZABLE] actually
run concurrently depends on IBM Bob 2.0's concurrent agent support. If
parallel dispatch is not available, these stages run sequentially and the
session log notes the fallback.

---

## Stage 1 — Repository Discovery

Input: Local directory path provided by the developer.

Processing:
- Verify the path exists and is a directory.
- Recursively list all files.
- Filter by known source extensions (.py, .md, .txt, .toml, .yaml, .json,
  .env.example).
- Build a structured file tree.
- Identify source files, test files, documentation files, manifest files.

Output: file_tree.json

Responsible Component: Repository Inspector

Failure Conditions:
- Path does not exist → abort; report error; do not proceed.
- Path is not readable → abort; report error.
- No Python files found → continue with a warning; note in report.

Next Step: Stage 2 — Project Understanding

---

## Stage 2 — Project Understanding

Input: file_tree.json + raw file contents.

Processing:
- Read all Python source files.
- Read all documentation files.
- Read all manifest files (requirements.txt, pyproject.toml).
- Read all test files.
- Read configuration files (.env.example, config/*.py, etc.).
- Detect primary language (Python confirmed).
- Detect test framework (pytest, unittest, or unknown).
- Detect API framework (FastAPI, Flask, etc.).
- Build a project context object summarizing what was found.

Output: project_context.json

Responsible Component: Repository Inspector (continued)

Failure Conditions:
- Individual file read failure → log warning; skip file; list as "not analyzed"
  in report.
- No test files → record "no existing tests"; continue.

Next Step: Stage 3 — Documentation Understanding

---

## Stage 3 — Documentation Understanding

Input: Documentation files from Stage 2 + project_context.json.

Processing:
- Summarize key claims from README.md (setup, endpoints, behavior).
- Summarize API spec if present.
- Summarize architecture doc if present.
- Record which documents were found and which were absent.
- Create a documentation_context.json that subagents will use as reference.

Output: documentation_context.json

Responsible Component: Main Orchestrator (preparation step, not a subagent)

Failure Conditions:
- No documentation files found → record as a finding placeholder; continue.
  The Documentation Agent will flag the absence.

Next Step: Stage 4 — Workflow Planning

---

## Stage 4 — Workflow Planning

Input: project_context.json + documentation_context.json.

Processing:
- Determine which subagents to run based on what was found.
- All four agents run in the prototype even if some file categories are absent
  (absence is itself a finding).
- Mark agents as [PARALLELIZABLE] for Stage 5.
- Record the execution plan.

Output: execution_plan.json

Responsible Component: Task Planner

Failure Conditions: None. If uncertain, run all agents.

Next Step: Stage 5 — Parallel Analysis

---

## Stage 5 — Parallel Analysis [PARALLELIZABLE]

Input: Per-agent scoped file sets from project_context.json.

Processing:
The following four agents run concurrently (if platform supports it):

### 5a — Code Review Analysis [PARALLELIZABLE]

Input: Python source files.
Processing: Apply Code Review Agent analysis per SUBAGENT_SPEC.md.
Output: findings_code.json
Responsible: Code Review Agent
Failure: Agent error → log; record empty findings; note in report.

### 5b — Test Gap Analysis [PARALLELIZABLE]

Input: Source files + test files.
Processing: Apply Test Analysis Agent per SUBAGENT_SPEC.md.
Output: findings_tests.json
Responsible: Test Analysis Agent
Failure: No test files → agent reports "no existing tests" as a finding.

### 5c — Security Analysis [PARALLELIZABLE]

Input: Source files + manifest files + config files.
Processing: Apply Security Agent per SUBAGENT_SPEC.md.
Output: findings_security.json
Responsible: Security Agent
Failure: Agent error → log; record disclaimer + empty findings.

### 5d — Documentation Analysis [PARALLELIZABLE]

Input: Documentation files + source files.
Processing: Apply Documentation Agent per SUBAGENT_SPEC.md.
Output: findings_docs.json
Responsible: Documentation Agent
Failure: No documentation files → agent flags absence as a finding.

Next Step: Stage 6 — Finding Aggregation

---

## Stage 6 — Finding Aggregation

Input: findings_code.json, findings_tests.json, findings_security.json,
       findings_docs.json.

Processing:
1. Load all findings from all agents into a single list.
2. Group findings by (file, approximate location).
3. For each group with more than one finding at the same location:
   a. Merge into a single finding.
   b. Set severity to the highest value in the group.
   c. Combine explanations if they differ.
   d. Set source_agent to "multiple-agents".
4. Retain all other findings unchanged.

Output: deduplicated_findings.json

Responsible: Finding Aggregator (Orchestrator component)

Failure: If any findings file is missing → log warning; proceed with available
findings; note missing agent in report.

Next Step: Stage 7 — Duplicate Removal (already performed in Stage 6 as part
of aggregation).

---

## Stage 7 — Issue Prioritization

Input: deduplicated_findings.json.

Processing:
Sort all findings by:
1. Severity: Critical first, then High, Medium, Low.
2. Within severity: by file path alphabetically.

Output: prioritized_findings.json

Responsible: Issue Prioritizer (Orchestrator component)

Failure: None expected. If input is empty, output is an empty array.

Next Step: Stage 8 — Remediation Planning

---

## Stage 8 — Remediation Planning

Input: prioritized_findings.json + source code.

Processing:
For each finding:
1. Determine if a code fix is applicable.
2. If applicable:
   a. Classify fix risk (safe / moderate / high).
   b. Generate a proposed diff.
   c. Write the verification method.
3. If not applicable (e.g., documentation gap):
   a. Mark fix_risk as "not_applicable".
   b. Include a written recommendation.
4. Include the complete fix proposal in fix_plan.json.

Output: fix_plan.json

Responsible: Fix Planner (Orchestrator component)

Failure: If a fix cannot be generated for an applicable issue → mark as
"recommendation only" and include explanation.

Next Step: Stage 9 — Human Approval

---

## Stage 9 — Human Approval

Input: fix_plan.json.

Processing:
For each fix proposal in priority order:
- Display: issue title, severity, risk level, explanation, diff.
- Prompt developer: [A]pprove / [S]kip / [R]eject / [C]ancel all.
- Record decision with timestamp.

Special cases:
- High Risk fixes: Display recommendation text only. No approval prompt for
  application. Developer is informed they must implement manually.
- Security fixes: Require individual approval regardless of risk level.

Output: approved_fix_plan.json

Responsible: Human Approval Gate

Failure: Developer selects Cancel → write partial report with findings; halt
workflow.

Next Step: Stage 10 — Code Modification

---

## Stage 10 — Code Modification

Input: approved_fix_plan.json + repository files.

Processing:
For each approved fix:
1. Create file backup (filename.py → filename.py.devflow.bak).
2. Apply the proposed change.
3. Validate syntax (py_compile for Python).
4. If validation passes: record success in fix_application_log.json.
5. If validation fails: revert from backup; record failure.

Output: Modified repository files + fix_application_log.json

Responsible: Code Modifier

Failure: Revert failure → log critical error; alert developer; halt further
fix application for that file.

Next Step: Stage 11 — Test Generation

---

## Stage 11 — Test Generation

Input: prioritized_findings.json + source code + detected test framework.

Processing:
For each finding where a test is applicable:
1. Generate a test function based on the recommended_fix specification from
   the Test Analysis Agent finding.
2. Add issue ID comment to each test.
3. Write all generated tests to: tests/test_devflow_generated.py.

Output: tests/test_devflow_generated.py

Responsible: Test Generator

Failure: If test generation fails for an individual finding → skip; log; note
in report.

Next Step: Stage 12 — Test Execution (Baseline)

Note: If baseline test results were already recorded before Stage 10, skip
the baseline run. Run only the post-fix suite.

---

## Stage 12 — Test Execution

Processing order:
a. Run the full test suite (all existing + newly generated tests).
b. Capture all output.
c. Parse results.

Command (Python/pytest prototype):
  pytest --tb=short -v

Output: test_results_post_fix.json

If tests were also run before fixes were applied: test_results_baseline.json

Responsible: Test Runner

Failure: Test runner not found → log error; skip; note in report.
Test runner crashes → capture partial output; record remaining as Could Not Run.

Next Step: Stage 13 — Failure Analysis

---

## Stage 13 — Failure Analysis

Input: test_results_post_fix.json + source code + fix_application_log.json.

Processing:
For each failed test:
1. Read the failure message and traceback.
2. Identify the likely cause category:
   - Assertion failure (expected vs. actual mismatch)
   - Exception (unhandled error in the tested code)
   - Import error (test environment problem)
   - Missing fixture or setup error
3. Determine if the cause is within safe-fix scope.
4. Generate a plain-English failure explanation.

Output: failure_analysis.json

Responsible: Failure Analyzer

Next Step: Stage 14 — Iteration (if in-scope failures remain)

---

## Stage 14 — Iteration

Input: failure_analysis.json.

Condition: Only execute if:
- In-scope failures exist (not environment or import errors).
- This is the first iteration (maximum 2 total test runs after fixes).

Processing:
1. Apply in-scope fixes for identified failure causes.
2. Return to Stage 12 for a re-run.
3. Record this as the second iteration.
4. After the second iteration, proceed to Stage 15 regardless of remaining
   failures.

Next Step: Stage 15 — Final Verification

---

## Stage 15 — Final Verification

Input: Latest test_results_post_fix.json + fix_application_log.json.

Processing:
1. Confirm which predefined issues are now verified (their test passes).
2. Confirm which existing tests still pass (regression check).
3. List remaining failures with explanation.
4. List issues that could not be automatically fixed.
5. Confirm the session audit trail is complete.

Output: verification_summary.json

Responsible: Orchestrator

Next Step: Stage 16 — Final Report

---

## Stage 16 — Final Report

Input: All session JSON files.

Processing:
Assemble the Markdown report with these sections:
1. Project Summary
2. Findings (all issues by severity)
3. Remediation (fixes applied + recommendations)
4. Testing (baseline vs. post-fix results)
5. Productivity Metrics
6. Unresolved Issues
7. Audit Trail Reference

Output: final_report.md (written to session directory and repository root)

Responsible: Report Generator

Failure: Report generation failure → log error; dump raw JSON summary as
fallback.

End of Workflow.

---

## Parallelization Summary

| Stage | Parallelizable | Notes |
|---|---|---|
| 1 — Repository Discovery | No | Sequential prerequisite |
| 2 — Project Understanding | No | Sequential prerequisite |
| 3 — Documentation Understanding | No | Sequential prerequisite |
| 4 — Workflow Planning | No | Sequential prerequisite |
| 5a — Code Review | Yes | Independent of 5b, 5c, 5d |
| 5b — Test Analysis | Yes | Independent of 5a, 5c, 5d |
| 5c — Security Analysis | Yes | Independent of 5a, 5b, 5d |
| 5d — Documentation Analysis | Yes | Independent of 5a, 5b, 5c |
| 6 — Aggregation | No | Requires all Stage 5 outputs |
| 7 — Prioritization | No | Requires Stage 6 output |
| 8 — Fix Planning | No | Requires Stage 7 output |
| 9 — Human Approval | No | Blocking; requires developer |
| 10 — Code Modification | No | Requires Stage 9 output |
| 11 — Test Generation | No | Requires Stage 8 output |
| 12 — Test Execution | No | Requires Stages 10, 11 |
| 13 — Failure Analysis | No | Requires Stage 12 output |
| 14 — Iteration | No | Conditional; sequential |
| 15 — Verification | No | Requires Stage 14 or 12 |
| 16 — Final Report | No | Requires all outputs |
