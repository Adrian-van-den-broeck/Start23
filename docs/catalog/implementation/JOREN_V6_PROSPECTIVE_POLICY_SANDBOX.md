# Wombo V6 prospective planning-policy sandbox

2026-11-05, Europe/Amsterdam. Private developer evidence, offline and inactive.

The sandbox is a versioned evaluator and finite feasibility experiment. Passing
arithmetic or simulations grants neither Joren's scientific approval nor athlete
eligibility. The active planner does not enforce these prospective policies.

## Custody and isolation

Branch: `experiment/joren-v6-policy-sandbox`. Worktree:
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-policy-sandbox`.
Created directly from final performance delivery
`86c64e6e5b5b89f4f2c8901246793afdf924dd04`, whose only change after verified
implementation `67c293f7d395e2cb8a12911be37a925d23467aa9` is its delivery report.
Both the starting performance worktree and the new worktree were clean. The main
checkout's unrelated tracked/untracked changes were left untouched.

Root AGENTS.md, the current MVP roadmap, V6 integration/remaining-decisions,
beginner-simulation, budget-gap, BUILD correctness/benchmark/optimization reports
were read. There is no nearer backend/docs AGENTS.md. Seventeen exact ancestry
checks passed: Realized V2, C1 implementation/delivery, C2 implementation/delivery,
C2.1 implementation/delivery, A3-A9, first performance implementation, verified
BUILD implementation and final performance delivery. Exact earlier hashes are in
the [V6 integration report](JOREN_V6_CATALOG_INTEGRATION_REPORT.md#delivery-status-and-isolation).
Performance ancestors are `c7c1b43a5db354d2abea4e128f42ca050179d2ad`, `67c293f...`
and `86c64e6...`. All were verified with `git merge-base --is-ancestor SHA HEAD`.

The A5/A6 release remains clean at
`cd3e2dd438031cfb565858d0a5929e9963f7b31f`; the accepted performance branch
remains clean at `86c64e6...`. No existing source, workbook, fixture, planner,
physiology rule, migration, configuration, persistence or public API is changed.
Only new sandbox Python, tests and private reports/evidence are added.

## Evidence categories

| Category | Meaning in this delivery |
| --- | --- |
| CONFIRMED JOREN RULE | Triathlon 50/30/20 soft planned-load target; at most 20% HIGH active time per sport/local week; Z1/Z2 LOW, Z3-Z5 HIGH; zero HIGH allowed; stationary swim rest excluded; one suitable workout per sport where feasible. Owner-transmitted decisions, not an invented independent review record. |
| PROPOSED PRODUCT POLICY | Strict explicitly authorized weekly ceiling, proposed precedence, exact diagnostic ranking/distance, suitability evidence contract and treatment of UNVERIFIED by later consumers. No activation or approval inferred. |
| NUMERICALLY RECONSTRUCTED METHOD | `hypothetical-v6-displayed-source-p-exact-decimal-1`: exact Decimal construction from existing source-display P strings, solely for these experiments. No IF²/source precision approval follows from matching displays. |
| UNAPPROVED ATHLETE METADATA | All 77 actual rows retain unresolved individual suitability. Existing draft phase/bucket/capability/repetition projections remain hypothetical. |
| TESTED OFFLINE BEHAVIOR | Complete finite combinations, exact diagnostics, actual unchanged planner returns/rejections, full canonical 40-case regression and tests linked below. |
| ACTIVE PRODUCTION BEHAVIOR | Historical selection tolerances/objectives and existing safeguards remain unchanged. No new catalog entries or policy enforcement. |

## Pure contract and reasons

`backend/benchmarks/prospective_planning_policy.py` imports only the
standard library and existing pure physiology types/C2.1 evaluator. No I/O,
planner, FastAPI, database, Supabase or LLM dependency. No active application
module imports it; an architecture test protects that boundary. It lives outside
the application package, preserving C2.1's existing isolated-importer guard.

Version: `joren-v6-prospective-policy-sandbox-1`. Frozen typed results separate:

- `LEGACY_VALID`, `LEGACY_REJECTED`, `LEGACY_NOT_EVALUATED`, with explicit automatic,
  manual or offline-unselected origin and evidence reference.
- `PROSPECTIVE_BUDGET_WITHIN` / `PROSPECTIVE_BUDGET_EXCEEDED`, signed exact remaining
  budget, explicitly supplied per evaluation. There is no global 45 cap.
- `SPORT_COVERAGE_SATISFIED` / `SPORT_COVERAGE_MISSING` for structural occurrences,
  separately from `suitable_coverage=SUPPORTED/UNRESOLVED/MISSING`.
- `SPORT_ALLOCATION_DEVIATION`, exact/undefined/not-applicable alternatives,
  exact rational shares, signed deviations and budget-denominator components.
- `INTENSITY_TIME_COMPLIANT`, `INTENSITY_TIME_EXCEEDED`,
  `INTENSITY_TIME_UNVERIFIED`, not-applicable, independently per sport.
- `ATHLETE_SUITABILITY_UNAPPROVED`, excluded/supported evidence distinctions;
  `SOURCE_METHOD_UNAPPROVED`; blocked/unverified restriction findings.

Every finding includes a reason; no overall valid/invalid boolean grants approval.
`LEGACY_VALID` means the real planner returned a pending hypothetical draft,
not that it satisfies future policy or can be prescribed. Private load fields are
excluded from repr and never exported to API/UI/logging/analytics. The explicit
private evidence CLI is developer tooling; its default progress messages contain
case labels/outcomes, never load numbers. No athlete-facing endpoint was added.

## Suitability proposal

`joren-proposed-suitability-evidence-1` requires separate evidence for beginner
capability, sport experience, confirmed training capabilities, suitable duration/
distance, individual long-session scope, injury restrictions, recovery/taper,
repetition/frequency and phase/intensity requirements. Each item carries
SUPPORTED/EXCLUDED/UNRESOLVED, scope, rule version and approval reference. Scope
must identify athlete, template version, local week/phase and planned occurrence
context. A future approved adapter must verify that scope; the sandbox does not
resolve real eligibility from source rows or approve an eligibility algorithm.

Missing dimensions remain unresolved; explicit exclusions and existing blocked
restrictions cannot be overridden by budget or coverage. A sensor or swim pace
capability supports only the capability dimension. It does not establish physical
readiness. BIKE-013 is seven hours; it remains unapproved for beginners even in an
experiment with enough weekly load. No duration limit, medical clearance rule,
frequency value or taper factor is invented. Synthetic supported evidence exists
only in tests under invented `SYNTHETIC-*` identities, never on the 77 real rows.

The supported-suitability enumeration returns zero evidence-supported combinations
and `suitability_evidence_state=UNRESOLVED`. This is an evidence gap, not proof
that no human can perform the numerically feasible workouts. A separate synthetic
known injury case proves no supported three-sport combination can be selected
without weakening restrictions or redistributing load.

## Active-time policy and UNVERIFIED decisions

The evaluator delegates unchanged to `joren-planned-active-time-maximum-1`.
Inputs are actual ordered source segments, athlete-local dates, Monday-Sunday
week. Exact rational seconds preserve the 20% boundary. Stationary swimming rests
contribute zero active time. Unknown swimming block durations stay `None`;
distance, CSS, reference paces, source P and focus RPE never supply minutes.
All-Z2 swimming therefore remains UNVERIFIED, not numerically compliant.

| Decision/consumer | Offline conclusion | Operational gate |
| --- | --- | --- |
| Exact budget arithmetic, structural sport coverage and allocation diagnostics | Can be calculated independently of swim time, explicitly hypothetical. | Source method and suitability still unapproved. |
| Known RUN/BIKE maximum-high assessment | Can be assessed separately without diluting across sports. | Does not verify swimming or approve the whole plan. |
| Exploratory rankings and witness reports | May continue while retaining swim UNVERIFIED. | No authoritative recommendation/default follows. |
| Claim numeric swimming/whole-plan time compliance or available-minute feasibility | Blocked without actual prescribed duration evidence. | No inferred minutes, even for all-Z2. |
| Athlete-facing pending generation with UNVERIFIED, later confirmation/activation | No consumer exception is implemented or approved. | Owner/Joren must decide whether any such consumer may proceed and with what explicit unresolved-state semantics; accountable review remains required. |
| Progression from swimming completion or realized load | Not inferred from this planned-time evaluation. | Existing independent registration/Realized V2 provenance remains authoritative. |

This table identifies independent calculations and unresolved operational choices;
it does not approve proceeding with an unverified training prescription.

## Tested scope and performance preservation

The [budget report](JOREN_V6_STRICT_BUDGET_FEASIBILITY.md) establishes the automatic
45.1 overshoot and manual 43.1 witness, 33 mathematical fits and 23 legacy-fit
candidates. The [allocation report](JOREN_V6_SPORT_ALLOCATION_TRADEOFFS.md) compares
40.2 versus 44.8 without choosing authority.

The separate finite mechanism enumerates exactly one occurrence per required sport.
It checks the entire candidate product or returns `BOUND_EXCEEDED` with no winner.
The experiment bound is 20,000 combinations, above the full 16,632 space; it is
never a production search cap. It does not claim scheduling, unrestricted repeat
optimization or suitability feasibility. Real planner calls provide those legacy
results where required; no monkeypatch, scoring change or runtime policy flag.

Fixtures retain Monday 2026-10-26, Europe/Amsterdam, the existing independently
specified capabilities/history/availability, and the same V6 draft projections.
Forty unchanged scenarios cover zero-history, all-easy, mixed intervals, all BUILD
weeks, recovery/taper, one suitable workout per sport in synthetic evidence,
missing suitability/time/capabilities/dates, no suitable three-sport combination,
single-sport goals, infeasible low targets and existing restrictions/repeats.
All 40 full results and input fingerprints equal the accepted optimized delivery;
all 26 completed accepted-reference outcomes are exactly preserved. Current results
are 29 pending hypothetical plans, ten fail-closed outcomes and one timeout.
The accepted performance improvement of **14 -> 1** diagnostic timeouts is retained.

`current:build_4` remains `DIAGNOSTIC_TIMEOUT`, never declared infeasible.
Accepted partial profile: RSS 110.48 -> 153.59 MiB; resident states 95,327 ->
145,555; expansions 58,117 -> 306,754 at the eight-second checkpoints. The exact
shortcut reaches its optional work bound before continued nonexact DP growth.
No attempt was made to remove this timeout, change scoring/caps or lengthen its
deadline. Both completed search optimizations are unchanged. Partial profiles do
not establish final memory usage or production capacity.

## Reproduction and verification

From this worktree's backend, using the existing project virtualenv:

```text
python -B -m benchmarks.v6_policy_sandbox --private-output NEW_PRIVATE_EXPERIMENTS --regression-output NEW_PRIVATE_REGRESSION
python -B -m pytest -q -p no:cacheprovider tests/test_v6_policy_sandbox.py
python -B -m pytest -q -p no:cacheprovider
python -m ruff check app tests benchmarks
python -m ruff format --check app tests benchmarks
python -m mypy app tests benchmarks
```

Outputs are immutable private artifacts; use new paths for repeats. The regression
uses direct unchanged planner calls in serial owned subprocesses with the same
eight-second bound including imports/setup. Host load is uncontrolled. It compares
complete canonical dataclass outputs/errors, not just totals or workout IDs.

Private evidence: [experiments](policy-sandbox/experiments.json),
[40-case regression](policy-sandbox/regression.json). Verification counts, checksums,
final custody and local commit identifiers are recorded in the delivery addendum.
Backend verification includes OpenAPI/public privacy, recursive load leaks,
C1/C2/C2.1/V6, Realized V2 and A3-A9 retry/concurrency/persistence safeguards.
No old tests/goldens were weakened or replaced.

No database/mobile/API behavior changed. Hosted PostgreSQL/pgTAP/RLS and device
release gates remain open and were not exercised here; no claim of operational
or release completion is made. No push, merge, deploy, migration, historical
recalculation, active configuration/catalog change, hidden activation flag,
Play Store publication or C3-C8 continuation occurred.

## Final verification

All checks below ran after the evaluator was placed outside the application
package. The existing C2.1 isolation guard and all previous tests remain intact.

| Check | Final result |
| --- | --- |
| Focused policy + unchanged C2.1 tests | **65 passed**, 7.19s: 35 new policy cases and 30 existing C2.1 cases |
| Full backend pytest | **2,102 passed**, 165.23s; one existing Starlette/httpx deprecation warning |
| Ruff `check app tests benchmarks` | PASS |
| Ruff `format --check app tests benchmarks` | PASS; 183 files |
| Strict mypy `app tests benchmarks` | PASS; 182 source files; existing `strict=true` |
| Direct unmodified 40-case corpus | All input fingerprints and full canonical outcomes equal final performance delivery; all 26 accepted reference completions exact; all 29 returned plans pass independent legacy checks |
| Offline feasibility oracle | Exact full-set equality; 33 budget fits, 23 scalar legacy fits; 16,632 full-deck and 5,016 all-easy combinations completely examined |
| Source custody | All three archive/original V6 workbook SHA-256 values unchanged; no existing tracked files modified |
| A5/A6 and performance branches | Original clean worktrees/tips retained |
| Mobile/TypeScript | Not applicable to offline-only additions; no mobile or API contract change |
| Hosted PostgreSQL/pgTAP/RLS/device checks | Not run; existing external release gates remain open; no database access or migration |

The full backend suite includes unchanged public/OpenAPI/privacy-leak, Realized
TSS V2, planner/account/retry/stale/confirmation and A3-A9 regression coverage.
No test success is scientific acceptance or operational release approval.

The [verification manifest](policy-sandbox/verification.json) records commands,
counts, custody and open gates. Immutable private artifact SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| experiments.json | `f32d419fbc2d655283dae8f2358a2c215eb3356888b621c172f702a8da02fbe9` |
| regression.json | `3235d89bdbd1b02dd985c79fed514f47232ad6efe5721c206d241f41ee2d0341` |

The verified implementation/evidence Git SHA is recorded in the local delivery
addendum after commit. A following documentation-only commit records that exact
SHA; the final delivery tip is supplied in the final response and resolves with
`git rev-parse experiment/joren-v6-policy-sandbox`. A commit cannot embed its own
final hash.

WOMBO V6 POLICY SANDBOX COMPLETE — OPERATIONAL APPROVALS STILL REQUIRED
