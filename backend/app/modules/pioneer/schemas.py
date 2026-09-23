"""Public Pioneer beta access contracts."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PioneerPublicModel(BaseModel):
    """Strict base model for athlete-facing Pioneer payloads."""

    model_config = ConfigDict(extra="forbid")


class PioneerRedemptionRequest(PioneerPublicModel):
    """One normalized access code submitted by an authenticated athlete."""

    code: str = Field(min_length=8, max_length=32, pattern=r"^[A-Z0-9-]+$")

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class PioneerRedemptionResponse(PioneerPublicModel):
    """Public enrollment state without code or internal identifiers."""

    program: Literal["pioneer"]
    status: Literal["active"]
    redeemed_at: datetime
