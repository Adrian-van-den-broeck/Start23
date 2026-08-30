"""Deterministic field-test and Week-1 calibration tests."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.calibration.domain import (
    CALIBRATION_RULESET_VERSION,
    PROTOCOLS,
    CalibrationObservation,
    DataQuality,
    EvaluationStatus,
    NumericZoneVisibility,
    SetupRoute,
    SteadyExecution,
    SwimRepetition,
    ThresholdStatus,
    ZoneStatus,
    evaluate_protocol,
    numeric_zone_visibility,
    pace_seconds_per_100m,
    protocols_for_discipline,
    validate_test_schedule,
)
from app.modules.calibration.domain import TestSchedulingMode as SchedulingMode
from app.modules.physiology.models import Discipline
from app.modules.physiology.zones import ZoneMetricKind


def test_date_only_test_schedule_accepts_today_and_rejects_past() -> None:
    today = date(2026, 8, 26)

    decision = validate_test_schedule(
        protocol_id="start23_run_threshold_30min_v1",
        discipline=Discipline.RUN,
        scheduling_mode=SchedulingMode.STANDALONE,
        scheduled_date=today,
        athlete_today=today,
    )

    assert decision.scheduled_date == today
    with pytest.raises(ValueError, match="cannot be in the past"):
        validate_test_schedule(
            protocol_id="start23_run_threshold_30min_v1",
            discipline=Discipline.RUN,
            scheduling_mode=SchedulingMode.STANDALONE,
            scheduled_date=date(2026, 8, 25),
            athlete_today=today,
        )


def test_integrated_swim_test_fails_closed_without_planned_duration() -> None:
    with pytest.raises(ValueError, match="no approved planned-duration"):
        validate_test_schedule(
            protocol_id="start23_swim_css_400_200_v1",
            discipline=Discipline.SWIM,
            scheduling_mode=SchedulingMode.WEEKLY_PLAN,
            scheduled_date=date(2026, 8, 27),
            athlete_today=date(2026, 8, 26),
            plan_week_start=date(2026, 8, 24),
        )


def test_calibration_week_hides_numbers_until_reviewed_week_2_gate() -> None:
    assert (
        numeric_zone_visibility(
            setup_route=SetupRoute.CALIBRATION_WEEK,
            has_active_profile=False,
            week_2_evaluation_completed=False,
            has_pending_complete_proposal=False,
        )
        is NumericZoneVisibility.WEEK_2_EVALUATION_PENDING
    )
    assert (
        numeric_zone_visibility(
            setup_route=SetupRoute.CALIBRATION_WEEK,
            has_active_profile=False,
            week_2_evaluation_completed=True,
            has_pending_complete_proposal=True,
        )
        is NumericZoneVisibility.PROPOSAL_CONFIRMATION_PENDING
    )


def _observation(
    protocol_id: str,
    discipline: Discipline,
    segment_id: str,
    **overrides: object,
) -> CalibrationObservation:
    values: dict[str, object] = {
        "protocol_id": protocol_id,
        "discipline": discipline,
        "segment_id": segment_id,
        "completed": True,
        "interrupted": False,
        "quality_status": DataQuality.SUFFICIENT,
    }
    values.update(overrides)
    return CalibrationObservation(**values)  # type: ignore[arg-type]


def _run_test() -> tuple[CalibrationObservation, ...]:
    protocol = "start23_run_threshold_30min_v1"
    return (
        _observation(protocol, Discipline.RUN, "warmup", duration_seconds=900),
        _observation(protocol, Discipline.RUN, "strides", duration_seconds=300),
        _observation(
            protocol,
            Discipline.RUN,
            "test_30min",
            duration_seconds=1800,
            reported_block_rpe=9,
            average_pace_seconds_per_km=Decimal("290"),
            average_heart_rate_last_20min_bpm=Decimal("171.6"),
            data_completeness=Decimal("0.98"),
            stable_segment=True,
        ),
        _observation(
            protocol,
            Discipline.RUN,
            "cooldown",
            duration_seconds=600,
            reported_session_rpe=8,
        ),
    )


def _bike_ftp_test() -> tuple[CalibrationObservation, ...]:
    protocol = "start23_bike_ftp_30min_v1"
    return (
        _observation(protocol, Discipline.BIKE, "warmup", duration_seconds=1200),
        _observation(
            protocol,
            Discipline.BIKE,
            "test_30min",
            duration_seconds=1800,
            reported_block_rpe=9,
            average_power_last_20min_watts=Decimal("251"),
            data_completeness=Decimal("0.99"),
            stable_segment=True,
            power_source_calibrated=True,
        ),
        _observation(
            protocol,
            Discipline.BIKE,
            "cooldown",
            duration_seconds=600,
            reported_session_rpe=9,
        ),
    )


def _bike_hr_test() -> tuple[CalibrationObservation, ...]:
    protocol = "start23_bike_fthr_20min_v1"
    return (
        _observation(protocol, Discipline.BIKE, "warmup", duration_seconds=1200),
        _observation(
            protocol,
            Discipline.BIKE,
            "test_20min",
            duration_seconds=1200,
            reported_block_rpe=8,
            average_heart_rate_bpm=Decimal("169.5"),
            data_completeness=Decimal("0.95"),
        ),
        _observation(
            protocol,
            Discipline.BIKE,
            "cooldown",
            duration_seconds=600,
            reported_session_rpe=8,
        ),
    )


def _swim_css_test(
    *,
    pool_length: int = 25,
    time_400: str = "400",
    time_200: str = "180",
) -> tuple[CalibrationObservation, ...]:
    protocol = "start23_swim_css_400_200_v1"
    return (
        _observation(
            protocol,
            Discipline.SWIM,
            "warmup",
            distance_meters=600,
            pool_length_meters=pool_length,
        ),
        _observation(
            protocol,
            Discipline.SWIM,
            "tt_400m",
            distance_meters=400,
            elapsed_time_seconds=Decimal(time_400),
            pool_length_meters=pool_length,
            stroke="freestyle",
            equipment="none",
            reported_block_rpe=10,
        ),
        _observation(
            protocol,
            Discipline.SWIM,
            "active_recovery",
            duration_seconds=420,
        ),
        _observation(
            protocol,
            Discipline.SWIM,
            "tt_200m",
            distance_meters=200,
            elapsed_time_seconds=Decimal(time_200),
            pool_length_meters=pool_length,
            stroke="freestyle",
            equipment="none",
            reported_block_rpe=10,
        ),
        _observation(
            protocol,
            Discipline.SWIM,
            "cooldown",
            distance_meters=200,
            reported_session_rpe=9,
        ),
    )


def test_protocol_registry_contains_all_approved_fixture_protocols() -> None:
    assert set(PROTOCOLS) == {
        "start23_run_threshold_30min_v1",
        "start23_bike_ftp_30min_v1",
        "start23_bike_fthr_20min_v1",
        "start23_swim_css_400_200_v1",
        "start23_week1_run_calibration_v1",
        "start23_week1_bike_calibration_v1",
        "start23_week1_swim_calibration_v1",
    }
    assert len(protocols_for_discipline(Discipline.SWIM)) == 2
    assert len(protocols_for_discipline(Discipline.BIKE)) == 3
    assert len(protocols_for_discipline(Discipline.RUN)) == 2


def test_valid_run_test_estimates_thresholds_and_pending_zone_profiles() -> None:
    result = evaluate_protocol(
        protocol_id="start23_run_threshold_30min_v1",
        observations=_run_test(),
    )

    assert result.ruleset_version == CALIBRATION_RULESET_VERSION
    assert result.status is EvaluationStatus.THRESHOLD_ESTIMATED
    assert result.threshold_status is ThresholdStatus.ESTIMATED
    assert result.zone_status is ZoneStatus.PENDING_ATHLETE_CONFIRMATION
    assert result.requires_athlete_confirmation is True
    assert [(value.metric_kind, value.value) for value in result.thresholds] == [
        (ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM, Decimal("290")),
        (ZoneMetricKind.RUN_LTHR_BPM, Decimal("172")),
    ]
    assert result.reason_codes == ("zone_profile_pending_athlete_confirmation",)
    assert [profile.metric.kind for profile in result.zone_profiles] == [
        ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
        ZoneMetricKind.RUN_LTHR_BPM,
    ]
    assert result.zone_profiles[0].is_primary is True
    assert result.zone_profiles[0].boundaries[0].upper is None


def test_run_lthr_is_never_extrapolated_from_easy_pace() -> None:
    protocol = "start23_week1_run_calibration_v1"
    observations = (
        _observation(protocol, Discipline.RUN, "warmup", duration_seconds=600),
        _observation(
            protocol,
            Discipline.RUN,
            "comfortable_20min",
            duration_seconds=1200,
            reported_block_rpe=4,
            steady_execution=SteadyExecution.YES,
            average_heart_rate_bpm=Decimal("148"),
            average_pace_seconds_per_km=Decimal("365"),
            stable_segment=True,
        ),
        _observation(
            protocol,
            Discipline.RUN,
            "cooldown",
            duration_seconds=600,
            reported_session_rpe=5,
        ),
    )

    result = evaluate_protocol(protocol_id=protocol, observations=observations)

    assert result.status is EvaluationStatus.PROVISIONALLY_CALIBRATED
    assert result.threshold_status is ThresholdStatus.UNKNOWN
    assert result.thresholds == ()
    assert result.reason_codes == (
        "threshold_not_permitted_from_submaximal_calibration",
    )


def test_calibration_without_sensor_metrics_stays_rpe_only() -> None:
    protocol = "start23_week1_bike_calibration_v1"
    observations = (
        _observation(protocol, Discipline.BIKE, "warmup", duration_seconds=900),
        _observation(
            protocol,
            Discipline.BIKE,
            "comfortable_20min",
            duration_seconds=1200,
            reported_block_rpe=4,
            steady_execution=SteadyExecution.MOSTLY,
        ),
        _observation(
            protocol,
            Discipline.BIKE,
            "cooldown",
            duration_seconds=600,
            reported_session_rpe=4,
        ),
    )

    result = evaluate_protocol(protocol_id=protocol, observations=observations)

    assert result.status is EvaluationStatus.RPE_ONLY
    assert result.zone_status is ZoneStatus.UNKNOWN
    assert result.reason_codes == ("sensor_data_missing",)


def test_bike_ftp_uses_only_reviewed_power_formula_and_half_up_rounding() -> None:
    result = evaluate_protocol(
        protocol_id="start23_bike_ftp_30min_v1",
        observations=_bike_ftp_test(),
    )

    assert result.thresholds == (result.thresholds[0],)
    assert result.thresholds[0].metric_kind is ZoneMetricKind.BIKE_FTP_WATTS
    assert result.thresholds[0].value == Decimal("238")


def test_bike_ftp_is_never_derived_from_heart_rate() -> None:
    observations = list(_bike_ftp_test())
    test = observations[1]
    observations[1] = _observation(
        test.protocol_id,
        Discipline.BIKE,
        "test_30min",
        duration_seconds=1800,
        reported_block_rpe=9,
        average_heart_rate_bpm=Decimal("175"),
        data_completeness=Decimal("1"),
        stable_segment=True,
        power_source_calibrated=True,
    )

    result = evaluate_protocol(
        protocol_id=test.protocol_id,
        observations=tuple(observations),
    )

    assert result.status is EvaluationStatus.INSUFFICIENT_DATA
    assert result.thresholds == ()
    assert "power_data_missing" in result.reason_codes


def test_bike_and_run_threshold_heart_rate_are_distinct_metrics() -> None:
    bike = evaluate_protocol(
        protocol_id="start23_bike_fthr_20min_v1",
        observations=_bike_hr_test(),
    )
    run = evaluate_protocol(
        protocol_id="start23_run_threshold_30min_v1",
        observations=_run_test(),
    )

    assert (
        bike.thresholds[0].metric_kind is ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM
    )
    assert all(
        estimate.metric_kind is not ZoneMetricKind.RUN_LTHR_BPM
        for estimate in bike.thresholds
    )
    assert any(
        estimate.metric_kind is ZoneMetricKind.RUN_LTHR_BPM
        for estimate in run.thresholds
    )


@pytest.mark.parametrize("pool_length", [25, 50])
def test_valid_css_test_supports_both_approved_pool_lengths(pool_length: int) -> None:
    result = evaluate_protocol(
        protocol_id="start23_swim_css_400_200_v1",
        observations=_swim_css_test(pool_length=pool_length),
    )

    assert result.status is EvaluationStatus.THRESHOLD_ESTIMATED
    assert result.thresholds[0].metric_kind is ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M
    assert result.thresholds[0].value == Decimal("110")


def test_css_formula_is_not_used_for_an_inconsistent_pace_relationship() -> None:
    result = evaluate_protocol(
        protocol_id="start23_swim_css_400_200_v1",
        observations=_swim_css_test(time_400="400", time_200="205"),
    )

    assert result.status is EvaluationStatus.INSUFFICIENT_DATA
    assert result.thresholds == ()
    assert "pace_relationship_invalid" in result.reason_codes


def test_css_uses_canonical_whole_second_half_up_rounding() -> None:
    result = evaluate_protocol(
        protocol_id="start23_swim_css_400_200_v1",
        observations=_swim_css_test(time_400="401", time_200="180"),
    )

    assert result.status is EvaluationStatus.THRESHOLD_ESTIMATED
    assert result.thresholds[0].value == Decimal("111")
    assert result.zone_status is ZoneStatus.PENDING_ATHLETE_CONFIRMATION
    assert result.zone_profiles[0].boundaries[0].upper is None


def test_missing_session_rpe_prevents_evaluation_but_preserves_observations() -> None:
    observations = list(_run_test())
    observations[-1] = _observation(
        "start23_run_threshold_30min_v1",
        Discipline.RUN,
        "cooldown",
        duration_seconds=600,
    )

    result = evaluate_protocol(
        protocol_id="start23_run_threshold_30min_v1",
        observations=tuple(observations),
    )

    assert result.status is EvaluationStatus.INSUFFICIENT_DATA
    assert result.thresholds == ()
    assert "missing_session_rpe" in result.reason_codes


def test_duplicate_segment_observations_fail_closed() -> None:
    observations = _bike_hr_test()
    result = evaluate_protocol(
        protocol_id="start23_bike_fthr_20min_v1",
        observations=observations + (observations[1],),
    )

    assert result.status is EvaluationStatus.INSUFFICIENT_DATA
    assert "duplicate_segment_observation" in result.reason_codes


def test_swim_calibration_calculates_observation_pace_without_inventing_css() -> None:
    assert pace_seconds_per_100m(
        elapsed_time_seconds=Decimal("210"),
        distance_meters=200,
    ) == Decimal("105")
    protocol = "start23_week1_swim_calibration_v1"
    repetitions_200 = tuple(
        SwimRepetition(200, Decimal("210"), 30, True) for _ in range(4)
    )
    repetitions_100 = tuple(
        SwimRepetition(100, Decimal("95"), 25, True) for _ in range(4)
    )
    result = evaluate_protocol(
        protocol_id=protocol,
        observations=(
            _observation(
                protocol,
                Discipline.SWIM,
                "warmup",
                distance_meters=300,
                pool_length_meters=50,
            ),
            _observation(
                protocol,
                Discipline.SWIM,
                "4x200_comfortable",
                distance_meters=800,
                pool_length_meters=50,
                stroke="freestyle",
                equipment="none",
                reported_block_rpe=4,
                steady_execution=SteadyExecution.YES,
                repetitions=repetitions_200,
            ),
            _observation(
                protocol,
                Discipline.SWIM,
                "4x100_steady",
                distance_meters=400,
                pool_length_meters=50,
                stroke="freestyle",
                equipment="none",
                reported_block_rpe=6,
                steady_execution=SteadyExecution.YES,
                repetitions=repetitions_100,
            ),
            _observation(
                protocol,
                Discipline.SWIM,
                "cooldown",
                distance_meters=200,
                reported_session_rpe=5,
            ),
        ),
    )

    assert result.status is EvaluationStatus.PROVISIONALLY_CALIBRATED
    assert result.threshold_status is ThresholdStatus.UNKNOWN
    assert result.thresholds == ()


@pytest.mark.parametrize("rpe", [0, 11])
def test_rpe_outside_canonical_one_through_ten_is_rejected(rpe: int) -> None:
    with pytest.raises(ValueError, match="1 through 10"):
        _observation(
            "start23_week1_run_calibration_v1",
            Discipline.RUN,
            "comfortable_20min",
            reported_block_rpe=rpe,
        )
