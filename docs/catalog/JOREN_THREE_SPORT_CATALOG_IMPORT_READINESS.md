# Joren three-sport catalog import readiness

> Final review update, 2026-11-03: all three sources are now supplied. The current
> entry below supersedes prior-stage availability statements. Historical text
> is retained after the marked boundary; no previous source finding is discarded.

## Current final readiness — delivery complete, activation not ready

This final-stage entry updates the earlier swimming-stage readiness record retained
below. All three workbooks and the swim PDF are present; earlier “cycling absent”
text is historical. None of the 61 new templates has been activated or approved as
an actual new occurrence. The accepted application tree is unchanged.

| Gate | Final review status |
| --- | --- |
| Original sources | All 4 files byte-verified; RUN 20/BIKE 21/SWIM 20 |
| Cycling source |7,376bytes, SHA256 `5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df`; actual path in final reconciliation |
| Source structure |61/61 pass duration/distance/order/zone/RPE checks; cycling30s sprints exact |
| Mathematical reconciliation | RUN 17 and BIKE 21 differences from independent zone reference; IF² display reproduction is unapproved; SWIM 20/20 published-formula display matches |
| V2 structural/full |38 single,23 mixed;29 favorable timed conditional probes;9 SWIM singles lack T; actual newly established full eligibility0 |
| Metadata |61-row PROPOSED bucket/phase/capability/guidance/selection table; missing A–F acceptance, including long-session athlete scope |
| Current-distance-policy proposal | P 50 cannot fill new triathlon composition because SWIM P remains unavailable |
| Diagnostic distance-P | D61 can fit mixed/recovery/taper loads and explicit build 1–4; no invented swim duration, but time distribution incomplete |
| Automatic search |57 attempts:28 pending drafts,21 fail-closed,8 bounded8s timeouts; eight explicit build witnesses separately verified |
| Beginner limit | Zero-history triathlon target 45 cannot fit required minimum new source composition62 under current predicate; sparse seven-hour bike card is not beginner-qualified |
| Continuation | CURRENT and D61 each three real-planner explicit-witness weeks; unrecorded week 2 correctly holds next target; five measured/estimated/skip/unknown/partial/pending registration cases |
| Regression |439 focused backend tests pass; A 9 parity and existing V2/public contracts retained; no code/test changes |
| Methodology/activation | A–F OPEN; no actual acceptance or activation decision received |
| Database/release | PostgreSQL/pgTAP DEFERRED BY OWNER — PRE-BETA; hosted/security/storage/concurrency/scientific/device/performance gates open |

The fixed-distance swim planner gap is not a universal requirement to invent T:
current snapshot/date scheduler accepts distance-only rows, but source projection
withholds P and known-time/80/20 coverage remains partial. C5 proposes versioned
private planned-method provenance, accepted distance-P projection, lossless rests
and honest coverage, while retaining missing-T RPE exclusion. No distance-ratio
realized model or athlete-CSS scaling is approved.

This is a final review package, not an integration pass. The precise future
[sequence C1–C8](JOREN_THREE_SPORT_INTEGRATION_SEQUENCE.md) and
[Dutch approval brief](JOREN_THREE_SPORT_FINAL_DECISION_BRIEF_NL.md) supersede the
older next-step checklist without discarding its historical findings.
[All 61 results](JOREN_THREE_SPORT_FINAL_RECONCILIATION.md) and
[simulation details](JOREN_THREE_SPORT_PLANNING_SIMULATION.md) include exact source
hashes, scenarios, limits, proposed metadata and provenance conflicts.
No source, approved history, coefficient, UI/API behavior or production/staging
state changed. No adapter/migration/activation, push, merge or deployment occurred.

## Historical prior-stage report — retained unchanged

Review date: 2026-11-03 (Europe/Amsterdam). Review and preparation only.
Accepted engine: `feat/joren-realized-tss-v2` at `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch/worktree: `review/joren-new-workout-catalog`,
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Swimming originals are in the accepted engine worktree's `docs/trainings`, not the older root checkout:

| Original | Bytes | SHA-256 |
| --- | --- | --- |
| `Zwemtrainingen_Definitief_Optie1.xlsx` | 7333 | `bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674` |
| `Specificatie Zwem TSS.pdf` | 149021 | `ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a` |

Full original paths:
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Zwemtrainingen_Definitief_Optie1.xlsx`
and `F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings\Specificatie Zwem TSS.pdf`.
Private load numbers below are developer review evidence and must remain outside athlete-facing contracts.

