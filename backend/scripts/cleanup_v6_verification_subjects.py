"""Restricted synthetic Auth cleanup library; no generic deletion/SQL CLI.

Invocation is a separate approved hosted action. Production manifest validation
is unconditional. Auth cascades are used; this helper never deletes table rows.
An independent owner-descendant audit must still pass before cleanup is complete.
"""

import json
from pathlib import Path
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.core.config import Settings
from app.core.security import SupabaseAccessTokenVerifier
from app.verification_v6 import VerificationManifest, verify_isolated_target


def cleanup_manifested_subjects(
    settings: Settings,
    manifest: VerificationManifest,
    *,
    management_token: str,
    confirmation_run_id: UUID,
    journal_directory: Path,
    enabling_file: Path,
    access_tokens: dict[UUID, SecretStr],
) -> tuple[UUID, UUID]:
    if (
        confirmation_run_id != manifest.run_id
        or enabling_file.exists()
        or (journal_directory / "process.lock").exists()
        or set(access_tokens) != {o.auth_subject for o in manifest.owners}
    ):
        raise ValueError("Stopped exact-run cleanup custody required")
    for file in journal_directory.glob("*.json"):
        record = json.loads(file.read_text())
        if (
            record.get("manifest_sha256") != manifest.digest()
            or record.get("state") != "complete"
        ):
            raise ValueError("Reconcile all mutations before cleanup")
    verify_isolated_target(manifest, settings, management_token)
    verifier = SupabaseAccessTokenVerifier(settings)
    # Verify every subject BEFORE the first irreversible Auth action.
    for owner in manifest.owners:
        if (
            verifier.verify(
                access_tokens[owner.auth_subject].get_secret_value()
            ).user_id
            != owner.auth_subject
        ):
            raise ValueError("Cleanup token subject mismatch")
    with httpx.Client(
        base_url="https://" + manifest.hostname, follow_redirects=False, timeout=10
    ) as client:
        for owner in manifest.owners:
            # Exclusive marker prevents automatic retries after unknown deletion.
            marker = journal_directory / (
                "cleanup-" + str(owner.auth_subject) + ".attempt"
            )
            with marker.open("x", encoding="utf-8") as output:
                output.write(manifest.digest())
            logout = client.post(
                "/auth/v1/logout?scope=global",
                headers={
                    "apikey": settings.supabase_publishable_key,
                    "Authorization": "Bearer "
                    + access_tokens[owner.auth_subject].get_secret_value(),
                },
            )
            logout.raise_for_status()
            deleted = client.delete(
                "/auth/v1/admin/users/" + str(owner.auth_subject),
                headers={"apikey": settings.supabase_secret_key.get_secret_value()},
            )
            deleted.raise_for_status()
            absent = client.get(
                "/auth/v1/admin/users/" + str(owner.auth_subject),
                headers={"apikey": settings.supabase_secret_key.get_secret_value()},
            )
            if absent.status_code != 404:
                raise RuntimeError("Synthetic cleanup uncertain; inspect exact subject")
    return manifest.owners[0].auth_subject, manifest.owners[1].auth_subject
