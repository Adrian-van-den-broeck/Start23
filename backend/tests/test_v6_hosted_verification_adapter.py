"""Local signed-token security tests. No hosted GoTrue execution is claimed."""

import asyncio
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt import PyJWK, PyJWKClient
from jwt.algorithms import ECAlgorithm
from pydantic import SecretStr, ValidationError

from app import verification_v6 as adapter
from app.core.config import Settings
from app.core.security import SupabaseAccessTokenVerifier
from app.main import create_app
from app.modules.planning.router import get_planning_service


class Keys(PyJWKClient):
    def __init__(self, key: PyJWK) -> None:
        self.key = key

    def get_signing_key_from_jwt(self, token: str | bytes) -> PyJWK:
        return self.key


@dataclass
class Context:
    manifest: adapter.VerificationManifest
    settings: Settings
    key: ec.EllipticCurvePrivateKey
    directory: Path
    kill: Path
    requests: list[httpx.Request] = field(default_factory=list)
    preferences: dict[str, dict[str, Any]] = field(default_factory=dict)
    writes: int = 0
    drift: bool = False
    private_response: bool = False
    lose_response: bool = False
    deleted: set[str] = field(default_factory=set)

    def token(self, label: str = "A", **changes: Any) -> str:
        owner = next(o for o in self.manifest.owners if o.label == label)
        now = datetime.now(timezone.utc)
        claims = {
            "sub": str(owner.auth_subject),
            "role": "authenticated",
            "aud": "authenticated",
            "iss": self.manifest.issuer,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            **changes,
        }
        return jwt.encode(
            claims, self.key, algorithm="ES256", headers={"kid": "local-test"}
        )

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if request.url.host == "api.supabase.com":
            assert (
                request.method == "GET"
                and path == "/v1/projects/" + self.manifest.project_ref
            )
            return httpx.Response(
                200, json={"id": self.manifest.project_ref, "status": "ACTIVE_HEALTHY"}
            )
        if path.startswith("/auth/v1/admin/users/"):
            owner = next(
                o
                for o in self.manifest.owners
                if str(o.auth_subject) == path.rsplit("/", 1)[1]
            )
            if request.method == "DELETE":
                self.deleted.add(str(owner.auth_subject))
                return httpx.Response(200, json={})
            assert request.method == "GET"
            if str(owner.auth_subject) in self.deleted:
                return httpx.Response(404, json={})
            return httpx.Response(
                200, json={"id": str(owner.auth_subject), "email": owner.email}
            )
        if path == "/auth/v1/logout":
            assert request.method == "POST" and request.url.params["scope"] == "global"
            return httpx.Response(204)
        values = json.loads(request.content) if request.content else {}
        if path.endswith("/resolve_legacy_auth_user_id"):
            owner = next(
                o
                for o in self.manifest.owners
                if str(o.athlete_id) == values["p_athlete_id"]
            )
            return httpx.Response(200, json=str(owner.auth_subject))
        token = request.headers.get("authorization", "Bearer ").split(" ", 1)[1]
        claims = jwt.decode(token, options={"verify_signature": False}) if token else {}
        owner = next(
            o for o in self.manifest.owners if str(o.auth_subject) == claims["sub"]
        )
        if path.endswith("/get_current_athlete_id"):
            return httpx.Response(
                200, json=str(uuid4() if self.drift else owner.athlete_id)
            )
        if path.endswith("/save_frequency_preferences"):
            current = self.preferences.get(owner.label, {}).get("revision", 0)
            if values["p_expected_revision"] != current:
                return httpx.Response(
                    409,
                    json={"code": "PT409", "message": "frequency preference changed"},
                )
            self.writes += 1
            self.preferences[owner.label] = {
                "revision": current + 1,
                "operation_id": values["p_operation_id"],
                "preferences": values["p_preferences"],
                "confirmed_at": None,
                "recorded_at": None,
                "reconfirmation_required": [],
            }
            if self.lose_response:
                self.lose_response = False
                raise httpx.ReadTimeout("Lost synthetic acknowledgement")
            return httpx.Response(200, json=self.preferences[owner.label])
        if path.endswith("/get_frequency_preferences"):
            if self.private_response:
                return httpx.Response(
                    200, json={"nested": {"planned_tss": "PRIVATE_SENTINEL"}}
                )
            return httpx.Response(
                200,
                json=self.preferences.get(
                    owner.label,
                    {
                        "revision": 0,
                        "operation_id": None,
                        "preferences": {"run": None, "bike": None, "swim": None},
                        "confirmed_at": None,
                        "recorded_at": None,
                        "reconfirmation_required": [],
                    },
                ),
            )
        if path.endswith("/get_v6_move_workout_context"):
            return httpx.Response(404, json={"code": "P0002"})
        if path.endswith("/get_activity"):
            return httpx.Response(404, json={"code": "P0002"})
        raise AssertionError("Unexpected test transport operation: " + path)


