"""Approved Phase 13 source fixtures and discrete boundary ownership."""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP
from decimal import Decimal as D

import pytest

from app.modules.physiology.joren import (
    HR_ANCHORS,
    SPORT_MULTIPLIERS,
    SRPE_FACTORS,
    SRPE_FALLBACK_ENABLED,
    SWIM_ANCHORS,
    VERSION,
    ZONE_COEFFICIENTS,
    calibrate,
    is_taper_day,
    srpe_formula,
    starting_baseline,
    threshold_zones,
    zone_load,
)
from app.modules.physiology.models import Discipline


@pytest.mark.parametrize("sport", list(Discipline))
@pytest.mark.parametrize("rpe", range(1, 11))
def test_every_calibration_anchor(sport: Discipline, rpe: int) -> None:
    threshold = D(107 if sport is Discipline.SWIM else 165)
    anchor = (SWIM_ANCHORS if sport is Discipline.SWIM else HR_ANCHORS)[rpe - 1]
    result = calibrate(discipline=sport, observation=threshold * anchor, rpe=rpe)
    assert result.threshold == threshold
    assert result.ruleset_version == VERSION
    assert result.requires_athlete_confirmation


@pytest.mark.parametrize(
    "sport,observed,rpe,expected",
    [
        (Discipline.RUN, "145", 4, 165),
        (Discipline.BIKE, "152", 5, 167),
        (Discipline.RUN, "125", 6, 133),
        (Discipline.SWIM, "120", 3, 107),
        (Discipline.SWIM, "95", 6, 91),
    ],
)
def test_pdf_calibration_examples(
    sport: Discipline, observed: str, rpe: int, expected: int
) -> None:
    assert (
        calibrate(discipline=sport, observation=D(observed), rpe=rpe).threshold
        == expected
    )


def test_hr_rounding_and_exact_boundaries() -> None:
    result = calibrate(discipline=Discipline.RUN, observation=D("144.76"), rpe=4)
    assert result.threshold == 165  # 164.5 rounds half up.
    assert [(z.lower, z.upper) for z in result.zones] == [
        (None, 134),
        (135, 147),
        (148, 157),
        (158, 165),
        (166, None),
    ]


@pytest.mark.parametrize("sport", list(Discipline))
@pytest.mark.parametrize("threshold", [91, 107, 133, 140, 165, 167])
def test_every_integer_and_equality_has_exactly_one_owner(
    sport: Discipline, threshold: int
) -> None:
    zones = threshold_zones(sport, threshold)
    for value in range(0, 400):
        assert sum(z.contains(value) for z in zones) == 1
    for zone in zones:
        for edge in (zone.lower, zone.upper):
            if edge is not None:
                assert zone.contains(edge)


def test_swim_formula_closes_pdf_presentation_gap() -> None:
    # PDF D omits 123 seconds; formula owns 115% rounded CSS in Z2.
    zones = threshold_zones(Discipline.SWIM, 107)
    assert [(z.lower, z.upper) for z in zones] == [
        (124, None),
        (115, 123),
        (110, 114),
        (105, 109),
        (None, 104),
    ]
    # PDF E displays Z3 at 94; 102% * 91 rounds to 93, so Z3 begins 94.
    assert threshold_zones(Discipline.SWIM, 91)[2].lower == 94
    assert zones[4].contains(90) and zones[0].contains(150)


@pytest.mark.parametrize("threshold,warn", [(139, True), (140, False), (141, False)])
def test_suspicious_threshold_is_warning_only(threshold: int, warn: bool) -> None:
    for sport in (Discipline.RUN, Discipline.BIKE):
        result = calibrate(discipline=sport, observation=D(threshold), rpe=8)
        assert bool(result.warning_codes) is warn
        assert len(result.zones) == 5 and result.requires_athlete_confirmation


@pytest.mark.parametrize(
    "sport,coefficients",
    [
        (Discipline.SWIM, ("0.45", "0.72", "1.08", "1.44", "1.80")),
        (Discipline.BIKE, ("0.50", "0.80", "1.20", "1.60", "2.00")),
        (Discipline.RUN, ("0.58", "0.92", "1.38", "1.84", "2.30")),
    ],
)
def test_every_coefficient(sport: Discipline, coefficients: tuple[str, ...]) -> None:
    assert ZONE_COEFFICIENTS[sport] == tuple(map(D, coefficients))
    for i, coefficient in enumerate(coefficients):
        minutes = tuple(D(1 if j == i else 0) for j in range(5))
        measurement = zone_load(
            discipline=sport, total_minutes=D(1), minutes_by_zone=minutes
        )
        assert measurement.load is not None and measurement.load.value == D(coefficient)


