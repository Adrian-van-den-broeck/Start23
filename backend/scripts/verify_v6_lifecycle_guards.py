"""Real SQL fail-closed checks against captured automatic V6 check-in payloads."""

import argparse
import copy
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from app.modules.planning.repository import (
    PlanningRepositoryConflictError,
    PlanningRepositoryNotFoundError,
    PlanningRepositoryUnavailableError,
)
from scripts.verify_v6_lifecycle_completion import (
    client_for,
    prepare_checkin,
    request,
    state,
)
from scripts.verify_v6_postgres import USERS, LocalPostgres, literal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--week-start", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        raise SystemExit("Explicit disposable loopback database opt-in required")
    db = LocalPostgres()
    repo, client = client_for(db)
    original = repo._request
    captured: dict[str, Any] = {}

    async def capture_before_write(method: str, path: str, **kwargs: Any) -> Any:
        if path == "rpc/create_v6_weekly_plan_proposal":
            captured.update(kwargs["json"])
            raise PlanningRepositoryUnavailableError
        return await original(method, path, **kwargs)

    with client:
        cid = prepare_checkin(client, args.week_start.isoformat())
        endpoint = "/checkins/" + cid + "/plan-proposals"
        before = state(db)
        repo._request = capture_before_write  # type: ignore[method-assign]
        request(client, "POST", endpoint, expected=503)
        repo._request = original  # type: ignore[method-assign]
        assert state(db) == before and captured
        stale = copy.deepcopy(captured)

        def rejected(body: dict[str, Any], code: str) -> None:
            previous = state(db)
            try:
                db.execute(
                    "select public.create_v6_weekly_plan_proposal("
                    + literal(USERS[0])
                    + ","
                    + literal(body["p_payload"])
                    + ")",
                    service=True,
                )
            except (
                PlanningRepositoryConflictError,
                PlanningRepositoryNotFoundError,
            ) as error:
                if isinstance(error, PlanningRepositoryNotFoundError):
                    assert code == "P0002"
                else:
                    assert error.code == code
            else:
                raise AssertionError("Tampered or stale context committed")
            assert state(db) == previous

        original_context = db.execute(
            "select to_jsonb(c) - 'state' from public.weekly_checkin_contexts c "
            "where checkin_id=" + literal(cid) + " and state='confirmed'"
        )
        current = request(client, "GET", "/checkins/" + cid)
        fields = (
            "blocked_dates",
            "fatigue_level",
            "missed_workout_reasons",
            "recurring_activities_confirmed",
            "external_activities",
            "restrictions",
            "alarm_symptoms_acknowledged",
        )
        payload = {k: current["context"][k] for k in fields}
        payload.update(
            expected_revision=current["context_revision"],
            blocked_dates=[(args.week_start + timedelta(days=1)).isoformat()],
        )
        saved = request(client, "PUT", "/checkins/" + cid + "/context", body=payload)
        rejected(stale, "PT409")  # latest context is still an unconfirmed draft
        request(
            client,
            "POST",
            "/checkins/" + cid + "/context-confirmation",
            body={
                "expected_revision": saved["context_revision"],
                "context_fingerprint": saved["context"]["fingerprint"],
            },
        )

        rejected(stale, "PT409")
        assert (
            db.execute(
                "select to_jsonb(c) - 'state' from public.weekly_checkin_contexts c "
                "where checkin_id="
                + literal(cid)
                + " and revision=1 and state='superseded'"
            )
            == original_context
        )
        captured.clear()
        repo._request = capture_before_write  # type: ignore[method-assign]
        request(client, "POST", endpoint, expected=503)
        repo._request = original  # type: ignore[method-assign]
        foreign = copy.deepcopy(captured)
        foreign["p_payload"]["checkin_id"] = db.execute(
            "select to_jsonb(id) from public.weekly_checkins where athlete_id="
            + literal(USERS[1])
            + " limit 1"
        )
        rejected(foreign, "P0002")
        tampered = copy.deepcopy(captured)
        tampered["p_payload"]["workouts"][0]["source_revision_sha256"] = "0" * 64
        rejected(tampered, "23514")
        tampered = copy.deepcopy(captured)
        tampered["p_payload"]["target_tss"] = "999999"
        rejected(tampered, "23514")
        valid = request(client, "POST", endpoint)
        assert valid == request(client, "POST", endpoint)
        assert (
            request(client, "GET", "/checkins/" + cid)["plan_proposal_id"]
            == valid["proposal"]["id"]
        )
    args.output.write_text(
        json.dumps(
            {
                "stale_checkin_revision": "PT409",
                "foreign_checkin": "P0002",
                "tampered_source": "23514",
                "tampered_budget": "23514",
                "all_failed_transactions_rolled_back": True,
                "superseded_confirmation_provenance_preserved": True,
                "new_draft_blocks_old_confirmed_context": True,
                "valid_automatic_attachment_replayed": True,
            },
            indent=2,
        )
        + "\n"
    )
    print("Actual SQL check-in revision/source/owner/budget guards PASS")


if __name__ == "__main__":
    main()
