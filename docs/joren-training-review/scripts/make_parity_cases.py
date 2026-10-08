# ruff: noqa: E402
# The pinned backend path must be installed before importing the local oracle.
"""Generate synthetic offline parity inputs using the pinned Python engine as oracle."""

import json
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/joren-training-review"
sys.path.insert(0, str(ROOT / "backend"))
from app.modules.physiology.activity import (
    PlannedActivityExpectation,
    classify_activity_match,
)
from app.modules.physiology.joren import (
    average_hr_zone_load,
    calibrate,
    starting_baseline,
    zone_load,
)
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    IntensityBucket,
    InternalLoad,
)
from app.modules.planning.domain import (
    PlanLoadSample,
    resolve_target,
)
from app.modules.workouts.catalog import TrainingPhase

D = Decimal
cases = []


def cell(sheet, addr, value):
    return {"sheet": sheet, "cell": addr, "value": value}


def add(id, inputs, outputs, rule):
    cases.append({"id": id, "rule": rule, "inputs": inputs, "expected": outputs})


def serial(day):
    return (day - date(1899, 12, 30)).days


for n, hours in enumerate(
    [
        ("0", "0", "0"),
        ("1", "0", "0"),
        ("0", "1", "0"),
        ("0", "0", "1"),
        ("1", "2", "3"),
        ("0", "0", "3"),
        ("0", "0", "8"),
        ("0", "0", "15"),
        ("0.1", "0.2", "0.3"),
        ("0", "0", "168"),
        ("0", "0", "0.008"),
        ("0", "0", "0.016"),
    ]
):
    result = starting_baseline({s: D(h) * 60 for s, h in zip(Discipline, hours)})
    ins = [
        cell("01_ATHLETE_INPUTS", "B" + str(6 + i), float(h))
        for i, h in enumerate(hours)
    ]
    outs = [
        cell(
            "01_ATHLETE_INPUTS", "F" + str(6 + i), float(result.by_discipline[s].value)
        )
        for i, s in enumerate(Discipline)
    ]
    outs.append(cell("01_ATHLETE_INPUTS", "F9", float(result.total.value)))
    add(f"BASE-{n:02d}", ins, outs, "INIT-01/02")
for sp, row in [(Discipline.SWIM, 6), (Discipline.BIKE, 7), (Discipline.RUN, 8)]:
    for rpe in range(1, 11):
        obs = D("120") if sp is Discipline.SWIM else D("150")
        result = calibrate(discipline=sp, observation=obs, rpe=rpe)
        ins = [
            cell("03_CALIBRATION", f"B{row}", float(obs)),
            cell("03_CALIBRATION", f"C{row}", rpe),
        ]
        outs = [cell("03_CALIBRATION", f"E{row}", result.threshold)]
        zr = 6 + (row - 6) * 5
        for z in result.zones:
            outs += [
                cell(
                    "04_ZONES",
                    f"C{zr + z.zone - 1}",
                    z.lower if z.lower is not None else "OPEN",
                ),
                cell(
                    "04_ZONES",
                    f"D{zr + z.zone - 1}",
                    z.upper if z.upper is not None else "OPEN",
                ),
            ]
        add(f"CAL-{sp.value}-{rpe}", ins, outs, "CAL-01/02;ZONE-01/02")
for sp in Discipline:
    for zi in range(5):
        for frac in ["1", "0.5"]:
            mins = [D(0)] * 5
            mins[zi] = D(60) * D(frac)
            result = zone_load(
                discipline=sp, total_minutes=D(60), minutes_by_zone=tuple(mins)
            )
            ins = [
                cell("15_COMPLETED_ACTIVITIES", "A6", 1),
                cell("15_COMPLETED_ACTIVITIES", "B6", "synthetic"),
                cell("15_COMPLETED_ACTIVITIES", "C6", sp.value),
                cell("15_COMPLETED_ACTIVITIES", "D6", 60),
                cell("15_COMPLETED_ACTIVITIES", "J6", "YES"),
            ] + [
                cell("15_COMPLETED_ACTIVITIES", f"{chr(69 + i)}6", float(x))
                for i, x in enumerate(mins)
            ]
            outs = [
                cell("18_ACTUAL_LOAD", "H6", float(result.load.value)),
                cell("18_ACTUAL_LOAD", "F6", float(result.coverage_ratio)),
                cell("18_ACTUAL_LOAD", "J6", result.status),
            ]
            add(f"ZONELOAD-{sp.value}-{zi + 1}-{frac}", ins, outs, "LOAD-01/02")
