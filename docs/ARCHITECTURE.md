# DevFlow AI — Technical Architecture

Version: 1.0
Status: Draft

---

## 1. Overview

DevFlow AI uses a two-tier agent architecture running on IBM Bob 2.0.

Tier 1: A single main orchestrator agent manages workflow state and coordinates
all activities.

Tier 2: Four specialized subagents perform independent analysis tasks. Each
subagent has a defined input scope, output schema, and set of allowed
operations.

The architecture is designed to be as simple as possible for the MVP. No
microservices, no databases, no queues. State is held in memory during a
session and persisted to JSON files in a session output directory.

---

## 2. Component Map

```
Developer (CLI or Script)
        |
        ▼
   DevFlow Runner            Entry point; accepts repository path;
        |                    displays progress; handles approval prompts
        ▼
Main Orchestrator Agent      Manages workflow state; delegates tasks;
        |                    aggregates results; coordinates output
        |
        ├──▶ Repository Inspector   Reads file tree, source code,
        |                           docs, tests, manifests
        |
        ├──▶ Task Planner           Decides which agents to run and
        |                           in what order; identifies
        |                           parallelizable tasks
        |
        ├──▶ [Parallel Dispatch]
        |       ├──▶ Code Review Agent
        |       ├──▶ Test Analysis Agent
        |       ├──▶ Security Agent
        |       └──▶ Documentation Agent
        |
        ├──▶ Finding Aggregator     Merges and deduplicates results
        |
        ├──▶ Issue Prioritizer      Assigns severity ordering
        |
        ├──▶ Fix Planner            Generates fix proposals
        |
        ├──▶ Human Approval Gate    Presents proposals; waits for input
        |
        ├──▶ Code Modifier          Applies approved changes with backup
        |
        ├──▶ Test Generator         Creates test cases for issues
        |
        ├──▶ Test Runner            Executes pytest; captures output
        |
        ├──▶ Failure Analyzer       Reads test output; identifies causes
        |
        └──▶ Report Generator       Produces final Markdown report
```

---

## 3. Component Responsibilities

### DevFlow Runner

- Accepts repository path from command line or configuration.
- Initializes the orchestrator agent.
- Displays workflow progress to the developer.
- Handles human approval prompts (shows diff, waits for input).
- Writes final report to disk.

### Main Orchestrator Agent

- Owns workflow state throughout the session.
- Calls Repository Inspector to build project context.
- Calls Task Planner to determine execution plan.
- Dispatches subagents for analysis.
- Calls Finding Aggregator after all agents return.
- Calls Issue Prioritizer.
- Calls Fix Planner.
- Presents fix plan through the Human Approval Gate.
- Calls Code Modifier for approved fixes.
- Calls Test Generator.
- Calls Test Runner (baseline and post-fix).
- Calls Failure Analyzer on failures.
- Calls Report Generator.

### Repository Inspector

Input: Repository root path.

Output:
```
file_tree.json          Directory and file listing
source_files[]          Source code content (language-filtered)
doc_files[]             README, ARCHITECTURE, API spec, etc.
test_files[]            Test file content
manifest_files[]        requirements.txt, pyproject.toml, etc.
detected_language       Primary programming language
detected_test_framework pytest, unittest, etc.
```

Constraints:
- Reads files only; never modifies.
- Files exceeding a configurable size limit are flagged but not read.
- Unreadable files are logged as warnings, not errors.

### Task Planner

Input: Repository Inspector output.

Output: Execution plan listing which agents to run and which can run in
parallel.

Constraints:
- Does not perform any analysis itself.
- Marks agents as Optional if the relevant file type is absent (e.g., no
  documentation files → Documentation Agent is skipped with a note).

### Code Review Agent (Subagent)

Input: Source code files.
Output: findings_code.json (array of Finding objects, schema below).
Constraints: Read-only; no command execution; no file modification.

### Test Analysis Agent (Subagent)

Input: Source code files + test files.
Output: findings_tests.json.
Constraints: Read-only.

### Security Agent (Subagent)

Input: Source code files + manifest files + config files.
Output: findings_security.json.
Constraints: Read-only. Must not claim exhaustive security assurance.

### Documentation Agent (Subagent)

Input: Doc files + source code files (for consistency checking).
Output: findings_docs.json.
Constraints: Read-only.

### Finding Aggregator

Input: All findings_*.json files.

Processing:
1. Merge all findings into a single list.
2. Group by (file, approximate location).
3. Merge findings referencing the same location from different agents.
4. Preserve all severity levels; retain the highest for the merged record.
5. Mark source as "multiple-agents" when merged.

Output: deduplicated_findings.json.

### Issue Prioritizer

Input: deduplicated_findings.json.

Processing: Sort findings by severity (Critical → High → Medium → Low).
Within the same severity, sort by file path.

Output: prioritized_findings.json.

### Fix Planner

Input: prioritized_findings.json.

Processing: For each finding, determine:
- Whether a fix is applicable.
- The risk classification of the fix (Safe / Moderate / High).
- The proposed change (diff format).
- The verification method.

Output: fix_plan.json.

### Human Approval Gate

Input: fix_plan.json.

Processing:
- Display each proposed fix with: title, severity, risk, explanation, diff.
- Wait for developer input: Approve / Skip / Reject.
- Record decision per fix.

Output: approved_fix_plan.json.

Constraints:
- Must not proceed without at least one developer action.
- High Risk fixes are displayed as recommendations only; no approval prompt
  for application.

### Code Modifier

Input: approved_fix_plan.json + repository files.

Processing:
- For each approved fix:
  1. Create a backup of the target file (file.py → file.py.bak).
  2. Apply the change.
  3. Verify the file is syntactically valid (run py_compile or equivalent).
  4. If syntax check fails: revert to backup; record failure.
