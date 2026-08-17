"""Application orchestration for OAuth, webhook, and canonical Polar imports."""

import hashlib
import json
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid5

from app.core.config import Settings

from .domain import (
    IntegrationPayloadError,
    polar_exercise_to_activity,
    validate_polar_entity_id,
    verify_polar_webhook,
    webhook_event_key,
)
from .polar import PolarAuthorizationError, PolarProvider, PolarProviderError
from .repository import IntegrationRepository, IntegrationRepositoryError, JsonObject
from .schemas import (
    ImportRunResponse,
    OAuthCallbackResponse,
    OAuthStartResponse,
    ProviderConnectionResponse,
    WebhookReceiptResponse,
)

_IMPORT_NAMESPACE = UUID("f957ef4d-3b54-44d7-9d62-cbe4992a07d1")


class IntegrationService:
    """Keep every provider effect retry-safe and outside physiology modules."""

    def __init__(
        self,
        repository: IntegrationRepository,
        provider: PolarProvider,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._provider = provider
        self._webhook_secret = settings.polar_webhook_secret.get_secret_value()

    @staticmethod
    def _fingerprint(payload: JsonObject) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def start_oauth(self, access_token: str) -> OAuthStartResponse:
        state = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        authorization_url = self._provider.authorization_url(state)
        await self._repository.create_oauth_state(
            access_token,
            hashlib.sha256(state.encode()).hexdigest(),
            expires_at.isoformat(),
        )
        return OAuthStartResponse(
            authorization_url=authorization_url,
            expires_at=expires_at,
        )

    async def complete_oauth(self, code: str, state: str) -> OAuthCallbackResponse:
        if not code or len(code) > 500 or not state or len(state) > 500:
            raise IntegrationPayloadError("Invalid OAuth callback.")
        athlete_id = await self._repository.consume_oauth_state(
            hashlib.sha256(state.encode()).hexdigest()
        )
        token = await self._provider.exchange_code(code)
        registered_user = await self._provider.register_user(
            token.access_token,
            f"start23:{athlete_id}",
        )
        provider_user_id = registered_user or token.provider_user_id
        if not provider_user_id:
            raise PolarProviderError
        await self._repository.save_connection(
            athlete_id,
            provider_user_id,
            token.access_token,
            token.expires_at.isoformat() if token.expires_at else None,
        )
        return OAuthCallbackResponse(status="connected")

    async def get_connection(self, access_token: str) -> ProviderConnectionResponse:
        return ProviderConnectionResponse.model_validate(
            await self._repository.get_connection(access_token)
        )

    async def disconnect(self, athlete_id: UUID) -> None:
        credentials = await self._repository.get_credentials(athlete_id)
        try:
            await self._provider.revoke(
                str(credentials["access_token"]),
                str(credentials["provider_user_id"]),
            )
        except PolarAuthorizationError:
            await self._repository.disconnect(athlete_id, "revoked")
            return
        await self._repository.disconnect(athlete_id, "disconnected")

    @staticmethod
    def _import_response(row: JsonObject) -> ImportRunResponse:
        return ImportRunResponse.model_validate(row)

    async def list_imports(self, access_token: str) -> tuple[ImportRunResponse, ...]:
        return tuple(
            self._import_response(row)
            for row in await self._repository.list_imports(access_token)
        )

    async def _import_one(
        self,
        *,
        athlete_id: UUID,
        import_id: UUID,
        token: str,
        timezone_name: str,
        exercise: JsonObject,
    ) -> bool:
        entity_id = validate_polar_entity_id(exercise.get("id"))
        summary = polar_exercise_to_activity(exercise, athlete_timezone=timezone_name)
        payload = summary.model_dump(mode="json", exclude_none=True)
        result = await self._repository.import_activity(
            athlete_id,
            import_id,
            entity_id,
            uuid5(_IMPORT_NAMESPACE, f"polar:{entity_id}"),
            self._fingerprint(payload),
            payload,
        )
        activity = result.get("activity")
        if not isinstance(activity, dict):
            raise IntegrationPayloadError("Imported activity state is invalid.")
        raw_file = await self._provider.get_fit(token, entity_id)
        if raw_file:
            await self._repository.upload_activity_file(
                athlete_id,
                UUID(str(activity["id"])),
                entity_id,
                raw_file,
                hashlib.sha256(raw_file).hexdigest(),
            )
        return bool(result.get("created", False))

    async def import_historical(
        self,
        athlete_id: UUID,
        idempotency_key: UUID,
        days: int,
        *,
        today: date | None = None,
    ) -> ImportRunResponse:
        if days < 1 or days > 30:
            raise IntegrationPayloadError("Historical import must be 1 to 30 days.")
        range_end = today or datetime.now(timezone.utc).date()
        range_start = range_end - timedelta(days=days - 1)
        row = await self._repository.start_import(
            athlete_id,
            idempotency_key,
            {
                "kind": "historical",
                "range_start": range_start.isoformat(),
                "range_end": range_end.isoformat(),
            },
        )
        if row.get("status") in {"completed", "failed"}:
            return self._import_response(row)
        import_id = UUID(str(row["id"]))
        discovered = imported = skipped = 0
        try:
            credentials = await self._repository.get_credentials(athlete_id)
            token = str(credentials["access_token"])
            timezone_name = str(credentials["timezone"])
            exercises = await self._provider.list_exercises(token)
            eligible: list[JsonObject] = []
            for exercise in exercises:
                try:
                    started = datetime.fromisoformat(
                        str(exercise["start_time"]).replace("Z", "+00:00")
                    ).date()
                except (KeyError, ValueError):
                    discovered += 1
                    skipped += 1
                    continue
                if range_start <= started <= range_end:
                    eligible.append(exercise)
            discovered += len(eligible)
            for exercise in eligible:
                try:
                    created = await self._import_one(
                        athlete_id=athlete_id,
                        import_id=import_id,
                        token=token,
                        timezone_name=timezone_name,
                        exercise=exercise,
                    )
                except IntegrationPayloadError:
                    skipped += 1
                    continue
                if created:
                    imported += 1
                else:
                    skipped += 1
            return self._import_response(
                await self._repository.finish_import(
                    athlete_id,
                    import_id,
                    {
                        "status": "completed",
                        "discovered_count": discovered,
                        "imported_count": imported,
                        "skipped_count": skipped,
                    },
                )
            )
        except (
            PolarProviderError,
            IntegrationRepositoryError,
            IntegrationPayloadError,
            KeyError,
            ValueError,
        ):
            await self._repository.finish_import(
                athlete_id,
                import_id,
                {
                    "status": "failed",
                    "discovered_count": discovered,
                    "imported_count": imported,
                    "skipped_count": skipped,
                    "failure_code": "provider_unavailable",
                },
            )
            raise

    async def receive_webhook(
        self,
        raw_body: bytes,
        signature: str,
        *,
        now: datetime | None = None,
    ) -> tuple[WebhookReceiptResponse, UUID | None]:
        payload = verify_polar_webhook(
            raw_body,
            signature,
            self._webhook_secret,
            now=now or datetime.now(timezone.utc),
        )
        fingerprint = self._fingerprint(payload)
        result = await self._repository.record_webhook(
            webhook_event_key(payload),
            fingerprint,
            payload,
        )
        duplicate = bool(result.get("duplicate", False))
        receipt_id = (
            None if duplicate or payload["event"] == "PING" else UUID(str(result["id"]))
        )
        return (
            WebhookReceiptResponse(status="duplicate" if duplicate else "accepted"),
            receipt_id,
        )

    async def process_webhook(self, receipt_id: UUID) -> None:
        try:
            context = await self._repository.get_webhook_context(receipt_id)
            athlete_id = UUID(str(context["athlete_id"]))
            import_id = UUID(str(context["import_id"]))
            exercise = await self._provider.get_exercise(
                str(context["access_token"]), str(context["entity_id"])
            )
            await self._import_one(
                athlete_id=athlete_id,
                import_id=import_id,
                token=str(context["access_token"]),
                timezone_name=str(context["timezone"]),
                exercise=exercise,
            )
            await self._repository.finish_webhook(receipt_id, status="processed")
        except Exception:
            await self._repository.finish_webhook(
                receipt_id,
                status="failed",
                failure_code="provider_unavailable",
            )
