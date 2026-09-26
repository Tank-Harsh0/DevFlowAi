# DevFlow AI — Development Rules

Version: 1.0
Status: Mandatory

---

These rules govern all implementation work on DevFlow AI. They apply to every
agent, every component, every phase, and every code change.

Violations of these rules must be flagged and resolved before proceeding.

---

## Rule 1 — Source of Truth

The PRD.md and ARCHITECTURE.md are the source of truth. If code or behavior
conflicts with these documents, the documents win unless an explicit change has
been approved and recorded.

## Rule 2 — No Invented Requirements

Never add a feature, behavior, or constraint that is not in the PRD or
explicitly approved. If something seems like it should be included, document
the ambiguity instead of adding it.

## Rule 3 — No Invented APIs or Capabilities

Never assume an IBM Bob 2.0 API, library, or capability exists unless it has
been verified. If an assumed capability is needed, mark it as:
  Implementation Dependency: Requires Validation
and record it in PROJECT_STATE.md under "Not Yet Verified".

## Rule 4 — Inspect Before Modifying

Before changing any existing file, read it and understand its current state.
Do not overwrite without knowing what is there.

## Rule 5 — Prefer Minimal Changes

Use the smallest change that satisfies the requirement. Do not refactor
unrelated code. Do not improve code that does not need improvement.

## Rule 6 — Do Not Modify Unrelated Files

Only modify files that are directly required by the current task. If a change
affects a file that was not planned, stop and evaluate why.

## Rule 7 — Justified Dependencies Only

Do not add a library or package unless it is explicitly justified by a
requirement. Record all added dependencies in IMPLEMENTATION_PLAN.md with the
justification.

## Rule 8 — No Future Scope

Do not implement anything listed under Future Scope in the PRD. Future scope
features are explicitly excluded from the prototype.

## Rule 9 — No Unjustified Rewrites

Do not rewrite working code without a documented reason. If existing code
works and satisfies the requirement, leave it alone.

## Rule 10 — No Unverified Success Claims

Never state that code works, a fix was applied, or behavior is correct without
actually running or testing it. Unverified statements are prohibited.

## Rule 11 — No Unrun Test Claims

Never state that tests pass without actually executing them. Do not infer test
results from code inspection.

## Rule 12 — No Unvalidated Feature Claims

Never claim a feature works without demonstrating it. Claims require evidence.

## Rule 13 — Record Uncertainty

If something is unclear, ambiguous, or unknown, record it explicitly. Do not
guess. Do not fill in blanks. Write:
  Uncertainty: [description of what is unclear]
in the relevant document or in PROJECT_STATE.md.

## Rule 14 — Ask When Ambiguity Blocks Implementation

If an ambiguity would materially affect how something is built, stop and ask
for clarification before proceeding. Document the question and the answer.

## Rule 15 — Backward Compatibility

Unless a requirement explicitly changes behavior, preserve existing
functionality. Do not break working code while adding new code.

## Rule 16 — Preserve Existing Functionality

When adding new code alongside existing code, verify that existing behavior
still works after the change.

## Rule 17 — Trace Changes to Requirements

Every non-trivial code change should reference a specific requirement ID from
the PRD (e.g., FR-32) or a specific issue being fixed. Changes without
traceability are suspect.

## Rule 18 — Run Tests After Significant Changes

After any change that affects logic, run the relevant tests. Do not proceed
to the next task if tests are failing.

## Rule 19 — Investigate Failures Before Proceeding

If a test fails, understand why before making additional changes. Do not layer
changes on top of an ununderstood failure.

## Rule 20 — Stay Focused on the Current Task

Complete the current phase or task before starting the next one. Do not jump
ahead.

## Rule 21 — Avoid Repeated Repository Scans

Read each file once per session unless it has changed. Do not re-read files
to confirm something that was already read.

## Rule 22 — Minimize Unnecessary Tool Calls

Do not make redundant calls. Combine reads where possible. Do not call a tool
if the result is already in the current context.

## Rule 23 — Maintain PROJECT_STATE.md

After completing a phase or a significant milestone, update PROJECT_STATE.md.
It must always reflect the current state of the project accurately.

## Rule 24 — No Duplicate Documentation

Before creating a new document, check whether the information already exists
elsewhere. Add to an existing document rather than creating a new one.

## Rule 25 — Human Approval for High Risk Changes

No High Risk change (as defined in ARCHITECTURE.md) may be applied without
explicit developer approval. The approval must be recorded in the session
audit trail.

---

## Summary Checklist (Before Submitting Any Change)

- [ ] Change is traced to a requirement.
- [ ] No unrelated files were modified.
- [ ] No invented capabilities were assumed.
- [ ] No future scope was added.
- [ ] Relevant tests were run.
- [ ] Tests pass (or failures are documented and understood).
- [ ] PROJECT_STATE.md is up to date.
- [ ] No false claims about behavior or results.
