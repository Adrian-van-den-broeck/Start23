"""Validate private v16 evidence before any deterministic planning consumer."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.physiology.weekly_registration import (
    POLICY,
    RegistrationStatus,
    WeeklyCompleteness,
    WorkoutRegistration,
    aggregate_week,
)


class RegistrationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)
    activity_id: str | None
    occurrence_id: str | None
    status: RegistrationStatus
    value: str | None = Field(repr=False)
    method: str
    version: str
    eligible: bool
    calculation_id: str | None


class WeeklyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)
    policy: str
    expected_known: bool
    expected_occurrences: list[str]
    registrations: list[RegistrationEvidence] = Field(default_factory=list, repr=False)


def parse_weekly_registration(data: object) -> WeeklyCompleteness | None:
    if data is None:
        return None  # historical v15 reader; never used by the v16 repository
    evidence = WeeklyEvidence.model_validate(data)
    if evidence.policy != POLICY:
        raise ValueError("Unsupported weekly registration policy.")
    return aggregate_week(
        expected_known=evidence.expected_known,
        expected_occurrences=tuple(evidence.expected_occurrences),
        registrations=tuple(
            WorkoutRegistration(
                activity_id=row.activity_id,
                occurrence_id=row.occurrence_id,
                status=row.status,
                value=Decimal(row.value) if row.value is not None else None,
                method=row.method,
                version=row.version,
                eligible=row.eligible,
                calculation_id=row.calculation_id,
            )
            for row in evidence.registrations
        ),
    )
