"""Local-only safety regression tests for the production verification tools."""

from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest

from scripts import verify_v6_hosted_accounts as accounts_module
from scripts.verify_v6_hosted_accounts import HostedAccounts
from scripts.verify_v6_hosted_auth import PROJECT_URL, management_request
from scripts.verify_v6_hosted_inventory import identifier, query
from scripts.verify_v6_hosted_lifecycle import Lifecycle


@pytest.fixture
def accounts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> HostedAccounts:
    monkeypatch.setattr(accounts_module, "ROOT", tmp_path)
    result = HostedAccounts(
        tmp_path / ".runtime/hosted-auth/test", "unit-public", "unit-secret"
    )
    result.client.close()
    return result


def test_unknown_sql_never_reaches_the_management_endpoint() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match="fixed metadata"):
            management_request(
                client, "migrations", "select 1; drop table public.example"
            )
    assert requests == []


@pytest.mark.parametrize("unsafe", ["public;delete", 'a"b', "a.b", "unsafe\nname"])
def test_inventory_rejects_untrusted_catalog_identifiers(unsafe: str) -> None:
    with pytest.raises(ValueError):
        identifier(unsafe)


def test_inventory_never_accepts_a_write_query() -> None:
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: pytest.fail("must not dispatch"))
    ) as client:
        with pytest.raises(ValueError, match="SELECT only"):
            query(client, "delete from public.example")


def test_auth_admin_cannot_enumerate_or_delete_an_unmanifested_user(
    accounts: HostedAccounts,
) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200)

    accounts.client = httpx.Client(transport=httpx.MockTransport(handle))
    for method, path in (
        ("GET", "/auth/v1/admin/users"),
        ("DELETE", "/auth/v1/admin/users/" + str(UUID(int=99))),
    ):
        with pytest.raises(ValueError, match="Unapproved"):
            accounts.request("unit-denial", method, path, admin=True)
    assert calls == []
    accounts.client.close()


def test_uncertain_second_creation_never_creates_a_third_account(
    accounts: HostedAccounts,
) -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, json={"id": str(UUID(int=1))})
        raise httpx.ReadTimeout("unknown creation outcome", request=request)

    accounts.client = httpx.Client(
        base_url=PROJECT_URL, transport=httpx.MockTransport(handle)
    )
    with pytest.raises(httpx.ReadTimeout):
        accounts.create_two()
    with pytest.raises(RuntimeError, match="Uncertain account creation"):
        accounts.create_two()
    assert len(calls) == 2
    assert accounts.manifest["accounts"]["A"]["auth_user_id"] == str(UUID(int=1))
    assert accounts.manifest["accounts"]["B"]["creation_attempted"] is True
    accounts.client.close()


def test_cleanup_checks_run_ownership_before_deleting(accounts: HostedAccounts) -> None:
    for index, row in enumerate(accounts.manifest["accounts"].values(), 1):
        row.update(auth_user_id=str(UUID(int=index)), sessions_revoked=True)
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200, json={"email": "unrelated.invalid", "user_metadata": {}}
        )

    accounts.client = httpx.Client(
        base_url=PROJECT_URL, transport=httpx.MockTransport(handle)
    )
    with pytest.raises(RuntimeError, match="ownership mismatch"):
        accounts.cleanup()
    assert [request.method for request in calls] == ["GET"]
    accounts.client.close()


def test_unexpected_foreign_success_stops_the_affected_sequence(
    accounts: HostedAccounts,
) -> None:
    account: dict[str, Any] = {"current_session": {"access_token": "unit-only"}}
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"id": "unit-owned"})

    with httpx.Client(
        base_url="http://127.0.0.1",
        transport=httpx.MockTransport(handle),
    ) as client:
        flow = Lifecycle(accounts, client)
        with pytest.raises(RuntimeError, match="unexpectedly succeeded"):
            flow.call(
                "unit-foreign",
                account,
                "GET",
                "/api/v1/weekly-plans/unit",
                foreign=True,
            )
    assert len(calls) == 1


def test_public_private_load_leak_stops_before_more_requests(
    accounts: HostedAccounts,
) -> None:
    account: dict[str, Any] = {"current_session": {"access_token": "unit-only"}}
    with httpx.Client(
        base_url="http://127.0.0.1",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"nested": [{"planned_load": "unit-private"}]}
            )
        ),
    ) as client:
        flow = Lifecycle(accounts, client)
        with pytest.raises(RuntimeError, match="Private field"):
            flow.call("unit-leak", account, "GET", "/api/v1/weekly-plans/unit")
