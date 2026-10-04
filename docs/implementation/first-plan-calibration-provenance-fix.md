# First-plan calibration history provenance fix

Verified on 2026-10-04 in `fix/catalog-capacity-fresh-athlete`, based on
`6bb3a047139d91c71ac065c35a8af595221b54c5`. No UI V2 synchronization or push
was performed.

## Resumed evidence and root cause

The retained worktree had six modified files: planning domain/repository/service
and their corresponding tests. The changes already carried an approval marker
into first-plan classification and covered calibration history. They were
preserved and completed; the initial direct-table lookup was replaced with a
function-scoped read after hosted verification showed its SELECT grant was
deliberately unavailable.

The original authenticated failure was HTTP 409 `catalog_capacity_unsatisfied`,
request ID `2023c38e-dc30-458b-a18a-291cb9e6c977`, locally and in staging.
The athlete had RUN history of 180 minutes/week, BIKE/SWIM zero, completed
calibration/onboarding, no injuries or cross-training opt-ins, and no approved
weekly plan. Removing only the calibration activity/history row succeeded.

`get_plan_load_history_for_planning_v13`, wrapped by v14, creates complete
calendar weeks from the earliest plan **or activity**. `fetch_load_history`
passed those rows to `PlanningService._load_samples` and `resolve_target`.
The previous first-plan criterion was an empty history tuple. An activity row
therefore bypassed the first-plan exception and supplied a nonexistent approved
planned-load basis at a race-anchored recovery position.

## Approval criterion and baseline

The additive v15 history RPC joins `weekly_plans` to `plan_revisions` on
plan ID, athlete ID, and `active_revision = revision_number`. Only a revision
in `active` or `superseded` state, with a week strictly before the requested
week, establishes prior approval. The approval lifecycle sets this composite
foreign-key pointer; pending/rejected/expired proposals and activity rows do
not establish it.

This is an athlete-level existence check over the entire persisted history,
independent of the six-week load window or which plan is currently displayed.
For each historical week, the existing reader selects that plan's approved
`active_revision`; existing returning-athlete target selection continues to use
the latest eligible nonsick history and the existing realized-history rules.
Older historical approved plans still establish returning-athlete status.
No load, timestamp, or row-existence heuristic establishes approval.

The repository requires an explicit boolean from the trusted RPC. Domain/service
defaults never interpret absent or malformed approval provenance as approval.
An athlete without an approved prior plan takes onboarding BASE behavior in the
ordinary planning window, even when calibration/activity rows exist. Existing
taper/maintenance precedence is retained. Approval classification survives sick
week filtering; if a returning athlete has no eligible nonsick baseline, planning
fails closed instead of inventing a first-plan target.

The v15 function has an empty search path, checks the trusted JWT role, and grants
EXECUTE only to `service_role`. Table grants, RLS, public API models, and historical
load values/provenance remain unchanged.

## Verification

- Full backend: **778 passed**, one existing Starlette/httpx deprecation warning.
- Targeted final runs: repository/API **63 passed**, domain/repository **102
  passed**, catalog matrix **44 passed**; these cover **196 distinct tests**
  because the 13 repository tests are present in two runs.
- Strict mypy: **139 backend/test files**, plus the separately checked hosted
  replay script; Ruff, formatting (**140 files**), and `git diff --check` passed.
- OpenAPI/public-contract suite: **6 passed**, also included in the full suite.
- RUN first-plan matrices retain 0/1/3/6/8/10/15 hours, completed calibration,
  ordinary/missing-provenance activity history, BASE selection, valid workouts,
  HTTP 201, public privacy, and idempotent retries.
- Returning-athlete coverage retains normal progression, four-build/one-recovery
  rhythm, missed/fatigue/sick handling, taper, injury redistribution, repeated
  occurrences, catalog phase filters, stale/revision guards, and privacy.
- Development database: **27 suites, 562 pgTAP assertions, zero failures**,
  including **10** new approval-provenance/RLS/grant assertions. Docker/Podman
  was unavailable; the suites ran transactionally through the existing linked
  SQL transport with every TAP result collected and each fixture rolled back.
- Database lint and error-level security advisors passed; a subsequent migration
  dry run reported no pending migrations.

## Hosted exact sequence and cleanup

Final deployment `7b499763-a64b-4762-b67c-e606172cf5ba` reached SUCCESS on
Railway `r6-api` / `r6-staging`. Supabase target was exclusively `start23-dev`
(`isfumhgqphieoayqahjv`).

`scripts/verify_first_plan_calibration.py` creates one disposable athlete per
run through normal profile, race, 180-minute RUN history, calibration observation,
pending zone confirmation/approval, and onboarding APIs. Private verification
confirms the calibration history exists, no prior approval exists, the target is
onboarding BASE, and a valid workout combination exists, without logging load.

The successful hosted replay returned **HTTP 201** for the first swipe draft
and **HTTP 200** for its deck GET, with a nonempty candidate/workout count and
no capacity error or private-load leak. After its first plan was explicitly
approved, persisted provenance identified it as returning and the next week used
BUILD/missed-week progression rather than first-plan BASE.

The successful actor's sessions were revoked and Auth deletion was verified by
HTTP 404. Two earlier attempts stopped in helper/private-check setup and each
also revoked/deleted its actor. The original investigation's retained disposable
actor was separately owner-checked, deleted, and verified absent. No real
athlete's historical plans were modified.

One forward-only migration was required:
`20261004212750_first_plan_approved_provenance.sql`. It adds a read-only RPC;
no historical data transformation/recalculation was required. No catalog,
Start-TSS coefficients, BASE/recovery formulas, calibration physiology, target-fit
tolerance, selector bounds, eligibility, or public privacy behavior changed.
Production was not mutated. Main and all other branches were not pushed. The
coach edit, Garmin documentation, PDFs, unpublished regressions, and UI V2
worktrees/branches were preserved.

## UI V2 synchronization recommendation

The six Slice 1 commits are currently on `feat/wombo-ui-v2-workout-detail`, ending
at `45e948484f769516ba1d1626641b71a62e50d58c`; `feat/wombo-ui-v2` still points
at the V1 baseline commit. The annotated `wombo-ui-v1-pre-v2-6bb3a04` tag peels
to `6bb3a047139d91c71ac065c35a8af595221b54c5` and remains unchanged.

After explicit synchronization authorization, create an isolated sync branch
from that six-commit Slice 1 head, cherry-pick this bugfix commit, and rerun
backend, database, and relevant mobile gates. Then fast-forward
`feat/wombo-ui-v2` to the reviewed sync head. Preserve the six commits and V1 tag;
do not rebase or squash Slice 1. This adds one independently revertible bugfix
commit and preserves the existing UI rollback structure. No sync was performed.
