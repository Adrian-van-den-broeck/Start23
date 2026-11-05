# WOMBO V6 C3â€“C5 inactive integration report

2026-11-05, Europe/Amsterdam. Private development delivery.
Branch: `feat/joren-v6-phase-tss-integration`.
Worktree: `F:/Projecten Business/Start23/Code/.worktrees/joren-v6-phase-tss-integration`.

## Accepted starting point and isolation

`experiment/joren-v6-final-policy` was clean at exactly
`acdc5fbd36677680f9083a308cb1f760aa7c71eb` before changes.
`git merge-base --is-ancestor 7dc3f22595d4b9e22e1e84abaf148d9bd791fd33 acdc5fbd36677680f9083a308cb1f760aa7c71eb`
returned 0. The new worktree/branch was created directly at that accepted SHA.
Root `fix/pre-ui-beta-blockers` had pre-existing changes and was not used for
implementation, reset, stashed or cleaned. No existing worktree was modified.
The A5/A6 release branch remains outside scope at its original
`cd3e2dd438031cfb565858d0a5929e9963f7b31f`.

Read authority: root AGENTS.md, current MVP roadmap, C1/C2/C2.1/V6 source and
calculation reports, phase/suitability and IFÂ² decisions, final-policy update,
C3â€“C8 sequence, planned-source and Realized V2 implementation/specification,
A3â€“A9 planning/persistence contracts, BUILD-search correctness/performance evidence.
No nearer backend/docs AGENTS.md exists. Current explicit owner decisions override
older draft proposals without rewriting their historical evidence.

## Delivered software and preparation

| Slice | Implemented scope | Remaining boundary |
| --- | --- | --- |
| Source intake | Hash/length-verified immutable new archives; strict shared-string/phase adapter; all 77 rows, phases and original A:O lineage retained | Eight exact M-lexeme export changes documented; no invented generic equality tolerance |
| C3 | Frozen inactive `PhaseCatalog`/`PhaseTemplate`, stable logical keys, new UUID5 source/template revisions, complete source cells and predecessor event/RPE/focus records; immutable reproducible preparation payload | No durable catalog reader, active row, retirement, SQL migration or accepted active-template replacement mapping |
| C4 | Private versioned review of complete retained+proposed week; source phase filter, exact hypothetical hard ceiling/remaining capacity, explicit availability/goals/repeat checks, scope-bound safeguards, no HIGH minimum, per-sport maximum; no recommendation | Official load authority, existing-safeguard production adapter, metric/tie selection and durable pending persistence remain gated |
| C5 | Reuses the unchanged versioned swim estimator from a shared pure module; historical benchmark imports remain compatible; reference estimates and separately prescribed times evaluated independently | Estimated operational safety acceptance remains open; no observed-time inference or Realized V2 change |
| TSS decision | Owner-relayed approval recorded; exact earlier recommendations identified; concrete numerical proposal written after owner response | Owner explicitly requested proposal without implementation; official method/value/storage authority remains unset |

No new operational planner, public DTO, API, environment flag or activation switch
is exposed. The new modules have no active consumers; the dry-run job is their
only application entry point. They cannot persist a plan or zone change.
All template activation fields are immutable INACTIVE; all review approvals are
immutable false. No logical duplicate active templates are introduced because
zero active templates are emitted.

Source phase membership is authoritative only for the new source revisions.
The historical `SelectionDraft` stays inside predecessor evidence, clearly
separate from accepted phases; no athlete-level category is added or consumed.
Existing whole-workout legacy scoring/phase filtering is not relabeled as new
authority. No new per-block physiological/RPE rule is invented.

## Preserved behavior

The active application, catalog repository, planner domain/search, execution
boundary, pending-proposal writer, calendar/activity APIs, historical occurrence
snapshots, planned-source dispatch and Realized V2 dispatch are unchanged.
Measured-data priority, weekly registration/correction, retry/idempotency,
expected-version preconditions, account isolation and athlete confirmation remain
covered by the complete suite. No historical source/workout/occurrence method is
reassigned and no physiological/private load is recalculated.