## Readiness conclusion

**Not ready for catalog cutover or activation.** Swimming intake and published
formula verification are complete as a review; running source-method/selection
questions remain; cycling has not yet been supplied in the searched source paths.
The fixed swim distance model is new source evidence and is not integrated into
the accepted planner. No application or production/staging behavior changed.

| Sport | Actual supplied evidence | Source validation | Load method / selection / realization readiness |
| --- | --- | --- | --- |
| Running | Looptrainingen_Definitief_Optie1.xlsx, 20 rows | Prior all-row duration/zone/order review preserved; 16 single and four mixed | IF-based source hypothesis unconfirmed; 17 zone-reference differences; phase/bucket/guidance/version approvals open; no established eligible new occurrences |
| Swimming | New workbook, 20 rows, plus two-page PDF | All 20 distance/zone/order/RPE checks pass; nine single and eleven mixed; all source displays reconcile | Published fixed P method verified; current distance projection withholds P; all lack planned T for V2; rest representation and metadata/version decisions open |
| Cycling | **CYCLING CATALOG — SOURCE NOT YET AVAILABLE** | Not assessed; no placeholder data | New source method, structure, multiplier, eligibility and historical comparison unknown |

Original running source: 7,198 bytes,
SHA-256 `dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3`.
Its original location remains `F:\Projecten Business\Start23\Code\docs\trainings`.
Swimming hashes/paths are recorded above. The cycling search included ignored
files in known `docs/trainings`/`docs/requirements` in the older root, accepted
engine worktree and reused review worktree, then existing worktrees' known
`docs/trainings` locations (28 training-source directories total, including the
root). This is not a claim to have
searched arbitrary user storage or external attachments. No cycling schema or
formula is inferred from the old 50 BIK templates or either supplied sport.

## Source and engine boundaries

The published swim formula is exact fixed per-100 m A, with no extra 0.90 and
stationary rest zero. All delivered rows have zero Z1, so their totals equal the
unrounded reference-pace product B as well; the methods diverge for Z1 (0.98
versus 0.975 per 100 m). Athlete-specific CSS C is undefined and unsupported.
The representative CSS supplies no actual time and no authoritative planned T.
Original stored one-decimal P and exact formula P must remain distinct records;
TR-SWIM-010 is raw 28.4 and derived 28.44. C04 determines future operational P.

Current immutable distance-swim source records retain original source load, but
`with_current_load` yields P=None and ordinary selection filters unavailable P.
Fixed-distance P selection needs explicit S02 methodology/coverage acceptance and
subsequent engineering work; it is not enabled simply by adding source rows.
Current segment targets also cannot represent unzoned timed wall rest within a
distance-only prescription. Preserve source strings and zero-rest semantics;
never insert fake Z1 swimming or drop rests to satisfy the schema.

V2 remains the approved duration expression on an immutable approved snapshot.
Nine single swim rows have no T and eleven mixed rows remain excluded. Existing
actual observed-zone methods may process independently supported actual evidence;
new distance/P/CSS converters and an optional distance-ratio fallback require
separate approvals and versions. Actual RPE, expected intensity and prescribed
distance do not fabricate performance evidence. Measured values retain precedence.

## Isolated actual planner results

The actual unchanged Python planner ran 20 calls in this continuation review:
16 swimming scenario calls, two beginner-running reproductions and two current-
swim continuation attempts. No new combined/triathlon simulation was started.
The old-catalog parity tests are regression fixtures, not new-catalog readiness.

The swimming comparison uses:

- `current_56`: accepted deterministic migration projection from
  `benchmarks.planning.full_catalog()`, filtered to SWIM. It includes 54 current
  distance-only source templates (P unavailable) plus the two active timed
  built-ins with current P=23.40 and 54.90. Source-v2 IDs in this projection are
  stable synthetic migration-fixture IDs, not a hosted successor-UUID inventory.
