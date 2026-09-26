"""
Integration test — Phase 2: Orchestrator Skeleton.

Points the Repository Inspector at the sample-project/ directory and
verifies that project_context.json is produced with the expected structure.

The sample project is at: <repo_root>/sample-project/
Tests run from: backend/

The path is resolved relative to this file so it works regardless of the
current working directory.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.workflow import WorkflowStage
from app.services.orchestrator import Orchestrator
from app.services.repository_inspector import RepositoryInspector
from app.services.session_manager import SessionManager
from app.services.task_planner import TaskPlanner

# Absolute path to sample-project/ (one level up from backend/)
SAMPLE_PROJECT = (Path(__file__).parent.parent.parent / "sample-project").resolve()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_sessions(tmp_path, monkeypatch):
    """Redirect session output to a temp directory for all Phase 2 tests."""
    monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path / "devflow_sessions")
    yield


# ---------------------------------------------------------------------------
# Repository Inspector tests
# ---------------------------------------------------------------------------


class TestRepositoryInspector:
    def test_sample_project_exists(self):
        assert SAMPLE_PROJECT.exists(), f"sample-project not found at {SAMPLE_PROJECT}"

    def test_inspect_returns_project_context(self):
        inspector = RepositoryInspector()
        ctx = inspector.inspect(str(SAMPLE_PROJECT))
        assert ctx.repository_path == str(SAMPLE_PROJECT)

    def test_detects_python_language(self):
        inspector = RepositoryInspector()
        ctx = inspector.inspect(str(SAMPLE_PROJECT))
        assert ctx.detected_language == "python"

    def test_finds_source_files(self):
        inspector = RepositoryInspector()
        ctx = inspector.inspect(str(SAMPLE_PROJECT))
        source_paths = [f.path for f in ctx.source_files]
        assert any("main.py" in p for p in source_paths), (
            f"main.py not in source_files: {source_paths}"
        )

    def test_finds_manifest_file(self):
        inspector = RepositoryInspector()
        ctx = inspector.inspect(str(SAMPLE_PROJECT))
        manifest_paths = [f.path for f in ctx.manifest_files]
        assert any("requirements.txt" in p for p in manifest_paths), (
            f"requirements.txt not in manifest_files: {manifest_paths}"
        )

    def test_finds_doc_files(self):
        inspector = RepositoryInspector()
        ctx = inspector.inspect(str(SAMPLE_PROJECT))
        doc_paths = [f.path for f in ctx.doc_files]
        assert any("README" in p.upper() for p in doc_paths), (
            f"README.md not in doc_files: {doc_paths}"
        )

    def test_reads_main_py_content(self):
        inspector = RepositoryInspector()
        ctx = inspector.inspect(str(SAMPLE_PROJECT))
        main_content = next(
            (v for k, v in ctx.file_contents.items() if "main.py" in k), None
        )
        assert main_content is not None, "main.py content not loaded"
        assert "FastAPI" in main_content

    def test_invalid_path_raises(self):
        inspector = RepositoryInspector()
        with pytest.raises(FileNotFoundError):
            inspector.inspect("/nonexistent/path/that/does/not/exist")


# ---------------------------------------------------------------------------
# Task Planner tests
# ---------------------------------------------------------------------------


class TestTaskPlanner:
    def _get_context(self):
        return RepositoryInspector().inspect(str(SAMPLE_PROJECT))

    def test_plan_returns_execution_plan(self):
        ctx = self._get_context()
        plan = TaskPlanner().plan("test-session", ctx)
        assert plan.session_id == "test-session"

    def test_plan_enables_code_review(self):
        ctx = self._get_context()
        plan = TaskPlanner().plan("test-session", ctx)
        code_review = next(t for t in plan.tasks if t.agent == "code_review")
        assert code_review.enabled

    def test_plan_enables_security(self):
        ctx = self._get_context()
        plan = TaskPlanner().plan("test-session", ctx)
        security = next(t for t in plan.tasks if t.agent == "security")
        assert security.enabled

    def test_plan_enables_documentation(self):
        ctx = self._get_context()
        plan = TaskPlanner().plan("test-session", ctx)
        documentation = next(t for t in plan.tasks if t.agent == "documentation")
        assert documentation.enabled

    def test_plan_has_four_tasks(self):
        ctx = self._get_context()
        plan = TaskPlanner().plan("test-session", ctx)
        assert len(plan.tasks) == 4

    def test_parallel_not_supported(self):
        """IBM Bob 2.0 parallel API not yet validated — must be False."""
        ctx = self._get_context()
        plan = TaskPlanner().plan("test-session", ctx)
        assert plan.parallel_supported is False


# ---------------------------------------------------------------------------
# Session Manager tests
# ---------------------------------------------------------------------------


class TestSessionManager:
    def test_create_creates_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        sm = SessionManager("20260926T130000")
        sm.create()
        assert (tmp_path / "20260926T130000").is_dir()
        sm.close()

    def test_write_and_read_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        sm = SessionManager("20260926T130001")
        sm.create()
        sm.write_json("test.json", {"key": "value"})
        data = sm.read_json("test.json")
        assert data == {"key": "value"}
        sm.close()

    def test_duplicate_session_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        sm1 = SessionManager("20260926T130002")
        sm1.create()
        sm2 = SessionManager("20260926T130002")
        with pytest.raises(FileExistsError):
            sm2.create()
        sm1.close()


# ---------------------------------------------------------------------------
# Orchestrator integration test
# ---------------------------------------------------------------------------


class TestOrchestratorPhase2:
    def test_run_produces_project_context_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        orch = Orchestrator(str(SAMPLE_PROJECT), decisions={})
        result = orch.run()
        ctx_path = Path(result["project_context"])
        assert ctx_path.exists(), "project_context.json was not created"

    def test_project_context_json_is_valid(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        orch = Orchestrator(str(SAMPLE_PROJECT), decisions={})
        result = orch.run()
        data = json.loads(Path(result["project_context"]).read_text())
        assert "repository_path" in data
        assert "detected_language" in data
        assert data["detected_language"] == "python"
        assert "source_files" in data

    def test_run_produces_execution_plan_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        orch = Orchestrator(str(SAMPLE_PROJECT), decisions={})
        result = orch.run()
        plan_path = Path(result["execution_plan"])
        assert plan_path.exists(), "execution_plan.json was not created"

    def test_execution_plan_json_is_valid(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        orch = Orchestrator(str(SAMPLE_PROJECT), decisions={})
        result = orch.run()
        data = json.loads(Path(result["execution_plan"]).read_text())
        assert "tasks" in data
        assert len(data["tasks"]) == 4

    def test_workflow_reaches_complete_stage(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        orch = Orchestrator(str(SAMPLE_PROJECT), decisions={})
        orch.run()
        assert orch.state.stage == WorkflowStage.COMPLETE

    def test_session_log_is_created(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        orch = Orchestrator(str(SAMPLE_PROJECT), decisions={})
        result = orch.run()
        session_dir = Path(result["project_context"]).parent
        log_path = session_dir / "session.log"
        assert log_path.exists(), "session.log was not created"

    def test_session_log_contains_audit_entries(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        orch = Orchestrator(str(SAMPLE_PROJECT), decisions={})
        result = orch.run()
        session_dir = Path(result["project_context"]).parent
        log_content = (session_dir / "session.log").read_text()
        assert "Repository Inspector" in log_content
        assert "Task Planner" in log_content

    def test_invalid_repo_path_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import OrchestratorError
        orch = Orchestrator("/nonexistent/repo")
        with pytest.raises(OrchestratorError):
            orch.run()
