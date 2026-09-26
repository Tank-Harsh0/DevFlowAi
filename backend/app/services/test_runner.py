"""
Test Runner.

Runs pytest against the target repository and parses the output into a
structured JSON result.

Output: test_results_post_fix.json  (or test_results_baseline.json)

Schema per item:
  {
    "node_id":  "tests/test_foo.py::test_bar",
    "outcome":  "passed" | "failed" | "error" | "skipped",
    "duration": 0.123,          # seconds (float)
    "message":  ""              # failure/error message if applicable
  }

Summary:
  {
    "total": int,
    "passed": int,
    "failed": int,
    "error": int,
    "skipped": int,
    "duration_seconds": float,
    "items": [...]
  }

Constraints (WORKFLOW.md Stage 12):
  - Uses subprocess to invoke pytest with --tb=short -v --no-header.
  - Does not modify any file.
  - Timeout: 120 seconds (configurable).
  - If pytest is not found, logs and returns an empty result — not fatal.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_TIMEOUT = 120  # seconds

# Regex for pytest's verbose output lines, e.g.:
#   tests/test_foo.py::test_bar PASSED  [ 10%]
#   tests/test_foo.py::test_bar FAILED  [ 20%]
_LINE_RE = re.compile(
    r"^(?P<node_id>\S+::test\S*)\s+(?P<outcome>PASSED|FAILED|ERROR|SKIPPED)\s",
    re.MULTILINE,
)

# Duration lines: "X passed, Y failed in Z.Zs"
_SUMMARY_RE = re.compile(
    r"(?:(\d+) passed)?.*?(?:(\d+) failed)?.*?(?:(\d+) error)?.*?(?:(\d+) skipped)?.*?in ([\d.]+)s",
    re.IGNORECASE,
)

# Failure block: "FAILED tests/foo.py::test_bar - message"
_FAILURE_MSG_RE = re.compile(r"^FAILED\s+(\S+)\s+-\s+(.*)$", re.MULTILINE)


class PytestRunner:
    """Executes pytest and returns structured results."""

    # Prevent pytest from collecting this class as a test suite
    __test__ = False

    def __init__(self, repository_root: str, timeout: int = _DEFAULT_TIMEOUT) -> None:
        self._root = Path(repository_root).resolve()
        self._timeout = timeout

    def run(self, extra_args: list[str] | None = None) -> dict[str, object]:
        """Execute pytest in the repository root and parse results.

        Args:
            extra_args: Additional pytest arguments (e.g. specific test paths).

        Returns:
            Structured result dict matching the schema above.
        """
        cmd = [
            sys.executable, "-m", "pytest",
            "--tb=short", "-v", "--no-header",
            "-p", "no:cacheprovider",
        ]
        if extra_args:
            cmd.extend(extra_args)

        logger.info("Test Runner: executing %s in %s", " ".join(cmd), self._root)
        start = time.monotonic()

        try:
            proc = subprocess.run(
                cmd,
                cwd=self._root,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except FileNotFoundError:
            logger.error("Test Runner: pytest executable not found")
            return self._empty_result("pytest not found")
        except subprocess.TimeoutExpired:
            logger.error("Test Runner: timed out after %ds", self._timeout)
            return self._empty_result(f"timeout after {self._timeout}s")

        elapsed = time.monotonic() - start
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        combined = stdout + "\n" + stderr

        items = self._parse_items(stdout)
        failure_msgs = dict(_FAILURE_MSG_RE.findall(combined))

        # Attach failure messages to items
        for item in items:
            if item["outcome"] in ("failed", "error"):
                item["message"] = failure_msgs.get(item["node_id"], "")

        summary = self._parse_summary(combined, elapsed, items)
        logger.info(
            "Test Runner: %d passed, %d failed, %d error, %d skipped in %.1fs",
            summary["passed"], summary["failed"],
            summary["error"], summary["skipped"],
            summary["duration_seconds"],
        )
        return summary

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_items(stdout: str) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        seen: set[str] = set()
        for m in _LINE_RE.finditer(stdout):
            node_id = m.group("node_id")
            if node_id in seen:
                continue
            seen.add(node_id)
            items.append({
                "node_id": node_id,
                "outcome": m.group("outcome").lower(),
                "duration": 0.0,
                "message": "",
            })
        return items

    @staticmethod
    def _parse_summary(
        text: str,
        elapsed: float,
        items: list[dict[str, object]],
    ) -> dict[str, object]:
        passed  = sum(1 for i in items if i["outcome"] == "passed")
        failed  = sum(1 for i in items if i["outcome"] == "failed")
        error   = sum(1 for i in items if i["outcome"] == "error")
        skipped = sum(1 for i in items if i["outcome"] == "skipped")

        # Try to extract duration from pytest's own summary line
        duration = elapsed
        m = _SUMMARY_RE.search(text)
        if m and m.group(5):
            try:
                duration = float(m.group(5))
            except ValueError:
                pass

        return {
            "total": len(items),
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
            "duration_seconds": round(duration, 3),
            "items": items,
        }

    @staticmethod
    def _empty_result(reason: str) -> dict[str, object]:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "duration_seconds": 0.0,
            "error_reason": reason,
            "items": [],
        }
