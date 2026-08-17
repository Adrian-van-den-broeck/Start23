"""Polar contract-fixture mapping and webhook authentication tests."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.modules.integrations.domain import (
    IntegrationPayloadError,
    polar_exercise_to_activity,
    verify_polar_webhook,
)

_FIXTURE = Path(__file__).parent / "fixtures" / "polar" / "exercise.json"


def _exercise() -> dict[str, object]:
    value = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _signed(
    payload: dict[str, object],
    secret: str = "webhook-secret",
) -> tuple[bytes, str]:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return raw, hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def test_official_style_polar_fixture_maps_to_canonical_uc03_input() -> None:
    summary = polar_exercise_to_activity(
        _exercise(), athlete_timezone="Europe/Amsterdam"
    )

    assert summary.discipline.value == "run"
    assert str(summary.duration_minutes) == "62.5"
    assert summary.distance_meters == 12500
    assert summary.started_at.isoformat() == "2026-08-17T08:00:00+02:00"
    assert summary.metrics is not None
    assert summary.metrics.average_heart_rate_bpm == 149
    assert summary.metrics.max_heart_rate_bpm == 174
    assert "training_load" not in summary.model_dump()


def test_unsupported_sport_fails_closed_before_activity_creation() -> None:
    exercise = _exercise()
    exercise["sport"] = "OTHER"
    exercise["detailed_sport_info"] = "YOGA"

    with pytest.raises(IntegrationPayloadError, match="supported disciplines"):
        polar_exercise_to_activity(exercise, athlete_timezone="Europe/Amsterdam")


def test_webhook_signature_and_timestamp_are_both_required() -> None:
    now = datetime(2026, 8, 17, 10, tzinfo=timezone.utc)
    payload = {
        "event": "EXERCISE",
        "user_id": 475,
        "entity_id": "2AC312F",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "url": "https://www.polaraccesslink.com/v3/exercises/2AC312F",
    }
    raw, signature = _signed(payload)

    assert verify_polar_webhook(raw, signature, "webhook-secret", now=now) == payload
    with pytest.raises(IntegrationPayloadError, match="signature"):
        verify_polar_webhook(raw, "0" * 64, "webhook-secret", now=now)
    with pytest.raises(IntegrationPayloadError, match="replay window"):
        verify_polar_webhook(
            raw,
            signature,
            "webhook-secret",
            now=now + timedelta(minutes=11),
        )


def test_webhook_rejects_provider_controlled_fetch_host() -> None:
    now = datetime(2026, 8, 17, 10, tzinfo=timezone.utc)
    payload = {
        "event": "EXERCISE",
        "user_id": 475,
        "entity_id": "2AC312F",
        "timestamp": now.isoformat(),
        "url": "https://attacker.invalid/exercise",
    }
    raw, signature = _signed(payload)

    with pytest.raises(IntegrationPayloadError, match="URL"):
        verify_polar_webhook(raw, signature, "webhook-secret", now=now)


def test_webhook_rejects_path_unsafe_entity_identifier() -> None:
    now = datetime(2026, 8, 17, 10, tzinfo=timezone.utc)
    payload = {
        "event": "EXERCISE",
        "user_id": 475,
        "entity_id": "../other-athlete",
        "timestamp": now.isoformat(),
        "url": "https://www.polaraccesslink.com/v3/exercises/example",
    }
    raw, signature = _signed(payload)

    with pytest.raises(IntegrationPayloadError, match="exercise"):
        verify_polar_webhook(raw, signature, "webhook-secret", now=now)