The only earlier implementation file changed is the offline estimator module,
now a compatibility re-export of the identical implementation moved into
`workouts/planned_swim_estimate.py`. The estimator version, parameters, functions,
result fields and all historical evidence outputs are preserved. Tests assert
object identity through both import paths and reproduce previous artifacts.

## Existing-test adaptations, not weakened physiology or goldens

The first complete run reported 4 failures and 2385 passes. Three custody tests
assumed every entry in `docs/catalog/sources` was a file; the new source revision
directory exposed that obsolete layout assumption. They now recursively verify
**every file**, covering the new archives as well as every historical source.
Their exact-byte/history assertions remain unchanged.

The fourth failure was the earlier absolute offline-only import assertion for
the planned-intensity helper. This task explicitly authorizes its reuse in the
disabled C4 review seam. Only that named seam is admitted; a new AST boundary
test checks that no other application module imports the new integration.
The estimator dependency test now inspects the shared pure implementation and
retains the no-benchmark-import/no-infrastructure boundaries. No numerical test,
golden, physiological constraint, historical expected output, deadline or score
was weakened. The focused rerun passed all 408 tests.

## Verification record

Final full-suite, lint/type, historical regression, benchmark, custody and local
commit results are recorded in the final delivery addendum below and in
`phase-tss/verification.json`. Initial/final full test transcripts are retained
privately beside it. Evidence is based on the existing root backend virtualenv,
with this new worktree's backend as cwd; no packages were installed or updated.

Reproduction commands from `backend`:

```text
python -B -m app.jobs.joren_v6_phase_intake --dry-run --private-output NEW_PRIVATE_CATALOG.json
python -B -m benchmarks.v6_phase_integration --private-output NEW_PRIVATE_SIMULATION.json
python -B -m benchmarks.v6_phase_integration --search-output NEW_PRIVATE_PHASE_SEARCH.json
python -B -m pytest -q -p no:cacheprovider
python -m ruff check app tests benchmarks
python -m ruff format --check app tests benchmarks
python -m mypy app tests benchmarks
python -B -m benchmarks.v6_policy_sandbox --regression-output NEW_PRIVATE_REGRESSION.json
python -B -m benchmarks.v6_planner_performance --variant optimized --output NEW_PRIVATE_PERFORMANCE.json
```

Historical regression and performance run serially after tests/typechecks, with
the unchanged eight-second diagnostic bound including imports. Host load is not
controlled; local samples are not a production SLA. The known `current:build_4`
timeout remains a performance limitation, not a failed-feasibility proof.

## Review outcome and external gates

This is a coherent **partial inactive integration**, not active C3â€“C5 completion.
The exact official method binding and selection/suitability contracts prevent the
remaining operational portions. The owner requested a numerical proposal without
implementation; that request is honored. See
[official proposal](JOREN_V6_OFFICIAL_TSS_METHOD_APPROVAL.md),
[eligibility contract](JOREN_V6_TSS_BASED_ELIGIBILITY.md),
[phase-aware scenarios](JOREN_V6_PHASE_AWARE_PLANNING_SIMULATION.md) and
[Dutch release gates](JOREN_V6_REMAINING_RELEASE_GATES_NL.md).

No PostgreSQL schema, RLS or grant change is made or claimed verified. Hosted
SQL/pgTAP/RLS/two-real-user verification remains deferred, not passed. There is no
mobile/public contract change requiring a new TypeScript implementation; existing
A5/A6/mobile/device release gates remain separately open. No automatic C6â€“C8,
push, merge, deploy, migrate, publish, catalog activation or production access.

## Final local verification

