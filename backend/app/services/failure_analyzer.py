"""
Failure Analyzer.

Examines test_results_post_fix.json and classifies each failed test into
a cause category. Identifies which failures are within safe-fix scope.

Output: failure_analysis.json

Schema per item:
  {
    "node_id":    "tests/test_foo.py::test_bar",
    "cause":      "assertion_failure" | "exception" | "import_error" |
                  "fixture_error" | "unknown",
    "in_scope":   true | false,
    "explanation": "Plain English description of why the test failed"
  }

Summary:
  {
    "total_failures": int,
    "in_scope":  int,
    "out_of_scope": int,
    "items": [...]
  }

Constraints (WORKFLOW.md Stage 13):
  - Read-only: never modifies files.
  - in_scope = True only when the cause is assertion_failure or exception
    from the application (not from test infrastructure).
  - Import errors and fixture errors are out-of-scope.
"""
from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns that indicate environment/infrastructure failures (out of scope)
_OUT_OF_SCOPE_PATTERNS = [
    "importerror",
    "modulenotfounderror",
    "no module named",
    "fixture",
    "could not find",
    "collection error",
    "syntaxerror",
]

# Patterns for each cause category (checked in order)
_CAUSE_PATTERNS: list[tuple[str, list[str]]] = [
    ("import_error",   ["importerror", "modulenotfounderror", "no module named"]),
    ("fixture_error",  ["fixture", "pytest.fixture", "setup error"]),
    ("assertion_failure", ["assertionerror", "assert ", "expected ", "got "]),
    ("exception",      ["error:", "exception:", "traceback", "raise "]),
]


class FailureAnalyzer:
    """Classifies test failures and determines which are in scope for retry."""

    def analyze(self, test_results: dict[str, object]) -> dict[str, object]:
        """Classify failures from a test_results dict (produced by TestRunner).

        Args:
            test_results: Dict returned by TestRunner.run().

        Returns:
            failure_analysis dict with per-failure classification.
        """
        raw = test_results.get("items")
        items_raw: list[object] = list(raw) if isinstance(raw, list) else []
        items: list[dict[str, object]] = [
            i for i in items_raw
            if isinstance(i, dict) and i.get("outcome") in ("failed", "error")
        ]

        classified: list[dict[str, object]] = []
        for item in items:
            node_id = str(item.get("node_id", ""))
            message = str(item.get("message", ""))
            cause, in_scope, explanation = self._classify(node_id, message)
            classified.append({
                "node_id": node_id,
                "cause": cause,
                "in_scope": in_scope,
                "explanation": explanation,
            })

        in_scope_count = sum(1 for c in classified if c["in_scope"])
        out_of_scope_count = len(classified) - in_scope_count

        logger.info(
            "Failure Analyzer: %d failure(s) — %d in-scope, %d out-of-scope",
            len(classified),
            in_scope_count,
            out_of_scope_count,
        )

        return {
            "total_failures": len(classified),
            "in_scope": in_scope_count,
            "out_of_scope": out_of_scope_count,
            "items": classified,
        }

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    @staticmethod
    def _classify(
        node_id: str, message: str
    ) -> tuple[str, bool, str]:
        """Return (cause, in_scope, explanation)."""
        msg_lower = (node_id + " " + message).lower()

        # Check for out-of-scope patterns first
        for pattern in _OUT_OF_SCOPE_PATTERNS:
            if pattern in msg_lower:
                cause = (
                    "import_error"
                    if "import" in pattern or "module" in pattern
                    else "fixture_error"
                )
                msg_short = message[:200] or "no message captured"
                return cause, False, f"Test infrastructure failure (out of scope): {msg_short}"

        # Classify by cause pattern
        for cause, patterns in _CAUSE_PATTERNS:
            for pattern in patterns:
                if pattern in msg_lower:
                    in_scope = cause in ("assertion_failure", "exception")
                    explanation = _build_explanation(cause, message)
                    return cause, in_scope, explanation

        # Unknown — treat as out of scope (conservative)
        return "unknown", False, (
            f"Cause could not be determined: {message[:200] or 'no message captured'}"
        )


def _build_explanation(cause: str, message: str) -> str:
    short_msg = message[:200] if message else "no message captured"
    if cause == "assertion_failure":
        return (
            f"The test assertion failed — the application returned an unexpected value. {short_msg}"
        )
    if cause == "exception":
        return f"An unhandled exception was raised during the test. {short_msg}"
    if cause == "import_error":
        return f"A module could not be imported — environment or dependency issue. {short_msg}"
    if cause == "fixture_error":
        return f"A pytest fixture failed to set up the test environment. {short_msg}"
    return f"Unknown failure cause. {short_msg}"
