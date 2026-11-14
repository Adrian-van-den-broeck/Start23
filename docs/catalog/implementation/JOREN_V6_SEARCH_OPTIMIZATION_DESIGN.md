# V6 exact multi-session search optimization

14 November 2026, Europe/Amsterdam. Branch
`perf/joren-v6-exact-multi-session-search`, isolated worktree
`.worktrees/joren-v6-exact-multi-session-search`, accepted starting commit
`e85cbaa8b5e702c283186fc61fcadda74ad36faf`. No production activation.

The three demonstrated incomplete requests now complete with exact independently
verified optima under the unchanged 200,000-node limit. The optimization changes
two production Python files. Frequency policy/resolution, physiological methods,
source revisions, service/persistence wiring, schemas and mobile are unchanged.
The source/evidence hashes and tested implementation commit are recorded in
[`search-optimization/verification.json`](search-optimization/verification.json).

## Authority and baseline

Root AGENTS and the current MVP roadmap govern this change; the Git inventory
contains no nearer backend/docs AGENTS. The automatic-selection, multi-session,
frequency approval/implementation/authorization/latest verification reports,
historical performance contracts, deterministic scheduler and A9 process
executor were inspected. Historical policy reports do not reopen the approved
frequency policy. The historical default planner remains the default dependency.

The original review probe was found read-only in the accepted worktree's private
runtime. `benchmarks/v6_exact_search.py` preserves its exact 15 definitions,
including athlete UUID 1, week 2026-10-26, Amsterdam, all seven dates, race twelve
weeks later, TEST_ONLY reference string, full test capabilities, BASE/BUILD-4
targets and the normal 35/105-minute onboarding inputs without target override.
The entire matrix was reproduced before production changes: every reported node
count and all three honest incomplete results matched. Official workloads come
from `official_catalog()`, including the existing exceptional-duration exclusion.

The earlier 10.8-second domain observation is reproduced as a workload, not an
approved deadline. The historical corpus's eight-second bound applies only to
that corpus. No worker, HTTP or historical timeout was extended.

## Change

The former search built complete per-sport multisets, joined every product under
budget, built a large tuple of weeks, computed each complete rank, sorted that
collection and finally tried scheduling. The budget-300 request exhausted shared
nodes during joining, before any scheduling. Sorting dominated several completed
requests; the budget-250 fixture materialized over a hundred thousand weeks.

The existing per-sport canonical expansion is retained. It now attaches immutable
cached load/count/request/UUID metadata to each complete sport option. Options
are partitioned by exact count and sorted by load. A request-local heap explores
disjoint boxes of those option lists, prioritized by an optimistic five-component
rank. Splitting boxes narrows exact load intervals. A singleton has its actual
rank and is materialized only when it precedes every remaining optimistic bound.

`multi_options` therefore becomes a lazy iterator of **exactly ordered** complete
weeks. `build_v6_plan` consumes that order directly for the explicit-frequency
automatic path. It retains the original complete-week sorting/20,000-combination
path when no frequency record exists, and the original explicit-selection path.
The first successfully scheduled week has a global optimality certificate for
the same authorized catalog/count/prefix scope as before. A final call to the
existing complete-week validator checks the selected week before it is returned.
The existing private `EXHAUSTIVE_GLOBAL_OPTIMUM` result label is retained for
compatibility; its completeness is now certified by disjoint bounds rather than
by materializing every product. It never denotes a resource-truncated incumbent.

See the [proof](JOREN_V6_SEARCH_OPTIMALITY_PROOF.md) for every bound and exclusion.
No HIGH-heavy partial prefix is discarded, no states are merged by load, no
template dominance is assumed, and no aggregate calculation asserts scheduling
feasibility. The unchanged scheduler still owns deterministic dates, immutable
occurrence identities, retained dates, same-day placement, rest and HIGH spacing.

## Resource contract

The limits stay at 24 complete-week occurrences and 200,000 shared successful
worknodes. The next attempted node raises `v6_search_incomplete`; evidence records
that failing 200,001st probe separately from the allowed completed work. Sport
expansion, box admission/testing and scheduling share the same counter. Heap
removals/splits are bounded by charged admissions. Sorts operate only on bounded
sport-option metadata, with no complete-week candidate sort on the new path.

Memory is proportional to bounded metadata and pending boxes. Spans share their
immutable option lists; templates and UUID strings are reused. No global mutable
cache or cross-athlete state is introduced. Exhaustion at any stage aborts the
proposal, including when some mathematically attractive weeks already exist.
There is no arbitrary incumbent, silent request reduction or false rest week.

A9's single spawned process, one waiting request, fail-fast further admission,
caller Decimal context and shielded worker ownership remain unchanged. Cancelling
an owner cannot release its CPU slot early or continue into persistence. Both
existing HTTP cancellation tests and a new optimized V6 worker test verify this.

## Verification design

The existing 30 independent multi-session oracle seeds and all historical oracles
remain. A second independent exhaustive reference visits all complete products,
implements source predicates/arithmetic/ranking separately with scaled integers,
and searches dates independently. It verifies all 15 full-catalog results,
including the three formerly incomplete ones, without sharing any box bounds.
New tests also falsify individual bounds and exercise non-placeable top ranks,
fixed repeated identities/dates, restricted availability, caps, injury/capability,
all phases, BUILD restrictions, partial/rest outcomes and lazy global ordering.
The old exact Decimal, 20% HIGH boundary and repetition tests are unchanged.

Actual worker/HTTP before/after measurements use the same inputs and machine.
The baseline transport process imports application/tests/catalog sources from an
accepted Git archive under this task's ignored runtime, so spawned children run
the original algorithm too. No protected worktree is modified. The application
archive is distinct from the instrumented benchmark scripts copied into it.

Durable SQL includes the original 35-minute synthetic multi-session trace, its
concurrency suite, the regular frequency/revocation runner, and a new 105-minute
normal-budget trace covering an incomplete no-write attempt, exact A5 retry,
pending replacement, separate confirmation, activity registration, preserved
completed sibling, immutable original revision, move retry and Calendar readback.
Real PostgREST tests close TCP replies after commits, and complete database/process
restart tests check exact recovery. The synthetic harness's pre-existing limited
test-role membership is temporary and revoked before the regular-path network
tests and final audit. No actual reviewer or numerical authorization is issued.

See [measurements](JOREN_V6_SEARCH_BEFORE_AFTER_BENCHMARKS.md) and
[regressions](JOREN_V6_SEARCH_INTEGRATION_REGRESSIONS.md) for executed results and
the [Dutch release register](JOREN_V6_REMAINING_RELEASE_GATES_NL.md) for independent
operational/scientific gates. No latency SLA is inferred from these measurements.
