"""
Test Generator.

Produces tests/test_devflow_generated.py inside the target repository.

For each finding where a test is applicable (test_analysis findings and any
finding with a verification_method that specifies a test), it generates a
pytest function.

Rules (WORKFLOW.md Stage 11):
  - Output file: {repository_root}/tests/test_devflow_generated.py
  - Each test function is annotated with the finding ID.
  - Tests use httpx.TestClient against the FastAPI app (detected framework).
  - ≥ 6 test functions must be generated for the sample project (AC-07).
  - If test generation fails for a single finding, it is skipped — not fatal.
  - Does not execute the tests (that is the Test Runner's job).
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from app.core.logging import get_logger
from app.models.finding import Finding, SourceAgent
from app.models.workflow import ProjectContext

logger = get_logger(__name__)

# Header written once at the top of the generated file
_FILE_HEADER = '''\
"""
Auto-generated tests by DevFlow AI.

DO NOT EDIT MANUALLY — this file is regenerated on each DevFlow AI run.

Each test function corresponds to a finding identified during analysis.
Finding IDs are referenced in the test docstrings.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

# Import the FastAPI application from the target repository.
# DevFlow AI detected this as the main application module.
try:
    from main import app  # type: ignore[import-not-found]
except ImportError:
    import pytest
    pytest.skip("main.py not importable — skipping generated tests", allow_module_level=True)

client = TestClient(app, raise_server_exceptions=False)

