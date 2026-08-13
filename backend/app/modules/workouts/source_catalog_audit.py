"""Read-only validation for the Phase 8 160-row training source export."""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

_SPORT_PREFIXES = {"Fietsen": "BIK-", "Lopen": "RUN-", "Zwemmen": "SWI-"}
_BUCKETS = {"80%", "20%"}
_MINUTE_PATTERN = re.compile(r"^(\d+)'$")
_DISTANCE_PATTERN = re.compile(r"^(\d+)m$")


@dataclass(frozen=True, slots=True)
class SourceCatalogAudit:
    """Aggregate validation result without exposing the source TSS column."""

    row_count: int
    sport_counts: dict[str, int]
    bucket_counts: dict[str, int]
    issue_counts: dict[str, int]
    taper_marker_present: bool

    @property
    def structurally_importable(self) -> bool:
        return not any(self.issue_counts.values())


def _positive_integer(value: str) -> bool:
    return value.isdigit() and int(value) > 0


def audit_source_catalog(path: Path) -> SourceCatalogAudit:
    """Validate identifiers, buckets, duration/distance, RPE, and segment zones."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        rows = tuple(reader)

    issues: Counter[str] = Counter()
    identifiers: set[str] = set()
    for row in rows:
        identifier = row.get("ID", "").strip()
        sport = row.get("Sport", "").strip()
        bucket = row.get("Emmer (80/20)", "").strip()
        rpe = row.get("Expected RPE", "").strip()
        total_duration = row.get("Totale Duur (min)", "").strip()
        total_distance = row.get("Totale Afstand (m)", "").strip()

        if not identifier or identifier in identifiers:
            issues["identifier"] += 1
        identifiers.add(identifier)
        expected_prefix = _SPORT_PREFIXES.get(sport)
        if expected_prefix is None or not identifier.startswith(expected_prefix):
            issues["discipline"] += 1
        if bucket not in _BUCKETS:
            issues["bucket"] += 1
        if not _positive_integer(rpe) or not 1 <= int(rpe) <= 10:
            issues["rpe"] += 1
        elif (bucket == "80%" and int(rpe) > 5) or (bucket == "20%" and int(rpe) < 6):
            issues["bucket_rpe"] += 1
        if not _positive_integer(total_duration):
            issues["duration"] += 1
        if sport == "Zwemmen" and not _positive_integer(total_distance):
            issues["distance"] += 1

        segment_minutes = 0
        segment_distance = 0
        segment_found = False
        blank_seen = False
        for sequence in range(1, 31):
            time_value = row.get(f"Tijd {sequence}", "").strip()
            distance_value = row.get(f"Afstand {sequence}", "").strip()
            zone = row.get(f"Zone {sequence}", "").strip()
            present = bool(time_value or distance_value or zone)
            if not present:
                blank_seen = True
                continue
            segment_found = True
            if blank_seen:
                issues["segment_order"] += 1
            if zone not in {"1", "2", "3", "4", "5"}:
                issues["zone"] += 1
            if not time_value and not distance_value:
                issues["segment_measure"] += 1
            if time_value:
                match = _MINUTE_PATTERN.fullmatch(time_value)
                if match is None:
                    issues["segment_time"] += 1
                else:
                    segment_minutes += int(match.group(1))
            if distance_value:
                match = _DISTANCE_PATTERN.fullmatch(distance_value)
                if match is None:
                    issues["segment_distance"] += 1
                else:
                    segment_distance += int(match.group(1))
        if not segment_found:
            issues["segments_missing"] += 1
        if _positive_integer(total_duration) and segment_minutes != int(total_duration):
            issues["duration_sum"] += 1
        if _positive_integer(total_distance) and segment_distance != int(
            total_distance
        ):
            issues["distance_sum"] += 1

    taper_marker_present = any("taper" in header.casefold() for header in headers)
    return SourceCatalogAudit(
        row_count=len(rows),
        sport_counts=dict(Counter(row.get("Sport", "").strip() for row in rows)),
        bucket_counts=dict(
            Counter(row.get("Emmer (80/20)", "").strip() for row in rows)
        ),
        issue_counts=dict(issues),
        taper_marker_present=taper_marker_present,
    )
