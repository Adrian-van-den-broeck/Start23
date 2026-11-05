# V6 automatic selection implementation

2026-11-05, Europe/Amsterdam. Policy `joren-v6-automatic-selection-1`.
Branch `feat/joren-v6-automatic-selection`; isolated worktree
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-automatic-selection`.

## Starting point and authority

Accepted `feat/joren-v6-phase-tss-integration` was clean at exact SHA
`fc876f10b5eb779a7f3004b460744da899cc739b`. Ancestry from accepted final policy
`acdc5fbd36677680f9083a308cb1f760aa7c71eb` was verified before creating this new
branch/worktree. Root/nearest AGENTS, current roadmap, C3–C5/phase/TSS reports,
final-policy decisions, A3–A9 planning/persistence contracts, Realized V2 and
existing optimized-search evidence were read. No nearer backend/docs AGENTS exists.
No pre-existing worktree, A5/A6 release branch or production system was changed.

The current owner instruction accepts the official TSS proposal and requires an
automatic choice, partial-week fallback and suitable swipe alternatives. It
permits L1 as the engineering allocation metric. These supersede prior selection
and numerical review-only gates prospectively, without rewriting those reports.
No athlete experience categories or blanket missing-experience gate are added.

## Actual selector

`planning/v6_selection.py` returns a concrete scheduled `V6Plan`, compatible with
the existing `WeeklyPlanDraft` contract. It does not merely enumerate witnesses.
It uses pinned source phase tuples and final official planned-TSS Decimals, existing
capabilities, confirmed injury/low-only restrictions, the existing target/history/
recovery/progression resolver, existing injury allocation/caps when applicable,
and the existing date-only scheduler with rest/anti-stack validation.

The initial search scope is **at most one new occurrence per present goal sport**.
The finite full 77-row space is at most 29×28×23 = 18,676 options, including empty
sport choices. All scope options are examined before ranking, with a 20,000-option
engineering work bound. An expanded future space exceeding that bound returns
`v6_search_incomplete`; no truncated winner is published. Retained prefixes and
explicit complete selections support existing repeated occurrences. This version
does not claim a globally optimal arbitrary repeated multi-session training week.

All complete scope options must satisfy the hard authorized weekly ceiling,
revision-specific repetition bounds where supplied, existing safety caps, and
at most 20% HIGH active time independently per sport. Ordered source segments own
time classification: Z1/Z2 LOW, Z3–Z5 HIGH, wall rest zero. There is no HIGH-load,
Z5 or minimum-fill requirement. The existing BUILD-week-four Z5 **occurrence
restriction** remains; it is not a minimum. No old BUILD scoring predicate is used.

Rank valid options lexicographically by:

1. Greatest feasible goal-sport coverage: three, then two, one, zero.
2. For a triathlon goal, smallest L1 allocation distance.
3. Greatest official load not exceeding the authorized ceiling.
4. Lexicographically smallest sorted immutable template-UUID tuple.

Allocation identifier `selected-total-share-l1-unrenormalized-1` means
`SUM_s ABS(official_load_s / selected_official_total - target_s)` with original
BIKE .50/RUN .30/SWIM .20, including zero shares for omitted sports. No quotas,
independent sport budgets, tolerance or renormalized partial targets are created.
Empty totals have no allocation ratio; non-triathlon goals skip the triathlon
metric. UUID comparison is ordinal string comparison. The existing scheduler owns
deterministic placement ties. The owner authorized this engineering choice; no
independent Joren approval of a mathematical distance metric is claimed.

Options are ranked before scheduling, then the unchanged scheduler tries them
in rank order. The first feasible schedule is optimal within the fully searched
scope. If no nonempty option can be scheduled, the honest rest/zero-workout result
remains available. Explicit invalid selections reject instead of being repaired.

## Functional inactive integration

`planning/v6_service.py` provides `V6PlanningService`, a successor adapter to the
existing `PlanningService`. The existing initial pending proposal, swipe-draft,
accept/pass/undo/reset, placement, submit, alternatives/edit-proposals and athlete
confirmation contracts remain in use. Thin planner/catalog/filter injection points
default to the historical implementation. `app.main`, default dependency wiring,
public schemas and route definitions do not register V6 or change their defaults.

Local integration tests explicitly inject V6 into the existing authenticated HTTP
routes and use the real spawned `PlanningComputation` worker. They return actual
workouts, persist pending snapshots in an owner-scoped in-memory repository, swipe
and replace them, then use the existing separate approval endpoint. No alternative
approval state machine or mobile UI is introduced. No TSS-bearing field is public.

The V6 repository contract requires complete frozen source/method/parameter/
target/control/ordered-rest snapshots, owner-scoped edit retry lookup and atomic
pending-revision/proposal compare-and-swap. A repository must advertise support;
the present Supabase writer does not, so accidental construction fails closed.
The test repository implements this contract and reuses existing owner, draft CAS,
approval and confirmation behavior. Hosted persistence is an external activation
gate, not silently assumed implemented or verified by the fake.

Every V6 template remains immutable INACTIVE. Context fingerprints bind actor,
week, input, history, catalog, policy and trusted controls; generated occurrence
identities are additionally namespaced by actor/week. Two athletes get disjoint
occurrence IDs for the same selected templates. No client user ID or private
budget overrides token identity. Generation fingerprints include the exact frozen
method/target/snapshot basis. The existing bounded worker, cancellation ownership
and pending-only writes remain intact.

## Safety and provenance boundaries

Known TR-BIKE-013 is excluded with
`individual_420_minute_duration_evidence_missing` unless exact-template,
athlete/week-scoped duration evidence exists. No arbitrary duration ceiling or
experience classification is invented; other eligible workouts continue to be
considered. TSS fit remains load compatibility, not physical-readiness proof.

Reference swimming time is usable only in this inactive local preview and carries
ESTIMATED provenance and a qualitative warning. Operational acceptance remains a
release gate. Supplying independently prescribed segment times requires separate
athlete/week/reference provenance; reference estimates never become observations.
The legacy public time totals/percentages include source-prescribed timed segments
only, while private whole-week checks use the separately attributable time basis.
Source meters, individual time evidence and observed activities remain distinct.

No historical planned or realized load, ID, source archive, occurrence snapshot,
Realized V2 dispatch, grant, RLS policy, SQL migration or mobile file is changed.
The active optimized planner and its legacy tolerance/minima remain the default.
No C6–C8, migration execution, push, merge, publication, deployment or activation.

## Verification and reproducibility

See [exact simulations](JOREN_V6_EXACT_TSS_PLANNING_SIMULATIONS.md),
[swipe validation](JOREN_V6_SWIPE_ALTERNATIVES_VALIDATION.md), and
`automatic-selection/verification.json` for final test counts, evidence hashes,
historical parity and local delivery SHA. Run from `backend` with the project venv:

```text
python -B -m pytest -q -p no:cacheprovider
python -m ruff check app tests benchmarks
python -m ruff format --check app tests benchmarks
python -m mypy app tests benchmarks
python -B -m benchmarks.v6_automatic_evidence --private-output NEW_PRIVATE_PATH
python -B -m benchmarks.v6_policy_sandbox --regression-output NEW_PRIVATE_PATH
```

The first full run found a captured legacy builder bypassing the unchanged worker
control tests. Default dispatch was corrected to resolve the original builder
when constructing the request-scoped service; the original cancellation/read
assertions remain untouched. A Windows checkout also changed a prior LF artifact
to CRLF. `.gitattributes` now preserves canonical LF evidence, and the old catalog
file was restored to its exact accepted Git blob, without changing a golden value.
The earlier import-boundary assertion admits only the newly authorized inactive
official successor; new tests forbid V6 registration in default startup/router.
No old numerical expected result, deadline, score or safety assertion was weakened.

## Final local verification

| Check | Result |
| --- | --- |
| Full backend pytest | **2487 passed**, 194.64s; one existing Starlette/httpx deprecation warning |
| New V6 cases | **98** additional tests, including 77 independent per-row arithmetic checks and actual HTTP selection/swipe cases |
| Focused final worker/HTTP/custody repair checks | 11 passed, 27.30s |
| Independent exhaustive optimum | Base/Build 45, Recovery 25.86, Taper 15.085, one-sport and zero outcomes match the returned plans |
| Ruff lint / formatting | PASS; 203 files formatted |
| Strict mypy | PASS; 202 source files, existing strict=true |
| Historical corpus | All 40 input fingerprints and full canonical outcomes exactly equal accepted phase delivery; all 26 accepted reference completions preserved |
| Historical outcomes | 29 independently checked returned hypothetical plans, 10 fail-closed, one unchanged `current:build_4` diagnostic timeout |
| Regression canonical LF SHA-256 | `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`, identical to accepted historical evidence |
| Official source/evidence | All three pinned hashes and 77 source rows pass; private automatic evidence reproduces byte-for-byte |
| Earlier phase catalog custody | Exact accepted Git blob SHA-256 `20d23f1ad35c65fd93a9f6a7afb95d9bcbb272f8c30a3edade7dcdcf619be1ea`, unchanged content |
| API/identity/pending/privacy | Existing public contracts retained; new real-route/spawned-worker tests cover whole-week alternatives, retention, duplicates, retries, CAS, undo/dates, two owners and separate confirmation |
| Realized V2 | Existing dispatch unchanged; new planned-method RPE fallback explicitly rejected, observed-data priority retained |
| PostgreSQL/RLS/pgTAP/mobile | Not run or declared verified; durable-storage, mobile/device and release gates remain open |

The complete suite retains A3–A9, optimized exhaustive/differential search tests,
public/OpenAPI/private-load leaks, history/future-week, weekly completeness,
correction, retry/idempotency, stale/version and confirmation coverage. The old
planner corpus ran serially after pytest/typechecks, using the unchanged eight-
second including-imports bound. No deadline or scoring was changed to remove its
one known timeout. Prior performance artifacts remain historical; no unrelated
optimization campaign was performed.

All 77 source-method projections, selected example weeks and alternative week
results are in [evidence.json](automatic-selection/evidence.json); full canonical
historical outcomes are in [regression.json](automatic-selection/regression.json).
[verification.json](automatic-selection/verification.json) records environment,
all ancestor checks, source hashes, exact counts and artifact hashes. Initial and
final test transcripts are private artifacts; UTF-8/LF normalization removes only
transcript formatting differences. No production connection, deployment, SQL,
catalog activation or A5/A6 change occurred.

## Local delivery provenance

Implementation, tests and full evidence are committed as
`6cc8de1989311a52a934e38cbc715558421b695d` on
`feat/joren-v6-automatic-selection`, directly after accepted base
`fc876f10b5eb779a7f3004b460744da899cc739b`. A documentation-only successor
records this implementation SHA and the final staged-artifact custody check;
there are no code or test changes in that successor. All staged evidence hashes
match the ledger, and the prior phase catalog remains the exact accepted blob.
The accepted parent worktree remains clean at its original SHA; A5/A6 remains
at `cd3e2dd438031cfb565858d0a5929e9963f7b31f`.

WOMBO V6 AUTOMATIC SELECTION + SWIPE IMPLEMENTED — ACTIVATION GATES REMAIN
