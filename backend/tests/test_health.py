"""Health endpoint contract tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Create a test client with deterministic settings."""
    settings = Settings(environment="test")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.mark.parametrize("path", ["/health", "/api/v1/health"])
def test_health_endpoint(client: TestClient, path: str) -> None:
    """Both public health routes return the same stable contract."""
    response = client.get(path)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Start23 API",
        "version": "0.1.0",
        "environment": "test",
    }


@pytest.mark.parametrize("path", ["/ready", "/api/v1/ready"])
def test_readiness_endpoint(client: TestClient, path: str) -> None:
    """Both readiness routes return the same stable contract."""
    response = client.get(path)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "Start23 API",
        "version": "0.1.0",
        "environment": "test",
    }
    assert response.headers["x-request-id"]
