"""Two explicitly scoped synthetic GoTrue accounts; no migrations or V6 injection.

The private manifest is created BEFORE the first account request. An uncertain
creation is never retried automatically. Existing real accounts are never listed.
"""

import argparse
import json
import logging
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import jwt

from app.core.config import Settings
from app.core.security import SupabaseAccessTokenVerifier
from scripts.verify_v6_hosted_auth import PROJECT_REF, PROJECT_URL, ROOT, write_json


def credentials(path: Path) -> tuple[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    if values.get("START23_SUPABASE_URL", "").rstrip("/") != PROJECT_URL:
        raise ValueError("Credential endpoint differs from the authorized project.")
    return (
        values["START23_SUPABASE_PUBLISHABLE_KEY"],
        values["START23_SUPABASE_SECRET_KEY"],
    )


def require_safe_preflight(preflight: dict[str, Any]) -> None:
    if (
        preflight.get("project", {}).get("id") != PROJECT_REF
        or preflight["project"].get("status") != "ACTIVE_HEALTHY"
        or preflight.get("metadata", {}).get("network_functions") != []
        or preflight["metadata"].get("side_effect_relations") != []
        or preflight.get("log_drains", {}).get("entry_count") != 0
    ):
        raise ValueError("The production safety preflight is incomplete or changed.")
    auth = preflight.get("auth", {})
    if not auth.get("external_email_enabled"):
        raise ValueError("Email authentication is unavailable.")
    if any(
        value
        for key, value in auth.items()
        if (key.startswith("hook_") or key.startswith("mailer_notifications_"))
        and key.endswith("_enabled")
    ):
        raise ValueError("An Auth callback or notification requires separate review.")
    triggers = [
        row
        for row in preflight["metadata"].get("triggers", [])
        if row["schema"] == "auth" and row["table"] == "users"
    ]
    if len(triggers) != 1 or triggers[0]["function"] != "ensure_athlete_identity_map":
        raise ValueError("The signup trigger requires renewed review.")
    definitions = preflight["metadata"].get("signup_function", [])
    if len(definitions) != 1:
        raise ValueError("The signup function has not been inspected.")
    source = definitions[0]["definition"]
    # This exact known function writes only the new subject's identity-map row.
    normalized = " ".join(source.split()).lower()
    expected = (
        "create or replace function private.ensure_athlete_identity_map() "
        "returns trigger language plpgsql security definer set search_path to '' "
        "as $function$ begin insert into private.athlete_identity_map "
        "( auth_user_id, creation_source ) values (new.id, 'auth_user_trigger') "
        "on conflict (auth_user_id) do nothing; return new; end; $function$"
    )
    if normalized != expected:
        raise ValueError("The signup function differs from the reviewed definition.")


class HostedAccounts:
    def __init__(self, directory: Path, public_key: str, secret_key: str) -> None:
        self.directory = directory.resolve()
        permitted = (ROOT / ".runtime/hosted-auth").resolve()
        if not self.directory.is_relative_to(permitted):
            raise ValueError("Private outputs must stay inside ignored hosted runtime.")
        self.path = self.directory / "manifest.private.json"
        self.public_key, self.secret_key = public_key, secret_key
        self.client = httpx.Client(
            base_url=PROJECT_URL, timeout=20, follow_redirects=False
        )
        self.summary: list[dict[str, Any]] = []
        if self.path.exists():
            self.manifest = json.loads(self.path.read_text(encoding="utf-8"))
            result_path = self.directory / "results.json"
            if result_path.exists():
                self.summary = json.loads(result_path.read_text(encoding="utf-8"))
            if self.manifest.get("project_ref") != PROJECT_REF:
                raise ValueError("Manifest project mismatch.")
        else:
            run_id = (
                datetime.now(timezone.utc).strftime("wombo-hosted-%Y%m%dT%H%M%SZ-")
                + uuid4().hex[:8]
            )
            self.manifest = {
                "run_id": run_id,
                "project_ref": PROJECT_REF,
                "accounts": {
                    label: {
                        "email": f"{run_id}-{label.lower()}@auth-verification.invalid",
                        "password": secrets.token_urlsafe(30),
                    }
                    for label in ("A", "B")
                },
            }
            self.persist()

    def persist(self) -> None:
        write_json(self.path, self.manifest)
        write_json(self.directory / "results.json", self.summary)

    def request(
        self,
        label: str,
        method: str,
        path: str,
        *,
        account: dict[str, Any] | None = None,
        admin: bool = False,
        body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        bearer: str | None = None,
    ) -> httpx.Response:
        allowed = {
            ("POST", "/auth/v1/admin/users"),
            ("POST", "/auth/v1/token"),
            ("GET", "/auth/v1/user"),
            ("POST", "/auth/v1/logout"),
            ("GET", "/auth/v1/.well-known/jwks.json"),
            ("GET", "/auth/v1/health"),
            ("POST", "/rest/v1/rpc/get_current_athlete_id"),
        }
        known_ids = {
            row.get("auth_user_id") for row in self.manifest["accounts"].values()
        }
        scoped_admin = (
            method in {"GET", "DELETE"}
            and path.startswith("/auth/v1/admin/users/")
            and path.rsplit("/", 1)[-1] in known_ids
            and admin
        )
        if (method, path) not in allowed and not scoped_admin:
            raise ValueError("Unapproved hosted Auth operation.")
        headers = {"apikey": self.secret_key if admin else self.public_key}
        if bearer is not None:
            headers["Authorization"] = "Bearer " + bearer
        response = self.client.request(
            method, path, headers=headers, json=body, params=params
        )
        self.summary.append({"case": label, "http_status": response.status_code})
        self.persist()
        return response

    def create_two(self) -> None:
        for label, account in self.manifest["accounts"].items():
            if account.get("auth_user_id"):
                continue
            if account.get("creation_attempted"):
                raise RuntimeError(
                    "Uncertain account creation: inspect the exact private manifest; "
                    "do not retry."
                )
            account["creation_attempted"] = True
            self.persist()
            response = self.request(
                label + ":admin_create",
                "POST",
                "/auth/v1/admin/users",
                admin=True,
                body={
                    "email": account["email"],
                    "password": account["password"],
                    "email_confirm": True,
                    "user_metadata": {"verification_run": self.manifest["run_id"]},
                },
            )
            if response.status_code not in (200, 201):
                raise RuntimeError(
                    "Synthetic creation rejected; response body was not logged."
                )
            data = response.json()
            account["auth_user_id"] = str(UUID(data["id"]))
            self.persist()

    def authenticate(self) -> None:
        verifier = SupabaseAccessTokenVerifier(
            Settings(
                environment="test",
                supabase_url=PROJECT_URL,
                _env_file=None,
            )
        )
        for label, account in self.manifest["accounts"].items():
            response = self.request(
                label + ":password_login",
                "POST",
                "/auth/v1/token",
                params={"grant_type": "password"},
                body={"email": account["email"], "password": account["password"]},
            )
            if response.status_code != 200:
                raise RuntimeError("Real password login failed.")
            session = response.json()
            account["current_session"] = session
            account["sessions_revoked"] = False
            account.setdefault("original_access_token", session["access_token"])
            self.persist()
            # Scheduling only: acceptance still uses the unchanged real verifier.
            issued = jwt.decode(
                session["access_token"], options={"verify_signature": False}
            )["iat"]
            delay = max(0.0, float(issued) - time.time())
            if delay > 5:
                raise RuntimeError("Local clock precedes the issued token; stop.")
            if delay:
                self.summary.append(
                    {
                        "case": label + ":local_clock_wait_until_iat",
                        "seconds": round(delay, 3),
                    }
                )
                time.sleep(delay + 0.05)
            identity = verifier.verify(session["access_token"])
            if str(identity.user_id) != account["auth_user_id"]:
                raise RuntimeError("Verified Auth subject mismatch.")
            self.summary.append(
                {"case": label + ":real_JWKS_ES256_issuer_audience", "status": "PASS"}
            )
            user = self.request(
                label + ":auth_user",
                "GET",
                "/auth/v1/user",
                bearer=session["access_token"],
            )
            if user.status_code != 200 or user.json()["id"] != account["auth_user_id"]:
                raise RuntimeError("GoTrue identity mismatch.")
            mapped = self.request(
                label + ":opaque_mapping",
                "POST",
                "/rest/v1/rpc/get_current_athlete_id",
                bearer=session["access_token"],
                body={},
            )
            if mapped.status_code != 200:
                raise RuntimeError("Opaque athlete mapping unavailable.")
            athlete_id = str(UUID(mapped.json()))
            if athlete_id == account["auth_user_id"]:
                raise RuntimeError("The domain identity was not opaque.")
            account["athlete_id"] = athlete_id
            self.persist()
        if len({a["athlete_id"] for a in self.manifest["accounts"].values()}) != 2:
            raise RuntimeError("Test accounts share a domain identity.")

    def auth_checks(self) -> None:
        from cryptography.hazmat.primitives.asymmetric import ec

        settings = Settings(
            environment="test", supabase_url=PROJECT_URL, _env_file=None
        )
        jwks = jwt.PyJWKClient(settings.supabase_jwks_url)
        for label, account in self.manifest["accounts"].items():
            token = account["current_session"]["access_token"]
            key = jwks.get_signing_key_from_jwt(token)
            for case, overrides, error_type in (
                (
                    "wrong_issuer",
                    {"issuer": "https://unexpected.invalid/auth/v1"},
                    jwt.InvalidIssuerError,
                ),
                (
                    "wrong_audience",
                    {"audience": "unexpected-audience"},
                    jwt.InvalidAudienceError,
                ),
                (
                    "wrong_key",
                    {"key": ec.generate_private_key(ec.SECP256R1()).public_key()},
                    jwt.InvalidSignatureError,
                ),
            ):
                values: dict[str, Any] = {
                    "key": key,
                    "algorithms": ["ES256"],
                    "issuer": settings.supabase_jwt_issuer,
                    "audience": "authenticated",
                    **overrides,
                }
                try:
                    jwt.decode(token, **values)
                except error_type:
                    self.summary.append(
                        {
                            "case": label + ":" + case,
                            "status": "PASS",
                            "scope": "local_verifier_real_issued_token",
                        }
                    )
                else:
                    raise RuntimeError(
                        "A genuine token passed an invalid verification context."
                    )
            parts = token.split(".")
            parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
            tampered = self.request(
                label + ":tampered_token",
                "GET",
                "/auth/v1/user",
                bearer=".".join(parts),
            )
            if tampered.status_code not in (401, 403):
                raise RuntimeError("GoTrue did not reject the tampered credential.")
            refresh = self.request(
                label + ":refresh",
                "POST",
                "/auth/v1/token",
                params={"grant_type": "refresh_token"},
                body={"refresh_token": account["current_session"]["refresh_token"]},
            )
            if refresh.status_code != 200:
                raise RuntimeError("Genuine refresh failed.")
            session = refresh.json()
            if session["refresh_token"] == account["current_session"]["refresh_token"]:
                raise RuntimeError("The refresh credential did not rotate.")
            account["current_session"] = session
            self.persist()
            user = self.request(
                label + ":refreshed_user",
                "GET",
                "/auth/v1/user",
                bearer=session["access_token"],
            )
            if user.status_code != 200 or user.json()["id"] != account["auth_user_id"]:
                raise RuntimeError("Refreshed identity mismatch.")
            for case, headers in (
                ("missing_api_key", {"Authorization": "Bearer " + token}),
                (
                    "invalid_api_key",
                    {
                        "apikey": "invalid-verification-key",
                        "Authorization": "Bearer " + token,
                    },
                ),
                ("publishable_without_user", {"apikey": self.public_key}),
            ):
                response = self.client.post(
                    "/rest/v1/rpc/get_current_athlete_id", headers=headers, json={}
                )
                self.summary.append(
                    {"case": label + ":" + case, "http_status": response.status_code}
                )
                if response.status_code not in (401, 403, 404):
                    raise RuntimeError(
                        "API-key-only or invalid routing unexpectedly "
                        "resolved an athlete."
                    )
            response = self.client.get(
                "/auth/v1/user", headers={"apikey": self.public_key}
            )
            self.summary.append(
                {
                    "case": label + ":missing_access_token",
                    "http_status": response.status_code,
                }
            )
            if response.status_code not in (401, 403):
                raise RuntimeError("Missing access credential was accepted.")
            self.persist()

    def logout_checks(self) -> None:
        for label, account in self.manifest["accounts"].items():
            session = account["current_session"]
            response = self.request(
                label + ":global_logout",
                "POST",
                "/auth/v1/logout",
                bearer=session["access_token"],
                params={"scope": "global"},
            )
            if response.status_code not in (200, 204):
                raise RuntimeError("Test-only logout failed.")
            refreshed = self.request(
                label + ":revoked_refresh",
                "POST",
                "/auth/v1/token",
                params={"grant_type": "refresh_token"},
                body={"refresh_token": session["refresh_token"]},
            )
            if refreshed.status_code not in (400, 401, 403):
                raise RuntimeError("A revoked test refresh credential was accepted.")
            self.request(
                label + ":residual_access_auth",
                "GET",
                "/auth/v1/user",
                bearer=session["access_token"],
            )
            self.request(
                label + ":residual_access_data_api",
                "POST",
                "/rest/v1/rpc/get_current_athlete_id",
                bearer=session["access_token"],
                body={},
            )
            account["sessions_revoked"] = True
            self.persist()

    def security_reads(self) -> None:
        for caller, target in (("A", "B"), ("B", "A")):
            source = self.manifest["accounts"][caller]
            victim = self.manifest["accounts"][target]
            headers = {
                "apikey": self.public_key,
                "Authorization": "Bearer " + source["current_session"]["access_token"],
            }
            for table, params in (
                ("weekly_plans", {"id": "eq." + victim["plan"]["id"], "select": "id"}),
                (
                    "athlete_physiology_profiles",
                    {
                        "athlete_id": "eq." + victim["athlete_id"],
                        "select": "athlete_id",
                    },
                ),
            ):
                response = self.client.get(
                    "/rest/v1/" + table, params=params, headers=headers
                )
                self.summary.append(
                    {
                        "case": caller + ":gateway_foreign_" + table,
                        "http_status": response.status_code,
                    }
                )
                if response.status_code != 200 or response.json() != []:
                    raise RuntimeError(
                        "Foreign gateway read unexpectedly returned data; stop."
                    )
            private = self.client.get(
                "/rest/v1/planned_workout_loads",
                params={
                    "planned_workout_id": "eq." + victim["plan"]["workouts"][0]["id"],
                    "select": "planned_workout_id",
                },
                headers={**headers, "Accept-Profile": "private"},
            )
            self.summary.append(
                {
                    "case": caller + ":private_schema_gateway_denial",
                    "http_status": private.status_code,
                }
            )
            if private.status_code != 406:
                raise RuntimeError("Private schema exposure differs; stop for review.")
            generated = self.client.post(
                "/rest/v1/rpc/create_weekly_plan_proposal_v3",
                headers=headers,
                json={"p_athlete_id": victim["auth_user_id"], "p_payload": {}},
            )
            self.summary.append(
                {
                    "case": caller + ":athlete_cannot_call_service_generation",
                    "http_status": generated.status_code,
                }
            )
            if generated.status_code not in (403, 404):
                raise RuntimeError("The service-only generator was not denied; stop.")
            admin = self.client.get(
                "/auth/v1/admin/users/" + victim["auth_user_id"], headers=headers
            )
            self.summary.append(
                {
                    "case": caller + ":athlete_cannot_use_auth_admin",
                    "http_status": admin.status_code,
                }
            )
            if admin.status_code not in (401, 403):
                raise RuntimeError(
                    "Athlete accessed another synthetic Auth admin record; stop."
                )
            self.persist()

    def expiry_checks(self) -> None:
        settings = Settings(
            environment="test", supabase_url=PROJECT_URL, _env_file=None
        )
        verifier = SupabaseAccessTokenVerifier(settings)
        jwks = jwt.PyJWKClient(settings.supabase_jwks_url)
        for label, account in self.manifest["accounts"].items():
            if any(
                row.get("case") == label + ":genuine_expiry_unchanged_verifier"
                and row.get("status") == "PASS"
                for row in self.summary
            ):
                continue
            token = account["original_access_token"]
            expires = jwt.decode(token, options={"verify_signature": False})["exp"]
            if time.time() <= float(expires):
                raise RuntimeError(
                    "The genuine original token has not expired; do not simulate."
                )
            key = jwks.get_signing_key_from_jwt(token)
            try:
                jwt.decode(
                    token,
                    key,
                    algorithms=["ES256"],
                    audience="authenticated",
                    issuer=settings.supabase_jwt_issuer,
                )
            except jwt.ExpiredSignatureError:
                pass
            else:
                raise RuntimeError("Real-time expiry was not rejected.")
            from app.core.security import InvalidAccessTokenError

            try:
                verifier.verify(token)
            except InvalidAccessTokenError:
                pass
            else:
                raise RuntimeError("The unchanged verifier accepted an expired token.")
            response = self.request(
                label + ":genuine_expired_gateway_token",
                "POST",
                "/rest/v1/rpc/get_current_athlete_id",
                bearer=token,
                body={},
            )
            if response.status_code != 401 or "expired" not in response.text.lower():
                raise RuntimeError("Gateway expiry rejection was not explicit.")
            self.summary.append(
                {
                    "case": label + ":genuine_expiry_unchanged_verifier",
                    "status": "PASS",
                    "clock_or_token_patched": False,
                }
            )
            self.persist()

    def cleanup(self) -> None:
        for label, account in self.manifest["accounts"].items():
            if account.get("deleted"):
                continue
            uid = str(UUID(account["auth_user_id"]))
            path = "/auth/v1/admin/users/" + uid
            check = self.request(
                label + ":cleanup_verify_identity", "GET", path, admin=True
            )
            if check.status_code != 200:
                raise RuntimeError(
                    "Cleanup identity cannot be confirmed; leave isolated."
                )
            user = check.json()
            if (
                user.get("id") != uid
                or user.get("email") != account["email"].lower()
                or user.get("user_metadata", {}).get("verification_run")
                != self.manifest["run_id"]
            ):
                raise RuntimeError("Cleanup manifest ownership mismatch; no deletion.")
            if not account.get("sessions_revoked"):
                raise RuntimeError("Revoke test sessions before cleanup.")
            deletion = self.request(
                label + ":delete_exact_test_user", "DELETE", path, admin=True
            )
            if deletion.status_code not in (200, 204):
                raise RuntimeError(
                    "Supported test-user deletion failed; no SQL fallback."
                )
            account["deleted"] = True
            self.persist()
            absence = self.request(
                label + ":deleted_user_absent", "GET", path, admin=True
            )
            if absence.status_code != 404:
                raise RuntimeError("Deleted test user remains accessible.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-two-synthetic-accounts", action="store_true")
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--credential-file", type=Path, required=True)
    parser.add_argument("--private-directory", type=Path, required=True)
    parser.add_argument(
        "--phase",
        choices=(
            "authenticate",
            "auth-checks",
            "security-reads",
            "logout",
            "cleanup",
            "expiry",
        ),
        default="authenticate",
    )
    args = parser.parse_args()
    if not args.execute_two_synthetic_accounts:
        parser.error("Explicit scoped execution is required.")
    require_safe_preflight(json.loads(args.preflight.read_text(encoding="utf-8")))
    public_key, secret_key = credentials(args.credential_file)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    runner = HostedAccounts(args.private_directory, public_key, secret_key)
    if args.phase == "authenticate":
        runner.create_two()
        runner.authenticate()
    elif args.phase == "auth-checks":
        runner.auth_checks()
    elif args.phase == "logout":
        runner.logout_checks()
    elif args.phase == "security-reads":
        runner.security_reads()
    elif args.phase == "expiry":
        runner.expiry_checks()
    else:
        runner.cleanup()
    print("Scoped genuine Auth phase completed:", args.phase)


if __name__ == "__main__":
    main()
