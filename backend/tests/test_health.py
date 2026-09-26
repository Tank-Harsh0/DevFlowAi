"""
Health endpoint tests.

Verifies GET /health returns the expected response shape and status code.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_status_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_healthy(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["status"] == "healthy"


def test_health_returns_service_name(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["service"] == "devflow-ai"


def test_health_returns_version(client: TestClient) -> None:
    data = client.get("/health").json()
    assert "version" in data


def test_health_returns_environment(client: TestClient) -> None:
    data = client.get("/health").json()
    assert "environment" in data
