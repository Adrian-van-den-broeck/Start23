"""Lossless private catalog format; never an athlete-facing serialization.

The explicit type registry permits reconstruction without rereading a workbook or
recalculating a historical value. No class name supplied by storage is imported.
"""

import json
from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)
from app.modules.physiology.planned_v6 import OfficialPlannedLoad
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    TrainingPhase,
    WorkoutSegment,
    ZoneRequirement,
)
from app.modules.workouts.joren_draft import (
    DraftField,
    DraftLoad,
    SelectionDraft,
    SourceCell,
    SwimDistance,
    TimedZone,
    WallRest,
)
from app.modules.workouts.joren_v6 import V6Workout
from app.modules.workouts.joren_v6_official import V6Template
from app.modules.workouts.joren_v6_phase import PhaseTemplate

FORMAT = "joren-v6-private-catalog-json-1"
_TYPES: dict[str, Any] = {
    cls.__name__: cls
    for cls in (
        Discipline,
        IntensityBucket,
        InternalLoad,
        TrainingZone,
        OfficialPlannedLoad,
        FallbackCompatibility,
        TrainingPhase,
        WorkoutSegment,
        ZoneRequirement,
        DraftField,
        DraftLoad,
        SelectionDraft,
        SourceCell,
        SwimDistance,
        TimedZone,
        WallRest,
        V6Workout,
        V6Template,
        PhaseTemplate,
    )
}


def encode(value: Any) -> Any:
    """Every Decimal is a string, including all original source lexemes."""
    if isinstance(value, Enum):
        return {"type": type(value).__name__, "value": value.value}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("invalid_v6_decimal")
        return {"type": "decimal", "value": str(value)}
    if isinstance(value, UUID):
        return {"type": "uuid", "value": str(value)}
    if is_dataclass(value) and not isinstance(value, type):
        if type(value).__name__ not in _TYPES:
            raise ValueError("unsupported_v6_storage_type")
        return {
            "type": type(value).__name__,
            "fields": {f.name: encode(getattr(value, f.name)) for f in fields(value)},
        }
    if isinstance(value, tuple):
        return {"type": "tuple", "value": [encode(v) for v in value]}
    if isinstance(value, frozenset):
        return {
            "type": "frozenset",
            "value": sorted(
                (encode(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True)
            ),
        }
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("unsupported_v6_storage_type")


def decode(value: Any) -> Any:
    if not isinstance(value, dict):
        if value is None or type(value) in (str, int, bool):
            return value
        raise ValueError("invalid_v6_storage_value")
    kind = value["type"]
    if kind == "decimal":
        result: Any = Decimal(value["value"])
        if not result.is_finite():
            raise ValueError("invalid_v6_decimal")
        return result
    if kind == "uuid":
        return UUID(value["value"])
    if kind == "tuple":
        return tuple(decode(v) for v in value["value"])
    if kind == "frozenset":
        return frozenset(decode(v) for v in value["value"])
    cls = _TYPES[kind]
    if issubclass(cls, Enum):
        return cls(value["value"])
    stored = value["fields"]
    if set(stored) != {f.name for f in fields(cls)}:
        raise ValueError("invalid_v6_storage_fields")
    result = cls(**{f.name: decode(stored[f.name]) for f in fields(cls) if f.init})
    if encode(result) != value:
        raise ValueError("invalid_v6_storage_constants")
    return result


def catalog_document(template: V6Template) -> dict[str, Any]:
    return {"format": FORMAT, "template": encode(template)}


def parse_catalog_document(document: dict[str, Any]) -> V6Template:
    if document.get("format") != FORMAT:
        raise ValueError("unsupported_v6_storage_format")
    result = decode(document["template"])
    if not isinstance(result, V6Template):
        raise ValueError("invalid_v6_template")
    return result


def canonical_document(document: dict[str, Any]) -> str:
    return json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