- `new_9_current_projection`: only TR-SWIM-001–009, since these are rest-free and
  representable without inventing mixed block RPE. In-memory draft metadata
  assumes low, all four phases, pace capability, incompatible HR fallback,
  automatic selection and source namespace `REVIEW-ONLY-NOT-APPROVED`.
  UUIDs are `UUID(int=4001+i)`, keys `5001+i`, version 1. Source pair 3–4 is
  preserved and scalar segment RPE 3 is selected solely to construct a fixture.
  Original distance and source P are passed through the real `with_current_load`;
  every projected P becomes None. This is a deliberate test of present engine
  behavior, not a proposed shortcut around it or an approved import mapping.

All swim cases use goal SWIM only, week 2026-10-26, Europe/Amsterdam, no injury
unless specified, known capabilities and zero-history baseline 45.0. All seven
available dates and race 2027-03-15 apply by default. One-day/no-day cases restrict
those dates. Build/recovery/taper use four prior approved build weeks P=R=100 with
per-SWIM planned load 100; race dates are 2026-12-14, 2027-01-04 and 2026-11-02.
Repeat cases restrict to current Aerobic swim or new TR-SWIM-001. Injury blocks
SWIM with no eligible historical recipient baseline.

Successful cells show `planned P / known planned minutes / occurrences`; results
are pending drafts. Capacity warnings are nearest-fit outcomes, not exact target
fulfillment or a claim of beginner suitability.

| Case | Current 56 | New nine through current projection |
| --- | --- | --- |
| beginner_swim | 46.80 / 80 / 2 [gap] | catalog_empty |
| one_available_day | 46.80 / 80 / 2 [gap] | catalog_empty |
| no_available_days | availability_required | catalog_empty |
| build | catalog_capacity_unsatisfied | catalog_empty |
| recovery | 70.20 / 120 / 3 [gap] | catalog_empty |
| taper | taper_catalog_coverage_unavailable | catalog_empty |
| repeated_template | 46.80 / 80 / 2 [gap] | catalog_empty |
| injury | 0 / 0 / 0 | 0 / 0 / 0 |

Current beginner P target is 45.0: two Aerobic swim occurrences total 46.80 and
80 minutes. One-day availability consolidates both on 2026-10-26 with a warning;
there is no per-day minute budget in that input. Repeats are allowed with distinct
occurrences in the existing system. Recovery target 60 selects three occurrences,
70.20 and 120 minutes, with a capacity warning. Current build cannot fit the
available safe composition; current taper lacks eligible coverage. Those genuine
results must not be described as adequate catalog coverage merely because a
numeric source TSS exists.

For new swimming the normal distance projection fails early `catalog_empty`,
even before evaluating date or later phase constraints. The all-injured case
correctly returns an injury rest-only pending draft before candidate selection;
it does not prove useful workout coverage. No swimmer duration was reverse-
engineered from the representative paces. Repeats cannot cure missing usable P.
The nine candidates' source P range 14.4–72.0 is source diversity, not approved
engine capacity or a justified beginner minimum distance.

For the beginner runner, reusing the prior review's conditions gives:

| Deck / metadata status | Target | Planned P | Minutes | Count | Warnings |
| --- | --- | --- | --- | --- | --- |
| current_52 | 45.0 | 45 | 75 | 2 | none |
| conditional_16_run_source | 45.0 | 46.4 | 80 | 2 | target_outside_catalog_capacity |

The conditional 16-run source deck retains the earlier review's explicit synthetic
metadata assumptions; running source-method approvals remain open. Its other
zone-method comparisons, repeats and three-week unknown-completion hold remain
unchanged in [running validation](JOREN_RUNNING_CATALOG_VALIDATION.md).

**Beginner triathlete/new three-sport experiments were withheld:** cycling is
absent, current new-swim planning capacity is unavailable, and metadata approvals
are incomplete. Mixing old cycling or fabricated swim time into a success case
would not establish readiness of the proposed three-sport catalog.

## Multi-week, realization and registration experiments

A current-swim-only continuation used complete synthetic observed-zone evidence
matching each timed built-in's exact approved prescription; no source distance or
RPE was used to infer those actual minutes. It succeeded for the first week,
then failed the next build week:

| Week | Result | Target / planned / usable when successful |
| --- | --- | --- |
| 2026-10-26 | pending draft | 45.0 / 46.80 / 46.80 |
| 2026-11-02 | catalog_capacity_unsatisfied | not available; no draft generated |

A new-swim-only continuation cannot start under present P projection; no later
success is claimed. Focused regression tests cover historical ten-week parity and
new V2 complete/incomplete multi-week consumer behavior separately from this
catalog capacity failure.

All 20 new-swim favorable-provenance probes withheld the RPE estimate: nine
`missing_duration`, eleven `unsupported_structure`. They are conservative probes,
not fabricated accepted occurrences. Independent observed time remains supported.
A four-case weekly-registration experiment (one RUN estimate 32.3 plus expected
SWIM, previous approved P=60, next week 2026-10-26/race 2026-12-27) returned:

| Swim completion | Known subtotal | Usable total | Next target / basis |
| --- | --- | --- | --- |
| unknown | 32.3 | None | 60 / prior_planned_hold |
| unavailable | 32.3 | None | 60 / prior_planned_hold |
| skipped | 32.3 | 32.3 | 32.3 / realized_baseline |
| independent_measured | 53.9 | 53.9 | 66.00 / realized_progression |

The measured row is an independently complete synthetic 30-minute Z2 observation
(21.6), not evidence derived from this distance source. Unknown/unavailable swims
withhold usable load; explicit skip differs from missing completion. The separate
rest-containing 35-minute example remains partial under current coverage rules.
No partial/unknown session is zero-filled or upgraded to complete. Volume
progression, fatigue/illness/injury/recovery/taper precedence and measured-intensity
coverage remain unchanged. Evidence-bound pending plans retain stale-safe approval.

Measured local swimming planning calls were 0.010–5.390 ms in this small fixture;
these failures/tiny decks say nothing about full-catalog deployed performance.
Do not compare them as a meaningful speedup. The previous running report's exact-
fit search timings already show that changed load grids can expand state space.
Final three-sport performance and concurrent responsiveness remain required gates.

## Versioned integration preparation

No applied migration is edited or run here. The future implementation must use a
versioned manifest and preserve original and derived evidence:

| Area | Required accepted input / engineering plan | Current status |
| --- | --- | --- |
| Original bytes | Read-only original files, sizes/hashes, source sheet/cell lineage, PDF pages/hash | RUN and SWIM verified; BIKE absent |
| Version/identity | Accepted sport source/method revisions, stable IDs and explicit replacement map | C01 open; no suffix/title merges |
| Source P authority | RUN exact method; SWIM fixed-distance method scope; BIKE actual evidence | R01/S01/S02 and BIKE intake open |
| Precision | Original raw P, exact computed P, declared Decimal/rounding policy and occurrence method/version | C04 open; no workbook edits |
| Ordered execution | Complete distance/time/zone validation, explicit stationary rest seconds, per-block guidance | Source checks pass for supplied files; C03 rest/guidance mapping open |
| Selection | Approved row bucket/phase/capability/auto/explicit flags; current repeats/spacing/availability/injury filters | C02 open; concrete SWIM proposal prepared |
| Distance vs time | Do not infer T/A; define prospective distance P planning and time-distribution behavior | S02/S03 open; no automatic conversion |
| Realized V2 | Immutable exact occurrence P/T/zone/method/version; confirmed A; observations retain precedence | Existing contract retained; zero new-swim fallback eligibility |
| Weekly completeness | Expected occurrence set, unknown/skip/partial distinctions, supported actual loads and exact evidence IDs | Existing policy retained/tested; no fake source-P realization |
| Multi-week behavior | Beginner/build/recovery/taper, injury, missing completions, repeats/candidate shortage with real accepted decks | Conditional limits documented; final combined run deferred |
| Database | Forward-only immutable records, service-private load lineage, current historical readers, RLS/grants/owner integrity | No migration authored/applied; execution deferred by owner |
| Rollback | Prospective selection reverts to prior accepted set; preserve all approved snapshots/calculations/readers | C05 future activation decision; no deletion/backfill |
| Performance | Deterministic outputs/intermediates and bounded worker behavior, realistic search grids and responsiveness | Old A9 parity retained; new combined benchmark deferred |
| Privacy | Private P/E/ratio/factor/subtotal/provenance excluded from athlete APIs/UI/logs/accessibility/analytics/LLM | Current contracts unchanged; relevant regression tests passed |

Recommended later sequence:

1. Obtain cycling originals and method evidence; intake every worksheet/workout
   independently. Resolve C01–C04 and sport-specific blocking method decisions
   without changing approved coefficients. A deferred distance-ratio fallback
   may remain disabled; never claim full RPE swim coverage if so.
2. Freeze an accepted combined manifest with all file hashes, row counts, source
   versions, replacement relations, original/derived P and method/precision policy,
   approved selection metadata and lossless ordered/rest/guidance structure.
3. In a separately authorized implementation, prepare a dry-run adapter using
   existing modular patterns. The old CSV helper does not accept TR IDs/new schema;
   do not force IDs/decimals into it. Explicit rest events require a reviewed
   contract; do not encode fake Z1. No distance-to-time inference is a shortcut.
4. Prepare forward-only new immutable templates/successors and private load
   records. Retain all old source-v1/v2, built-in/protocol versions, approved plan
   revisions and append-only realized corrections. Unsupported new method/version
   combinations stay unavailable until explicit dispatch is approved. No history
   is recalculated or relabelled.
5. Run an isolated final combined test matrix only after all accepted sources and
   supported methods exist: every sport, source P, phase, candidate, availability,
   high spacing, injury/illness/fatigue, single/mixed/RPE/measured/unknown/skip,
   multi-week progression and historical compatibility. Include exact snapshot
   persistence, stale evidence and retry idempotency. Repeat private-contract,
   backend/static/type/mobile checks appropriate to that implementation.
6. At the owner's pre-beta gate run PostgreSQL/pgTAP fresh/upgrade replay,
   forced-RLS/grant/owner tests, actual numeric storage, immutable history,
   concurrency/idempotency, evidence-bound stale plan/zone approval and correction
   readers. **DEFERRED BY OWNER — PRE-BETA**; no tooling installed now.
7. Complete scientific/release acceptance, real-token/device and representative
   deployed performance gates. Prepare a concrete cutover/rollback artifact and
   obtain the future explicit activation decision C05. No push/merge/deployment
   or hosted change is part of this review.

## Verification and preservation evidence

Focused accepted-backend tests: **395 passed**, 33.94 seconds, one existing
Starlette/httpx deprecation warning. Test families include catalog/seed/repository,
source audits/migration static contracts, Realized V2/context/planning/weekly,
RPE/zone coefficients, OpenAPI/privacy contracts, exact A9 outputs/intermediates
and historical continuation. No test, scientific coefficient, API, UI or migration
was changed. The accepted source is preserved at the exact SHA above; unchanged
application diff and both source-file hashes are verified after document writing.

The three running findings reports remain byte-identical to their starting
SHA-256 values:

| Report | Preserved SHA-256 |
| --- | --- |
| JOREN_RUNNING_CATALOG_VALIDATION.md | f908ee52c1ab093faaae07849ca4ce43fc790ef6b29e45f7b93d0cb44f7c8efb |
| JOREN_RUNNING_TSS_RECONCILIATION.md | fc64b05f16738cca70cddeff6b6e1fdfd3acc6e0d00e1328f6c4f7da134ac2c4 |
| JOREN_RUNNING_REALIZED_V2_ELIGIBILITY.md | 8bbaf19aca59198da4a6daebd9548e582aaf7dfe9ff859532a2c6dbd2eaa33b1 |

The existing import plan's original hash was
`0fdcc83f67f522d0ae6cc01e5e1c7e3f0669ae5ffa2f167361dbb4c870c309f6`;
its original content is retained with an evidence-based update/addendum. The five
new swimming/combined reports and that narrow plan update are this task's changes.
Scratch extraction/analysis/rendering lives in ignored `.runtime/swimming/`;
no original spreadsheet/PDF is overwritten or imported into the active catalog.

This review makes no new claim that full mobile tests/strict TypeScript, live
PostgreSQL, hosted RLS/RPCs, real devices or release gates passed. Previous running
review and accepted implementation verification remain attributed to their exact
recorded source. No reset/discard, push, merge, deployment or hosted mutation took
place. Full replacement and final combined simulation remain pending.

Related: [unified decisions](JOREN_THREE_SPORT_CATALOG_DECISION_REGISTER.md),
[swim validation](JOREN_SWIMMING_CATALOG_VALIDATION.md),
[swim reconciliation](JOREN_SWIMMING_TSS_RECONCILIATION.md),
[swim V2 eligibility](JOREN_SWIMMING_REALIZED_V2_ELIGIBILITY.md),
[updated original import plan](JOREN_WORKOUT_CATALOG_IMPORT_PLAN.md).
