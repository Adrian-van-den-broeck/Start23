"""Public authenticated identity schemas."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MeResponse(BaseModel):
    """Public representation of the authenticated user."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    role: Literal["authenticated"]
