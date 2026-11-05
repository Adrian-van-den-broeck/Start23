"""C2.1 policy boundaries, source correction custody and offline-only behavior."""

import ast
import json
import socket
from datetime import date
from decimal import ROUND_DOWN, Decimal, Inexact, localcontext
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

import pytest

from app.jobs.joren_c2_dry_run import main, private_json
from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.planned_intensity_policy import (
    PlannedSegment,
    PlannedSession,
    evaluate_training_week,
)
from app.modules.workouts.catalog import CURRENT_CATALOG, active_catalog
from app.modules.workouts.joren_c2_verification import SWIM_IF2_SOURCE
from app.modules.workouts.joren_c21_corrections import correction_evidence
from app.modules.workouts.joren_draft import DEFAULT_SOURCES, ROOT

D = Decimal
MONDAY = date(2026, 11, 2)
ARTIFACT = ROOT / "docs/catalog/implementation/joren_c21_swim_corrections_v1.json"


def session(
    sport: Discipline, low: str, high: str, zone: TrainingZone = TrainingZone.ZONE_5
) -> PlannedSession:
    return PlannedSession(
        sport,
        MONDAY,
        (PlannedSegment(D(low), TrainingZone.ZONE_2), PlannedSegment(D(high), zone)),
    )


@pytest.mark.parametrize(
    "low,high,status",
    (
        ("100", "0", "ACCEPTED"),
        ("80", "20", "ACCEPTED"),
        ("79.9999999999999999999999", "20", "REJECTED"),
        ("0", "100", "REJECTED"),
    ),
)
@pytest.mark.parametrize("sport", tuple(Discipline))
def test_maximum_not_minimum(
    low: str, high: str, status: str, sport: Discipline
) -> None:
    results = evaluate_training_week(MONDAY, (session(sport, low, high),))
    result = next(r for r in results if r.sport == sport)
    assert result.status == status
    assert result.high_ratio == Fraction(D(high)) / (
        Fraction(D(low)) + Fraction(D(high))
    )
    assert all(r.status == "NOT APPLICABLE" for r in results if r.sport != sport)


def test_sport_accounting_is_independent_and_week_is_explicit() -> None:
    results = {
        r.sport: r
        for r in evaluate_training_week(
            MONDAY,
            (
                session(Discipline.RUN, "0", "20"),
                session(Discipline.BIKE, "1000", "0"),
                session(Discipline.SWIM, "80", "20"),
            ),
        )
    }
    assert results[Discipline.RUN].status == "REJECTED"
    assert results[Discipline.BIKE].high_ratio == 0
    assert results[Discipline.SWIM].high_ratio == Fraction(1, 5)
    with pytest.raises(ValueError, match="session_outside_training_week"):
        evaluate_training_week(
            MONDAY, (PlannedSession(Discipline.RUN, date(2026, 11, 9), ()),)
        )
    with pytest.raises(ValueError, match="week_start_must_be_monday"):
        evaluate_training_week(date(2026, 11, 3), ())


@pytest.mark.parametrize("zone", tuple(TrainingZone))
def test_segment_taxonomy_including_z3(zone: TrainingZone) -> None:
    result = next(
        r
        for r in evaluate_training_week(
            MONDAY, (session(Discipline.RUN, "80", "20", zone),)
        )
        if r.sport == Discipline.RUN
    )
    assert result.high_ratio == (Fraction(0) if zone.value <= 2 else Fraction(1, 5))


def test_interval_seconds_not_session_count_focus_or_load() -> None:
    # One hard block in a single interval session does not make all 100s high.
    # Load, workout-focus and distance are deliberately absent from the contract.
    interval = session(Discipline.BIKE, "80", "20")
    split = (
        PlannedSession(Discipline.BIKE, MONDAY, (interval.segments or ())[:1]),
        PlannedSession(Discipline.BIKE, MONDAY, (interval.segments or ())[1:]),
    )
    assert evaluate_training_week(MONDAY, (interval,)) == evaluate_training_week(
        MONDAY, split
    )
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        result = evaluate_training_week(
            MONDAY, (session(Discipline.RUN, "80.001", "20"),)
        )
    assert next(r for r in result if r.sport == Discipline.RUN).status == "ACCEPTED"


@pytest.mark.parametrize(
    "segments",
    (
        None,
        (PlannedSegment(None, TrainingZone.ZONE_2),),
        (PlannedSegment(D(60)),),
        (
            PlannedSegment(D(600), TrainingZone.ZONE_2),
            PlannedSegment(None, TrainingZone.ZONE_5),
        ),
    ),
)
def test_missing_reliable_swim_time_or_classification_is_unverified(
    segments: tuple[PlannedSegment, ...] | None,
) -> None:
    result = evaluate_training_week(
        MONDAY, (PlannedSession(Discipline.SWIM, MONDAY, segments),)
    )[0]
    assert result.status == "UNVERIFIED" and result.high_ratio is None


