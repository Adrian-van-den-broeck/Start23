"""Server-only Supabase access to the durable planning catalog."""

from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx

from app.core.config import Settings
from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    TrainingPhase,
    WorkoutSegment,
    WorkoutTemplate,
    ZoneRequirement,
)

PlanningCatalogRow = dict[str, Any]


class PlanningCatalogUnavailableError(Exception):
    """The private planning catalog could not be loaded safely."""


def parse_planning_catalog(
    rows: tuple[PlanningCatalogRow, ...],
) -> tuple[WorkoutTemplate, ...]:
    """Validate durable RPC rows as the same immutable domain catalog."""
    templates: list[WorkoutTemplate] = []
    try:
        for row in rows:
            segments_payload = row["segments"]
            if not isinstance(segments_payload, list):
                raise ValueError("Catalog segments must be a list.")
            segments = tuple(
                WorkoutSegment(
                    sequence=int(segment["sequence"]),
                    name=str(segment["name"]),
                    instructions=str(segment["instructions"]),
                    duration_minutes=Decimal(str(segment["duration_minutes"])),
                    distance_meters=(
                        int(segment["distance_meters"])
                        if segment.get("distance_meters") is not None
                        else None
                    ),
                    zone=TrainingZone(int(segment["zone_number"])),
                    expected_rpe=int(segment["expected_rpe"]),
                    is_swim_technique=bool(segment["is_swim_technique"]),
                )
                for segment in segments_payload
            )
            templates.append(
                WorkoutTemplate(
                    id=UUID(str(row["id"])),
                    template_key=UUID(str(row["template_key"])),
                    version=int(row["version"]),
                    discipline=Discipline(str(row["discipline"])),
                    name=str(row["name"]),
                    description=str(row["description"]),
                    duration_minutes=Decimal(str(row["duration_minutes"])),
                    distance_meters=(
                        int(row["distance_meters"])
                        if row.get("distance_meters") is not None
                        else None
                    ),
                    intensity_bucket=IntensityBucket(str(row["intensity_bucket"])),
                    expected_rpe_min=int(row["expected_rpe_min"]),
                    expected_rpe_max=int(row["expected_rpe_max"]),
                    training_phases=tuple(
                        TrainingPhase(str(value)) for value in row["training_phases"]
                    ),
                    zone_requirements=tuple(
                        ZoneRequirement(str(value))
                        for value in row["zone_requirements"]
                    ),
                    fallback_compatibility=FallbackCompatibility(
                        str(row["fallback_compatibility"])
                    ),
                    segments=segments,
                    internal_planned_load=InternalLoad(
                        Decimal(str(row["planned_tss"]))
                    ),
                )
            )
    except (KeyError, TypeError, ValueError) as error:
        raise PlanningCatalogUnavailableError(
            "The durable planning catalog is invalid."
        ) from error
    return tuple(templates)


class SupabaseWorkoutCatalogRepository:
    """Read the TSS-bearing catalog through its service-only RPC."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._secret_key = settings.supabase_secret_key.get_secret_value()
        self._base_url = f"{str(settings.supabase_url).rstrip('/')}/rest/v1"
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.supabase_data_api_timeout_seconds,
        )

    async def fetch_for_planning(self) -> tuple[PlanningCatalogRow, ...]:
        """Return all immutable versions, including server-internal planned load."""
        if not self._secret_key:
            raise PlanningCatalogUnavailableError("secret key is not configured")
        try:
            response = await self._client.post(
                f"{self._base_url}/rpc/get_workout_catalog_for_planning",
                headers={
                    "apikey": self._secret_key,
                    "Accept-Profile": "public",
                    "Content-Profile": "public",
                },
                json={},
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PlanningCatalogUnavailableError from error

        if not response.is_success:
            raise PlanningCatalogUnavailableError
        payload = response.json()
        if not isinstance(payload, list) or any(
            not isinstance(row, dict) for row in payload
        ):
            raise PlanningCatalogUnavailableError
        return tuple(dict(row) for row in payload)

    async def aclose(self) -> None:
        """Close only clients constructed by this repository."""
        if self._owns_client:
            await self._client.aclose()
