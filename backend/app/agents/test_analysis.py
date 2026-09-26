"""
Test Analysis Agent.

Analyzes source code and existing test files to identify coverage gaps,
missing edge cases, and regression risks.

Issues targeted in sample-project/:
  SP-06 — no test files at all
  SP-10 — no test for invalid ObjectId input

Constraints (SUBAGENT_SPEC.md §2):
  - Generates test specifications only, not test code.
  - Read-only; no command execution.
  - Reports only gaps observable from the provided files.
"""
from __future__ import annotations

import ast
import re

from app.agents.base import BaseAgent
from app.models.finding import Finding, FixRisk, Severity, SourceAgent
from app.models.workflow import ProjectContext

# Route decorator patterns
_ROUTE_RE = re.compile(
    r"""@\w+\.(get|post|put|patch|delete)\s*\(\s*["']([^"']+)["']""",
    re.MULTILINE,
)


def _extract_routes(content: str) -> list[tuple[str, str]]:
    """Return list of (method, path) tuples from FastAPI route decorators."""
    return [(m.group(1).upper(), m.group(2)) for m in _ROUTE_RE.finditer(content)]


def _test_names_in(content: str) -> set[str]:
    """Return all test function names defined in *content*."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test")
    }


class TestingAnalysisAgent(BaseAgent):
    """Identifies test coverage gaps and missing edge-case tests."""

    @property
    def name(self) -> str:
        return "test_analysis"

    def analyze(self, context: ProjectContext) -> list[Finding]:
        findings: list[Finding] = []

        has_test_files = len(context.test_files) > 0

        # SP-06 — no tests at all
        if not has_test_files:
            findings.append(self._no_tests_finding(context))
            # If there are no tests, we can still report per-route gaps
            # by inspecting source routes and noting each has no coverage.
            findings.extend(self._route_coverage_gaps(context, existing_test_names=set()))
            return findings

        # Gather all test function names across all test files
        existing_test_names: set[str] = set()
        for tf in context.test_files:
            content = context.file_contents.get(tf.path, "")
            existing_test_names |= _test_names_in(content)

        findings.extend(self._route_coverage_gaps(context, existing_test_names))
        findings.extend(self._invalid_id_test_gap(context, existing_test_names))
        return findings

    # ── Checks ──────────────────────────────────────────────────────────────

    def _no_tests_finding(self, context: ProjectContext) -> Finding:
        """SP-06 — no test files found."""
        source_count = len(context.source_files)
        return Finding(
            id="TA-001",
            source_agent=SourceAgent.TEST_ANALYSIS,
            title="No test files found — entire codebase is untested",
            severity=Severity.HIGH,
            file="tests/",
            location="file-level (missing)",
            explanation=(
                f"The repository contains {source_count} source file(s) but "
                "no test files were detected. None of the API endpoints, "
                "business logic, or error handling has automated test coverage."
            ),
            impact=(
                "Bugs introduced by future changes will not be caught "
                "automatically. The project cannot be safely refactored or "
                "deployed with confidence."
            ),
            recommended_fix=(
                "Create a tests/ directory and add a test file using pytest:\n"
                "  Test function: test_create_todo_returns_201\n"
                "  Input: POST /todos {\"text\": \"Buy milk\"}\n"
                "  Expected: HTTP 201 with {\"id\": <string>}\n"
                "  Framework: pytest + httpx AsyncClient"
            ),
            verification_method="Run pytest and confirm at least one test passes.",
            fix_risk=FixRisk.NOT_APPLICABLE,
        )

    def _route_coverage_gaps(
        self, context: ProjectContext, existing_test_names: set[str]
    ) -> list[Finding]:
        """One finding per endpoint with no evident test coverage."""
        out: list[Finding] = []
        n = 2  # TA-001 is reserved for the no-tests finding

        source_paths = {f.path for f in context.source_files}
        for rel_path, content in context.file_contents.items():
            if rel_path not in source_paths:
                continue
            for method, route in _extract_routes(content):
                # Heuristic: look for the route path fragment in any test name
                route_slug = route.replace("/", "_").replace("{", "").replace("}", "").strip("_")
                covered = any(route_slug in t for t in existing_test_names)
                if not covered:
                    out.append(Finding(
                        id=f"TA-{n:03d}",
                        source_agent=SourceAgent.TEST_ANALYSIS,
                        title=f"No test coverage for {method} {route}",
                        severity=Severity.MEDIUM,
                        file=rel_path,
                        location=f"{method} {route}",
                        explanation=(
                            f"No existing test function appears to exercise "
                            f"{method} {route}. The endpoint's happy-path, "
                            f"error cases, and validation behaviour are unverified."
                        ),
                        impact=(
                            "Regressions in this endpoint will not be detected "
                            "by the test suite."
                        ),
                        recommended_fix=(
                            f"Test function: test_{method.lower()}"
                            f"_{route_slug}_returns_expected_response\n"
                            f"Input: {method} {route} with a valid payload\n"
                            f"Expected: 2xx response with correct response body\n"
                            f"Framework: pytest + httpx TestClient"
                        ),
                        verification_method=(
                            "Run pytest and confirm the new test passes."
                        ),
                        fix_risk=FixRisk.NOT_APPLICABLE,
                    ))
                    n += 1
        return out

    def _invalid_id_test_gap(
        self, context: ProjectContext, existing_test_names: set[str]
    ) -> list[Finding]:
        """SP-10 — no test for invalid ObjectId."""
        # Check if any test name hints at invalid-id testing
        if any(
            keyword in name
            for name in existing_test_names
            for keyword in ("invalid_id", "bad_id", "invalid_object", "objectid")
        ):
            return []

        # Only report if ObjectId is used in source
        uses_objectid = any(
            "ObjectId" in c
            for p, c in context.file_contents.items()
            if p in {f.path for f in context.source_files}
        )
        if not uses_objectid:
            return []

        n = 50  # reserve TA-002..TA-049 for route gaps; start high to avoid collisions
        return [Finding(
            id=f"TA-{n:03d}",
            source_agent=SourceAgent.TEST_ANALYSIS,
            title="No test for invalid ObjectId input — unhandled 500 error not verified",
            severity=Severity.HIGH,
            file="tests/",
            location="file-level (missing test)",
            explanation=(
                "The source code passes user-supplied IDs directly to "
                "bson.ObjectId() without validation. Sending a malformed ID "
                "(e.g. 'abc') raises an InvalidId exception that produces an "
                "HTTP 500 response. No test verifies this failure path."
            ),
            impact=(
                "The unhandled exception is invisible to the test suite. "
                "Any fix for this bug cannot be regression-tested without "
                "a covering test."
            ),
            recommended_fix=(
                "Test function: test_get_todo_invalid_id_returns_400_or_404\n"
                "Input: GET /todos/not-a-valid-objectid\n"
                "Expected: HTTP 400 or 422 — NOT 500\n"
                "Framework: pytest + httpx TestClient"
            ),
            verification_method=(
                "Run the test. Confirm the response is 4xx, not 5xx."
            ),
            fix_risk=FixRisk.NOT_APPLICABLE,
        )]