def test_stationary_rest_never_dilutes_ratio_and_zero_is_not_applicable() -> None:
    swim = session(Discipline.SWIM, "60", "20")
    result = evaluate_training_week(
        MONDAY,
        (
            PlannedSession(
                Discipline.SWIM,
                MONDAY,
                (
                    *(swim.segments or ()),
                    PlannedSegment(D(10000), stationary_rest=True),
                ),
            ),
        ),
    )[0]
    assert result.status == "REJECTED" and result.high_ratio == Fraction(1, 4)
    for segments in (
        (),
        (PlannedSegment(D(0)),),
        (PlannedSegment(None, stationary_rest=True),),
    ):
        results = evaluate_training_week(
            MONDAY, (PlannedSession(Discipline.SWIM, MONDAY, segments),)
        )
        assert all(
            r.status == "NOT APPLICABLE" and r.high_ratio is None for r in results
        )
    assert all(r.status == "NOT APPLICABLE" for r in evaluate_training_week(MONDAY, ()))


@pytest.mark.parametrize("seconds", (D(-1), D("NaN"), D("Infinity")))
def test_invalid_duration_fails_closed(seconds: Decimal) -> None:
    with pytest.raises(ValueError, match="invalid_planned_duration"):
        PlannedSegment(seconds, TrainingZone.ZONE_2)


def test_all_twenty_derived_rows_and_six_corrections() -> None:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert artifact == json.loads(private_json(correction_evidence()))
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        assert artifact == json.loads(private_json(correction_evidence()))
    assert artifact["parent_source"]["sha256"] == SWIM_IF2_SOURCE.sha256
    assert artifact["approval"]["id"] == "C2.1-SWIM-1"
    corrected_ids = set()
    expected_six = ("39.88125", "54.759375", "69.6375") * 2
    assert len(artifact["records"]) == 20
    for index, row in enumerate(artifact["records"]):
        original = row["original"]
        assert row["structure_status"] == "CONSISTENT"
        assert row["derived_ordered_zones"] == original["source_zones"]
        assert row["activation_status"] == "INACTIVE" and row["operational_p"] is None
        assert row["time_compliance"] == "UNVERIFIED"
        if row["correction"]:
            corrected_ids.add(row["source_id"])
            assert original["structure_status"] == "SOURCE-CONFLICTED"
            assert original["cells"][13]["value"] == row["correction"]["before"]
            assert row["derived_prescription"] == row["correction"]["before"].replace(
                "300m Z3", "300m Z2", 1
            )
            assert row["derived_events"][1:] == original["events"][1:]
            assert row["derived_events"][0] == {
                **original["events"][0],
                "zone": 2,
                "raw_token": "300m Z2 ",
            }
            assert row["derived_guidance"][0]["rpe_min"] == 3
        else:
            assert row["derived_events"] == original["events"]
        calculations = row["calculations_unapproved_method"]
        assert calculations["RECONSTRUCTED_rounded_minutes"]["source_display_matches"]
        confirmed = calculations["confirmed_if_pdf_reference"]
        if index in (9, 10, 13):
            assert confirmed == {"error": "missing_if_anchor"}
        else:
            assert confirmed["operational_value"] is None
            if index >= 14:
                assert D(confirmed["decimal_value"]) == D(expected_six[index - 14])
    assert corrected_ids == {f"TR-SWIM-{i:03d}" for i in range(15, 21)}


def test_custody_determinism_rejection_and_no_activation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources = {p: p.read_bytes() for p in DEFAULT_SOURCES.rglob("*") if p.is_file()}
    catalog = active_catalog(CURRENT_CATALOG)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("network access in correction intake")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    output = tmp_path / "private.json"
    args = ["--dry-run", "--approved-corrections", "--private-output", str(output)]
    assert main(args) == 0
    summary = capsys.readouterr().out
    assert main(args) == 0 and capsys.readouterr().out == summary
    assert output.read_bytes() == ARTIFACT.read_bytes()
    assert not any(s in summary for s in ("39.9", "69.6", "decimal_value"))
    assert (
        main(
            [
                "--dry-run",
                "--approved-corrections",
                "--private-output",
                str(DEFAULT_SOURCES / SWIM_IF2_SOURCE.filename),
            ]
        )
        == 1
    )
    assert "artifact_revision_conflict" in capsys.readouterr().out
    assert {p: p.read_bytes() for p in sources} == sources
    assert (
        sha256(sources[DEFAULT_SOURCES / SWIM_IF2_SOURCE.filename]).hexdigest()
        == SWIM_IF2_SOURCE.sha256
    )
    assert active_catalog(CURRENT_CATALOG) == catalog


def test_isolated_modules_have_no_active_importers() -> None:
    allowed = {
        "joren_c2_dry_run.py",
        "joren_c21_corrections.py",
        "planned_intensity_policy.py",
        # Authorized disabled C4 review seam; no active consumer (separate test).
        "v6_phase_review.py",
    }
    for path in (ROOT / "backend/app").rglob("*.py"):
        if path.name in allowed:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    s in (node.module or "")
                    for s in ("planned_intensity_policy", "joren_c21_corrections")
                )
            if isinstance(node, ast.Import):
                assert not any(
                    s in n.name
                    for n in node.names
                    for s in ("planned_intensity_policy", "joren_c21_corrections")
                )