@pytest.fixture
def context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Context:
    ref = "abcdefghijklmnopqrst"
    manifest = adapter.VerificationManifest(
        version=1,
        run_id=uuid4(),
        project_ref=ref,
        issuer=f"https://{ref}.supabase.co/auth/v1",
        audience="authenticated",
        hostname=ref + ".supabase.co",
        target_kind="isolated_synthetic",
        owner_approval_reference="LOCAL-TEST-ONLY",
        owners=tuple(
            adapter.SyntheticOwner(
                label=label,
                auth_subject=uuid4(),
                athlete_id=uuid4(),
                email=f"verification-{label.lower()}@wombo.invalid",
            )
            for label in ("A", "B")
        ),
    )
    settings = Settings(
        environment="staging",
        supabase_url="https://" + manifest.hostname,
        supabase_publishable_key="sb_publishable_local",
        supabase_secret_key="sb_secret_local",
        _env_file=None,
    )
    key = ec.generate_private_key(ec.SECP256R1())
    kill = tmp_path / "enabled"
    kill.write_text(manifest.digest())
    ctx = Context(manifest, settings, key, tmp_path / "journal", kill)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original_client(
            transport=httpx.MockTransport(ctx.handle), **kwargs
        ),
    )
    monkeypatch.setattr(
        httpx, "AsyncHTTPTransport", lambda **kwargs: httpx.MockTransport(ctx.handle)
    )
    jwk = ECAlgorithm.to_jwk(key.public_key(), as_dict=True)
    assert isinstance(jwk, dict)
    real_verifier = SupabaseAccessTokenVerifier(
        settings,
        jwks_client=Keys(PyJWK.from_dict({**jwk, "kid": "local-test", "alg": "ES256"})),
    )
    monkeypatch.setattr(adapter, "SupabaseAccessTokenVerifier", lambda _: real_verifier)
    return ctx


def application(context: Context) -> Any:
    return adapter.create_verification_app(
        context.settings,
        context.manifest,
        management_token="local-management",
        journal_directory=context.directory,
        kill_file=context.kill,
    )


@pytest.fixture
def client(context: Context) -> Iterator[TestClient]:
    with TestClient(application(context)) as client:
        yield client


def headers(
    context: Context, label: str = "A", operation: UUID | None = None
) -> dict[str, str]:
    result = {"Authorization": "Bearer " + context.token(label)}
    if operation:
        result["X-Verification-Operation"] = str(operation)
    return result


@pytest.mark.parametrize(
    "field,value",
    [
        ("project_ref", adapter.PRODUCTION_PROJECT),
        ("hostname", "127.0.0.1"),
        ("hostname", "abcdefghijklmnopqrst.supabase.co.attacker.invalid"),
        ("issuer", "https://other.supabase.co/auth/v1"),
        ("audience", "service_role"),
        ("owner_approval_reference", ""),
    ],
)
def test_exact_manifest_target(context: Context, field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        adapter.VerificationManifest.model_validate(
            {**context.manifest.model_dump(), field: value}
        )


def test_independent_target_and_account_preflight(context: Context) -> None:
    adapter.verify_isolated_target(
        context.manifest, context.settings, "local-management"
    )
    assert sum("/admin/users/" in r.url.path for r in context.requests) == 2
    assert all(
        r.method == "GET" or r.url.path.endswith("resolve_legacy_auth_user_id")
        for r in context.requests
    )
    with pytest.raises(ValueError):
        adapter.verify_isolated_target(
            context.manifest,
            context.settings.model_copy(
                update={"supabase_url": "https://elsewhere.invalid"}
            ),
            "local-management",
        )


@pytest.mark.parametrize(
    "claims",
    [
        {"aud": "wrong"},
        {"iss": "https://foreign.invalid/auth/v1"},
        {"role": "service_role"},
        {"sub": str(uuid4())},
        {"exp": 0},
    ],
)
def test_real_signature_claim_boundaries(
    context: Context, client: TestClient, claims: dict[str, Any]
) -> None:
    response = client.get(
        "/api/v1/me", headers={"Authorization": "Bearer " + context.token(**claims)}
    )
    assert response.status_code == 401
    assert context.writes == 0


def test_missing_and_tampered_tokens(context: Context, client: TestClient) -> None:
    assert client.get("/api/v1/me").status_code == 401
    token = context.token()
    pieces = token.split(".")
    pieces[2] = ("A" if pieces[2][0] != "A" else "B") + pieces[2][1:]
    assert (
        client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + ".".join(pieces)}
        ).status_code
        == 401
    )


