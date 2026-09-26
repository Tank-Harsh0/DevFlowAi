# DevFlow AI — Subagent Specifications

Version: 1.0
Status: Draft

---

## General Rules for All Subagents

1. Subagents are read-only. They do not modify files.
2. Subagents do not execute commands.
3. Subagents do not communicate with each other.
4. Subagents return findings only for issues they can support with evidence
   from the code they were given.
5. Subagents do not infer issues beyond what is observable in the provided
   files.
6. Subagents use the Finding schema defined in ARCHITECTURE.md.
7. Subagents do not make claims about completeness (e.g., "no other bugs
   exist"). They report what they found.

---

## Finding Output Schema

```json
{
  "id": "AGENT_PREFIX-NNN (e.g., CR-001, TA-001, SA-001, DA-001)",
  "source_agent": "code_review | test_analysis | security | documentation",
  "title": "Short descriptive title",
  "severity": "critical | high | medium | low",
  "file": "relative/path/to/file.py",
  "location": "Line number, function name, or 'file-level'",
  "explanation": "Plain English explanation of the problem",
  "impact": "What could go wrong if this is not addressed",
  "recommended_fix": "What should be changed and how",
  "verification_method": "How to confirm the fix worked",
  "fix_risk": "safe | moderate | high | not_applicable"
}
```

Fix risk classification:
- safe: Targeted single-location change; easy to verify; cannot break unrelated
  code. Examples: adding a missing HTTPException, adding input validation.
- moderate: Change affects multiple locations or has non-trivial logic.
  Examples: refactoring a utility function, changing an error format.
- high: Involves architectural change, authentication logic, database schema,
  or large-scale restructuring. Never auto-applied.
- not_applicable: The finding cannot be fixed by code change (e.g., a
  documentation gap or a process issue).

---

## 1. Code Review Agent

### Purpose

Analyze source code for functional bugs, code quality issues, and
maintainability problems.

### Input

- Source code files (language-filtered to Python for the prototype).
- Project context summary from Repository Inspector.

### Responsibilities

| Category | What to Look For |
|---|---|
| Logic errors | Off-by-one errors, wrong conditionals, incorrect return values |
| Bugs | Null/None access, unhandled exceptions, incorrect type assumptions |
| Missing error handling | Endpoints or functions that do not handle failure cases |
| Code smells | Functions that are too long, deeply nested code, magic numbers |
| Duplicate code | Repeated logic that should be shared |
| Exception handling | Bare except clauses, swallowed exceptions, missing finally |
| Performance | N+1 queries, synchronous blocking in async context |
| Hardcoded values | Values that should be environment variables or constants |
| Maintainability | Unclear variable names, missing type hints in public functions |

### Output

findings_code.json — array of Finding objects with source_agent = "code_review".

### Constraints

- Report only issues observable in the provided code.
- Do not flag style preferences as bugs.
- Do not report issues about files not provided.
- Do not claim that no other bugs exist.

### Example Finding

```json
{
  "id": "CR-001",
  "source_agent": "code_review",
  "title": "GET /todos/{id} does not return 404 when item is not found",
  "severity": "high",
  "file": "app/routers/todos.py",
  "location": "get_todo function, approximately line 42",
  "explanation": "When a requested todo item does not exist in the database, the function raises an unhandled exception instead of returning an HTTP 404 response. The client receives a 500 error.",
  "impact": "API clients cannot distinguish between a server error and a missing resource. Standard REST behavior is violated.",
  "recommended_fix": "Add a check after the database query: if the result is None, raise HTTPException(status_code=404, detail='Todo not found').",
  "verification_method": "Call GET /todos/{nonexistent-id}. Confirm the response is HTTP 404 with a structured error body.",
  "fix_risk": "safe"
}
```

---

## 2. Test Analysis Agent

### Purpose

Analyze existing tests and identify coverage gaps, missing edge cases, and
regression risks.

### Input

- Source code files.
- Existing test files.
- Project context summary.

### Responsibilities

| Category | What to Look For |
|---|---|
| Existing test inventory | Map each test to the code it exercises |
| Missing test cases | Endpoints, functions, or branches with no corresponding test |
| Missing edge cases | Empty input, maximum values, boundary conditions |
| Missing failure tests | No tests for expected error responses (404, 422, 500) |
| Missing regression tests | Issues that were fixed but have no test to prevent recurrence |
| Test quality | Tests that assert nothing, tests that always pass regardless of code |
| Coverage gaps | Significant code paths with no test coverage |

### Output Format

findings_tests.json — array of Finding objects with source_agent = "test_analysis".

For test gap findings, the recommended_fix field contains the recommended
test case specification in this format:

```
Test function: test_get_todo_returns_404_for_invalid_id
Input: GET /todos/invalid-id-that-does-not-exist
Expected behavior: HTTP 404 response with {"detail": "Todo not found"}
Framework: pytest + httpx
```

### Constraints

- Do not generate test code. Generate specifications only.
- Actual test code is generated by the Test Generator component.
- Report only gaps that are observable from the provided code and test files.
- Do not claim complete coverage mapping without evidence.

### Example Finding

```json
{
  "id": "TA-001",
  "source_agent": "test_analysis",
  "title": "No test for GET /todos/{id} with an invalid ID",
  "severity": "high",
  "file": "tests/test_todos.py",
  "location": "file-level (missing test)",
  "explanation": "The existing test file has no test case that sends a GET request with a nonexistent todo ID. This means the 404 handling (or lack of it) is not verified.",
  "impact": "A bug in 404 handling can go undetected, causing clients to receive unexpected 500 errors in production.",
  "recommended_fix": "Test function: test_get_todo_returns_404_for_invalid_id\nInput: GET /todos/nonexistent-id\nExpected: HTTP 404 with {\"detail\": \"Todo not found\"}\nFramework: pytest + httpx AsyncClient",
  "verification_method": "Run the new test and confirm it passes.",
  "fix_risk": "not_applicable"
}
```

---

## 3. Security Agent

### Purpose

Identify security-relevant issues in source code, configuration, and
dependency usage.

### Input

- Source code files.
- Manifest files (requirements.txt, pyproject.toml).
- Configuration files (.env.example, config files).
- Project context summary.

### Responsibilities

| Category | What to Look For |
|---|---|
| Hardcoded credentials | Passwords, API keys, tokens, connection strings in source code |
| Unsafe input handling | Missing validation, no length limits, raw user input in queries |
| Authentication gaps | Unprotected endpoints that should require authentication |
| Authorization gaps | Missing ownership checks, no role verification |
| Sensitive data exposure | Returning internal fields, logging sensitive data |
| Dependency risks | Obviously outdated or deprecated packages (flag; do not claim CVE knowledge) |
| OWASP patterns | Common weaknesses applicable to the detected stack |

### Output

findings_security.json — array of Finding objects with source_agent = "security".

### Constraints

- Must not claim that the project is completely secure.
- Must not claim to have performed a dynamic security test (static analysis only).
- All security findings are classified as high or critical fix_risk by default.
  The orchestrator will require human approval before applying any security fix.
- Do not flag theoretical vulnerabilities without evidence in the code.

### Mandatory Disclaimer in Output

The security agent output must include a top-level field:

```json
{
  "disclaimer": "This analysis is limited to static code inspection. It does not guarantee that the project is free from all security vulnerabilities. Dynamic, runtime, or infrastructure-level vulnerabilities are not covered.",
  "findings": [...]
}
```

### Example Finding

```json
{
  "id": "SA-001",
  "source_agent": "security",
  "title": "MongoDB connection string is hardcoded in source code",
  "severity": "critical",
  "file": "app/database.py",
  "location": "Module level, MONGODB_URI assignment",
  "explanation": "The MongoDB connection string including credentials is hardcoded as a string literal in the source file. Anyone with access to the code repository can obtain the database credentials.",
  "impact": "Credential exposure in version control; unauthorized database access if the repository is public or shared.",
  "recommended_fix": "Read the connection string from an environment variable: MONGODB_URI = os.getenv('MONGODB_URI'). Add MONGODB_URI to .env.example. Add .env to .gitignore.",
  "verification_method": "Verify that the hardcoded string is removed and the application reads from the environment variable.",
  "fix_risk": "safe"
}
```

---

## 4. Documentation Agent

### Purpose

Assess the completeness and accuracy of project documentation.

### Input

- Documentation files (README.md, ARCHITECTURE.md, API specs, etc.).
- Source code files (for consistency checking).
- Project context summary.

### Responsibilities

| Category | What to Look For |
|---|---|
| README completeness | Project description, prerequisites, installation, usage, examples |
| Setup accuracy | Are the documented setup steps correct and sufficient? |
| API documentation | Are all endpoints documented with request/response examples? |
| Docstring coverage | Do public functions and classes have docstrings? |
| Documentation drift | Does documented behavior match the actual implementation? |
| Missing documents | No architecture doc, no contribution guide (flag; not an error) |
| Broken references | Links to files or sections that do not exist |

### Minimum README Checklist

The agent checks for the presence of these README sections:

- [ ] Project name and description
- [ ] Prerequisites (Python version, MongoDB, etc.)
- [ ] Installation steps
- [ ] Environment variable configuration
- [ ] How to run the application
- [ ] How to run the tests
- [ ] API endpoint list or link to API documentation

Missing sections are reported as individual findings.

### Output

findings_docs.json — array of Finding objects with source_agent = "documentation".

### Consistency Check Rule

For each documented API endpoint (if an API spec or README endpoint list
exists), the agent checks whether a corresponding route exists in the source
code. Mismatches are reported as findings.

### Constraints

- Do not evaluate writing style or grammar.
- Only flag factual inaccuracies or missing required information.
- If no documentation exists at all, report a single Critical finding rather
  than listing every possible missing section.

### Example Finding

```json
{
  "id": "DA-001",
  "source_agent": "documentation",
  "title": "README is missing installation and setup instructions",
  "severity": "medium",
  "file": "README.md",
  "location": "file-level",
  "explanation": "The README file does not contain instructions for installing dependencies or setting up environment variables. A new developer cannot set up the project using the README alone.",
  "impact": "Onboarding friction; developers must examine source code to understand how to run the project.",
  "recommended_fix": "Add a Setup section to README.md covering: pip install -r requirements.txt, copying .env.example to .env, setting MONGODB_URI, and running uvicorn app.main:app.",
  "verification_method": "A new developer can set up and run the project using only the README instructions.",
  "fix_risk": "safe"
}
```
