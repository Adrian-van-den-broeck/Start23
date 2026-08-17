"""Public, TSS-free contracts for the Phase 9 Polar integration."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IntegrationPublicModel(BaseModel):
    """Reject accidental persistence or credential fields."""

    model_config = ConfigDict(extra="forbid")


class OAuthStartResponse(IntegrationPublicModel):
    provider: Literal["polar"] = "polar"
    authorization_url: str
    expires_at: datetime


class OAuthCallbackResponse(IntegrationPublicModel):
    provider: Literal["polar"] = "polar"
    status: Literal["connected"]


class ProviderConnectionResponse(IntegrationPublicModel):
    id: UUID
    provider: Literal["polar"]
    status: Literal["connected", "disconnected", "revoked", "error"]
    connected_at: datetime
    disconnected_at: datetime | None
    last_import_at: datetime | None


class HistoricalImportRequest(IntegrationPublicModel):
    """Polar exposes only the post-registration rolling 30-day exercise set."""

    days: int = Field(default=30, ge=1, le=30)


class ImportRunResponse(IntegrationPublicModel):
    id: UUID
    provider: Literal["polar"]
    kind: Literal["historical", "webhook"]
    status: Literal["running", "completed", "failed"]
    range_start: date | None
    range_end: date | None
    discovered_count: int = Field(ge=0)
    imported_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    failure_code: str | None
    created_at: datetime
    completed_at: datetime | None


class WebhookReceiptResponse(IntegrationPublicModel):
    status: Literal["accepted", "duplicate"]
