"""Application service for Pioneer beta access."""

from hashlib import sha256
from uuid import UUID

from .repository import PioneerRepository
from .schemas import PioneerRedemptionRequest, PioneerRedemptionResponse


class PioneerDomainError(Exception):
    """A deterministic public redemption refusal."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PioneerService:
    def __init__(self, repository: PioneerRepository) -> None:
        self._repository = repository

    async def redeem(
        self,
        athlete_id: UUID,
        idempotency_key: UUID,
        request: PioneerRedemptionRequest,
    ) -> PioneerRedemptionResponse:
        code_digest = sha256(request.code.encode("ascii")).hexdigest()
        request_fingerprint = sha256(
            f"pioneer-redemption-v1:{request.code}".encode("ascii")
        ).hexdigest()
        result = await self._repository.redeem(
            athlete_id,
            code_digest,
            idempotency_key,
            request_fingerprint,
        )
        result_status = str(result.get("status", ""))
        if result_status == "success":
            redemption = result.get("redemption")
            if isinstance(redemption, dict):
                return PioneerRedemptionResponse.model_validate(
                    {
                        field: redemption[field]
                        for field in PioneerRedemptionResponse.model_fields
                        if field in redemption
                    }
                )
            raise PioneerDomainError(
                "pioneer_response_invalid",
                "The Pioneer redemption result was invalid.",
            )
        errors = {
            "invalid": (
                "pioneer_code_invalid",
                "The Pioneer access code is invalid.",
            ),
            "expired": (
                "pioneer_code_expired",
                "The Pioneer access code has expired.",
            ),
            "revoked": (
                "pioneer_code_revoked",
                "The Pioneer access code has been revoked.",
            ),
            "unauthorized": (
                "pioneer_code_unauthorized",
                "This Pioneer access code is not assigned to this athlete.",
            ),
            "reused": (
                "pioneer_code_reused",
                "The Pioneer access code has already been redeemed.",
            ),
            "idempotency_conflict": (
                "pioneer_idempotency_conflict",
                "This idempotency key was used for another redemption request.",
            ),
            "rate_limited": (
                "pioneer_rate_limited",
                "Too many access-code attempts. Try again later.",
            ),
        }
        code, message = errors.get(
            result_status,
            (
                "pioneer_response_invalid",
                "The Pioneer redemption result was invalid.",
            ),
        )
        raise PioneerDomainError(code, message)

    async def current(
        self,
        access_token: str,
    ) -> PioneerRedemptionResponse | None:
        row = await self._repository.fetch_current(access_token)
        return PioneerRedemptionResponse.model_validate(row) if row else None
