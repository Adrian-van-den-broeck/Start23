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


def test_openai_configuration_is_server_only_bounded_and_redacted() -> None:
    settings = Settings(
        environment="test",
        openai_api_key="openai-secret-do-not-log",
        openai_model="gpt-5.6-luna",
        openai_api_timeout_seconds=7,
    )

    assert settings.openai_model == "gpt-5.6-luna"
    assert settings.openai_api_timeout_seconds == 7
    assert "openai-secret-do-not-log" not in repr(settings)

    with pytest.raises(ValidationError, match="openai_model"):
        Settings(environment="test", openai_model="   ")


def test_polar_configuration_requires_secrets_when_enabled_and_redacts_them() -> None:
    with pytest.raises(ValidationError, match="must be configured together"):
        Settings(environment="test", polar_client_id="partial-client")

    disabled = Settings(
        environment="test",
        polar_client_secret="dormant-polar-secret",
        polar_webhook_secret="dormant-webhook-secret",
    )
    assert disabled.polar_client_id == ""

    settings = Settings(
        environment="test",
        polar_client_id="polar-client",
        polar_client_secret="polar-secret-do-not-log",
        polar_webhook_secret="webhook-secret-do-not-log",
    )

    assert "polar-secret-do-not-log" not in repr(settings)
    assert "webhook-secret-do-not-log" not in repr(settings)


def test_production_requires_accountable_physiology_review() -> None:
    with pytest.raises(ValidationError, match="physiology review record"):
        Settings(
            environment="production",
            supabase_publishable_key="sb_publishable_test",
            supabase_secret_key="sb_secret_test",
        )


def test_production_polar_requires_approvals_https_owner_and_retention() -> None:
    base = {
        "environment": "production",
        "supabase_publishable_key": "sb_publishable_test",
        "supabase_secret_key": "sb_secret_test",
        "physiology_review_record_id": "review-2026-08",
        "physiology_accountable_owner": "qualified-reviewer",
        "polar_client_id": "polar-client",
        "polar_client_secret": "polar-secret",
        "polar_webhook_secret": "webhook-secret",
    }
    with pytest.raises(ValidationError, match="legal, privacy"):
        Settings(**base)

    settings = Settings(
        **base,
        polar_legal_approved=True,
        polar_privacy_approved=True,
        polar_provider_terms_approved=True,
        polar_operational_owner="integration-owner",
        polar_oauth_redirect_url=(
            "https://api.start23.example/api/v1/integrations/polar/oauth/callback"
        ),
        polar_raw_fit_retention_days=14,
        polar_canonical_activity_retention_days=365,
    )

    assert settings.polar_raw_fit_retention_days == 14
