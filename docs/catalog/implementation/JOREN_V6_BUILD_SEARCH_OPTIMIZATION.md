# Joren V6 BUILD search optimization

2026-11-05, Europe/Amsterdam. Local implementation only; no activation or release.

## Custody and scope

Accepted starting branch: `perf/joren-v6-planner`.
Exact starting SHA: `12fde3bd542b42e8259b130be797f673a8c2ded6`.
Verified implementation ancestor: `c7c1b43a5db354d2abea4e128f42ca050179d2ad`.
Ancestry was checked with `git merge-base --is-ancestor`; the accepted performance
worktree was clean. New worktree:
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-planner-build-search`,
branch `perf/joren-v6-planner-build-search`, created directly from the accepted tip.

The main workspace had pre-existing user changes. They and all existing
worktrees were preserved. The A5/A6 release worktree remains outside scope at
`cd3e2dd438031cfb565858d0a5929e9963f7b31f`. Root and nearest applicable AGENTS.md,
the current MVP roadmap, the five requested V6 reports, and existing A9 evidence
were read. No nearer backend/docs AGENTS.md exists.

Only `backend/app/modules/planning/domain.py` changes runtime behavior, through
search-equivalent accelerations inside the existing deterministic selector.
Benchmark instrumentation, frozen oracle, tests, an isolated prospective policy
fixture, and private reports/evidence accompany it. No physiology ruleset or
catalog version changes: formulas and policy are identical.

## Changes

1. Prove exact bounded additions from Decimal precision/exponents before using
   commutativity. Unsupported contexts and rounding/underflow traps fall back.
2. Precompute a necessary, overapproximating BUILD high-load reachability table
   per remaining slot count. Remove states that cannot satisfy the unchanged
   high-load interval with any continuation.
3. For exact, uncapped, unambiguous multi-sport BUILD states, expand only
   nondecreasing UUID suffixes. The historical canonical state representative is
   preserved; fixed prefixes are never reordered.
4. Try complete short exact layers with a deterministic meet-in-the-middle join,
   preserving repeated templates and the exact historical state key. Each complete
   layer retains canonical representatives before the original feasibility check.
   Return only the same earliest exact-layer optimum the DP would return.
5. Build request-local option suffixes and exact integer join keys once. Integers
   are derived directly from all coefficient digits and exponents, with no load
   rounding, approximation, or source-value replacement.

The formal arguments, including athlete scope, limited uses, Z5, sport caps,
arbitrary Decimal contexts, callback rejection, and tie-breaking, are in
[correctness](JOREN_V6_BUILD_SEARCH_CORRECTNESS.md). The proofs justify every
discard, not merely a measured reduction in states.

All new paths require multi-discipline BUILD. Sport caps disable permutation
elimination and the exact shortcut because per-sport load is absent from the
historical key; the independent high-load bound remains sound with caps. Duplicate
deck IDs, large option sets, unsupported arithmetic, or optional-work limits retain
the corresponding accepted fallback. No candidate is arbitrarily removed.

The high table has separate 32,768-entry construction/result ceilings. The exact
join uses all options: at most six appended occurrences for <=64 options, four
for 65-128, and at most 200,000 matching joins. Reaching a ceiling abandons the
shortcut and continues the accepted search. The automatic 24-occurrence search,
legacy fit tolerance, score ordering, and Phase 1 overshoot pruning remain.

## Historical behavior and safety

The old oracle and existing evidence are immutable. A second digest-pinned oracle
captures the exact accepted Phase 1 function. The original complete 40 inputs
and source fingerprints are reused. Completed reference outcomes require full
canonical equality, including failure messages and all dataclass fields, rather
than total-load equality. Newly returned plans get independent legacy checks.

An exploratory version skipped three intermediate scheduling results in A9's
single-sport BUILD trace while returning the identical final plan. That version
was not accepted. New paths were restricted to the multi-discipline scope; the
original A9 assertions and goldens remain unchanged. The accepted single-sport
behavior and its intermediate metadata are retained exactly.

No new cache survives a planning request. No account identity, access token,
database client, or credential enters these tables. Existing A9 subprocess
admission, Decimal-context restoration, cancellation, pending-state confirmation,
idempotency, and stale/version preconditions are untouched. Tables/work are bounded;
the fallback's existing exponential search remains subject to the unchanged
execution boundary. Benchmark timeouts retain the original eight-second limit.

No public DTO, endpoint, mobile code, logging, telemetry, accessibility text,
database/RLS/grants, migration, source workout, planned/realized calculation,
coefficient, zone, injury/recovery/progression rule, or release configuration changes.

## Outcome and remaining gate

The serial cold matrix reduces timeouts **14 -> 1**. All **26** accepted returned
outcomes are exactly preserved. All four V6 BUILD cases now return. The remaining
`current:build_4` timeout is not declared infeasible: its bounded profile shows
continuing combination expansion after the exact shortcut reaches its work cap.
Detailed times, counters, RSS, preloaded runs, and every input/output check are in
[benchmarks](JOREN_V6_BUILD_SEARCH_BENCHMARKS.md).

Uninstrumented V6 BUILD planner calls are 0.053144 / 0.053477 / 0.057002 /
0.014454 seconds (weeks 1-4). Instrumented BUILD 1 replaces a partial
1,526,931-transition search with 45,760 half entries, 11,027 join attempts,
and 158 exact-state evaluations; peak process RSS is 157.49 -> 44.12 MiB.
These compare incomplete accepted work with a completed new search, not two
completed-search speed or memory ratios.

The residual `current:build_4` illustrates the memory limitation honestly:
observed peak RSS is 110.48 -> 153.59 MiB, resident DP states 95,327 -> 145,555,
and expansions 58,117 -> 306,754 at the timeout checkpoints. The optimized run
gets substantially deeper within the same bound; both measurements are partial,
so this does not establish complete-search memory consumption. Optional tables
are explicitly bounded, but the accepted nonexact DP still has combinatorial
state growth. No claim that memory falls for every case, or that this remaining
search is production-capacity-verified, is made.

The automatic beginner result remains 45.1 against 45, classified
**LEGACY_VALID / PROSPECTIVE_BUDGET_EXCEEDED**. Neither it nor the manually
selected 43.1 witness is an approved beginner plan. The separate
[policy gap](JOREN_V6_BUDGET_POLICY_GAP.md) preserves the unactivated budget,
50/30/20 target, per-sport active-time maximum, suitability, Source-P/IF²/Z3,
and missing swimming-duration gates. No general 45 cap is added.

## Final verification and commits

| Check | Final result |
| --- | --- |
| Full backend `python -B -m pytest -q -p no:cacheprovider` | **2,067 passed**, 156.10s; one existing Starlette/httpx deprecation warning |
| New focused BUILD/exhaustive/context/policy tests | **560 cases**, included in the passing final full suite; 240 independent exhaustive cases and 240 seeded accepted-engine differentials, plus explicit edge/context cases |
| Existing A9 parity | All 15 historical single-week cases, spawned-process corpus, and ten-week chain pass with original full-output/intermediate assertions |
| Realized TSS V2, public contract/privacy, account isolation, planning/calendar/activity, cancellation/retry/stale safeguards | Included in the passing full backend suite |
| Ruff lint | PASS, app/tests/benchmarks |
| Ruff formatting | PASS, 180 files already formatted |
| Strict mypy | PASS, 179 source files; existing strict=true configuration |
| Cold / preloaded / instrumented paired corpus | 40 unchanged inputs each, **26 full reference completions exact** in each mode, **14 -> 1 timeouts** in each mode |
| Independent legacy checks | All **29 returned optimized plans** pass in each mode; ten fail-closed outcomes remain exact |
| Report/evidence consistency checker | PASS; compares complete result dictionaries, output hashes, all 40 input fingerprints, and instrumented/uninstrumented transparency |
| Sources / protected branches | Catalog, physiology, SQL, mobile, execution/persistence/release paths unchanged; accepted and A5/A6 worktrees retain their original tips and clean status |
| PostgreSQL/pgTAP / hosted/mobile release | Existing external gates remain open; no database, mobile, API or migration behavior changed or claimed verified by these local checks |

All source, test, and evidence checks were run after the final behavioral change.
Subsequent edits only assemble reports/custody metadata. The immutable
implementation SHA is recorded in the delivery addendum. The final delivery SHA
is also supplied in the delivery response; a commit cannot embed its own hash.
Resolve the local delivery tip with
`git rev-parse perf/joren-v6-planner-build-search`.

No push, merge, deployment, migration, catalog activation, publication, database
access, or automatic C3–C8 continuation is authorized or performed. Source catalog,
A5/A6 release, and production remain untouched. PostgreSQL/pgTAP and hosted/mobile
release verification remain their existing external gates; local backend success
does not close them.
