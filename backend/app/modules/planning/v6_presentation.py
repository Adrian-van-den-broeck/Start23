"""Allowlisted source presentation; never exports calculation or safety evidence."""

from decimal import Context, Decimal, localcontext

from app.modules.workouts.joren_draft import SwimDistance, TimedZone, WallRest
from app.modules.workouts.joren_v6_official import V6Template
from app.modules.workouts.planned_swim_estimate import estimate_swim
from app.modules.workouts.schemas import SourceBlock, SourcePrescription


def source_prescription(template: V6Template) -> SourcePrescription:
    record = template.source_revision.predecessor
    estimate = estimate_swim(record) if record.sport == "swim" else None
    with localcontext(Context(prec=50)):
        minutes = estimate.low_minutes + estimate.high_minutes if estimate else None
        return SourcePrescription(
            source_workout_id=record.original_workout_id,
            source_release=template.source_revision.source_release,
            session_effort=record.original_expected_rpe,
            focus=record.original_training_focus,
            original_text=record.original_execution_structure,
            zone_distribution=record.original_zone_distribution,
            distribution_unit=record.distribution_unit,
            blocks=tuple(
                SourceBlock(
                    sequence=event.sequence,
                    kind=event.kind,
                    text=event.raw_token,
                    zone=event.zone,
                    seconds=event.seconds
                    if isinstance(event, TimedZone | WallRest)
                    else None,
                    meters=int(event.meters)
                    if isinstance(event, SwimDistance)
                    else None,
                )
                for event in record.events
            ),
            estimated_active_minutes=(
                Decimal(minutes.numerator) / Decimal(minutes.denominator)
                if minutes is not None
                else None
            ),
            duration_basis=estimate.status if estimate else None,
        )