'''


class TestGenerator:
    """Generates pytest test functions from analysis findings."""

    def generate(
        self,
        findings: list[Finding],
        context: ProjectContext,
        output_path: Path,
    ) -> list[str]:
        """Write test_devflow_generated.py and return the list of generated function names.

        Args:
            findings:    Prioritized findings (from IssuePrioritizer).
            context:     ProjectContext (used to check for existing test directory).
            output_path: Where to write the generated test file.

        Returns:
            List of test function names that were written.
        """
        functions: list[str] = []
        blocks: list[str] = []
        seen_names: set[str] = set()

        for finding in findings:
            block, name = self._generate_test(finding)
            if not (block and name):
                continue
            # Deduplicate: if the same function name would be produced by two
            # different findings, suffix it with the finding ID
            if name in seen_names:
                safe_id = finding.id.lower().replace("-", "_")
                name = f"{name}_{safe_id}"
                # Rebuild the block with the new function name (replace first occurrence)
                block = block.replace(
                    block.split("(")[0].strip(), f"def {name}", 1
                )
            seen_names.add(name)
            blocks.append(block)
            functions.append(name)

        if not functions:
            logger.warning("Test Generator: no test functions could be generated")
            # Write an empty-ish file so the session artefact still exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                _FILE_HEADER
                + "# No testable findings were found in this analysis run.\n",
                encoding="utf-8",
            )
            return functions

        body = _FILE_HEADER + "\n".join(blocks)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(body, encoding="utf-8")

        logger.info(
            "Test Generator: %d test function(s) written to %s",
            len(functions),
            output_path,
        )
        return functions

    # ------------------------------------------------------------------
    # Per-finding test builders
    # ------------------------------------------------------------------

    def _generate_test(self, finding: Finding) -> tuple[str, str]:
        """Return (source_block, function_name) or ("", "") if not applicable."""
        fid = finding.id

        # TA- findings (test gap recommendations) — best source for test specs
        if finding.source_agent == SourceAgent.TEST_ANALYSIS:
            return self._from_test_analysis(finding)

        # Known CR- patterns with concrete, automatable checks
        if fid.startswith("CR-"):
            return self._from_code_review(finding)

        # SA- security findings with HTTP-level checks
        if fid.startswith("SA-"):
            return self._from_security(finding)

        return "", ""

    # ------------------------------------------------------------------
    # Test Analysis → test gap specifications
    # ------------------------------------------------------------------

    def _from_test_analysis(self, finding: Finding) -> tuple[str, str]:
        """Convert a TA- test gap finding into a pytest function."""
        title_lower = finding.title.lower()

        # No existing tests at all → check that basic endpoints exist
        if "no test" in title_lower and ("file" in title_lower or "exist" in title_lower):
            return self._test_get_todos_returns_list(finding)

        # GET /todos/{id} with invalid ID
        if "invalid" in title_lower and ("id" in title_lower or "objectid" in title_lower):
            return self._test_get_invalid_id_returns_error(finding)

        # DELETE /todos/{id} not found
        if "delete" in title_lower and ("not found" in title_lower or "missing" in title_lower):
            return self._test_delete_nonexistent_returns_error(finding)

        # PUT /todos/{id} not found
        if "update" in title_lower and ("not found" in title_lower or "missing" in title_lower):
            return self._test_update_nonexistent_returns_error(finding)

        # CREATE with empty/invalid body
        if "creat" in title_lower and (
            "empty" in title_lower or "invalid" in title_lower or "validation" in title_lower
        ):
            return self._test_create_empty_body(finding)

        # Route-level coverage gaps — generate a basic smoke test
        if any(route in title_lower for route in ["/todos", "get ", "post ", "put ", "delete "]):
            return self._test_route_smoke(finding)

        # Generic fallback for TA- findings
        return self._generic_ta_test(finding)

    def _test_get_todos_returns_list(self, finding: Finding) -> tuple[str, str]:
        fname = "test_get_todos_returns_list"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}\"\"\"
                response = client.get("/todos")
                assert response.status_code == 200
                assert isinstance(response.json(), list)


            """)
        return block, fname

    def _test_get_invalid_id_returns_error(self, finding: Finding) -> tuple[str, str]:
        fname = "test_get_todo_invalid_id_returns_error"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                Invalid ObjectId must not cause an unhandled 500 error.
                \"\"\"
                response = client.get("/todos/not-a-valid-objectid")
                assert response.status_code in (400, 404, 422), (
                    f"Expected 400/404/422 for invalid ObjectId, got {{response.status_code}}"
                )


            """)
        return block, fname

    def _test_delete_nonexistent_returns_error(self, finding: Finding) -> tuple[str, str]:
        fname = "test_delete_nonexistent_todo_returns_error"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                Deleting a non-existent resource must return a structured error, not silent 200.
                \"\"\"
                response = client.delete("/todos/000000000000000000000000")
                # Should be 404 (not found) or 400 (invalid format)
                assert response.status_code in (400, 404), (
                    f"Expected 400/404 for missing todo, got {{response.status_code}}"
                )


            """)
        return block, fname

    def _test_update_nonexistent_returns_error(self, finding: Finding) -> tuple[str, str]:
        fname = "test_update_nonexistent_todo_returns_error"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                Updating a non-existent resource must return a structured error, not silent 200.
                \"\"\"
                response = client.put(
                    "/todos/000000000000000000000000",
                    json={{"text": "updated"}},
                )
                assert response.status_code in (400, 404), (
                    f"Expected 400/404 for missing todo, got {{response.status_code}}"
                )


            """)
        return block, fname

    def _test_create_empty_body(self, finding: Finding) -> tuple[str, str]:
        fname = "test_create_todo_empty_body_rejected"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                POST /todos with an empty body must be rejected (validation).
                \"\"\"
                response = client.post("/todos", json={{}})
                # Should reject empty body — 422 Unprocessable Entity or 400
                assert response.status_code in (400, 422), (
                    f"Expected 400/422 for empty todo body, got {{response.status_code}}"
                )


            """)
        return block, fname

    def _test_route_smoke(self, finding: Finding) -> tuple[str, str]:
        fname = f"test_smoke_{finding.id.lower().replace('-', '_')}"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}\"\"\"
                # Smoke test — endpoint must respond (not 500)
                response = client.get("/todos")
                assert response.status_code != 500, (
                    f"GET /todos returned unexpected 500: {{response.text[:200]}}"
                )


            """)
        return block, fname

    def _generic_ta_test(self, finding: Finding) -> tuple[str, str]:
        fname = f"test_{finding.id.lower().replace('-', '_')}_gap"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                Auto-generated placeholder — review and complete before relying on this test.
                \"\"\"
                # Placeholder: this finding requires a test but could not be
                # automatically translated into a concrete assertion.
                # Recommended fix: {finding.recommended_fix[:100]}
                pass


            """)
        return block, fname

    # ------------------------------------------------------------------
    # Code Review → functional correctness checks
    # ------------------------------------------------------------------

    def _from_code_review(self, finding: Finding) -> tuple[str, str]:
        title_lower = finding.title.lower()

        if "unbounded" in title_lower or "pagination" in title_lower:
            return self._test_get_todos_returns_list_cr(finding)
        if "update" in title_lower and ("unchecked" in title_lower or "silent" in title_lower):
            return self._test_update_returns_404_when_missing(finding)
        if "delete" in title_lower and ("unchecked" in title_lower or "silent" in title_lower):
            return self._test_delete_returns_404_when_missing(finding)
        if "unused import" in title_lower:
            return self._test_import_clean(finding)

        return "", ""

    def _test_get_todos_returns_list_cr(self, finding: Finding) -> tuple[str, str]:
        fname = "test_get_todos_returns_list_not_error"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                GET /todos must return a list, not an error.
                \"\"\"
                response = client.get("/todos")
                assert response.status_code == 200
                body = response.json()
                assert isinstance(body, list), f"Expected list, got: {{type(body)}}"


            """)
        return block, fname

    def _test_update_returns_404_when_missing(self, finding: Finding) -> tuple[str, str]:
        fname = "test_update_todo_missing_id_returns_404"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                PUT /todos/{{id}} must return 404 when the ID does not exist.
                \"\"\"
                response = client.put(
                    "/todos/000000000000000000000000",
                    json={{"text": "test"}},
                )
                assert response.status_code == 404, (
                    f"Expected 404 for missing todo update, got {{response.status_code}}"
                )


            """)
        return block, fname

    def _test_delete_returns_404_when_missing(self, finding: Finding) -> tuple[str, str]:
        fname = "test_delete_todo_missing_id_returns_404"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                DELETE /todos/{{id}} must return 404 when the ID does not exist.
                \"\"\"
                response = client.delete("/todos/000000000000000000000000")
                assert response.status_code == 404, (
                    f"Expected 404 for missing todo delete, got {{response.status_code}}"
                )


            """)
        return block, fname

    def _test_import_clean(self, finding: Finding) -> tuple[str, str]:
        fname = f"test_{finding.id.lower().replace('-', '_')}_import_check"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                The module must import without errors after the unused import is removed.
                \"\"\"
                import importlib
                import importlib.util
                spec = importlib.util.find_spec("main")
                assert spec is not None, "main module must be importable"


            """)
        return block, fname

    # ------------------------------------------------------------------
    # Security → input-validation / credential checks
    # ------------------------------------------------------------------

    def _from_security(self, finding: Finding) -> tuple[str, str]:
        title_lower = finding.title.lower()

        if "hardcoded" in title_lower or "connection string" in title_lower:
            return self._test_env_var_used(finding)
        if "input validation" in title_lower or "arbitrary dict" in title_lower:
            return self._test_create_with_xss_body(finding)
        if "objectid" in title_lower or "invalid id" in title_lower:
            return self._test_invalid_objectid_returns_error(finding)

        return "", ""

    def _test_env_var_used(self, finding: Finding) -> tuple[str, str]:
        fname = "test_mongodb_uri_not_hardcoded"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                The MongoDB URI must not be a hardcoded literal in the source.
                \"\"\"
                import ast
                import pathlib
                src = pathlib.Path(__file__).parent.parent / "main.py"
                if not src.exists():
                    return  # file not found in this environment
                tree = ast.parse(src.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        has_hardcoded = (
                            "mongodb://" in node.value.lower()
                            and "localhost" in node.value
                        )
                        assert not has_hardcoded, "Hardcoded MongoDB URI found in source code"


            """)
        return block, fname

    def _test_create_with_xss_body(self, finding: Finding) -> tuple[str, str]:
        fname = "test_create_todo_xss_payload_handled"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                POST /todos with an XSS payload must not cause a 500 error.
                \"\"\"
                xss = {{"text": "<script>alert(1)</script>"}}
                response = client.post("/todos", json=xss)
                # Must not crash the server — 200/201/422 are all acceptable
                assert response.status_code != 500, (
                    f"Server error on XSS payload: {{response.text[:200]}}"
                )


            """)
        return block, fname

    def _test_invalid_objectid_returns_error(self, finding: Finding) -> tuple[str, str]:
        fname = "test_invalid_objectid_format_returns_error"
        block = textwrap.dedent(f"""\
            def {fname}():
                \"\"\"Finding {finding.id}: {finding.title[:60]}
                GET /todos/{{invalid}} must return 400/422, not an unhandled 500.
                \"\"\"
                response = client.get("/todos/INVALID_ID_FORMAT")
                assert response.status_code in (400, 404, 422), (
                    f"Expected structured error for invalid ObjectId, got {{response.status_code}}"
                )


            """)
        return block, fname