for sp in [Discipline.RUN, Discipline.BIKE]:
    result = calibrate(discipline=sp, observation=D(150), rpe=4)
    for zone in result.zones:
        hr = zone.lower if zone.lower else zone.upper
        load = average_hr_zone_load(discipline=sp, total_minutes=D(60), zone=zone.zone)
        ins = [
            cell("03_CALIBRATION", "I" + str(8 if sp is Discipline.RUN else 7), True),
            cell("15_COMPLETED_ACTIVITIES", "A6", 1),
            cell("15_COMPLETED_ACTIVITIES", "B6", "synthetic"),
            cell("15_COMPLETED_ACTIVITIES", "C6", sp.value),
            cell("15_COMPLETED_ACTIVITIES", "D6", 60),
            cell("15_COMPLETED_ACTIVITIES", "J6", "NO"),
            cell("15_COMPLETED_ACTIVITIES", "K6", hr),
        ]
        outs = [
            cell("18_ACTUAL_LOAD", "G6", zone.zone),
            cell("18_ACTUAL_LOAD", "H6", float(load.load.value)),
            cell("18_ACTUAL_LOAD", "J6", load.status),
        ]
        add(f"MEAN-{sp.value}-{zone.zone}", ins, outs, "LOAD-03")
for ratio in [".899", ".9", "1", "1.1", "1.1001", "1.15", "1.1501"]:
    for rpe in [4, 7]:
        desired = D(100) * D(ratio)
        duration = desired / D(".92")
        measurement = zone_load(
            discipline=Discipline.RUN,
            total_minutes=duration,
            minutes_by_zone=(D(0), duration, D(0), D(0), D(0)),
        )
        match = classify_activity_match(
            duration=DurationMinutes(duration),
            rpe=rpe,
            planned=PlannedActivityExpectation(
                InternalLoad(D(100)), 3, 5, IntensityBucket.LOW
            ),
            measurement=measurement,
        )
        ins = [
            cell("15_COMPLETED_ACTIVITIES", "A6", 1),
            cell("15_COMPLETED_ACTIVITIES", "B6", "synthetic"),
            cell("15_COMPLETED_ACTIVITIES", "C6", "run"),
            cell("15_COMPLETED_ACTIVITIES", "D6", float(duration)),
            cell("15_COMPLETED_ACTIVITIES", "J6", "YES"),
            cell("15_COMPLETED_ACTIVITIES", "L6", rpe),
            cell("15_COMPLETED_ACTIVITIES", "M6", 100),
            cell("15_COMPLETED_ACTIVITIES", "N6", "low"),
            cell("15_COMPLETED_ACTIVITIES", "O6", 3),
            cell("15_COMPLETED_ACTIVITIES", "P6", 5),
        ] + [
            cell("15_COMPLETED_ACTIVITIES", f"{chr(69 + i)}6", float(x))
            for i, x in enumerate((D(0), duration, D(0), D(0), D(0)))
        ]
        add(
            f"MATCH-{ratio}-{rpe}",
            ins,
            [
                cell("16_RPE_AND_OBSERVATIONS", "E6", match.result.value),
                cell(
                    "16_RPE_AND_OBSERVATIONS",
                    "F6",
                    match.correction_reason.value if match.correction_reason else "",
                ),
            ],
            "ACT-01",
        )
