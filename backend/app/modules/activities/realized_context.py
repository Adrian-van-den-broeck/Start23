"""Private occurrence snapshots and conservative selection for realized v2."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.physiology.joren import VERSION as OBSERVED_VERSION
from app.modules.physiology.joren import ZoneLoad
from app.modules.physiology.realized_v2 import METHOD, VERSION, estimate_realized


def single_planned_zone(segments: list[dict[str, Any]]) -> int | None:
    """Only explicit, uniform zones in the approved snapshot establish a zone."""
    if not segments:
        return None
    zones: set[int] = set()
    for segment in segments:
        zone = segment.get("zone_target")
        if "zone_target" not in segment:
            zone = segment.get("zone")  # historical explicit snapshot spelling
        elif "zone" in segment and segment["zone"] != zone:
            return None
        if type(zone) is not int or not 1 <= zone <= 5:
            return None
        if segment.get("protocol_target") or segment.get("rpe_target"):
            return None
        zones.add(zone)
    return next(iter(zones)) if len(zones) == 1 else None


@dataclass(frozen=True, slots=True, repr=False)
class ApprovedWorkoutBasis:
    plan_id: UUID
    revision_id: UUID
    approved_revision: int
    occurrence_id: UUID
    template_id: UUID
    template_version: int
    planned_load: Decimal | None
    planned_minutes: Decimal | None
    planned_method: str
    planned_version: str
    planned_zone: int | None
    snapshot: Mapping[str, Any]

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "ApprovedWorkoutBasis":
        if data.get("context_version") != VERSION:
            raise ValueError("Unsupported approved-workout context.")
        segments = data["segments"]
        if not isinstance(segments, list) or any(
            not isinstance(segment, dict) for segment in segments
        ):
            raise ValueError("Invalid approved-workout structure.")
        revision = data["approved_revision"]
        template_version = data["template_version"]
        if (
            type(revision) is not int
            or revision < 1
            or (type(template_version) is not int or template_version < 1)
        ):
            raise ValueError("Invalid approved-workout revision.")
        return cls(
            UUID(str(data["plan_id"])),
            UUID(str(data["revision_id"])),
            revision,
            UUID(str(data["occurrence_id"])),
            UUID(str(data["template_id"])),
            template_version,
            Decimal(str(data["planned_tss"]))
            if data.get("planned_tss") is not None
            else None,
            Decimal(str(data["planned_duration_minutes"]))
            if data.get("planned_duration_minutes") is not None
            else None,
            str(data["planned_method"]),
            str(data["planned_version"]),
            single_planned_zone(segments),
            dict(data),
        )


@dataclass(frozen=True, slots=True, repr=False)
class RpeSelection:
    """Independent estimate; the original observation always remains intact."""

    value: Decimal | None
    reason: str | None
    planner_eligible: bool
    provenance: Mapping[str, Any]


def select_rpe_estimate(
    *,
    basis: ApprovedWorkoutBasis | None,
    measurement: ZoneLoad,
    actual_minutes: Decimal | None,
    duration_confirmed: bool,
    rpe: int,
) -> RpeSelection:
    """D03-D06/D09: observations outrank estimates, including partial/all-zero bins.

    Callers exclude explicit bins even if all zero. No power/pace converter exists.
    Changed durations are calculated but withheld from automatic consumers until
    an approved reliability policy exists; no numerical cutoff is invented.
    """
    reason: str | None = None
    if measurement.load is not None:
        reason = "observation_selected"
    elif basis is None:
        reason = "missing_approved_occurrence"
    elif (
        basis.planned_version != OBSERVED_VERSION.value
        or basis.planned_method
        not in {
            "planned_zone_minutes",
            "source_catalog_predefined_tss",
        }
    ):
        reason = "unsupported_planned_method_version"
    elif basis.planned_zone is None:
        reason = "unsupported_structure"
    elif basis.planned_load is None or basis.planned_load == 0:
        reason = "missing_or_zero_planned_basis"
    elif not duration_confirmed:
        reason = "performed_duration_unconfirmed"
    elif actual_minutes is None or basis.planned_minutes is None:
        reason = "missing_duration"
    elif basis.planned_minutes == 0 or actual_minutes == 0:
        reason = "zero_duration"
    if reason is not None:
        return RpeSelection(
            None,
            reason,
            False,
            {
                "version": VERSION,
                "mapping_version": VERSION,
                "rpe": rpe,
                "planned": dict(basis.snapshot) if basis is not None else None,
                "observation_method": measurement.calculation_method,
                "observation_version": measurement.ruleset_version.value,
                "observation_status": measurement.status,
            },
        )
    assert basis is not None and basis.planned_load is not None
    assert basis.planned_minutes is not None and actual_minutes is not None
    assert basis.planned_zone is not None
    estimate = estimate_realized(
        planned_load=basis.planned_load,
        planned_minutes=basis.planned_minutes,
        actual_minutes=actual_minutes,
        planned_zone=basis.planned_zone,
        rpe=rpe,
    )
    unchanged_duration = actual_minutes == basis.planned_minutes
    return RpeSelection(
        estimate.value,
        None if unchanged_duration else "duration_reliability_policy_missing",
        unchanged_duration,
        {
            "version": VERSION,
            "method": METHOD,
            "numeric_policy": estimate.numeric_policy,
            "planned": dict(basis.snapshot),
            "rpe": rpe,
            "mapping_version": VERSION,
            "reported_zone": estimate.reported_zone,
            "planned_zone": basis.planned_zone,
            "zone_provenance": "all_approved_segment_zones_equal",
            "factor": str(estimate.factor),
            "actual_minutes": str(actual_minutes),
            "duration_source": "athlete_confirmed",
            "duration_ratio": str(estimate.duration_ratio),
            "ratio_numerator": str(actual_minutes),
            "ratio_denominator": str(basis.planned_minutes),
        },
    )