| Check | Final result |
| --- | --- |
| New source/phase/lineage/inactive integration cases | 139 new tests; included in the complete passing suite |
| Focused phase + earlier partial/final policy tests | 287 passed, 11.71s |
| Focused C1/C2/C2.1 custody + new integration rerun | 408 passed, 10.28s |
| Complete backend pytest | **2389 passed**, 195.15s; one existing Starlette/httpx deprecation warning |
| Ruff lint / formatting | PASS; 195 files formatted |
| Strict mypy | PASS; 194 source files, existing strict=true retained |
| Official-TSS implementation | Not added; concrete proposal only, per owner follow-up |
| Source custody | Three exact hash/length matches; copies byte-identical to originals; all 77 rows and eight exact lexeme differences retained |
| Historical 40-case corpus | Full input fingerprints and complete canonical results equal accepted final-policy delivery; all 26 accepted completions preserved |
| Historical outcomes | 29 returned hypothetical plans independently checked, 10 exact fail-closed, one unchanged `current:build_4` timeout |
| Regression canonical LF SHA-256 | `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`, identical to final-policy evidence |
| Existing optimized cold performance matrix | All 40 input/output results equal preserved BUILD-search delivery; all 29 independent plan checks pass; same eight-second deadline |
| New phase-projected legacy diagnostics | All 20 completed; four history-based BUILD searches complete; no prospective-approval claim |
| Historical software/source preservation | Existing planner, active catalog, APIs, persistence, Realized V2, SQL, mobile and old evidence unchanged; only documented estimator relocation and test-boundary adaptations |
| PostgreSQL/pgTAP/RLS | DEFERRED / NOT VERIFIED; no new schema, grants, RLS or migration |
| A5/A6/mobile/device | Outside scope; existing release gates retained |

Cold benchmark planner-only V6 BUILD weeks 1â€“4: .058711 / .067180 / .072461 /
.017100 seconds; including-imports wall .982066 / .972991 / .948753 / .899413.
Current-catalog BUILD 1â€“3: 3.323482 / 3.509416 / 3.782762 planner seconds;
`current:build_4` times out at 8.006387 wall seconds. These are one local sample
per case, not a speed claim or SLA. Prior preloaded/instrumented/oracle matrices
are preserved but were not regenerated in this slice. Exhaustive/differential
search-correctness tests remain in the complete passing backend suite.

The complete suite includes existing A3â€“A9, adjacent-week, public/OpenAPI,
recursive private-load leak, measured-data priority, weekly registration and
correction, stale/version, retry/idempotence, athlete-confirmation and
account-isolation tests. No public load field is introduced. Production was not
accessed; all production systems and existing worktrees remain untouched.

Machine-readable [verification](phase-tss/verification.json) includes ancestor
checks for Realized V2, A3â€“A9, partial approval and accepted BUILD-search delivery,
all evidence hashes, environment, exact source bytes and result counts.

WOMBO V6 PHASE + TSS INTEGRATION PARTIAL â€” SPECIFIC APPROVAL GAPS DOCUMENTED

## Immutable private evidence hashes

| Artifact | SHA-256 |
| --- | --- |
| phase-tss/catalog.json | `20d23f1ad35c65fd93a9f6a7afb95d9bcbb272f8c30a3edade7dcdcf619be1ea` |
| phase-tss/decision.json | `b2365a1dab8f4383f2d490771e0194e5d43f52718f9dab390413649e7f418173` |
| phase-tss/performance.json | `c9a839bc27401b87685c942c620cafc01641d4da73b24d22adc56266b9bf74c7` |
| phase-tss/phase-search.json | `763a98e92b60d8f91db364a327d498c7a132fc28fbf8b8c7e76ac2e55ce9b4a8` |
| phase-tss/pytest-full.txt | `034121068238d91e5897db951595e2d75a1fcfdc6b92ee59ba31e48c52725ceb` |
| phase-tss/pytest-initial.txt | `b6ce64a6061322da8f74e2f699572ccc8f942afaea11a614ff12d041fed4c888` |
| phase-tss/regression.json | `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341` |
| phase-tss/simulation.json | `ad14bdab3c4601f9c528a7fd3d9f2051093b220b7df689b5fb6d4bd6fd5823b9` |
