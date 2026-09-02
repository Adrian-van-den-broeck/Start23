"""Canonical triathlon RPE zones reviewed for the Start23 MVP."""

from dataclasses import dataclass

from app.modules.physiology.models import Discipline, TrainingZone


@dataclass(frozen=True, slots=True)
class RpeZoneDefinition:
    """Athlete-facing RPE guidance for one discipline and training zone."""

    zone: TrainingZone
    rpe_min: int
    rpe_max: int
    training_type: str
    description: str

    @property
    def rpe_label(self) -> str:
        return (
            str(self.rpe_min)
            if self.rpe_min == self.rpe_max
            else f"{self.rpe_min}-{self.rpe_max}"
        )

    @property
    def display_label(self) -> str:
        return f"Zone {self.zone.value} · RPE {self.rpe_label}"


_RPE_RANGES = {
    TrainingZone.ZONE_1: (2, 3),
    TrainingZone.ZONE_2: (4, 4),
    TrainingZone.ZONE_3: (5, 6),
    TrainingZone.ZONE_4: (7, 8),
    TrainingZone.ZONE_5: (9, 10),
}

_SPORT_GUIDANCE = {
    Discipline.RUN: {
        TrainingZone.ZONE_1: (
            "Herstel",
            "Heel ontspannen; moeiteloos praten en zingen.",
        ),
        TrainingZone.ZONE_2: (
            "Duur",
            "Comfortabel tempo; vlot babbelen in hele zinnen.",
        ),
        TrainingZone.ZONE_3: ("Tempo", "Pittig; praten lukt enkel in korte zinnen."),
        TrainingZone.ZONE_4: ("Drempel", "Zwaar; praten is onmogelijk, enkel ja/nee."),
        TrainingZone.ZONE_5: ("Sprint", "Maximaal; korte all-out, maximaal hijgen."),
    },
    Discipline.BIKE: {
        TrainingZone.ZONE_1: ("Losrijden", "Zeer lichte weerstand; volkomen rustig."),
        TrainingZone.ZONE_2: ("Basisduur", "Constante lichte druk; makkelijk praten."),
        TrainingZone.ZONE_3: (
            "Moderato",
            "Pittige pedaaldruk; praten in korte zinnen.",
        ),
        TrainingZone.ZONE_4: (
            "Klimtempo",
            "Zware inspanning (klimgevoel); niet meer praten.",
        ),
        TrainingZone.ZONE_5: ("Sprint", "Volle kracht; brandende benen, totaal leeg."),
    },
    Discipline.SWIM: {
        TrainingZone.ZONE_1: ("Inzwemmen", "Zeer rustig; niet buiten adem."),
        TrainingZone.ZONE_2: (
            "Duurzwemmen",
            "Gelijkmatig en beheerst ritme; goed vol te houden.",
        ),
        TrainingZone.ZONE_3: (
            "Drempel",
            "Stevig tempo; intensievere ademhaling en keerpunten.",
        ),
        TrainingZone.ZONE_4: (
            "Zwaar",
            "Hard zwemmen; verzurende armen en diepe ademhaling.",
        ),
        TrainingZone.ZONE_5: (
            "Sprint",
            "Maximale slagfrequentie; volledig buiten adem aan de kant.",
        ),
    },
}


def rpe_zone(discipline: Discipline, zone: TrainingZone) -> RpeZoneDefinition:
    """Return the single reviewed definition used by planning and the public API."""
    rpe_min, rpe_max = _RPE_RANGES[zone]
    training_type, description = _SPORT_GUIDANCE[discipline][zone]
    return RpeZoneDefinition(
        zone=zone,
        rpe_min=rpe_min,
        rpe_max=rpe_max,
        training_type=training_type,
        description=description,
    )


def zone_for_rpe_range(rpe_min: int, rpe_max: int) -> TrainingZone:
    """Resolve an exact reviewed RPE range to its canonical zone."""
    for zone, rpe_range in _RPE_RANGES.items():
        if rpe_range == (rpe_min, rpe_max):
            return zone
    raise ValueError("RPE target does not match a canonical triathlon RPE zone.")


def zone_for_rpe_value(rpe: int) -> TrainingZone:
    """Map one legacy/session score to the canonical athlete-facing zone."""
    if not 1 <= rpe <= 10:
        raise ValueError("RPE must be within 1 through 10.")
    if rpe <= 3:
        return TrainingZone.ZONE_1
    if rpe == 4:
        return TrainingZone.ZONE_2
    if rpe <= 6:
        return TrainingZone.ZONE_3
    if rpe <= 8:
        return TrainingZone.ZONE_4
    return TrainingZone.ZONE_5
