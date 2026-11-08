"""In-memory test implementation of the additional frozen V6 storage contract.

Authentication, draft CAS, confirmation and ownership reuse the existing A3-A9
repository fixture. No hosted behavior is represented as externally verified.
"""

from copy import deepcopy
from uuid import UUID, uuid4

from test_planning import _NOW, MemoryPlanningRepository

from app.modules.planning.repository import (
    JsonObject,
    PlanningRepositoryConflictError,
    PlanningRepositoryNotFoundError,
)
from app.modules.workouts.joren_v6_official import V6Template


class V6MemoryRepository(MemoryPlanningRepository):
    supports_frozen_v6_snapshots = True

    def __init__(
        self, owners: dict[str, UUID], catalog: tuple[V6Template, ...]
    ) -> None:
        super().__init__(owners)
        self.catalog = {t.id: t for t in catalog}
        self.frozen_payloads: dict[tuple[UUID, int], JsonObject] = {}
        self.history: dict[tuple[UUID, int], JsonObject] = {}
        self.edit_results: dict[tuple[UUID, str], JsonObject] = {}
        for request in self._requests.values():
            request["input_snapshot"]["discipline_setups"] = []
            for row in request["input_snapshot"]["training_history"]:
                row["previous_month_weekly_minutes"] = "0"

    async def fetch_v6_edit_retry(
        self, athlete_id: UUID, operation_key: str
    ) -> JsonObject | None:
        return deepcopy(self.edit_results.get((athlete_id, operation_key)))

    async def fetch_workout_context(
        self, access_token: str, workout_id: UUID
    ) -> JsonObject:
        for pid, plan in self._plans.items():
            if self._plan_owners[pid] != self._owner(access_token):
                continue
            if plan["revision_state"] == "active" and any(
                str(workout_id) in {w["id"], w["physical_workout_id"]}
                for w in plan["workouts"]
            ):
                return {"plan": await self.fetch_plan(access_token, pid)}
        raise PlanningRepositoryNotFoundError

    async def move_v6_workout(
        self, athlete_id: UUID, payload: JsonObject
    ) -> JsonObject:
        key = (athlete_id, payload["operation_key"])
        if key in self.edit_results:
            return deepcopy(self.edit_results[key])
        pid = UUID(payload["plan_id"])
        current = self._plans[pid]
        if (
            self._plan_owners[pid] != athlete_id
            or current["active_revision"] != payload["expected_revision"]
        ):
            raise PlanningRepositoryConflictError("proposal_stale")
        self.history[pid, current["revision"]] = deepcopy(current)
        updated = deepcopy(current)
        updated["revision"] += 1
        updated["active_revision"] = updated["revision"]
        updated["revision_id"] = str(uuid4())
        updated["proposal"] = None
        for row in updated["workouts"]:
            row["physical_workout_id"] = str(uuid4())
            if row["id"] == payload["occurrence_id"]:
                row["scheduled_date"] = payload["scheduled_date"]
        frozen = deepcopy(self.frozen_payloads[pid, current["revision"]])
        for row in frozen["workouts"]:
            if row["occurrence_id"] == payload["occurrence_id"]:
                row["scheduled_date"] = payload["scheduled_date"]
        self.frozen_payloads[pid, updated["revision"]] = frozen
        self._plans[pid] = updated
        public = {k: v for k, v in updated.items() if not k.startswith("_")}
        self.edit_results[key] = {"plan": public, "proposal": None}
        return deepcopy(self.edit_results[key])

    async def create_plan_proposal(
        self, athlete_id: UUID, payload: JsonObject
    ) -> JsonObject:
        key = (athlete_id, str(payload["generation_fingerprint"]))
        if key in self._fingerprints:
            pid, retry_proposal, revision = self._fingerprints[key]
            return {
                "plan_id": str(pid),
                "proposal_id": str(retry_proposal),
                "revision": revision,
            }
        pid = UUID(payload["plan_id"]) if payload["plan_id"] else uuid4()
        current = self._plans.get(pid)
        if current is not None and self._plan_owners[pid] != athlete_id:
            raise PlanningRepositoryNotFoundError
        active = current["active_revision"] if current else None
        if (active or 0) != payload["expected_base_revision"]:
            raise PlanningRepositoryConflictError(
                "proposal_stale", "The active plan changed."
            )
        if payload.get("expected_pending_revision") is not None and (
            current is None
            or current["revision"] != payload["expected_pending_revision"]
            or current["proposal"]["id"] != payload["expected_proposal_id"]
            or current["proposal"]["state"] != "pending"
        ):
            raise PlanningRepositoryConflictError(
                "pending_revision_stale", "The pending plan changed."
            )
        revision = current["revision"] + 1 if current else 1
        if current:
            self.history[pid, current["revision"]] = deepcopy(current)
            if current["proposal"]["state"] == "pending":
                self._proposals[UUID(current["proposal"]["id"])]["state"] = "expired"
        revision_id = uuid4()
        proposal_id = uuid4()
        workouts = []
        for row in payload["workouts"]:
            t = self.catalog[UUID(row["template_id"])]
            segments = self._segments(t)
            for s, e in zip(segments, t.segments):
                s["duration_minutes"] = (
                    str(e.duration_minutes) if e.duration_minutes is not None else None
                )
            workouts.append(
                {
                    "id": row["occurrence_id"] or str(uuid4()),
                    "physical_workout_id": str(uuid4()),
                    "template_id": str(t.id),
                    "template_key": str(t.template_key),
                    "template_version": t.version,
                    "discipline": t.discipline.value,
                    "name": t.name,
                    "description": t.description,
                    "duration_minutes": str(t.duration_minutes)
                    if t.duration_minutes is not None
                    else None,
                    "distance_meters": t.distance_meters,
                    "intensity_bucket": t.intensity_bucket.value,
                    "expected_rpe_min": t.expected_rpe_min,
                    "expected_rpe_max": t.expected_rpe_max,
                    "segments": segments,
                    "scheduled_date": row["scheduled_date"],
                    "source": row["source"],
                    "status": "scheduled",
                    "warnings": [],
                }
            )
        proposal = {
            "id": str(proposal_id),
            "kind": "plan_revision",
            "state": "pending",
            "reason_codes": [w["code"] for w in payload["warnings"]]
            or ["weekly_plan_ready"],
            "public_explanation": "A deterministic weekly plan is ready for review.",
            "ruleset_version": payload["ruleset_version"],
            "created_at": _NOW.isoformat(),
            "target_plan_revision_id": str(revision_id),
            "base_plan_revision": payload["expected_base_revision"],
        }
        public = {
            k: payload[k]
            for k in (
                "week_start",
                "timezone",
                "phase",
                "target_basis",
                "taper_period",
                "total_duration_minutes",
                "low_intensity_percent",
                "high_intensity_percent",
                "confirmed_injuries",
                "low_only_disciplines",
                "available_dates",
                "availability_source",
            )
        }
        public.update(
            id=str(pid),
            state="active" if active else "pending_approval",
            active_revision=active,
            revision_id=str(revision_id),
            revision=revision,
            revision_state="pending_approval",
            workouts=workouts,
            warnings=[
                dict(
                    id=str(uuid4()),
                    planned_workout_id=None,
                    **{k: w[k] for k in ("rule_id", "code", "severity", "message")},
                )
                for w in payload["warnings"]
            ],
            proposal=proposal,
        )
        self._plans[pid] = {**public, "_target_tss": payload["target_tss"]}
        self._plan_owners[pid] = athlete_id
        self._proposals[proposal_id] = proposal
        self._proposal_owners[proposal_id] = athlete_id
        self._fingerprints[key] = (pid, proposal_id, revision)
        self.frozen_payloads[pid, revision] = deepcopy(payload)
        if payload.get("v6_edit_operation_key"):
            self.edit_results[athlete_id, payload["v6_edit_operation_key"]] = {
                "plan": deepcopy(public),
                "proposal": deepcopy(proposal),
            }
        return {
            "plan_id": str(pid),
            "proposal_id": str(proposal_id),
            "revision": revision,
        }

    async def fetch_plan(
        self, access_token: str, plan_id: UUID, revision: int | None = None
    ) -> JsonObject:
        if self._plan_owners.get(plan_id) != self._owner(access_token):
            raise PlanningRepositoryNotFoundError
        current = self._plans[plan_id]
        value = (
            current
            if revision is None or revision == current["revision"]
            else self.history.get((plan_id, revision))
        )
        if value is None:
            raise PlanningRepositoryNotFoundError
        return {k: deepcopy(v) for k, v in value.items() if not k.startswith("_")}

    async def fetch_plan_context(self, athlete_id: UUID, plan_id: UUID) -> JsonObject:
        context = await super().fetch_plan_context(athlete_id, plan_id)
        payload = self.frozen_payloads[plan_id, context["revision"]]
        context["v6_frozen_snapshot"] = deepcopy(payload["v6_frozen_snapshot"])
        return context
