# Sample Project — FastAPI + MongoDB Todo API

This is the **target repository** that DevFlow AI analyzes. It is NOT DevFlow AI itself.

It is a deliberately flawed FastAPI + MongoDB Todo API, seeded with 13 predefined issues
that DevFlow AI must detect.

## Predefined Issues

| # | ID | Severity | Category | Description |
|---|---|---|---|---|
| 1 | SP-01 | Critical | Security | Hardcoded MongoDB connection string with credentials |
| 2 | SP-02 | Critical | Security | No input validation on todo text (allows empty string / XSS content) |
| 3 | SP-03 | High | Bug | `update_todo` silently succeeds when ID does not exist |
| 4 | SP-04 | High | Bug | `delete_todo` silently succeeds when ID does not exist |
| 5 | SP-05 | High | Security | MongoDB ObjectId not validated before use (invalid ID causes 500 crash) |
| 6 | SP-06 | High | Testing | No tests for any endpoint |
| 7 | SP-07 | Medium | Bug | `get_todos` returns all todos with no pagination (unbounded query) |
| 8 | SP-08 | Medium | Code Quality | Duplicate database connection logic repeated across route handlers |
| 9 | SP-09 | Medium | Code Quality | Magic string `"todos"` used in every handler instead of a constant |
| 10 | SP-10 | Medium | Testing | No test for invalid ObjectId input |
| 11 | SP-11 | Medium | Documentation | README missing: setup instructions, environment variables, API endpoints |
| 12 | SP-12 | Low | Code Quality | No docstrings on any route handler |
| 13 | SP-13 | Low | Code Quality | Unused import (`datetime`) |

## Setup (for manual inspection only — DevFlow AI reads this directory)

```bash
pip install -r requirements.txt
```

Requires a running MongoDB instance (see SP-01 for the hardcoded URI).
