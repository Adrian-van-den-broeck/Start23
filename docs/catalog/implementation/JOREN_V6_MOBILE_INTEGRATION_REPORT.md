# WOMBO V6 mobile integration

8 November 2026, Europe/Amsterdam. Branch `feat/joren-v6-mobile-lifecycle`.
Exact starting revision: `3d54615e6635cd662f5e3dfa246bedee924b9b06`, from
`verify/joren-v6-final-auth-security`. Isolated worktree
`.worktrees/joren-v6-mobile-lifecycle`. Tested implementation: f09941d405d25cdbb587b662fe1f5fe17c1c14eb.
The final report commit is a documentation-only successor; resolve the branch tip
with `git rev-parse feat/joren-v6-mobile-lifecycle`.

**WOMBO V6 MOBILE LIFECYCLE PARTIAL — EXACT BLOCKERS DOCUMENTED**

## Implemented

The existing Expo application remains the presentation. `PlanningFlowProvider`
and `usePlanningController` own recovery, generation, accept/pass, undo/reset,
placement, pending submission and separate confirmation. `usePendingWorkoutActions`
continues to request complete-week-validated alternatives. `PlanningCreationScreens`,
the proposal task, Calendar/Week controllers, both workout details presentations,
and the existing activity controller are reused. No parallel navigation, design,
approval state machine, mobile physiological calculation or client V6 flag exists.

`app.local_v6.install_local_v6` is explicit test-only dependency injection into
existing authenticated routes. It rejects deployed environments and non-loopback
Supabase configuration. Tests supply synthetic ownership/storage; a durable local
installation must supply the inactive repository and catalog, the existing token
verifier and the fully migrated isolated stack. `app.main` and default route
dependencies remain historical. The helper is not a runnable production switch.

Real V6 selection supplies actual cards and immutable template IDs/versions.
No example workout number is a default. The existing server revision, occurrence,
pending-proposal, date, retry and approval contracts are retained. Partial and
rest-only selection displays do not require all three disciplines. Exhaustion
preserves accepted cards; reset reopens passed choices without removing retained
cards. Swipes never approve a plan.

The additive `source_prescription` allowlist copies exact source session effort,
focus, full execution text, zone distribution, ordered timed/distance blocks and
stationary rests. Details use original session effort separately from actual block
zones; no interval RPE is assigned to recovery or wall rest. Historical templates
retain their existing presentation. Reference swim minutes are separately labeled
`ESTIMATED_FROM_APPROVED_REFERENCE_PACE`; prescribed and measured duration remain
independent. The operational swimming-time acceptance gate is still open.

The additive `physical_workout_id` binds logical public V6 occurrences to their
exact immutable revision rows for activity attachment and registration. Calendar
and plan projections use the same logical identity. A missing physical locator on
a source-backed V6 activity fails closed. Selecting V6 never pre-fills actual
distance or duration from the prescription. See the two mapping reports below.

## Provenance and unchanged policy

All 77 revisions remain INACTIVE. Official planned method
`joren-v6-planned-if2-1`, reference `joren-v6-approved-if-reference-1`, acceptance
`joren-v6-official-tss-acceptance-1`, source release
`joren-v6-phase-source-release-1` and selector
`joren-v6-automatic-selection-1` are unchanged. No physiology/domain, eligibility,
authorized limit, ranking, sport allocation, HIGH-time rule or historical outcome
was changed. Public fields contain source prescription, never private load or
internal calculation evidence. The old catalog-import generator explicitly excludes
the new optional presentation field to reproduce its exact applied SQL bytes.

The existing full-dictionary retained-workout assertions were updated because a
new immutable revision necessarily has new physical rows. Tests now assert exact
retained logical/source/date fields and explicitly different physical IDs. They
continue to cover duplicate occurrences, retry equality, stale requests and owners.
The old detail test now supplies the existing language/storage boundary required
by localized source presentation. No expected physiological result or timeout was
relaxed.

## Evidence boundaries

Final counts, hashes and commands are in [verification.json](mobile-lifecycle/verification.json).

Software results: **2,667 backend tests; 900 mobile tests / 84 suites; Ruff
lint/format; strict mypy (209 sources plus 3 scripts); strict TypeScript and
unused-code checks all pass.** Focused final-source/lifecycle and contract/
persistence/HTTP reruns pass 81 and 111 tests respectively; these overlap the full
suite and are not additional totals. All 40 historical cases and all 26 accepted
reference outcomes are byte-identical to the accepted corpus, including the
unchanged `current:build_4` diagnostic timeout and eight-second bound. Canonical
SHA-256: `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341`.

| Evidence | Scope |
| --- | --- |
| Backend | Full pytest, strict mypy, Ruff lint/format, public/OpenAPI/privacy and historical planner suites; final presentation subset and complete committed-tree rerun after source-only additions. |
| Mobile | Strict TypeScript/unused checks, full Expo/Jest component/navigation/transport/localization/privacy suites and source-backed V6 lifecycle tests. Transport, secure storage and sessions are simulated. |
| Cross-stack trace | Actual FastAPI routes and spawned V6 selector export public synthetic responses to `v6-http.test-fixture.json`; Jest consumes those responses through existing owners/screens. This is a test artifact, never an app data source. |
| PostgreSQL | Fresh local PostgreSQL 17.11, 60 migrations, 34 SQL suites / 654 assertions; actual source round trips, transactions, concurrency, retries, rollback and independent-process reload. New calendar/activity probe passes 14 check groups. SQL JWT claims are simulated. |
| Auth/device | Zero GoTrue sessions, zero gateway checks, zero authenticated-device scenarios. ADB inventory found no connected device/emulator. No new screenshots. |
| Builds | Android Hermes export and offline x86_64 debug APK build succeeded. Native compilation is not device execution. iOS compilation/signing is unavailable on this Windows host. |

The inherited 38 signed-token PostgREST checks are historical evidence from the
starting delivery. They were not rerun here and do not validate these new RPCs over
the complete gateway. The new SQL tests use role/claim simulation and real DB
authorization. The original A5 file is unchanged: all-suite runs explicitly use
the previously reviewed synthetic onboarding/32-character-fingerprint overlay.
That patch remains a separate adoption proposal.

## Remaining implementation and release gates

Confirmed V6 date moves require a new immutable revision path. The historical move
RPC clones a legacy revision without the V6 frozen context/mapping contract;
V6 therefore returns `v6_active_move_requires_revision` before writing. Pending
date placement and retention work. V6 check-in creation remains fail-closed because
the V6 writer is not integrated with A5's atomic attachment/replay transaction.
Neither safeguard was disabled.

See [occurrence mapping](JOREN_V6_CALENDAR_OCCURRENCE_MAPPING.md),
[activity compatibility](JOREN_V6_ACTIVITY_REGISTRATION_COMPATIBILITY.md),
[executed scenarios](JOREN_V6_MOBILE_SWIPE_E2E_TESTS.md) and
[Dutch release gates](JOREN_V6_FINAL_MOBILE_RELEASE_GATES_NL.md).

No push, merge, deployment, staging/production connection, hosted migration,
catalog activation or protected A5/A6 release change occurred.
