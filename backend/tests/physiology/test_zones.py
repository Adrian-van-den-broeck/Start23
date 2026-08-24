"""Examples, boundaries, and invalid-input tests for BR-009."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V1,
    PHASE_3_RULESET_V3,
    PhysiologySpecificationNotApproved,
)
from app.modules.physiology.zones import (
    ZONE_MODEL_EVIDENCE_VERSION,
    ZONE_MODEL_VERSION,
    ClinicalRange,
    ZoneBoundary,
    ZoneMetric,
    ZoneMetricKind,
    ZoneProfileSource,
    ZoneReviewReason,
    ZoneScaleDirection,
    ZoneSoftRangeRule,
    ZoneValidationState,
    assess_metric_with_soft_limits,
    calculate_age_220_karvonen_fallback,
    calculate_karvonen_fallback,
    calculate_zone_profile,
    calculate_zone_profiles,
    classify_calculated_zone_speed,
    classify_calculated_zone_value,
    classify_zone_value,
    format_pace_metric,
    metric_direction,
    parse_pace_metric,
    round_zone_boundary,
    validate_calculated_zone_profile,
    validate_zone_boundaries,
    validate_zone_profile,
)


def _ascending_boundaries() -> tuple[ZoneBoundary, ...]:
    return tuple(
        ZoneBoundary(
            zone=zone,
            lower=Decimal((zone.value - 1) * 100),
            upper=Decimal(zone.value * 100),
        )
        for zone in TrainingZone
    )


def _descending_pace_boundaries() -> tuple[ZoneBoundary, ...]:
    values = (
        (TrainingZone.ZONE_1, "400", "500"),
        (TrainingZone.ZONE_2, "350", "400"),
        (TrainingZone.ZONE_3, "300", "350"),
        (TrainingZone.ZONE_4, "250", "300"),
        (TrainingZone.ZONE_5, "200", "250"),
    )
    return tuple(
        ZoneBoundary(zone=zone, lower=Decimal(lower), upper=Decimal(upper))
        for zone, lower, upper in values
    )


def _bike_ftp(value: str) -> ZoneMetric:
    return ZoneMetric(
        discipline=Discipline.BIKE,
        kind=ZoneMetricKind.BIKE_FTP_WATTS,
        value=Decimal(value),
    )


@pytest.mark.parametrize(
    ("discipline", "kind"),
    [
        (Discipline.SWIM, ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M),
        (Discipline.BIKE, ZoneMetricKind.BIKE_FTP_WATTS),
        (Discipline.BIKE, ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM),
        (Discipline.RUN, ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM),
        (Discipline.RUN, ZoneMetricKind.RUN_LTHR_BPM),
    ],
)
def test_each_zone_metric_accepts_its_canonical_discipline(
    discipline: Discipline,
    kind: ZoneMetricKind,
) -> None:
    metric = ZoneMetric(
        discipline=discipline,
        kind=kind,
        value=Decimal("250"),
    )

    assert metric.discipline is discipline
    assert metric.kind is kind


def test_zone_metric_rejects_a_noncanonical_discipline() -> None:
    with pytest.raises(ValueError, match="does not belong"):
        ZoneMetric(
            discipline=Discipline.RUN,
            kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=Decimal("250"),
        )


@pytest.mark.parametrize("value", [Decimal("0"), Decimal("-1"), Decimal("NaN")])
def test_zone_metric_requires_positive_finite_value(value: Decimal) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        ZoneMetric(
            discipline=Discipline.BIKE,
            kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=value,
        )


def test_ruleset_v1_remains_closed_while_v3_is_the_active_zone_ruleset() -> None:
    with pytest.raises(PhysiologySpecificationNotApproved):
        assess_metric_with_soft_limits(
            _bike_ftp("250"),
            {},
            specification=PHASE_3_RULESET_V1,
        )

    result = assess_metric_with_soft_limits(_bike_ftp("250"), {})
    assert result.ruleset_version == PHASE_3_RULESET_V3.version


def test_zone_profile_sources_keep_manual_test_and_fallback_distinct() -> None:
    assert set(ZoneProfileSource) == {
        ZoneProfileSource.ATHLETE_ENTERED,
        ZoneProfileSource.FIELD_TEST,
        ZoneProfileSource.WEARABLE_IMPORT,
        ZoneProfileSource.ESTIMATED,
    }


def test_missing_soft_range_accepts_but_requires_review() -> None:
    result = assess_metric_with_soft_limits(_bike_ftp("250"), {})

    assert result.requires_review is True
    assert result.reason is ZoneReviewReason.SOFT_RANGE_NOT_CONFIGURED


def test_soft_range_endpoints_are_inclusive() -> None:
    limits = {
        ZoneMetricKind.BIKE_FTP_WATTS: ZoneSoftRangeRule(
            metric=ZoneMetricKind.BIKE_FTP_WATTS,
            discipline=Discipline.BIKE,
            unit="watts",
            limits=ClinicalRange(minimum=Decimal("100"), maximum=Decimal("500")),
            applicability="adult recreational cyclists",
            evidence_reference="evidence:test",
            reviewer="qualified-reviewer",
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 12, 31),
            ruleset_version=PHASE_3_RULESET_V3.version,
        )
    }

    for value in ("100", "500"):
        result = assess_metric_with_soft_limits(
            _bike_ftp(value), limits, as_of=date(2026, 8, 11)
        )
        assert result.requires_review is False
        assert result.reason is ZoneReviewReason.WITHIN_SOFT_RANGE


def test_outside_soft_range_requires_review_instead_of_rejection() -> None:
    limits = {
        ZoneMetricKind.BIKE_FTP_WATTS: ZoneSoftRangeRule(
            metric=ZoneMetricKind.BIKE_FTP_WATTS,
            discipline=Discipline.BIKE,
            unit="watts",
            limits=ClinicalRange(minimum=Decimal("100"), maximum=Decimal("500")),
            applicability="adult recreational cyclists",
            evidence_reference="evidence:test",
            reviewer="qualified-reviewer",
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 12, 31),
            ruleset_version=PHASE_3_RULESET_V3.version,
        )
    }

    result = assess_metric_with_soft_limits(
        _bike_ftp("2500"), limits, as_of=date(2026, 8, 11)
    )

    assert result.requires_review is True
    assert result.reason is ZoneReviewReason.OUTSIDE_SOFT_RANGE


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    [
        (Decimal("0"), Decimal("500")),
        (Decimal("500"), Decimal("100")),
        (Decimal("NaN"), Decimal("500")),
    ],
)
def test_clinical_range_requires_positive_ordered_finite_values(
    minimum: Decimal,
    maximum: Decimal,
) -> None:
    with pytest.raises(ValueError, match="positive and ordered"):
        ClinicalRange(minimum=minimum, maximum=maximum)


@pytest.mark.parametrize(
    ("kind", "text", "seconds", "formatted"),
    [
        (
            ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            "4:30",
            Decimal("270"),
            "4:30",
        ),
        (
            ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M,
            "1:42",
            Decimal("102"),
            "1:42",
        ),
    ],
)
def test_pace_formats_round_trip_to_canonical_seconds(
    kind: ZoneMetricKind,
    text: str,
    seconds: Decimal,
    formatted: str,
) -> None:
    metric = parse_pace_metric(kind=kind, text=text)

    assert metric.value == seconds
    assert format_pace_metric(metric) == formatted


@pytest.mark.parametrize("text", ["270", "4:5", "4:60", " 4:30", "4:30 "])
def test_pace_parser_rejects_noncanonical_formats(text: str) -> None:
    with pytest.raises(ValueError, match="minutes:seconds"):
        parse_pace_metric(
            kind=ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            text=text,
        )


def test_pace_parser_rejects_non_pace_metrics() -> None:
    with pytest.raises(ValueError, match="Only swim CSS"):
        parse_pace_metric(
            kind=ZoneMetricKind.BIKE_FTP_WATTS,
            text="4:30",
        )


def test_pace_metric_rejects_unapproved_fractional_seconds() -> None:
    with pytest.raises(ValueError, match="whole seconds"):
        ZoneMetric(
            discipline=Discipline.RUN,
            kind=ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            value=Decimal("270.5"),
        )


def test_metric_directions_are_explicit_for_inverse_pace_scales() -> None:
    assert (
        metric_direction(ZoneMetricKind.BIKE_FTP_WATTS) is ZoneScaleDirection.ASCENDING
    )
    assert (
        metric_direction(ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM)
        is ZoneScaleDirection.DESCENDING
    )


def test_ascending_boundary_equality_belongs_to_higher_zone() -> None:
    boundaries = _ascending_boundaries()

    assert (
        classify_zone_value(
            metric_kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=Decimal("200"),
            boundaries=boundaries,
        )
        is TrainingZone.ZONE_3
    )
    assert (
        classify_zone_value(
            metric_kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=Decimal("500"),
            boundaries=boundaries,
        )
        is TrainingZone.ZONE_5
    )


@pytest.mark.parametrize("value", [Decimal("-1"), Decimal("NaN")])
def test_zone_classification_rejects_invalid_values(value: Decimal) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        classify_zone_value(
            metric_kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=value,
            boundaries=_ascending_boundaries(),
        )


def test_zone_classification_rejects_value_outside_profile() -> None:
    with pytest.raises(ValueError, match="outside"):
        classify_zone_value(
            metric_kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=Decimal("501"),
            boundaries=_ascending_boundaries(),
        )


def test_descending_pace_profile_is_contiguous_and_classifiable() -> None:
    boundaries = _descending_pace_boundaries()

    validate_zone_profile(
        metric_kind=ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
        boundaries=boundaries,
    )
    assert (
        classify_zone_value(
            metric_kind=ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            value=Decimal("350"),
            boundaries=boundaries,
        )
        is TrainingZone.ZONE_3
    )
    assert (
        classify_zone_value(
            metric_kind=ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            value=Decimal("400"),
            boundaries=boundaries,
        )
        is TrainingZone.ZONE_2
    )


def test_pace_zone_boundaries_require_whole_seconds() -> None:
    boundaries = list(_descending_pace_boundaries())
    boundaries[0] = ZoneBoundary(
        zone=TrainingZone.ZONE_1,
        lower=Decimal("400.5"),
        upper=Decimal("500"),
    )

    with pytest.raises(ValueError, match="whole seconds"):
        validate_zone_profile(
            metric_kind=ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            boundaries=tuple(boundaries),
        )


def test_zone_boundaries_require_all_five_ordered_zones() -> None:
    with pytest.raises(ValueError, match="Zones 1 through 5"):
        validate_zone_boundaries(
            _ascending_boundaries()[:-1],
            direction=ZoneScaleDirection.ASCENDING,
        )


@pytest.mark.parametrize(
    "replacement",
    [
        ZoneBoundary(TrainingZone.ZONE_2, Decimal("101"), Decimal("200")),
        ZoneBoundary(TrainingZone.ZONE_2, Decimal("99"), Decimal("200")),
    ],
)
def test_ascending_zone_boundaries_reject_gaps_and_overlaps(
    replacement: ZoneBoundary,
) -> None:
    boundaries = list(_ascending_boundaries())
    boundaries[1] = replacement

    with pytest.raises(ValueError, match="must be contiguous"):
        validate_zone_boundaries(
            tuple(boundaries),
            direction=ZoneScaleDirection.ASCENDING,
        )


def test_zone_boundary_requires_typed_zone() -> None:
    with pytest.raises(ValueError, match="TrainingZone"):
        ZoneBoundary(
            zone=1,  # type: ignore[arg-type]
            lower=Decimal("0"),
            upper=Decimal("100"),
        )


@pytest.mark.parametrize(
    ("lower", "upper"),
    [
        (Decimal("-1"), Decimal("100")),
        (Decimal("100"), Decimal("100")),
        (Decimal("NaN"), Decimal("100")),
    ],
)
def test_zone_boundary_requires_finite_increasing_values(
    lower: Decimal,
    upper: Decimal,
) -> None:
    with pytest.raises(ValueError, match="finite and increasing"):
        ZoneBoundary(
            zone=TrainingZone.ZONE_1,
            lower=lower,
            upper=upper,
        )


def test_karvonen_fallback_uses_tanaka_hrr_and_remains_unvalidated() -> None:
    result = calculate_karvonen_fallback(
        age_years=40,
        resting_heart_rate_bpm=Decimal("60"),
    )

    assert result.ruleset_version == PHASE_3_RULESET_V3.version
    assert result.estimated_max_heart_rate_bpm == Decimal("180.0")
    assert result.source is ZoneProfileSource.ESTIMATED
    assert result.validation_state is ZoneValidationState.UNREVIEWED
    assert result.requires_confirmation is True
    assert [(boundary.lower, boundary.upper) for boundary in result.boundaries] == [
        (Decimal("120.00"), Decimal("132.00")),
        (Decimal("132.00"), Decimal("144.00")),
        (Decimal("144.00"), Decimal("156.00")),
        (Decimal("156.00"), Decimal("168.00")),
        (Decimal("168.00"), Decimal("180.00")),
    ]


def test_optional_220_age_karvonen_uses_resting_hr_and_remains_unreviewed() -> None:
    result = calculate_age_220_karvonen_fallback(
        age_years=30,
        resting_heart_rate_bpm=Decimal("50"),
    )

    assert result.ruleset_version.value == "start23-age-220-karvonen-v1"
    assert result.estimated_max_heart_rate_bpm == Decimal("190")
    assert result.source is ZoneProfileSource.ESTIMATED
    assert result.validation_state is ZoneValidationState.UNREVIEWED
    assert result.requires_confirmation is True
    assert [(boundary.lower, boundary.upper) for boundary in result.boundaries] == [
        (Decimal("120.00"), Decimal("134.00")),
        (Decimal("134.00"), Decimal("148.00")),
        (Decimal("148.00"), Decimal("162.00")),
        (Decimal("162.00"), Decimal("176.00")),
        (Decimal("176.00"), Decimal("190.00")),
    ]


@pytest.mark.parametrize(
    ("age", "resting"),
    [
        (0, Decimal("60")),
        (-1, Decimal("60")),
        (40, Decimal("0")),
        (40, Decimal("180")),
        (40, Decimal("NaN")),
    ],
)
def test_karvonen_fallback_rejects_invalid_biometrics(
    age: int,
    resting: Decimal,
) -> None:
    with pytest.raises(ValueError):
        calculate_karvonen_fallback(
            age_years=age,
            resting_heart_rate_bpm=resting,
        )


@pytest.mark.parametrize(
    ("kind", "threshold", "expected_edges"),
    [
        (
            ZoneMetricKind.BIKE_FTP_WATTS,
            "200",
            ("112", "152", "182", "212"),
        ),
        (
            ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM,
            "200",
            ("170", "180", "190", "206"),
        ),
        (
            ZoneMetricKind.RUN_LTHR_BPM,
            "200",
            ("170", "180", "190", "206"),
        ),
        (
            ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            "300",
            ("385", "341", "316", "294"),
        ),
        (
            ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M,
            "100",
            ("128", "114", "105", "98"),
        ),
    ],
)
def test_zone_model_v1_calculates_each_metric_with_open_outer_edges(
    kind: ZoneMetricKind,
    threshold: str,
    expected_edges: tuple[str, str, str, str],
) -> None:
    discipline = {
        ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M: Discipline.SWIM,
        ZoneMetricKind.BIKE_FTP_WATTS: Discipline.BIKE,
        ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM: Discipline.BIKE,
        ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM: Discipline.RUN,
        ZoneMetricKind.RUN_LTHR_BPM: Discipline.RUN,
    }[kind]
    profile = calculate_zone_profile(
        ZoneMetric(discipline=discipline, kind=kind, value=Decimal(threshold))
    )

    assert profile.zone_model_version == ZONE_MODEL_VERSION
    assert ZONE_MODEL_EVIDENCE_VERSION.endswith("v1.0")
    if metric_direction(kind) is ZoneScaleDirection.ASCENDING:
        assert profile.boundaries[0].lower == 0
        assert profile.boundaries[-1].upper is None
        assert (
            tuple(str(boundary.upper) for boundary in profile.boundaries[:-1])
            == expected_edges
        )
    else:
        assert profile.boundaries[0].upper is None
        assert profile.boundaries[-1].lower == 0
        assert (
            tuple(str(boundary.lower) for boundary in profile.boundaries[:-1])
            == expected_edges
        )
    validate_calculated_zone_profile(profile)


def test_zone_model_rounds_half_up_once() -> None:
    assert round_zone_boundary(Decimal("100.49")) == Decimal("100")
    assert round_zone_boundary(Decimal("100.50")) == Decimal("101")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("111", TrainingZone.ZONE_1),
        ("112", TrainingZone.ZONE_2),
        ("151", TrainingZone.ZONE_2),
        ("152", TrainingZone.ZONE_3),
        ("181", TrainingZone.ZONE_3),
        ("182", TrainingZone.ZONE_4),
        ("211", TrainingZone.ZONE_4),
        ("212", TrainingZone.ZONE_5),
        ("500", TrainingZone.ZONE_5),
    ],
)
def test_generated_power_boundaries_assign_equality_to_higher_intensity(
    value: str,
    expected: TrainingZone,
) -> None:
    profile = calculate_zone_profile(_bike_ftp("200"))

    assert (
        classify_calculated_zone_value(profile=profile, value=Decimal(value)).zone
        is expected
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("386", TrainingZone.ZONE_1),
        ("385", TrainingZone.ZONE_2),
        ("342", TrainingZone.ZONE_2),
        ("341", TrainingZone.ZONE_3),
        ("317", TrainingZone.ZONE_3),
        ("316", TrainingZone.ZONE_4),
        ("295", TrainingZone.ZONE_4),
        ("294", TrainingZone.ZONE_5),
        ("200", TrainingZone.ZONE_5),
    ],
)
def test_generated_pace_boundaries_use_speed_direction_and_boundary_ownership(
    value: str,
    expected: TrainingZone,
) -> None:
    profile = calculate_zone_profile(
        ZoneMetric(
            discipline=Discipline.RUN,
            kind=ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            value=Decimal("300"),
        )
    )

    result = classify_calculated_zone_value(profile=profile, value=Decimal(value))

    assert result.zone is expected
    assert result.relative_intensity == Decimal("300") / Decimal(value)


@pytest.mark.parametrize(
    ("metric", "cutoffs"),
    [
        (_bike_ftp("200"), (112, 152, 182, 212)),
        (
            ZoneMetric(
                Discipline.BIKE,
                ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM,
                Decimal("200"),
            ),
            (170, 180, 190, 206),
        ),
        (
            ZoneMetric(
                Discipline.RUN,
                ZoneMetricKind.RUN_LTHR_BPM,
                Decimal("200"),
            ),
            (170, 180, 190, 206),
        ),
        (
            ZoneMetric(
                Discipline.RUN,
                ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
                Decimal("300"),
            ),
            (385, 341, 316, 294),
        ),
        (
            ZoneMetric(
                Discipline.SWIM,
                ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M,
                Decimal("100"),
            ),
            (128, 114, 105, 98),
        ),
    ],
)
def test_every_metric_owns_each_boundary_and_adjacent_unit(
    metric: ZoneMetric,
    cutoffs: tuple[int, int, int, int],
) -> None:
    profile = calculate_zone_profile(metric)
    ascending = metric_direction(metric.kind) is ZoneScaleDirection.ASCENDING

    for index, cutoff in enumerate(cutoffs):
        lower_intensity_value = cutoff - 1 if ascending else cutoff + 1
        higher_intensity_value = cutoff + 1 if ascending else cutoff - 1
        lower_zone = TrainingZone(index + 1)
        higher_zone = TrainingZone(index + 2)

        assert (
            classify_calculated_zone_value(
                profile=profile,
                value=Decimal(lower_intensity_value),
            ).zone
            is lower_zone
        )
        assert (
            classify_calculated_zone_value(
                profile=profile,
                value=Decimal(cutoff),
            ).zone
            is higher_zone
        )
        assert (
            classify_calculated_zone_value(
                profile=profile,
                value=Decimal(higher_intensity_value),
            ).zone
            is higher_zone
        )


@pytest.mark.parametrize(
    ("kind", "discipline", "threshold", "distance", "values"),
    [
        (
            ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
            Discipline.RUN,
            "300",
            "1000",
            (386, 385, 342, 341, 317, 316, 295, 294, 200),
        ),
        (
            ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M,
            Discipline.SWIM,
            "100",
            "100",
            (129, 128, 115, 114, 106, 105, 99, 98, 80),
        ),
    ],
)
def test_speed_and_pace_classification_are_identical(
    kind: ZoneMetricKind,
    discipline: Discipline,
    threshold: str,
    distance: str,
    values: tuple[int, ...],
) -> None:
    profile = calculate_zone_profile(ZoneMetric(discipline, kind, Decimal(threshold)))

    for pace_value in values:
        pace_result = classify_calculated_zone_value(
            profile=profile,
            value=Decimal(pace_value),
        )
        speed_result = classify_calculated_zone_speed(
            profile=profile,
            speed_meters_per_second=Decimal(distance) / Decimal(pace_value),
        )

        assert speed_result == pace_result


def test_power_above_120_percent_is_supramaximal_but_stays_zone_5() -> None:
    profile = calculate_zone_profile(_bike_ftp("200"))

    at_cap = classify_calculated_zone_value(
        profile=profile,
        value=Decimal("240"),
    )
    above_cap = classify_calculated_zone_value(
        profile=profile,
        value=Decimal("241"),
    )

    assert at_cap.zone is TrainingZone.ZONE_5
    assert at_cap.supramaximal is False
    assert above_cap.zone is TrainingZone.ZONE_5
    assert above_cap.supramaximal is True


def test_multi_metric_profile_keeps_primary_execution_metric_first() -> None:
    profiles = calculate_zone_profiles(
        (
            ZoneMetric(
                Discipline.RUN,
                ZoneMetricKind.RUN_LTHR_BPM,
                Decimal("172"),
            ),
            ZoneMetric(
                Discipline.RUN,
                ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
                Decimal("290"),
            ),
        )
    )

    assert [profile.metric.kind for profile in profiles] == [
        ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
        ZoneMetricKind.RUN_LTHR_BPM,
    ]
    assert [profile.is_primary for profile in profiles] == [True, False]


def test_zone_model_rejects_missing_invalid_and_obsolete_inputs() -> None:
    with pytest.raises(ValueError, match="required"):
        calculate_zone_profile(None)
    with pytest.raises(ValueError, match="not active"):
        calculate_zone_profile(
            _bike_ftp("200"),
            zone_model_version=type(ZONE_MODEL_VERSION)("start23-zone-model-0.9"),
        )
    with pytest.raises(ValueError, match="distinct"):
        calculate_zone_profile(_bike_ftp("1"))


def test_zone_model_accepts_extreme_structurally_valid_threshold() -> None:
    profile = calculate_zone_profile(_bike_ftp("100000000000000000000"))

    assert profile.boundaries[-1].lower == Decimal("106000000000000000000")
