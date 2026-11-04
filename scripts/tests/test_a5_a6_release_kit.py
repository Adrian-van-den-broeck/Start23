"""Release packaging gates; no database/network operations."""

import json
import tarfile
from pathlib import Path

import pytest

from scripts.prepare_a5_a6_release_kit import A5_VERSION, BACKEND_SHA, prepare


def test_backend_kit_preserves_a5_a6_and_excludes_deferred_activation(
    tmp_path: Path,
) -> None:
    output = tmp_path / "candidate"
    manifest = prepare(output)
    assert manifest["backend_component_sha"] == BACKEND_SHA
    migrations = list((output / "isolated-db/supabase/migrations").glob("*.sql"))
    assert len(migrations) == 48
    assert max(p.name[:14] for p in migrations) == A5_VERSION
    with tarfile.open(output / "backend-source.tar") as archive:
        names = archive.getnames()
        assert not any("realized_v2" in n or "joren_draft" in n for n in names)
        router = archive.extractfile("backend/app/modules/planning/router.py")
        assert router is not None and b'"/weekly-plans/recovery"' in router.read()
        service = archive.extractfile("backend/app/modules/checkins/service.py")
        assert service is not None and b"fetch_attached_proposal" in service.read()
    sql = (output / "a5-catalog-readonly.sql").read_text()
    assert "begin transaction read only" in sql
    assert "get_checkin_plan_proposal(uuid)', false, true, false" in sql
    assert "create_weekly_plan_proposal_v3(uuid,jsonb)', true, false, true" in sql
    assert not manifest["deployment_authorized"]
    assert json.loads((output / "manifest.json").read_text()) == manifest


def test_packaging_never_overwrites_existing_review_material(tmp_path: Path) -> None:
    marker = tmp_path / "keep.txt"
    marker.write_text("owner evidence")
    with pytest.raises(ValueError, match="existing files"):
        prepare(tmp_path)
    assert marker.read_text() == "owner evidence"