def test_partial_observation_never_extrapolates() -> None:
    measured = zone_load(
        discipline=Discipline.BIKE,
        total_minutes=D(60),
        minutes_by_zone=tuple(map(D, (10, 20, 11, 0, 0))),
    )
    assert measured.load is not None and measured.load.value == D("34.20")
    assert measured.valid_minutes == 41 and measured.coverage_ratio == D(41) / D(60)
    assert measured.status == "partial_observed"
    assert "34.20" not in repr(measured)
    assert not SRPE_FALLBACK_ENABLED


def test_distance_only_or_missing_zones_is_unavailable() -> None:
    for duration in (None, D(60)):
        measurement = zone_load(
            discipline=Discipline.SWIM, total_minutes=duration, minutes_by_zone=None
        )
        assert measurement.load is None and measurement.status == "unavailable"


@pytest.mark.parametrize("rpe", range(1, 11))
@pytest.mark.parametrize("sport", list(Discipline))
def test_inactive_srpe_reference_formula(sport: Discipline, rpe: int) -> None:
    assert not SRPE_FALLBACK_ENABLED
    assert (
        srpe_formula(discipline=sport, duration_minutes=D(60), rpe=rpe).value
        == SRPE_FACTORS[rpe - 1] ** 2 * 100 * SPORT_MULTIPLIERS[sport]
    )


def test_srpe_pdf_arithmetic_discrepancy() -> None:
    # PDF prints 64.6, but its own formula is exactly 64.6875 (64.7 half up).
    assert srpe_formula(
        discipline=Discipline.RUN, duration_minutes=D(60), rpe=4
    ).value == D("64.6875")


@pytest.mark.parametrize(
    "minutes,total",
    [((0, 240, 60), "289.7"), ((0, 0, 0), "45.0"), ((150, 360, 180), "658.1")],
)
def test_onboarding_pdf_examples(minutes: tuple[int, ...], total: str) -> None:
    result = starting_baseline(dict(zip(Discipline, map(D, minutes))))
    assert result.total.value == D(total)
    assert result.zero_base is (not any(minutes))
    assert result.by_discipline[Discipline.SWIM].value == D(minutes[0]) / 60 * D(
        "50.625"
    )
    if minutes[0] == 150:
        # PDF uses rounded hourly factors. Exact swim is 126.5625 -> 126.6.
        assert result.by_discipline[Discipline.SWIM].value.quantize(
            D("0.1"), rounding=ROUND_HALF_UP
        ) == D("126.6")


@pytest.mark.parametrize("invalid", ["-1", "NaN", "Infinity", "-Infinity", "10081"])
def test_invalid_onboarding_duration(invalid: str) -> None:
    with pytest.raises(ValueError):
        starting_baseline({Discipline.RUN: D(invalid)})


def test_combined_week_limit() -> None:
    starting_baseline({Discipline.RUN: D(10080)})
    with pytest.raises(ValueError):
        starting_baseline({Discipline.RUN: D(6000), Discipline.BIKE: D(5000)})


def test_exact_taper_on_every_race_weekday() -> None:
    for weekday in range(7):
        race = date(2026, 9, 14) + timedelta(days=weekday)
        for offset in range(-10, 3):
            assert is_taper_day(race + timedelta(days=offset), race) is (
                -7 <= offset <= -1
            )


def test_anchor_tables_match_authoritative_source() -> None:
    assert HR_ANCHORS == tuple(
        map(
            D,
            (
                "0.70",
                "0.78",
                "0.84",
                "0.88",
                "0.91",
                "0.94",
                "0.97",
                "1.00",
                "1.03",
                "1.06",
            ),
        )
    )
    assert SWIM_ANCHORS == tuple(
        map(
            D,
            (
                "1.25",
                "1.18",
                "1.12",
                "1.08",
                "1.06",
                "1.04",
                "1.01",
                "1.00",
                "0.96",
                "0.92",
            ),
        )
    )
    assert SRPE_FACTORS == tuple(
        map(
            D,
            (
                "0.45",
                "0.55",
                "0.65",
                "0.75",
                "0.82",
                "0.88",
                "0.94",
                "1.00",
                "1.05",
                "1.15",
            ),
        )
    )


@pytest.mark.parametrize("sport", list(Discipline))
def test_all_ten_textual_descriptions_are_available(sport: Discipline) -> None:
    from app.modules.physiology.rpe_zones import rpe_description

    descriptions = [rpe_description(sport, rpe) for rpe in range(1, 11)]
    assert len(set(descriptions)) == 10
    assert all(description.strip() for description in descriptions)
