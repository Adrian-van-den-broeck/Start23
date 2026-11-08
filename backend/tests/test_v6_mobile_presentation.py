"""Public source presentation and inactive application boundary regressions."""

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI

from app.local_v6 import install_local_v6
from app.modules.planning.v6_presentation import source_prescription
from app.modules.workouts.joren_draft import WallRest
from app.modules.workouts.joren_v6_official import V6Template, official_catalog


@pytest.fixture(scope="module")
def catalog() -> tuple[V6Template, ...]:
    return official_catalog()


@pytest.mark.parametrize("index", range(77))
def test_exact_original_session_and_blocks(
    catalog: tuple[V6Template, ...], index: int
) -> None:
    template = catalog[index]
    source = template.source_revision.predecessor
    public = source_prescription(template)
    assert public.session_effort == source.original_expected_rpe
    assert public.focus == source.original_training_focus
    assert public.original_text == source.original_execution_structure
    assert public.zone_distribution == source.original_zone_distribution
    assert [b.text for b in public.blocks] == [e.raw_token for e in source.events]
    assert [b.sequence for b in public.blocks] == [e.sequence for e in source.events]
    for block, event in zip(public.blocks, source.events):
        if isinstance(event, WallRest):
            assert block.zone is None and block.meters is None
            assert block.seconds == event.seconds
    if source.sport == "swim":
        assert template.duration_minutes is None
        assert public.duration_basis == "ESTIMATED_FROM_APPROVED_REFERENCE_PACE"
        assert public.estimated_active_minutes is not None
        assert public.estimated_active_minutes > Decimal(0)
    else:
        assert public.estimated_active_minutes is None and public.duration_basis is None
    encoded = public.model_dump_json().lower()
    assert all(
        token not in encoded
        for token in ("tss", "planned_load", "official", "input_fingerprint")
    )


@pytest.mark.parametrize(
    "environment,url",
    [("production", None), ("staging", None), ("test", "https://example.supabase.co")],
)
def test_local_seam_refuses_nonisolated_configuration(
    environment: Any, url: str | None
) -> None:
    app = FastAPI()
    app.state.settings = SimpleNamespace(environment=environment, supabase_url=url)
    with pytest.raises(ValueError, match="isolated test"):
        install_local_v6(app, None, None)  # type: ignore[arg-type]
