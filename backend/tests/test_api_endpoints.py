"""
API endpoint tests — verifies all /api/v1/* routes respond correctly.

These do NOT run a full orchestrator (too slow for CI).
They validate: routing, request/response shapes, store behaviour.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.store import store
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_store():
    """Reset the in-memory store before each test."""
    store.clear()
    yield
    store.clear()


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

class TestRepositoriesEndpoints:
    def test_list_repositories_empty(self):
        r = client.get("/api/v1/repositories")
        assert r.status_code == 200
        assert r.json() == []

    def test_add_repository(self):
        r = client.post(
            "/api/v1/repositories", json={"url": "/tmp/my-project", "name": "my-project"}
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "my-project"
        assert data["url"] == "/tmp/my-project"
        assert data["status"] == "idle"
        assert "id" in data

    def test_add_repository_derives_name_from_url(self):
        r = client.post("/api/v1/repositories", json={"url": "/projects/todo-api"})
        assert r.status_code == 201
        assert r.json()["name"] == "todo-api"

    def test_get_repository(self):
        add = client.post("/api/v1/repositories", json={"url": "/tmp/repo"}).json()
        r = client.get(f"/api/v1/repositories/{add['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == add["id"]

    def test_get_repository_not_found(self):
        r = client.get("/api/v1/repositories/nonexistent")
        assert r.status_code == 404

    def test_delete_repository(self):
        add = client.post("/api/v1/repositories", json={"url": "/tmp/repo"}).json()
        r = client.delete(f"/api/v1/repositories/{add['id']}")
        assert r.status_code == 204
        r2 = client.get(f"/api/v1/repositories/{add['id']}")
        assert r2.status_code == 404

    def test_delete_repository_not_found(self):
        r = client.delete("/api/v1/repositories/nonexistent")
        assert r.status_code == 404

    def test_list_repositories_after_add(self):
        client.post("/api/v1/repositories", json={"url": "/a"})
        client.post("/api/v1/repositories", json={"url": "/b"})
        r = client.get("/api/v1/repositories")
        assert r.status_code == 200
        assert len(r.json()) == 2


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

class TestWorkflowsEndpoints:
    def _add_repo(self, path: str = "/tmp/repo") -> dict:
        return client.post("/api/v1/repositories", json={"url": path, "name": "testrepo"}).json()

    def test_list_workflows_empty(self):
        r = client.get("/api/v1/workflows")
        assert r.status_code == 200
        assert r.json() == []

    def test_start_workflow_unknown_repo(self):
        r = client.post("/api/v1/workflows", json={"repositoryId": "bad-id"})
        assert r.status_code == 404

    def test_start_workflow_creates_run(self):
        repo = self._add_repo()
        r = client.post("/api/v1/workflows", json={"repositoryId": repo["id"]})
        assert r.status_code == 201
        data = r.json()
        assert data["repositoryId"] == repo["id"]
        assert data["status"] in ("running", "pending")
        assert len(data["steps"]) > 0
        assert "id" in data

    def test_get_workflow_not_found(self):
        r = client.get("/api/v1/workflows/nonexistent")
        assert r.status_code == 404

    def test_get_workflow_returns_run(self):
        repo = self._add_repo()
        run = client.post("/api/v1/workflows", json={"repositoryId": repo["id"]}).json()
        r = client.get(f"/api/v1/workflows/{run['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == run["id"]

    def test_submit_approval(self):
        repo = self._add_repo()
        run = client.post("/api/v1/workflows", json={"repositoryId": repo["id"]}).json()
        r = client.post(
            f"/api/v1/workflows/{run['id']}/steps/awaiting_approval/approval",
            json={"approved": True, "note": "looks good"},
        )
        assert r.status_code == 200

    def test_submit_approval_unknown_workflow(self):
        r = client.post(
            "/api/v1/workflows/bad-id/steps/awaiting_approval/approval",
            json={"approved": True},
        )
        assert r.status_code == 404

    def test_report_not_available_for_running_workflow(self):
        repo = self._add_repo()
        run = client.post("/api/v1/workflows", json={"repositoryId": repo["id"]}).json()
        r = client.get(f"/api/v1/workflows/{run['id']}/report")
        # Report not ready yet (workflow is still running in background)
        assert r.status_code == 404

    def test_filter_workflows_by_repository(self):
        repo1 = self._add_repo("/a")
        repo2 = self._add_repo("/b")
        client.post("/api/v1/workflows", json={"repositoryId": repo1["id"]})
        client.post("/api/v1/workflows", json={"repositoryId": repo2["id"]})
        r = client.get(f"/api/v1/workflows?repositoryId={repo1['id']}")
        assert r.status_code == 200
        assert all(w["repositoryId"] == repo1["id"] for w in r.json())


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

class TestFindingsEndpoints:
    def test_list_findings_empty(self):
        r = client.get("/api/v1/findings")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_finding_not_found(self):
        r = client.get("/api/v1/findings/nonexistent")
        assert r.status_code == 404

    def test_approve_finding_not_found(self):
        r = client.post("/api/v1/findings/nonexistent/approve", json={})
        assert r.status_code == 404

    def test_reject_finding_not_found(self):
        r = client.post("/api/v1/findings/nonexistent/reject", json={})
        assert r.status_code == 404

    def test_approve_finding_changes_status(self):
        from datetime import UTC, datetime

        from app.api.schemas import (
            AgentSource,
            FindingLocationOut,
            FindingOut,
            FindingSeverity,
            FindingStatus,
        )
        now = datetime.now(tz=UTC).isoformat()
        f = FindingOut(
            id="f1", workflowId="w1", severity=FindingSeverity.HIGH,
            status=FindingStatus.OPEN, agent=AgentSource.CODE_REVIEW,
            title="Test", description="desc",
            location=FindingLocationOut(file="main.py"),
            createdAt=now, updatedAt=now,
        )
        store.findings["f1"] = f
        r = client.post("/api/v1/findings/f1/approve", json={})
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    def test_reject_finding_changes_status(self):
        from datetime import UTC, datetime

        from app.api.schemas import (
            AgentSource,
            FindingLocationOut,
            FindingOut,
            FindingSeverity,
            FindingStatus,
        )
        now = datetime.now(tz=UTC).isoformat()
        f = FindingOut(
            id="f2", workflowId="w1", severity=FindingSeverity.MEDIUM,
            status=FindingStatus.OPEN, agent=AgentSource.SECURITY,
            title="Test", description="desc",
            location=FindingLocationOut(file="main.py"),
            createdAt=now, updatedAt=now,
        )
        store.findings["f2"] = f
        r = client.post("/api/v1/findings/f2/reject", json={"reason": "not relevant"})
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class TestReportsEndpoints:
    def test_list_reports_empty(self):
        r = client.get("/api/v1/reports")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_report_not_found(self):
        r = client.get("/api/v1/reports/nonexistent")
        assert r.status_code == 404