def test_both_manifested_owners_and_map_drift(
    context: Context, client: TestClient
) -> None:
    for label in ("A", "B"):
        assert (
            client.get("/api/v1/me", headers=headers(context, label)).status_code == 200
        )
    context.drift = True
    assert client.get("/api/v1/me", headers=headers(context)).status_code == 401
    assert context.writes == 0


def test_narrow_routes_no_production_injection(
    context: Context, client: TestClient
) -> None:
    normal = create_app(context.settings)
    assert get_planning_service not in normal.dependency_overrides
    for path in (
        "/openapi.json",
        "/api/v1/integrations/polar/webhook",
        "/sql",
        "/migrations",
        "/enable-v6",
    ):
        assert client.post(
            path, headers=headers(context, operation=uuid4()), json={}
        ).status_code in {404, 405}
    from app.local_v6 import install_local_v6

    with pytest.raises(ValueError, match="isolated test"):
        install_local_v6(
            normal,
            normal.state.planning_repository,
            normal.state.planning_catalog_provider,
        )


def test_exact_success_retry_foreign_operation_and_stale_request(
    context: Context, client: TestClient
) -> None:
    op = uuid4()
    body = {
        "expected_revision": 0,
        "operation_id": str(uuid4()),
        "preferences": {"run": 2, "bike": None, "swim": 0},
    }
    first = client.put(
        "/api/v1/me/frequency-preferences",
        headers=headers(context, operation=op),
        json=body,
    )
    assert first.status_code == 200
    assert (
        client.put(
            "/api/v1/me/frequency-preferences",
            headers=headers(context, operation=op),
            json=body,
        ).content
        == first.content
    )
    assert context.writes == 1
    assert (
        client.put(
            "/api/v1/me/frequency-preferences",
            headers=headers(context, "B", op),
            json=body,
        ).status_code
        == 403
    )
    assert (
        client.put(
            "/api/v1/me/frequency-preferences",
            headers=headers(context, operation=op),
            json={**body, "expected_revision": 1},
        ).status_code
        == 403
    )
    stale = client.put(
        "/api/v1/me/frequency-preferences",
        headers=headers(context, operation=uuid4()),
        json={**body, "operation_id": str(uuid4())},
    )
    assert stale.status_code == 409
    assert context.writes == 1


def test_lost_acknowledgement_blocks_mutations_and_survives_restart(
    context: Context,
) -> None:
    op = uuid4()
    body = {
        "expected_revision": 0,
        "operation_id": str(uuid4()),
        "preferences": {"run": None, "bike": None, "swim": None},
    }
    context.lose_response = True
    with TestClient(application(context)) as client:
        result = client.put(
            "/api/v1/me/frequency-preferences",
            headers=headers(context, operation=op),
            json=body,
        )
        assert result.status_code == 503
        assert (
            json.loads((context.directory / (str(op) + ".json")).read_text())["state"]
            == "uncertain"
        )
    with TestClient(application(context)) as client:
        assert (
            client.put(
                "/api/v1/me/frequency-preferences",
                headers=headers(context, operation=uuid4()),
                json=body,
            ).status_code
            == 403
        )
        committed_preference = dict(context.preferences["A"])
        context.preferences["A"]["operation_id"] = str(uuid4())
        assert (
            client.put(
                "/api/v1/me/frequency-preferences",
                headers=headers(context, operation=op),
                json=body,
            ).status_code
            == 403
        )
        context.preferences["A"] = committed_preference
        reconciled = client.put(
            "/api/v1/me/frequency-preferences",
            headers=headers(context, operation=op),
            json=body,
        )
        assert reconciled.status_code == 200 and reconciled.json()["revision"] == 1
        assert (
            client.put(
                "/api/v1/me/frequency-preferences",
                headers=headers(context, operation=op),
                json=body,
            ).content
            == reconciled.content
        )
        assert (
            client.get(
                "/api/v1/me/frequency-preferences", headers=headers(context)
            ).json()["revision"]
            == 1
        )
    assert context.writes == 1


