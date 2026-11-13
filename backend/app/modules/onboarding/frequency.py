"""Optional owner preferences; no public authorization or medical evidence."""

from datetime import datetime
from typing import Annotated, Literal, Protocol, cast
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.api.dependencies import get_access_token, get_authenticated_athlete
from app.core.security import AuthenticatedAthlete
from app.modules.physiology.models import Discipline

from .repository import (
    JsonObject,
    OnboardingRepository,
    RepositoryError,
    RepositoryUnavailableError,
)
from .router import _raise_public_error, error_responses, get_onboarding_repository

Count = Annotated[int, Field(strict=True, ge=0, le=24)]


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run: Count | None
    bike: Count | None
    swim: Count | None

    @model_validator(mode="after")
    def technical_envelope(self) -> "Preferences":
        if sum(v or 0 for v in (self.run, self.bike, self.swim)) > 24:
            raise ValueError("At most 24 sessions can be requested together.")
        return self


class PreferenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0)
    operation_id: UUID | None
    preferences: Preferences
    confirmed_at: datetime | None
    recorded_at: datetime | None
    reconfirmation_required: tuple[Discipline, ...]


class PreferenceSave(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(strict=True, ge=0)
    operation_id: UUID
    preferences: Preferences


class InterruptionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    reason: Literal["illness", "training_interruption", "injury"]
    sport: Discipline | None = None

    @model_validator(mode="after")
    def sport_scope(self) -> "InterruptionReport":
        if (self.reason == "injury") != (self.sport is not None):
            raise ValueError("Only injury reports require the affected sport.")
        return self


def public_preference(value: JsonObject) -> PreferenceResponse:
    try:
        return PreferenceResponse.model_validate(value)
    except ValidationError as error:
        raise RepositoryUnavailableError from error


router = APIRouter(tags=["frequency preferences"])
Repository = Annotated[OnboardingRepository, Depends(get_onboarding_repository)]
Token = Annotated[str, Depends(get_access_token)]
Athlete = Annotated[AuthenticatedAthlete, Depends(get_authenticated_athlete)]


class PreferenceRepository(Protocol):
    async def fetch_frequency_preferences(self, access_token: str) -> JsonObject: ...
    async def save_frequency_preferences(
        self, access_token: str, values: JsonObject
    ) -> JsonObject: ...
    async def report_frequency_interruption(
        self, access_token: str, values: JsonObject
    ) -> JsonObject: ...


@router.get(
    "/me/frequency-preferences",
    response_model=PreferenceResponse,
    responses=error_responses,
)
async def get_preferences(
    token: Token, athlete: Athlete, repository: Repository
) -> PreferenceResponse:
    try:
        return public_preference(
            await cast(PreferenceRepository, repository).fetch_frequency_preferences(
                token
            )
        )
    except RepositoryError as error:
        _raise_public_error(error)


@router.put(
    "/me/frequency-preferences",
    response_model=PreferenceResponse,
    responses=error_responses,
)
async def save_preferences(
    request: PreferenceSave, token: Token, athlete: Athlete, repository: Repository
) -> PreferenceResponse:
    try:
        return public_preference(
            await cast(PreferenceRepository, repository).save_frequency_preferences(
                token, request.model_dump(mode="json")
            )
        )
    except RepositoryError as error:
        _raise_public_error(error)


@router.post(
    "/me/frequency-preferences/interruption",
    response_model=PreferenceResponse,
    responses=error_responses,
)
async def report_interruption(
    request: InterruptionReport, token: Token, athlete: Athlete, repository: Repository
) -> PreferenceResponse:
    try:
        return public_preference(
            await cast(PreferenceRepository, repository).report_frequency_interruption(
                token, request.model_dump(mode="json")
            )
        )
    except RepositoryError as error:
        _raise_public_error(error)
