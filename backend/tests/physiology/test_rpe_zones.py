import pytest

from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.rpe_zones import (
    rpe_zone,
    zone_for_rpe_range,
    zone_for_rpe_value,
)


@pytest.mark.parametrize("discipline", list(Discipline))
def test_every_discipline_uses_the_reviewed_rpe_ranges(discipline: Discipline) -> None:
    assert [
        (rpe_zone(discipline, zone).rpe_min, rpe_zone(discipline, zone).rpe_max)
        for zone in TrainingZone
    ] == [(2, 3), (4, 4), (5, 6), (7, 8), (9, 10)]


def test_rpe_zone_exposes_sport_specific_display_guidance() -> None:
    swim = rpe_zone(Discipline.SWIM, TrainingZone.ZONE_1)
    bike = rpe_zone(Discipline.BIKE, TrainingZone.ZONE_2)

    assert swim.display_label == "Zone 1 · RPE 2-3"
    assert swim.training_type == "Inzwemmen"
    assert "techn" not in swim.description.casefold()
    assert bike.training_type == "Basisduur"


def test_noncanonical_rpe_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="canonical"):
        zone_for_rpe_range(3, 4)


def test_legacy_session_score_maps_to_reviewed_zone() -> None:
    assert zone_for_rpe_value(1) is TrainingZone.ZONE_1
    assert zone_for_rpe_value(8) is TrainingZone.ZONE_4
    assert zone_for_rpe_value(10) is TrainingZone.ZONE_5
