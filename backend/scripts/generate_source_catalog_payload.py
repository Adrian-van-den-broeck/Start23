"""Generate the deterministic SQL JSON payload for the START23 v0.1 catalog."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "trainings" / "Trainingen START23.v01.xlsx - Sheet1.csv"
DISCIPLINES = {"Fietsen": ("bike", 1), "Lopen": ("run", 2), "Zwemmen": ("swim", 3)}
ZONE_RPE = {1: 2, 2: 4, 3: 5, 4: 7, 5: 9}
ZONE_PATTERN = re.compile(r"Zone ([1-5])")


def _identifier_uuid(prefix: int, identifier: str, *, template: bool) -> str:
    sequence = int(identifier.split("-")[1])
    root = "57000000" if template else "57100000"
    return f"{root}-0000-0000-000{prefix}-{sequence:012d}"


def _segments(row: dict[str, str], *, distance_only: bool) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for sequence in range(1, 31):
        time_value = row[f"Tijd {sequence}"].strip()
        distance_value = row[f"Afstand {sequence}"].strip()
        zone_label = row[f"Zone {sequence}"].strip()
        if not time_value and not distance_value and not zone_label:
            continue
        zone_match = ZONE_PATTERN.search(zone_label)
        if zone_match is None:
            raise ValueError(f"{row['ID']} segment {sequence} has no zone")
        zone_number = int(zone_match.group(1))
        measure = distance_value if distance_only else time_value
        details = [measure, zone_label]
        for field in (f"Materiaal {sequence}", f"Slag {sequence}"):
            if value := row[field].strip():
                details.append(value)
        result.append(
            {
                "sequence": len(result) + 1,
                "name": f"Blok {len(result) + 1}",
                "instructions": " · ".join(details),
                "duration_minutes": None
                if distance_only
                else int(time_value.removesuffix("'")),
                "distance_meters": (
                    int(distance_value.removesuffix("m")) if distance_value else None
                ),
                "zone_number": zone_number,
                "expected_rpe": ZONE_RPE[zone_number],
            }
        )
    return result


def generate_payload() -> list[dict[str, object]]:
    """Map each reviewed CSV row without inferring a missing measure."""
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    payload: list[dict[str, object]] = []
    for row in rows:
        discipline, prefix = DISCIPLINES[row["Sport"]]
        distance_only = discipline == "swim"
        segments = _segments(row, distance_only=distance_only)
        payload.append(
            {
                "id": _identifier_uuid(prefix, row["ID"], template=False),
                "template_key": _identifier_uuid(prefix, row["ID"], template=True),
                "version": 1,
                "source_workout_id": row["ID"],
                "discipline": discipline,
                "name": f"{row['ID']} · {row['Type Training']}",
                "description": (
                    f"START23-catalogustraining voor {row['Doelwit Evenement']}. "
                    f"{row['Expected RPE']}."
                ),
                "duration_minutes": (
                    None if distance_only else int(row["Totale Duur (min)"])
                ),
                "distance_meters": (
                    int(row["Totale Afstand (m)"])
                    if row["Totale Afstand (m)"]
                    else None
                ),
                "intensity_bucket": (
                    "low" if row["Emmer (80/20)"] == "80%" else "high"
                ),
                "expected_rpe_min": min(
                    int(str(segment["expected_rpe"])) for segment in segments
                ),
                "expected_rpe_max": max(
                    int(str(segment["expected_rpe"])) for segment in segments
                ),
                "planned_tss": int(row["TSS"]),
                "segments": segments,
            }
        )
    return payload


if __name__ == "__main__":
    print(json.dumps(generate_payload(), ensure_ascii=False, separators=(",", ":")))
