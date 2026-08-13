"""Parity checks for the approved protocol CSV bundle in docs/trainings."""

import csv
from pathlib import Path
from zipfile import ZipFile

from app.modules.calibration.domain import PROTOCOLS

_BUNDLE = (
    Path(__file__).parents[2]
    / "docs"
    / "trainings"
    / "START23_test_en_kalibratie_CSVs_v1_APPROVED.zip"
)


def _rows(archive: ZipFile, name: str) -> list[dict[str, str]]:
    with archive.open(name) as raw:
        text = (line.decode("utf-8-sig") for line in raw)
        return list(csv.DictReader(text))


def test_python_protocol_registry_matches_every_approved_csv_fixture() -> None:
    with ZipFile(_BUNDLE) as archive:
        index = _rows(archive, "START23_TEST_PROTOCOL_INDEX_V1.csv")
        assert {row["protocol_id"] for row in index} == set(PROTOCOLS)

        for index_row in index:
            protocol = PROTOCOLS[index_row["protocol_id"]]
            assert protocol.discipline.value == index_row["discipline"]
            assert protocol.protocol_type.value == index_row["protocol_type"]
            assert (
                protocol.result_status_on_success.value == index_row["intended_result"]
            )
            assert protocol.review_status.value == index_row["review_status"]

            segment_rows = _rows(archive, index_row["file_name"])
            assert {row["protocol_id"] for row in segment_rows} == {
                protocol.protocol_id
            }
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