for n, (planned, realized, count, reduced) in enumerate(
    [
        (100, None, 1, False),
        (100, 80, 1, False),
        (100, 79, 1, False),
        (100, 110, 1, False),
        (100, 120, 1, False),
        (100, 50, 1, True),
        (100, 0, 0, False),
    ]
):
    week = date(2026, 10, 12)
    race = date(2027, 2, 1)
    sample = PlanLoadSample(
        week_start=week - timedelta(days=7),
        load=InternalLoad(D(planned)),
        phase=TrainingPhase.BUILD,
        realized_load=None if realized is None else InternalLoad(D(realized)),
        completed_activity_count=count,
        reduced_realized_progression=reduced,
        has_prior_approved_plan=True,
    )
    result = resolve_target(
        week_start=week,
        race_date=race,
        prior_loads=(sample,),
        initial_catalog_load=InternalLoad(D("194.1")),
    )
    # Explicit 42d average input is the same single eligible realized sample.
    ins = [
        cell("19_NEXT_WEEK", "C6", True),
        cell("19_NEXT_WEEK", "D6", planned),
        cell("19_NEXT_WEEK", "E6", realized),
        cell("19_NEXT_WEEK", "F6", count),
        cell("19_NEXT_WEEK", "G6", reduced),
        cell("19_NEXT_WEEK", "I6", realized),
    ]
    add(
        f"TARGET-{n:02d}",
        ins,
        [
            cell("19_NEXT_WEEK", "J6", result.phase.value),
            cell("19_NEXT_WEEK", "K6", result.basis.value),
            cell("19_NEXT_WEEK", "L6", float(result.target.value)),
        ],
        "PLAN-07/08/09/10",
    )
# Fresh-athlete invariance: an activity row does not establish approval.
for existing in [False, True]:
    ins = [
        cell("19_NEXT_WEEK", "C6", False),
        cell("19_NEXT_WEEK", "D6", 100 if existing else None),
        cell("19_NEXT_WEEK", "E6", 100 if existing else None),
    ]
    add(
        "FRESH-" + str(existing),
        ins,
        [cell("19_NEXT_WEEK", "J6", "base"), cell("19_NEXT_WEEK", "L6", 194.1)],
        "PLAN-01",
    )
# Gaps must stay unavailable.
for n, (raw, total, zones, expected) in enumerate(
    [
        ("YES", 60, [0, 0, 0, 0, 0], "UNAVAILABLE"),
        ("YES", 60, [0, 30, 0, 0, 0], 27.6),
        ("NO", 60, [0, 0, 0, 0, 0], "UNAVAILABLE"),
    ]
):
    ins = [
        cell("15_COMPLETED_ACTIVITIES", "A6", 1),
        cell("15_COMPLETED_ACTIVITIES", "B6", "synthetic"),
        cell("15_COMPLETED_ACTIVITIES", "C6", "run"),
        cell("15_COMPLETED_ACTIVITIES", "D6", total),
        cell("15_COMPLETED_ACTIVITIES", "J6", raw),
        cell("15_COMPLETED_ACTIVITIES", "K6", 150),
        cell("03_CALIBRATION", "I8", False),
    ] + [
        cell("15_COMPLETED_ACTIVITIES", f"{chr(69 + i)}6", v)
        for i, v in enumerate(zones)
    ]
    add(f"MISSING-{n:02d}", ins, [cell("18_ACTUAL_LOAD", "H6", expected)], "LOAD-02/03")

# Phase/failure precedence: reference evaluation, not precomputed branch labels.
from app.modules.planning.domain import PlanningConstraintError

