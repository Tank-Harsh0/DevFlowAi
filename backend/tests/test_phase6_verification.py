"""
Integration tests — Phase 6: Verification.

Tests per IMPLEMENTATION_PLAN Phase 6:
  1. TestGenerator produces ≥ 6 test functions for sample-project (AC-07).
  2. TestRunner executes pytest and produces test_results_post_fix.json.
  3. FailureAnalyzer classifies failures correctly.
  4. Orchestrator reaches COMPLETE through all Phase 6 stages.
  5. All Phase 6 artefacts are written to the session directory.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.services.failure_analyzer import FailureAnalyzer
from app.services.finding_aggregator import FindingAggregator
from app.services.issue_prioritizer import IssuePrioritizer
from app.services.repository_inspector import RepositoryInspector
from app.services.test_generator import TestGenerator
from app.services.test_runner import PytestRunner

SAMPLE_PROJECT = (Path(__file__).parent.parent.parent / "sample-project").resolve()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sample_context():
    return RepositoryInspector().inspect(str(SAMPLE_PROJECT))


@pytest.fixture(scope="module")
def prioritized_findings(sample_context):
    from app.agents.code_review import CodeReviewAgent
    from app.agents.documentation import DocumentationAgent
    from app.agents.security import SecurityAgent
    from app.agents.test_analysis import TestingAnalysisAgent

    raw = []
    for agent in [CodeReviewAgent(), TestingAnalysisAgent(), SecurityAgent(), DocumentationAgent()]:
        raw.extend(agent.safe_analyze(sample_context))
    return IssuePrioritizer().prioritize(FindingAggregator().aggregate(raw))


@pytest.fixture
def repo_copy(tmp_path):
    """Isolated copy of sample-project for tests that may write to it."""
    dest = tmp_path / "sample-project"
    shutil.copytree(SAMPLE_PROJECT, dest)
    return dest


# ---------------------------------------------------------------------------
# TestGenerator unit tests
# ---------------------------------------------------------------------------


class TestTestGenerator:
    def test_generates_at_least_six_functions(
        self, tmp_path, prioritized_findings, sample_context
    ):
        """AC-07: TestGenerator must produce ≥ 6 test functions for the sample project."""
        output = tmp_path / "tests" / "test_devflow_generated.py"
        names = TestGenerator().generate(prioritized_findings, sample_context, output)
        assert len(names) >= 6, (
            f"Expected ≥ 6 test functions, got {len(names)}: {names}"
        )

    def test_output_file_is_written(self, tmp_path, prioritized_findings, sample_context):
        output = tmp_path / "tests" / "test_devflow_generated.py"
        TestGenerator().generate(prioritized_findings, sample_context, output)
        assert output.exists(), "test_devflow_generated.py was not created"

    def test_output_file_is_valid_python(self, tmp_path, prioritized_findings, sample_context):
        """Generated file must be syntactically valid Python."""
        import py_compile
        output = tmp_path / "tests" / "test_devflow_generated.py"
        TestGenerator().generate(prioritized_findings, sample_context, output)
        # Should not raise
        py_compile.compile(str(output), doraise=True)

    def test_output_contains_finding_ids(self, tmp_path, prioritized_findings, sample_context):
        """Each test function block must reference its finding ID."""
        output = tmp_path / "tests" / "test_devflow_generated.py"
        TestGenerator().generate(prioritized_findings, sample_context, output)
        content = output.read_text(encoding="utf-8")
        # At least one finding ID reference in the file
        any_id = any(f.id in content for f in prioritized_findings)
        assert any_id, "No finding IDs found in generated test file"

    def test_output_contains_testclient_import(
        self, tmp_path, prioritized_findings, sample_context
    ):
        output = tmp_path / "tests" / "test_devflow_generated.py"
        TestGenerator().generate(prioritized_findings, sample_context, output)
        content = output.read_text(encoding="utf-8")
        assert "TestClient" in content

    def test_function_names_are_unique(self, tmp_path, prioritized_findings, sample_context):
        output = tmp_path / "tests" / "test_devflow_generated.py"
        names = TestGenerator().generate(prioritized_findings, sample_context, output)
        assert len(names) == len(set(names)), "Duplicate test function names generated"

    def test_empty_findings_writes_file(self, tmp_path, sample_context):
        """Even with no findings, an output file must be written."""
        output = tmp_path / "tests" / "test_devflow_generated.py"
        names = TestGenerator().generate([], sample_context, output)
        assert output.exists()
        assert names == []


# ---------------------------------------------------------------------------
# TestRunner unit tests
# ---------------------------------------------------------------------------


class TestPytestRunner:
    def test_run_returns_dict_with_required_keys(self, repo_copy):
        result = PytestRunner(str(repo_copy)).run()
        for key in ("total", "passed", "failed", "error", "skipped", "duration_seconds", "items"):
            assert key in result, f"Missing key: {key}"

    def test_run_items_is_list(self, repo_copy):
        result = PytestRunner(str(repo_copy)).run()
        assert isinstance(result["items"], list)

    def test_run_counts_are_non_negative(self, repo_copy):
        result = PytestRunner(str(repo_copy)).run()
        assert result["passed"] >= 0
        assert result["failed"] >= 0
        assert result["error"] >= 0
        assert result["skipped"] >= 0

    def test_run_total_equals_sum_of_outcomes(self, repo_copy):
        result = PytestRunner(str(repo_copy)).run()
        expected = (
            int(result["passed"])
            + int(result["failed"])
            + int(result["error"])
            + int(result["skipped"])
        )
        assert result["total"] == expected

    def test_invalid_path_returns_empty_result(self, tmp_path):
        """A repo with no tests should return a valid (possibly empty) result, not crash."""
        (tmp_path / "empty_project").mkdir()
        result = PytestRunner(str(tmp_path / "empty_project")).run()
        assert isinstance(result, dict)
        assert "total" in result


# ---------------------------------------------------------------------------
# FailureAnalyzer unit tests
# ---------------------------------------------------------------------------


class TestFailureAnalyzer:
    def _make_results(self, items: list[dict]) -> dict:
        return {
            "total": len(items),
            "passed": 0,
            "failed": len(items),
            "error": 0,
            "skipped": 0,
            "duration_seconds": 0.0,
            "items": items,
        }

    def test_empty_results_returns_zero_failures(self):
        result = FailureAnalyzer().analyze({"items": [], "failed": 0})
        assert result["total_failures"] == 0
        assert result["in_scope"] == 0
        assert result["out_of_scope"] == 0

    def test_assertion_failure_is_in_scope(self):
        items = [{"node_id": "tests/test_foo.py::test_bar", "outcome": "failed",
                  "message": "AssertionError: assert 404 == 200"}]
        result = FailureAnalyzer().analyze(self._make_results(items))
        assert result["total_failures"] == 1
        assert result["in_scope"] == 1
        classified = result["items"][0]
        assert classified["cause"] == "assertion_failure"
        assert classified["in_scope"] is True

    def test_import_error_is_out_of_scope(self):
        items = [{"node_id": "tests/test_foo.py::test_bar", "outcome": "failed",
                  "message": "ImportError: No module named 'pymongo'"}]
        result = FailureAnalyzer().analyze(self._make_results(items))
        assert result["out_of_scope"] == 1
        assert result["items"][0]["in_scope"] is False

    def test_exception_is_in_scope(self):
        items = [{"node_id": "tests/test_foo.py::test_bar", "outcome": "failed",
                  "message": "Exception: raise HTTPException(status_code=500)"}]
        result = FailureAnalyzer().analyze(self._make_results(items))
        assert result["items"][0]["cause"] == "exception"
        assert result["items"][0]["in_scope"] is True

    def test_unknown_cause_is_out_of_scope(self):
        items = [{"node_id": "tests/test_foo.py::test_bar", "outcome": "failed",
                  "message": ""}]
        result = FailureAnalyzer().analyze(self._make_results(items))
        assert result["items"][0]["in_scope"] is False

    def test_result_has_items_list(self):
        result = FailureAnalyzer().analyze({"items": [], "failed": 0})
        assert isinstance(result["items"], list)

    def test_counts_sum_correctly(self):
        items = [
            {"node_id": "t::a", "outcome": "failed", "message": "AssertionError"},
            {"node_id": "t::b", "outcome": "failed", "message": "ImportError: no module"},
        ]
        result = FailureAnalyzer().analyze(self._make_results(items))
        assert result["in_scope"] + result["out_of_scope"] == result["total_failures"]


# ---------------------------------------------------------------------------
# Orchestrator Phase 6 integration tests
# ---------------------------------------------------------------------------


class TestOrchestratorPhase6:
    def test_run_produces_generated_tests_manifest(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "generated_tests_manifest.json").exists()

    def test_run_produces_test_results_post_fix_json(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "test_results_post_fix.json").exists()

    def test_run_produces_failure_analysis_json(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "failure_analysis.json").exists()

    def test_result_has_phase6_keys(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        assert "generated_tests" in result
        assert "tests_passed" in result
        assert "tests_failed" in result
        assert "in_scope_failures" in result

    def test_generated_tests_count_meets_minimum(self, repo_copy, tmp_path, monkeypatch):
        """AC-07: ≥ 6 test functions generated for the sample project."""
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        assert result["generated_tests"] >= 6, (
            f"Expected ≥ 6 generated tests, got {result['generated_tests']}"
        )

    def test_test_results_json_is_valid(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        data = json.loads((session_dir / "test_results_post_fix.json").read_text())
        assert "total" in data
        assert "passed" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_failure_analysis_json_is_valid(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        data = json.loads((session_dir / "failure_analysis.json").read_text())
        assert "total_failures" in data
        assert "in_scope" in data
        assert "out_of_scope" in data
        assert "items" in data

    def test_workflow_still_reaches_complete(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.models.workflow import WorkflowStage
        from app.services.orchestrator import Orchestrator
        orch = Orchestrator(str(repo_copy), decisions={})
        orch.run()
        assert orch.state.stage == WorkflowStage.COMPLETE