- Log all modifications to fix_application_log.json.

Output: Modified files + fix_application_log.json.

### Test Generator

Input: prioritized_findings.json + source code files + detected test framework.

Output: Generated test files (tests/test_devflow_generated.py for pytest).

Each generated test includes a comment: # DevFlow issue: [issue-id].

### Test Runner

Input: Repository root.

Processing:
1. Run the test suite using the detected runner (e.g., pytest --tb=short -v).
2. Capture stdout and stderr.
3. Parse results into structured format.

Output: test_results.json (array of TestResult objects, schema below).

Constraint: The test runner executes real commands. Results must come from
actual execution, not inference.

### Failure Analyzer

Input: test_results.json + source code files.

Processing:
- For each failed test, read the failure message and traceback.
- Identify the likely cause (assertion error, exception, missing resource).
- Determine if the cause is within safe-fix scope.
- Generate a failure explanation.

Output: failure_analysis.json.

### Report Generator

Input: All session JSON files + metadata.

Output: final_report.md (Markdown).

---

## 4. Data Schemas

### Finding Object

```json
{
  "id": "string (unique, e.g. CR-001)",
  "source_agent": "code_review | test_analysis | security | documentation",
  "title": "string",
  "severity": "critical | high | medium | low",
  "file": "relative/path/to/file.py",
  "location": "line number or function name or 'unknown'",
  "explanation": "string (plain English)",
  "impact": "string",
  "recommended_fix": "string",
  "verification_method": "string",
  "fix_risk": "safe | moderate | high | not_applicable"
}
```

### Fix Proposal Object

```json
{
  "finding_id": "string",
  "fix_risk": "safe | moderate | high",
  "description": "string",
  "rationale": "string",
  "files_affected": ["relative/path/to/file.py"],
  "diff": "string (unified diff format)",
  "verification_method": "string",
  "status": "pending | approved | skipped | rejected"
}
```

### TestResult Object

```json
{
  "test_id": "string",
  "name": "string",
  "status": "passed | failed | could_not_run | skipped",
  "message": "string | null",
  "related_issue_id": "string | null"
}
```

---

## 5. Session Output Directory

Each run creates a timestamped session directory:

```
devflow_sessions/
└── 2026-09-26T130000/
    ├── file_tree.json
    ├── findings_code.json
    ├── findings_tests.json
    ├── findings_security.json
    ├── findings_docs.json
    ├── deduplicated_findings.json
    ├── prioritized_findings.json
    ├── fix_plan.json
    ├── approved_fix_plan.json
    ├── fix_application_log.json
    ├── test_results_baseline.json
    ├── test_results_post_fix.json
    ├── failure_analysis.json
    └── final_report.md
```

This directory forms the complete audit trail for the session.

---

## 6. Agent Communication

Subagents do not communicate with each other directly. All communication
passes through the orchestrator.

Communication pattern:
- Orchestrator passes file content and context to subagents as input.
- Subagents return structured JSON output.
- Orchestrator aggregates outputs before passing them to the next stage.

Implementation Dependency: The exact mechanism for passing data to and
receiving data from subagents depends on the IBM Bob 2.0 agent API. This must
be validated in the target runtime.

---

## 7. Parallel Execution

The four analysis subagents (Code Review, Test Analysis, Security,
Documentation) are logically independent during the analysis phase and can run
concurrently.

Implementation Dependency: True parallel execution requires IBM Bob 2.0 to
support concurrent subagent dispatch. If this is not available, agents run
sequentially and the session log notes the fallback.

---

## 8. Error Handling

| Scenario | Behavior |
|---|---|
| Subagent returns an error | Log error; continue with available findings; note in report |
| File cannot be read | Log warning; skip file; list in report as "not analyzed" |
| Fix causes a syntax error | Revert from backup; log failure; mark fix as failed in report |
| Test runner not found | Log error; skip test execution; note in report |
| Test runner crashes | Capture error output; record as Could Not Run; note in report |

No error causes a silent failure. Every error is logged and surfaces in the
final report.

---

## 9. Human Approval Points

| Point | Trigger | Blocking |
|---|---|---|
| Fix plan review | After fix plan is generated | Yes; workflow pauses |
| Moderate risk fix | Before applying each moderate-risk change | Yes; per-fix |
| Security fix | Before applying any security-related change | Yes; per-fix |
| Dependency change | Before adding or updating a dependency | Yes |
| Generated test review | Before generated tests are written to disk | Optional |

---

## 10. Repository Interaction Rules

- The system reads repository files at the start of the session.
- Files are not re-read during the session unless explicitly required.
- Only the Code Modifier component writes to repository files.
- All other components are read-only.
- Backups are created before any modification.
- The system does not modify files outside the target repository directory.

---

## 11. Logging

All significant events are logged to a session log file:

```
devflow_sessions/2026-09-26T130000/session.log
```

Log format:
```
[TIMESTAMP] [LEVEL] [COMPONENT] Message
```

Levels: INFO, WARNING, ERROR, DECISION, CHANGE.

DECISION events record orchestrator decisions.
CHANGE events record every file modification.

---

## 12. Auditability

The complete session output directory constitutes the audit trail. It contains:

- All intermediate JSON files (agent inputs and outputs).
- The session log.
- Backup files for all modified files.
- The final report.

This allows any run to be reviewed, replayed, or debugged after the fact.

---

## 13. MVP Constraints

- Python 3.11+ only.
- FastAPI + MongoDB prototype only.
- pytest as test runner.
- Local directory only (no remote repository access).
- No user authentication.
- No persistent database for session history.
- Single sequential session (no concurrent runs).