def test_kill_switch_and_foreign_ids(context: Context, client: TestClient) -> None:
    for label in ("A", "B"):
        assert (
            client.get(
                "/api/v1/activities/" + str(uuid4()), headers=headers(context, label)
            ).status_code
            == 404
        )
    context.kill.unlink()
    assert client.get("/api/v1/me", headers=headers(context)).status_code == 403
    assert context.writes == 0


@pytest.mark.parametrize(
    "value",
    [
        {"x": [{"realized_tss": 12}]},
        {"x": {"provenance": {}}},
        {"message": "PRIVATE sb_secret_sentinel"},
        {"x": "planned TSS 123"},
        {"x": {"plannedLoad": 123}},
        {"x": [{"realized-load": 123}]},
        {"message": "realized load 123"},
    ],
)
def test_recursive_private_data_redaction(value: Any) -> None:
    with pytest.raises(ValueError, match="response rejected"):
        adapter.public_only(value)


def test_upstream_private_dto_is_not_echoed(
    context: Context, client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    context.private_response = True
    result = client.get("/api/v1/me/frequency-preferences", headers=headers(context))
    assert result.status_code in {403, 503}
    assert "PRIVATE_SENTINEL" not in result.text and "planned_tss" not in result.text
    assert "PRIVATE_SENTINEL" not in caplog.text


@pytest.mark.parametrize(
    "path,payload",
    [
        ("rpc/register_frequency_decision", {}),
        ("rpc/apply_migration", {}),
        ("rpc/get_v6_frequency_context", {"p_athlete_id": str(uuid4())}),
        ("rpc/create_v6_weekly_plan_proposal", {"p_athlete_id": str(uuid4())}),
        ("rpc/TEST_ONLY", {}),
    ],
)
def test_transport_rejects_unlisted_operations_and_foreign_service_owners(
    context: Context, path: str, payload: dict[str, Any]
) -> None:
    async def exercise() -> None:
        transport = adapter.RestrictedDataTransport(context.manifest, context.kill)
        token = adapter._custody.set(
            adapter.RequestCustody(context.manifest.owners[0], context.token())
        )
        try:
            async with httpx.AsyncClient(transport=transport) as client:
                with pytest.raises(httpx.RequestError):
                    await client.post(
                        "https://" + context.manifest.hostname + "/rest/v1/" + path,
                        json=payload,
                    )
        finally:
            adapter._custody.reset(token)

    asyncio.run(exercise())
    assert not context.requests


def test_cleanup_is_bound_to_two_stopped_manifested_subjects(
    context: Context, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts import cleanup_v6_verification_subjects as cleanup

    jwk = ECAlgorithm.to_jwk(context.key.public_key(), as_dict=True)
    assert isinstance(jwk, dict)
    verifier = SupabaseAccessTokenVerifier(
        context.settings, jwks_client=Keys(PyJWK.from_dict(jwk))
    )
    monkeypatch.setattr(cleanup, "SupabaseAccessTokenVerifier", lambda _: verifier)
    context.directory.mkdir()
    values = {
        o.auth_subject: SecretStr(context.token(o.label))
        for o in context.manifest.owners
    }

    def invoke() -> tuple[UUID, UUID]:
        return cleanup.cleanup_manifested_subjects(
            context.settings,
            context.manifest,
            management_token="local-management",
            confirmation_run_id=context.manifest.run_id,
            journal_directory=context.directory,
            enabling_file=context.kill,
            access_tokens=values,
        )

    with pytest.raises(ValueError, match="Stopped"):
        invoke()
    context.kill.unlink()
    deleted = invoke()
    assert set(deleted) == {o.auth_subject for o in context.manifest.owners}
    assert context.deleted == {str(x) for x in deleted}
    delete_requests = [r for r in context.requests if r.method == "DELETE"]
    assert len(delete_requests) == 2
    assert all(
        r.url.path == "/auth/v1/admin/users/" + str(o.auth_subject)
        for r, o in zip(delete_requests, context.manifest.owners, strict=True)
    )
