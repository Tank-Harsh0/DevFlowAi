"""
Integration tests — Phase 7: Reporting and Demo.

Tests per IMPLEMENTATION_PLAN Phase 7:
  1. ReportGenerator produces final_report.md.
  2. Report contains all required sections (PRD FR-60 / WORKFLOW.md Stage 16).
  3. Report is copied to the repository root.
  4. Orchestrator runs through REPORTING stage and reaches COMPLETE.
  5. The 'report' key is present in the orchestrator result dict.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.services.report_generator import ReportGenerator

SAMPLE_PROJECT = (Path(__file__).parent.parent.parent / "sample-project").resolve()

# Required sections (WORKFLOW.md Stage 16)
REQUIRED_SECTIONS = [
    "## 1. Project Summary",
    "## 2. Findings",
    "## 3. Remediation",
    "## 4. Testing",
    "## 5. Productivity Metrics",
    "## 6. Unresolved Issues",
    "## 7. Audit Trail",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo_copy(tmp_path):
    dest = tmp_path / "sample-project"
    shutil.copytree(SAMPLE_PROJECT, dest)
    return dest


@pytest.fixture
def minimal_session_dir(tmp_path):
    """A session directory with just enough artefacts for the report generator."""
    sd = tmp_path / "session"
    sd.mkdir()
    import json

    # Write minimal artefacts
    ctx = {
        "repository_path": str(tmp_path),
        "detected_language": "python",
        "detected_test_framework": "pytest",
        "source_files": [{"path": "main.py", "size_bytes": 100, "readable": True}],
        "test_files": [],
        "doc_files": [],
    }
    (sd / "project_context.json").write_text(json.dumps(ctx))
    (sd / "prioritized_findings.json").write_text(json.dumps([
        {
            "id": "CR-001", "source_agent": "code_review",
            "title": "Test finding", "severity": "high",
            "file": "main.py", "location": "line 1",
            "explanation": "test", "impact": "test",
            "recommended_fix": "test", "verification_method": "test",
            "fix_risk": "safe",
        }
    ]))
    (sd / "fix_plan.json").write_text(json.dumps([]))
    (sd / "approved_fix_plan.json").write_text(json.dumps([]))
    (sd / "fix_application_log.json").write_text(json.dumps([]))
    (sd / "generated_tests_manifest.json").write_text(json.dumps(
        {"output_file": "tests/test_devflow_generated.py", "functions": ["test_foo"]}
    ))
    (sd / "test_results_post_fix.json").write_text(json.dumps(
        {"total": 1, "passed": 1, "failed": 0, "error": 0, "skipped": 0,
         "duration_seconds": 0.1, "items": []}
    ))
    (sd / "failure_analysis.json").write_text(json.dumps(
        {"total_failures": 0, "in_scope": 0, "out_of_scope": 0, "items": []}
    ))
    (sd / "session.log").write_text("")
    return sd


# ---------------------------------------------------------------------------
# ReportGenerator unit tests
# ---------------------------------------------------------------------------


class TestReportGenerator:
    def test_report_file_is_created(self, minimal_session_dir, tmp_path):
        gen = ReportGenerator()
        path = gen.generate(minimal_session_dir, str(tmp_path), "TEST001")
        assert path.exists(), "final_report.md was not created"
        assert path.name == "final_report.md"

    def test_report_contains_all_required_sections(self, minimal_session_dir, tmp_path):
        """WORKFLOW.md Stage 16 — all 7 sections must be present."""
        gen = ReportGenerator()
        path = gen.generate(minimal_session_dir, str(tmp_path), "TEST001")
        content = path.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in content, f"Missing required section: {section}"

    def test_report_contains_session_id(self, minimal_session_dir, tmp_path):
        gen = ReportGenerator()
        path = gen.generate(minimal_session_dir, str(tmp_path), "SESSION42")
        content = path.read_text(encoding="utf-8")
        assert "SESSION42" in content

    def test_report_copied_to_repo_root(self, minimal_session_dir, tmp_path):
        """Report must also be written to the repository root."""
        gen = ReportGenerator()
        gen.generate(minimal_session_dir, str(tmp_path), "TEST001")
        assert (tmp_path / "final_report.md").exists()

    def test_report_contains_finding_ids(self, minimal_session_dir, tmp_path):
        gen = ReportGenerator()
        path = gen.generate(minimal_session_dir, str(tmp_path), "TEST001")
        content = path.read_text(encoding="utf-8")
        assert "CR-001" in content

    def test_report_with_missing_artefacts_does_not_crash(self, tmp_path):
        """Report generator must handle missing JSON files gracefully."""
        empty_dir = tmp_path / "empty_session"
        empty_dir.mkdir()
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        gen = ReportGenerator()
        path = gen.generate(empty_dir, str(repo_dir), "EMPTY")
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        # All sections must still be present
        for section in REQUIRED_SECTIONS:
            assert section in content, f"Missing section {section} in empty-artefact report"

    def test_report_is_valid_markdown(self, minimal_session_dir, tmp_path):
        """Report must start with a top-level heading."""
        gen = ReportGenerator()
        path = gen.generate(minimal_session_dir, str(tmp_path), "TEST001")
        content = path.read_text(encoding="utf-8")
        assert content.startswith("# DevFlow AI")

    def test_productivity_section_contains_measured_label(self, minimal_session_dir, tmp_path):
        gen = ReportGenerator()
        path = gen.generate(minimal_session_dir, str(tmp_path), "TEST001")
        content = path.read_text(encoding="utf-8")
        assert "Measured" in content

    def test_audit_trail_lists_session_log(self, minimal_session_dir, tmp_path):
        gen = ReportGenerator()
        path = gen.generate(minimal_session_dir, str(tmp_path), "TEST001")
        content = path.read_text(encoding="utf-8")
        assert "session.log" in content


# ---------------------------------------------------------------------------
# Orchestrator Phase 7 integration tests
# ---------------------------------------------------------------------------


class TestOrchestratorPhase7:
    def test_run_produces_final_report_md(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "final_report.md").exists()

    def test_result_has_report_key(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        assert "report" in result
        assert Path(result["report"]).exists()

    def test_final_report_contains_all_required_sections(self, repo_copy, tmp_path, monkeypatch):
        """PRD FR-60: final_report.md must contain all required sections."""
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        content = Path(result["report"]).read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in content, f"Missing section in orchestrator report: {section}"

    def test_workflow_reaches_complete_after_reporting(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.models.workflow import WorkflowStage
        from app.services.orchestrator import Orchestrator
        orch = Orchestrator(str(repo_copy), decisions={})
        orch.run()
        assert orch.state.stage == WorkflowStage.COMPLETE
