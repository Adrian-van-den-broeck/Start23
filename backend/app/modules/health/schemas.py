"""Public health-check schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Public application health response."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Public application readiness response."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ready"] = "ready"
    service: str
    version: str
    environment: str
