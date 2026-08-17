"""Deployment configuration safety tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_deployed_environments_require_both_supabase_keys() -> None:
    with pytest.raises(ValidationError, match="supabase_publishable_key"):
        Settings(
            environment="production",
            supabase_publishable_key="",
            supabase_secret_key="sb_secret_test",
        )

    with pytest.raises(ValidationError, match="supabase_secret_key"):
        Settings(
            environment="staging",
            supabase_publishable_key="sb_publishable_test",
            supabase_secret_key="",
        )


def test_secret_key_is_redacted_from_settings_representation() -> None:
    settings = Settings(
        environment="test",
        supabase_secret_key="sb_secret_do_not_log",
    )

    assert "sb_secret_do_not_log" not in repr(settings)


def test_polar_configuration_is_all_or_nothing_and_secrets_are_redacted() -> None:
    with pytest.raises(ValidationError, match="must be configured together"):
        Settings(environment="test", polar_client_id="partial-client")

    settings = Settings(
        environment="test",
        polar_client_id="polar-client",
        polar_client_secret="polar-secret-do-not-log",
        polar_webhook_secret="webhook-secret-do-not-log",
    )

    assert "polar-secret-do-not-log" not in repr(settings)
    assert "webhook-secret-do-not-log" not in repr(settings)
