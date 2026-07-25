"""Cross-cutting public API contract tests."""

from collections.abc import Iterator, Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

_FORBIDDEN_LOAD_KEYS = {"tss", "ptss", "rtss", "plannedtss", "realizedtss"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Create a test application for OpenAPI contract inspection."""
    settings = Settings(environment="test")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _assert_no_forbidden_load_key(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            normalized_key = "".join(
                character for character in str(key).lower() if character.isalnum()
            )
            assert normalized_key not in _FORBIDDEN_LOAD_KEYS
            _assert_no_forbidden_load_key(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _assert_no_forbidden_load_key(nested_value)


def test_openapi_contains_expected_foundation_paths(client: TestClient) -> None:
    """Foundation and identity routes remain stable."""
    schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {
        "/health",
        "/ready",
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/me",
    }


def test_openapi_excludes_hidden_load_fields(client: TestClient) -> None:
    """No planned or realized TSS field can enter the public schema."""
    schema = client.get("/openapi.json").json()

    _assert_no_forbidden_load_key(schema)


def test_openapi_documents_authentication_error(client: TestClient) -> None:
    """The current-user operation advertises the stable error envelope."""
    schema = client.get("/openapi.json").json()
    unauthorized = schema["paths"]["/api/v1/me"]["get"]["responses"]["401"]

    assert (
        unauthorized["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )
