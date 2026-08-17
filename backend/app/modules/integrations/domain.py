"""Pure normalization and webhook-authentication rules for Polar AccessLink."""

import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlparse

from pydantic import ValidationError

from app.modules.activities.schemas import ActivityMetricInput, ActivitySummaryInput
from app.modules.physiology.models import Discipline

JsonObject = dict[str, Any]
_DURATION = re.compile(
    r"^P(?:\d+D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?$"
)
_ENTITY_ID = re.compile(r"^[A-Za-z0-9_-]{1,200}$")
_MAX_WEBHOOK_SKEW = timedelta(minutes=10)
_MAX_WEBHOOK_BYTES = 16 * 1024


class IntegrationPayloadError(ValueError):
    """A provider payload cannot safely enter the canonical activity path."""


def validate_polar_entity_id(value: Any) -> str:
    """Return one path-safe Polar hashed exercise identifier."""
    entity_id = value if isinstance(value, str) else ""
    if _ENTITY_ID.fullmatch(entity_id) is None:
        raise IntegrationPayloadError("Invalid webhook exercise.")
    return entity_id


def verify_polar_webhook(
    raw_body: bytes,
    signature: str,
    secret: str,
    *,
    now: datetime,
) -> JsonObject:
    """Authenticate one Polar payload and enforce a bounded timestamp window."""
    if len(raw_body) > _MAX_WEBHOOK_BYTES:
        raise IntegrationPayloadError("Webhook payload is too large.")
    if not secret or not signature:
        raise IntegrationPayloadError("Missing webhook authentication.")
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.lower()):
        raise IntegrationPayloadError("Invalid webhook signature.")
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IntegrationPayloadError("Invalid webhook payload.") from error
    if not isinstance(payload, dict):
        raise IntegrationPayloadError("Invalid webhook payload.")
    event = payload.get("event")
    if event not in {"PING", "EXERCISE"}:
        raise IntegrationPayloadError("Unsupported webhook event.")
    try:
        occurred_at = datetime.fromisoformat(
            str(payload["timestamp"]).replace("Z", "+00:00")
        )
    except (KeyError, ValueError) as error:
        raise IntegrationPayloadError("Invalid webhook timestamp.") from error
    if occurred_at.tzinfo is None:
        raise IntegrationPayloadError("Invalid webhook timestamp.")
    utc_now = now.astimezone(timezone.utc)
    if abs(utc_now - occurred_at.astimezone(timezone.utc)) > _MAX_WEBHOOK_SKEW:
        raise IntegrationPayloadError("Webhook timestamp is outside the replay window.")
    if event == "EXERCISE":
        if not isinstance(payload.get("user_id"), int):
            raise IntegrationPayloadError("Invalid webhook user.")
        validate_polar_entity_id(payload.get("entity_id"))
        url = payload.get("url")
        parsed = urlparse(str(url))
        if parsed.scheme != "https" or parsed.hostname != "www.polaraccesslink.com":
            raise IntegrationPayloadError("Invalid webhook exercise URL.")
    return payload


def webhook_event_key(payload: JsonObject) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _duration_minutes(value: Any) -> Decimal:
    match = _DURATION.fullmatch(str(value))
    if match is None:
        raise IntegrationPayloadError("Invalid Polar exercise duration.")
    try:
        hours = Decimal(match.group("hours") or "0")
        minutes = Decimal(match.group("minutes") or "0")
        seconds = Decimal(match.group("seconds") or "0")
    except InvalidOperation as error:
        raise IntegrationPayloadError("Invalid Polar exercise duration.") from error
    result = hours * 60 + minutes + seconds / 60
    if result <= 0:
        raise IntegrationPayloadError("Invalid Polar exercise duration.")
    return result


def _discipline(payload: JsonObject) -> Discipline:
    value = (
        f"{payload.get('sport', '')} {payload.get('detailed_sport_info', '')}"
    ).upper()
    if any(token in value for token in ("SWIM", "AQUA")):
        return Discipline.SWIM
    if any(token in value for token in ("CYCL", "BIKE", "BICYCL")):
        return Discipline.BIKE
    if any(token in value for token in ("RUN", "JOG")):
        return Discipline.RUN
    raise IntegrationPayloadError(
        "Polar exercise is outside the supported disciplines."
    )


def _started_at(payload: JsonObject) -> datetime:
    try:
        local = datetime.fromisoformat(
            str(payload["start_time"]).replace("Z", "+00:00")
        )
        if local.tzinfo is None:
            offset_minutes = int(payload.get("start_time_utc_offset", 0))
            local = local.replace(tzinfo=timezone(timedelta(minutes=offset_minutes)))
        return local
    except (KeyError, TypeError, ValueError) as error:
        raise IntegrationPayloadError("Invalid Polar exercise start time.") from error


def polar_exercise_to_activity(
    payload: JsonObject,
    *,
    athlete_timezone: str,
) -> ActivitySummaryInput:
    """Map an approved Polar fixture into the exact UC-03 input model."""
    heart_rate = payload.get("heart_rate")
    metric: ActivityMetricInput | None = None
    if isinstance(heart_rate, dict):
        values = {
            "average_heart_rate_bpm": heart_rate.get("average"),
            "max_heart_rate_bpm": heart_rate.get("maximum"),
        }
        values = {key: value for key, value in values.items() if value is not None}
        if values:
            try:
                metric = ActivityMetricInput.model_validate(values)
            except ValidationError as error:
                raise IntegrationPayloadError(
                    "Invalid Polar heart-rate summary."
                ) from error
    try:
        distance_value = payload.get("distance")
        distance = (
            int(Decimal(str(distance_value)).quantize(Decimal("1")))
            if distance_value is not None
            else None
        )
        return ActivitySummaryInput(
            discipline=_discipline(payload),
            started_at=_started_at(payload),
            timezone=athlete_timezone,
            duration_minutes=_duration_minutes(payload.get("duration")),
            distance_meters=distance if distance and distance > 0 else None,
            metrics=metric,
        )
    except (InvalidOperation, ValidationError) as error:
        raise IntegrationPayloadError("Invalid Polar exercise summary.") from error
