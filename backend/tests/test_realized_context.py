"""D03-D06/D09 evidence hierarchy and exact immutable occurrence fixtures."""

from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from app.modules.activities.realized_context import (
    ApprovedWorkoutBasis,
    select_rpe_estimate,
    single_planned_zone,
)
from app.modules.physiology.joren import zone_load
from app.modules.physiology.models import Discipline
from app.modules.physiology.realized_v2 import VERSION


def planned_context(**changes: Any) -> dict[str, Any]:
    return {
        "context_version": VERSION,
        "plan_id": str(uuid4()),
        "revision_id": str(uuid4()),
        "approved_revision": 2,
        "occurrence_id": str(uuid4()),
        "template_id": str(uuid4()),
        "template_version": 1,
        "planned_tss": "100",
        "planned_duration_minutes": "60",
        "planned_method": "planned_zone_minutes",
        "planned_version": "phase-13-joren-ruleset-1",
        "segments": [{"zone_target": 2}],
        "source_catalog": "original-snapshot",
        **changes,
    }


def selection(**changes: Any) -> Any:
    args: dict[str, Any] = {
        "basis": ApprovedWorkoutBasis.parse(planned_context()),
        "measurement": zone_load(
            discipline=Discipline.BIKE, total_minutes=Decimal(60), minutes_by_zone=None
        ),
        "actual_minutes": Decimal(60),
        "duration_confirmed": True,
        "rpe": 3,
        **changes,
    }
    return select_rpe_estimate(**args)


@pytest.mark.parametrize(
    "segments",
    [
        [],
        [{"zone_target": 1}, {"zone_target": 5}],
        [{"rpe_target": {"target_rpe_min": 3, "target_rpe_max": 4}}],
        [{"protocol_target": {"protocol_id": "warmup"}}],
        [{"zone_target": True}],
    ],
)
def test_no_inferred_planned_zone(segments: list[dict[str, Any]]) -> None:
    assert single_planned_zone(segments) is None
    assert (
        selection(
            basis=ApprovedWorkoutBasis.parse(planned_context(segments=segments))
        ).reason
        == "unsupported_structure"
    )


def test_uniform_multisegment_is_eligible_without_using_expected_rpe() -> None:
    basis = ApprovedWorkoutBasis.parse(
        planned_context(
            segments=[
                {"zone_target": 2, "expected_rpe": 3},
                {"zone_target": 2, "expected_rpe": 4},
            ]
        )
    )
    assert selection(basis=basis).value == Decimal(100)
    assert selection(basis=basis).planner_eligible
    assert selection(basis=basis).provenance["planned"]["occurrence_id"] == str(
        basis.occurrence_id
    )


@pytest.mark.parametrize("bins", [(0, 60, 0, 0, 0), (10, 20, 0, 0, 0)])
def test_complete_and_partial_observations_always_win(bins: tuple[int, ...]) -> None:
    observed = zone_load(
        discipline=Discipline.BIKE,
        total_minutes=Decimal(60),
        minutes_by_zone=tuple(Decimal(value) for value in bins),
    )
    result = selection(measurement=observed, rpe=9)
    assert result.value is None
    assert result.reason == "observation_selected"
    assert observed.load is not None


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"duration_confirmed": False}, "performed_duration_unconfirmed"),
        ({"basis": None}, "missing_approved_occurrence"),
        ({"actual_minutes": None}, "missing_duration"),
        ({"actual_minutes": Decimal(0)}, "zero_duration"),
    ],
)
def test_missing_evidence_is_unavailable(changes: dict[str, Any], reason: str) -> None:
    result = selection(**changes)
    assert result.value is None and not result.planner_eligible
    assert result.reason == reason


@pytest.mark.parametrize(
    "changes", [{"planned_version": "legacy"}, {"planned_method": "power_tss"}]
)
def test_unsupported_basis_is_not_converted(changes: dict[str, Any]) -> None:
    assert (
        selection(basis=ApprovedWorkoutBasis.parse(planned_context(**changes))).value
        is None
    )


def test_overrun_keeps_exact_value_and_blocks_automatic_use() -> None:
    result = selection(actual_minutes=Decimal(90), rpe=1)
    assert result.value == Decimal("131.25")
    assert result.provenance["ratio_numerator"] == "90"
    assert not result.planner_eligible
    assert result.reason == "duration_reliability_policy_missing"


def test_repeated_template_preserves_distinct_occurrences_and_original_load() -> None:
    first = planned_context()
    second = {**first, "occurrence_id": str(uuid4()), "planned_tss": "120"}
    assert selection(basis=ApprovedWorkoutBasis.parse(first)).value == 100
    assert selection(basis=ApprovedWorkoutBasis.parse(second)).value == 120
    assert first["planned_tss"] == "100"


@pytest.mark.parametrize(
    "duration,bins,value",
    [
        ("15", ("15", "0", "0", "0", "0"), "7.50"),
        ("30", ("30", "0", "0", "0", "0"), "15.00"),
        ("30", ("0", "0", "0", "0", "30"), "60.00"),
    ],
)
def test_warmup_skipped_hard_block_and_hard_only_keep_observed_evidence(
    duration: str,
    bins: tuple[str, ...],
    value: str,
) -> None:
    basis = ApprovedWorkoutBasis.parse(
        planned_context(
            planned_tss="75",
            segments=[{"zone_target": 1}, {"zone_target": 5}, {"zone_target": 1}],
        )
    )
    observed = zone_load(
        discipline=Discipline.BIKE,
        total_minutes=Decimal(duration),
        minutes_by_zone=tuple(Decimal(item) for item in bins),
    )
    result = selection(
        basis=basis, measurement=observed, actual_minutes=Decimal(duration)
    )
    assert result.value is None and result.reason == "observation_selected"
    assert observed.load is not None and observed.load.value == Decimal(value)
    assert (
        selection(basis=basis, actual_minutes=Decimal(duration)).reason
        == "unsupported_structure"
    )


def test_original_source_load_version_is_not_silently_relabelled() -> None:
    basis = ApprovedWorkoutBasis.parse(
        planned_context(
            planned_method="source_catalog_predefined_tss",
            planned_version="start23-source-catalog-v0.1",
        )
    )
    assert selection(basis=basis).reason == "unsupported_planned_method_version"