for ident, week, race, sample_present, approved in [
    ("RECOVERY", date(2026, 12, 28), date(2027, 2, 1), True, True),
    ("FULL-TAPER", date(2027, 1, 25), date(2027, 2, 1), True, True),
    ("PARTIAL-TAPER", date(2027, 1, 25), date(2027, 1, 31), True, True),
    ("TAPER-MISSING", date(2027, 1, 25), date(2027, 2, 1), False, False),
    ("PAST-RACE", date(2026, 10, 12), date(2026, 10, 11), True, True),
    ("INVALID-MONDAY", date(2026, 10, 13), date(2027, 2, 1), True, True),
    ("APPROVED-MISSING", date(2026, 10, 12), date(2027, 2, 1), False, True),
    ("PRIORITY-MISSING-TAPER", date(2027, 1, 25), date(2027, 1, 31), False, True),
]:
    sample = PlanLoadSample(
        week_start=week - timedelta(days=7),
        load=InternalLoad(D(200)),
        phase=TrainingPhase.BUILD,
        realized_load=InternalLoad(D(200)),
        completed_activity_count=1,
        has_prior_approved_plan=approved,
    )
    try:
        resolved = resolve_target(
            week_start=week,
            race_date=race,
            prior_loads=(sample,) if sample_present else (),
            initial_catalog_load=InternalLoad(D("194.1")),
            prior_approved_plan_exists=approved,
        )
        expected = [
            cell("19_NEXT_WEEK", "J6", resolved.phase.value),
            cell("19_NEXT_WEEK", "K6", resolved.basis.value),
            cell("19_NEXT_WEEK", "L6", float(resolved.target.value)),
        ]
    except PlanningConstraintError as exc:
        expected = [cell("19_NEXT_WEEK", "L6", exc.code)]
    except ValueError:
        expected = [cell("19_NEXT_WEEK", "L6", "INVALID_MONDAY")]
    add(
        "PHASE-" + ident,
        [
            cell("02_GOAL", "B11", serial(week)),
            cell("02_GOAL", "B7", serial(race)),
            cell("19_NEXT_WEEK", "C6", approved),
            cell("19_NEXT_WEEK", "D6", 200 if sample_present else None),
            cell("19_NEXT_WEEK", "E6", 200 if sample_present else None),
            cell("19_NEXT_WEEK", "F6", 1),
            cell("19_NEXT_WEEK", "I6", 200 if sample_present else None),
        ],
        expected,
        "PLAN-01/02/03/05/06",
    )

# Experimental constant isolation is a workbook property, not current-engine parity.
add(
    "PROPERTY-EXPERIMENTAL-GROWTH",
    [
        cell("00_START_HERE", "B21", "JOREN EXPERIMENTAL RULES"),
        cell("06_PARAMETERS", "C11", 1.2),
        cell("19_NEXT_WEEK", "C6", True),
        cell("19_NEXT_WEEK", "D6", 100),
        cell("19_NEXT_WEEK", "E6", 100),
        cell("19_NEXT_WEEK", "F6", 1),
    ],
    [
        cell("06_PARAMETERS", "B11", 1.1),
        cell("06_PARAMETERS", "D11", 1.2),
        cell("19_NEXT_WEEK", "L6", 110),
        cell("19_NEXT_WEEK", "M6", 120),
    ],
    "PROPERTY: original constant/output isolation",
)
add(
    "PROPERTY-RESTHR-UNUSED",
    [cell("01_ATHLETE_INPUTS", "B12", 40)],
    [cell("01_ATHLETE_INPUTS", "F9", 194.1)],
    "PROPERTY: resting HR not in baseline",
)


add(
    "PROPERTY-DEFAULT-CALENDAR-DATES",
    [],
    [
        cell("02_GOAL", "B7", serial(date(2027, 2, 1))),
        cell("02_GOAL", "B11", serial(date(2026, 10, 12))),
    ],
    "PROPERTY: exported calendar dates have no time component",
)
add(
    "PROPERTY-EXPERIMENTAL-HR-ZONE",
    [
        cell("06_PARAMETERS", "C40", 0.75),
        cell("03_CALIBRATION", "I8", True),
        cell("15_COMPLETED_ACTIVITIES", "A6", 1),
        cell("15_COMPLETED_ACTIVITIES", "B6", "synthetic"),
        cell("15_COMPLETED_ACTIVITIES", "C6", "run"),
        cell("15_COMPLETED_ACTIVITIES", "D6", 60),
        cell("15_COMPLETED_ACTIVITIES", "J6", "NO"),
        cell("15_COMPLETED_ACTIVITIES", "K6", 150),
    ],
    [
        cell("18_ACTUAL_LOAD", "G6", 2),
        cell("18_ACTUAL_LOAD", "L6", 1),
        cell("18_ACTUAL_LOAD", "H6", 55.2),
        cell("18_ACTUAL_LOAD", "I6", 34.8),
    ],
    "PROPERTY: experimental HR threshold drives its own zone",
)

(OUT / "fixtures/parity_cases.json").write_text(
    json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf8"
)
print(
    json.dumps(
        {
            "scenarios": len(cases),
            "assertions": sum(len(x["expected"]) for x in cases),
            "oracle": "pinned implementation",
            "full_engine": False,
        }
    )
)
