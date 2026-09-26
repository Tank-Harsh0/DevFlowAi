# DevFlow AI — Orchestrator Agent Specification

Version: 1.0
Status: Draft

---

## 1. Purpose

The main orchestrator agent is the central controller for the DevFlow AI
workflow. It is the only agent with write access to the repository and the
only agent that interacts with the developer during an active session.

All other agents (subagents) are read-only analysis workers that report
findings to the orchestrator.

---

## 2. Responsibilities

The orchestrator must perform these tasks in order:

```
1.  Accept the repository path and developer request.
2.  Run the Repository Inspector.
3.  Run the Task Planner.
4.  Dispatch analysis subagents (in parallel if supported).
5.  Wait for all subagents to complete.
6.  Run the Finding Aggregator.
7.  Run the Issue Prioritizer.
8.  Run the Fix Planner.
9.  Present the fix plan to the developer via the Human Approval Gate.
10. Run the Code Modifier for each approved fix.
11. Run the Test Generator.
12. Run the Test Runner (baseline before fixes if applicable, then post-fix).
13. Run the Failure Analyzer on any failures.
14. Attempt to apply additional fixes for in-scope failures.
15. Run the Test Runner again if additional fixes were applied.
16. Run the Report Generator.
17. Write the final report to disk.
```

---

## 3. Allowed Actions

| Action | Notes |
|---|---|
| Read any file in the repository | Via Repository Inspector |
| Write to repository files | Only via Code Modifier; only for approved fixes |
| Create new test files | Only via Test Generator; after optional developer review |
| Create backup files | Before any modification |
| Execute test runner command | Via Test Runner only |
| Create session output files | JSON intermediates and final report |
| Display output to developer | Via DevFlow Runner interface |
| Request developer input | Via Human Approval Gate |

---

## 4. Restricted Actions

| Action | Reason |
|---|---|
| Apply a fix without developer approval | Violates human control requirement |
| Apply a High Risk fix automatically | High Risk fixes require manual implementation |
| Delete repository files | Not permitted in MVP |
| Rename repository files | Not permitted in MVP |
| Install new dependencies | Not permitted in MVP |
| Make network requests | Not required in MVP; out of scope |
| Modify files outside the target repository | Not permitted |
| Re-read files already in session context without reason | Wastes resources |
| Claim a fix worked without running tests | Prohibited by AI rules |
| Claim tests pass without executing them | Prohibited by AI rules |

---

## 5. Inputs

| Input | Type | Required |
|---|---|---|
| repository_path | string (local directory path) | Yes |
| developer_request | string (what the developer wants to achieve) | Optional; defaults to "full workflow" |
| session_config | object (optional overrides) | No |

Session config options (all optional):
- max_file_size_kb: Skip files larger than this limit (default: 500).
- require_approval_for_safe_fixes: Boolean (default: true).
- output_directory: Where to write session files (default: ./devflow_sessions).

---

## 6. Outputs

| Output | Format | Location |
|---|---|---|
| file_tree.json | JSON | session directory |
| findings_*.json | JSON | session directory |
| deduplicated_findings.json | JSON | session directory |
| prioritized_findings.json | JSON | session directory |
| fix_plan.json | JSON | session directory |
| approved_fix_plan.json | JSON | session directory |
| fix_application_log.json | JSON | session directory |
| test_results_baseline.json | JSON | session directory |
| test_results_post_fix.json | JSON | session directory |
| failure_analysis.json | JSON | session directory |
| session.log | Text | session directory |
| final_report.md | Markdown | session directory + repository root |

---

## 7. Decision Rules

### When to skip an agent

- If the repository contains no test files → Test Analysis Agent is run but
  notes "no existing tests found" rather than being skipped (the absence of
  tests is itself a finding).
- If the repository contains no documentation files → Documentation Agent runs
  and flags the absence as a finding.
- If a specific file type is missing (e.g., no API spec) → the relevant
  analysis scope is reduced; the agent notes what was absent.

### When to stop the workflow

- If the Repository Inspector fails to read the repository → abort; report
  the error; do not proceed.
- If the Human Approval Gate receives a "Cancel" response → stop the workflow;
  write a partial report with findings to that point.
- If the Code Modifier encounters an unrecoverable file error → stop fix
  application for that file; continue with other approved fixes.

### When to iterate

- After running the test suite post-fix, if failures remain and the Failure
  Analyzer identifies in-scope causes → attempt one additional fix iteration.
- Maximum iterations: 2 (baseline run, post-fix run, one optional re-run).
- If failures remain after the maximum iterations → list them as "Unresolved"
  in the final report.

---

## 8. Error Handling

| Error | Action |
|---|---|
| Subagent returns empty findings | Log as "no findings from agent"; continue |
| Subagent returns malformed JSON | Log error; skip that agent's output; note in report |
| Fix Planner cannot generate a fix | Mark finding as "recommendation only" |
| Code Modifier revert fails | Log critical error; halt fix application; alert developer |
| Test Runner cannot be located | Log error; skip test execution; note in report |
| Test execution timeout | Terminate test process; record results up to that point |

---

## 9. Human Approval Requirements

The orchestrator must never bypass developer approval at these points:

1. Before applying any proposed code change.
2. Before applying a Moderate Risk change (per-fix confirmation required).
3. Before applying a security-related change (per-fix confirmation required).
4. High Risk changes are presented as recommendations only; no application.

Approval is recorded in approved_fix_plan.json with timestamp and decision.

---

## 10. Failure Recovery

If the orchestrator crashes mid-session:

- All JSON files written to that point are preserved in the session directory.
- The session log records the last completed step.
- Resuming a session is not supported in MVP. The developer must start a new
  run.
- The intermediate files remain available for manual inspection.

---

## 11. Behavioral Rules

1. The orchestrator must not perform analysis tasks itself. Analysis is
   delegated to subagents.
2. The orchestrator must not modify repository files without going through the
   Code Modifier component and the Human Approval Gate.
3. The orchestrator must not claim that an action was performed if it was not
   executed.
4. The orchestrator must record every significant decision in the session log.
5. The orchestrator must distinguish between what was measured and what was
   estimated in all outputs.
6. The orchestrator must surface all findings including those it cannot fix.
