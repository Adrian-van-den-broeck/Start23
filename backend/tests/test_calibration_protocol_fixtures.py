"""Parity checks for the committed approved protocol CSV fixtures."""

import csv
from pathlib import Path

from app.modules.calibration.domain import PROTOCOLS
from app.modules.physiology.rpe_zones import rpe_zone, zone_for_rpe_range

_FIXTURES = Path(__file__).parents[2] / "docs" / "trainings"


def _rows(name: str) -> list[dict[str, str]]:
    with (_FIXTURES / name).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def test_python_protocol_registry_matches_every_approved_csv_fixture() -> None:
    index = _rows("START23_TEST_PROTOCOL_INDEX_V1.csv")
    assert {row["protocol_id"] for row in index} == set(PROTOCOLS)

    for index_row in index:
        protocol = PROTOCOLS[index_row["protocol_id"]]
        assert protocol.discipline.value == index_row["discipline"]
        assert protocol.protocol_type.value == index_row["protocol_type"]
        assert protocol.result_status_on_success.value == index_row["intended_result"]
        assert protocol.review_status.value == index_row["review_status"]

        segment_rows = _rows(index_row["file_name"])
        assert {row["protocol_id"] for row in segment_rows} == {protocol.protocol_id}
        assert [segment.order for segment in protocol.segments] == [
            int(row["segment_order"]) for row in segment_rows
        ]
        assert [segment.segment_id for segment in protocol.segments] == [
            row["segment_id"] for row in segment_rows
        ]
        assert [segment.duration_seconds for segment in protocol.segments] == [
            int(row["duration_seconds"]) if row["duration_seconds"] else None
            for row in segment_rows
        ]
        assert [segment.distance_meters for segment in protocol.segments] == [
            int(row["distance_meters"]) if row["distance_meters"] else None
            for row in segment_rows
        ]
        assert [segment.target_rpe_min for segment in protocol.segments] == [
            int(row["target_rpe_min"]) for row in segment_rows
        ]
        assert [segment.target_rpe_max for segment in protocol.segments] == [
            int(row["target_rpe_max"]) for row in segment_rows
        ]
        assert [row["rpe_zone"] for row in segment_rows] == [
            rpe_zone(
                protocol.discipline,
                zone_for_rpe_range(segment.target_rpe_min, segment.target_rpe_max),
            ).display_label
            for segment in protocol.segments
        ]
