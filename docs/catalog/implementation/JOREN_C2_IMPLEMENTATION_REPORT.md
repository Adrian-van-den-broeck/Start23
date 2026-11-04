# C2 implementation and verification report

## C2.1 current delivery — 2026-11-04

Status: **C2.1 COMPLETE — JOREN 80/20 POLICY LOCKED, BEGINNER SOURCE PENDING**.

Scope: decision consolidation and approved swimming source correction only.
Accepted branch `feat/joren-three-sport-catalog-c2` started **clean**, at exact
SHA `ed052211ce413dd045b2e91af0d6a8e59ee534ff`, verified against HEAD and its branch
ref. Worktree:
`F:\Projecten Business\Start23\Code\.worktrees\joren-three-sport-catalog-c2`.
The initial main checkout was on `fix/pre-ui-beta-blockers` with unrelated dirty
files; it and all other worktrees were left untouched. No branch switch, stash,
fetch, push, merge, production/staging access or deployment occurred.

Read root AGENTS.md (no nearer backend/docs instructions), current MVP roadmap,
C2 implementation report, current decision register and complete C1–C8 sequence.
Realized V2 and all seven A3–A9 SHAs listed in the historical report remain verified
ancestors. The latest explicit task approvals supersede older whole-workout and
exact-80/20 policy descriptions prospectively, without changing historical behavior.

**Joren's 80/20 maximum is formally confirmed.** Policy version
`joren-planned-active-time-maximum-1` records its evidence and existing
`phase-3-ruleset-3` segment taxonomy (Z1/Z2 low, Z3–Z5 high). The pure isolated
`physiology/planned_intensity_policy.py` evaluates active segment seconds for each
sport in one explicit athlete-local Monday–Sunday week. It uses exact rational
accounting and comparison: 0% and exactly 20% pass, above 20% fails. There is no
high minimum for beginner, recovery or taper weeks. Stationary swim rest is
excluded, segment intervals remain mixed, and no TSS, workout-count, distance,
CSS or session-focus input substitutes for active time. Complete empty/zero-time
sport/weeks are NOT APPLICABLE; missing reliable time or classification is
UNVERIFIED with no compliance ratio. No active planner imports the helper.
It does not approve plans or replace any existing safeguard.

The proposed BIKE/RUN/SWIM 50/30/20 weekly planned-TSS allocation remains separate;
target versus hard constraint and infeasible-allocation handling are still open.
No automatic load increase, baseline change, arbitrary source shortening,
progression exception or intensity-limit relaxation is introduced.

C2 had **not** produced an approved corrected derivative: its source evidence and
draft registry retained all six original conflicts. C2.1 adds the lossless revision
`joren-swim-if2-approved-prescription-overlay-1` in
`joren_c21_swim_corrections_v1.json`, digest
`a850a745e2170a3024f00ca201116880f8ba66de46d73e6b40ef8dbd380a948a`.
It records Joren's correction approval C2.1-SWIM-1, original source hash/bytes,
all original document/cell XML and ordered events, exact six before/after strings,
derived ordered events/guidance, aggregates and rerun arithmetic. Only N19–N24
change the single 300m Z3 block to Z2. No original cell is rewritten.

- **A — Original source:** six contradictions remain historical evidence.
- **B — Corrected derivative:** all 20 structures pass total/zone reconciliation.
  All six corrected rows pass IF² arithmetic with confirmed populated anchors and
  explicit historical reference parameters: 39.88125 / 54.759375 / 69.6375, repeated
  for 018–020, displaying 39.9 / 54.8 / 69.6. No remaining structural, arithmetic
  or provenance failure affects those six under the verification parameters.
- **C — Operational status:** INACTIVE. Reference paces, normalization, Z3 IF in
  010/011/014, intermediate rounding, source precision/storage, operational P
  authority, method/V2 compatibility, replacement identity and release approvals
  remain outstanding. Diagnostic reconstructed rounded paces match 20/20 displays;
  exact historical seconds with reconstructed Z3 match 16/20. Neither is approval.

All 20 swims, including corrected rows, still lack prescribed active minutes:
time-based compliance is UNVERIFIED. No minutes are inferred from reference paces,
CSS or meters. The original workbook and five pinned source archives, all four
historical JSON artifacts and all prior identities remain unchanged. Original
conflict markers in old artifacts apply to their original revision only.

**Beginner 45 versus 64.5 remains OPEN — ACTUAL LIGHTER SOURCES PENDING.** Joren
will supply additional lighter workouts. The C1 manifest addendum prepares the
existing SourceSpec/read_document/parse_events/normalize_row/immutable-output
intake path and required provenance, arithmetic, coverage and feasibility checks
for those real future revisions. No fabricated sessions, placeholders, new active
entries or premature 61-row beginner-ready claim are introduced.

Reproduce the corrected artifact from backend with
`python -B -m app.jobs.joren_c2_dry_run --dry-run --approved-corrections --private-output NEW_PATH`.
Default C1/C2 output is preserved; identical correction retries are read-only and
conflicting existing outputs reject. Output summaries remain private-load-free.

### C2.1 verification and local delivery

Using the existing root `backend/.venv/Scripts/python.exe`, with this worktree's
backend as cwd:

| Check | Final result |
| --- | --- |
| Focused C1/C2/C2.1 tests | **269 passed**, 5.90s; 30 new C2.1 tests, no existing test weakened |
| Full backend `python -B -m pytest -q -p no:cacheprovider` | **1,282 passed**, 149.59s; one existing Starlette/httpx deprecation warning |
| Ruff `python -m ruff check app tests benchmarks/joren_c2.py` | Pass |
| Formatting `python -m ruff format --check app tests benchmarks/joren_c2.py` | Pass, 166 files |
| Strict mypy `python -m mypy app tests benchmarks/joren_c2.py` | Pass, 166 source files; repository strict=true |
| Corrected artifact reproduction/retry | Exact canonical bytes/digest; conflicting output rejected; staged blob equals local artifact byte-for-byte |
| Source custody | Five external originals equal pinned archives; all nine original archive/historical JSON files equal accepted C2 blobs |
| History and isolation | All eight historical report bodies retained after marked addenda; V2 and A3–A9 ancestors verified; no active importer/entry added |
| Diff hygiene | `git diff --check` and staged equivalent pass |

Coverage includes 0%, exact 20%, strict-above-20%, all three sports independently,
segment accounting rather than workout count/focus/load, week boundaries, missing
swim time/classification, stationary rest, empty/zero weeks, six exact corrections,
all 20 aggregate checks, original immutability, offline behavior, repeatability,
caller Decimal-context independence and no activation. The full suite also covers
OpenAPI/public contracts, recursive private-load leaks, Realized V2 and A3–A9.

Exact verified implementation SHA is recorded in the C2.1 delivery addendum below.
The following report-only commit records that immutable SHA; the final branch-tip
SHA is supplied in the delivery response and resolves with
`git rev-parse feat/joren-three-sport-catalog-c2`.

No C3–C8 work is performed. PostgreSQL/pgTAP remains **DEFERRED BY OWNER —
PRE-BETA**, not passed. No database, mobile, API, active-catalog, Realized V2 or
planner implementation changes are made; no mobile checks are required for this
offline-only change. Database, scientific, device and later integration/release
gates stay open. No push, merge, deployment or catalog activation occurred.

### C2.1 local delivery addendum

Exact final verified C2.1 software/source/evidence SHA:
`5b6c960cf817dfebc31cffbd6e7f6fc58f2309be`, direct child of accepted
`ed052211ce413dd045b2e91af0d6a8e59ee534ff`. The worktree was clean after this
commit. This following report-only commit adds its immutable reference; its own
branch-tip SHA is recorded in the final delivery response (a commit cannot embed
its own hash). No implementation or artifact bytes change in that final commit.

All required local verification passed. Original and corrected source revisions
retain distinct status; the six corrections are structurally valid, all planned
swim active-time coverage stays UNVERIFIED, and catalog activation stays disabled.
Additional lighter workouts and remaining method/precision/release decisions are
pending. PostgreSQL/pgTAP: **DEFERRED BY OWNER — PRE-BETA**.

WOMBO C2.1 COMPLETE — JOREN 80/20 POLICY LOCKED, BEGINNER SOURCE PENDING

## Historical accepted C2 report — retained evidence

2026-11-04, Europe/Amsterdam. Private developer evidence.
Status: **PARTIAL COMPLETE — SOURCE AND BEGINNER POLICY APPROVALS PENDING**.

## Baseline and isolation

Exact starting SHA: `e436285e9f169908a45ff8f34aeed0e003ba6bc2`, verified tip of
`feat/joren-three-sport-catalog-c1`. New branch:
`feat/joren-three-sport-catalog-c2`; worktree:
`F:\Projecten Business\Start23\Code\.worktrees\joren-three-sport-catalog-c2`.
The main checkout and all unrelated worktrees/changes were left untouched.
No fetch, push, merge, deployment or production/staging operation was performed.
The local implementation commit is recorded in the delivery addendum below;
the following documentation-only commit records its exact immutable SHA.

All applicable root instructions and the current MVP roadmap were read, together
with the full C1 report, A–F brief, final reconciliation, planning simulation and
C1–C8 sequence. No nearer backend/docs AGENTS.md applies. Current owner decisions
take precedence over older open-decision descriptions without erasing them.

`git merge-base --is-ancestor` returned0 for every required ancestor:

| Baseline component | Verified ancestor SHA |
| --- | --- |
| Realized TSS V2 completed baseline | `cef4d0adfb09f5f1937528a98c594a6442816f20` |
| A3 restriction round trip | `b65ea78be1db886586d793f721bb2910ddbc6a41` |
| A4 plan handoff | `4bb0cdea8f46242018ad8e5d22fa79a706cbf207` |
| A5 proposal recovery | `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf` |
| A6 account-scoped recovery | `24b27ebd34ccfe662ca57994a736f4f853af8d0b` |
| A7 activity/cache synchronization | `75f172d4161f71a763247b04c027fd165901afbd` |
| A8 auth/network recovery | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` |
| A9 performance remediation | `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` |

## Source evidence and decisions

The new original was located at
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog\docs\trainings\Zwemtrainingen_IF2.xlsx`.
Its actual7405 bytes match SHA-256
`7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb`
before processing. An unchanged custody copy is archived under `docs/catalog/sources`.
The original swim workbook and PDF remain separate historical source versions.
Neither their values nor previous reports were replaced by the new intake.

All317 cells in each swim archive were inspected directly from OOXML, retaining
exact numeric lexemes, formula/cache absence, style/format, source coordinates
and cell XML. Twenty loads, ten titles, twelve aggregate cells in six rows and
one note change:43 value differences,83 complete cell-record differences including
formatting. The sheet name also changes. All ordered interval values remain
unchanged. See the [complete source comparison](JOREN_SWIMMING_IF2_SOURCE_DIFF.md).

TR-SWIM-015/016/017/018/019/020 are **SOURCE-CONFLICTED**. The source aggregate
Z2/Z3 is600/0; execution is300/300, including an initial300m Z3. Strict experimental
verification rejects these rows before arithmetic. Their complete originals are
retained. The [six-row Dutch correction request](JOREN_SWIMMING_IF2_CORRECTION_REQUEST_NL.md)
contains exact source values and full N strings; it was prepared and not sent.

Confirmed owner-relayed decisions are recorded separately in
[updated decision evidence](JOREN_C2_UPDATED_DECISIONS.md): IF² intent and existing
populated anchors, revised swimming source, distance/rest semantics, session focus
from the most intense block, and desired one-per-sport beginner composition.
The50/30/20 and per-sport80/20 proposals do not establish enforcement, denominator,
rounding or safety exceptions. Original decision dates/independent review references
were not supplied and are not invented.

## Calculation support and operational boundary

`physiology/planned_source.py` provides pure isolated arithmetic with explicit
Decimal input parameters, exact rational evidence and a reproducible50-digit
HALF_EVEN Decimal result. It has no framework, database, settings, network, LLM or
planner dependency. IF² timing uses the sport factor once; distance conversion
uses explicit reference paces without producing athlete duration. Stationary
rests add zero. Unknown versions, invalid inputs and missing populated anchors
reject. Historical fixed-distance dispatch stays separate and rejects a second.90.

`workouts/joren_c2_verification.py` verifies pinned source revisions, exposes a
strict conflict-rejecting experiment and keeps raw source P/display/exact calculated
P separate. Confirmed anchors never fill missing Z3. A distinct diagnostic branch
uses **RECONSTRUCTED** Z3=.88 and rounded reference minutes, explicitly unapproved.
No existing active application module imports this verification adapter or pure
calculator; only the offline job, tests and synthetic benchmark use them.

All20 new swimming comparisons, including exact-second and rounded-minute
experiments, raw lexemes, source displays, differences, structure and approval
status, are in the [complete calculation reconciliation](JOREN_SWIMMING_IF2_TSS_RECONCILIATION.md).
Exact historical reference seconds plus reconstructed Z3 reproduces16/20 aggregate
displays; rounding reference minutes first reproduces20/20. That fit is evidence,
not approval. Original pace/IF/normalization/rounding evidence remains required.
Three consistent rows reject missing Z3; the other eleven consistent rows accept
only explicit mathematical parameters and remain operationally unavailable.

All41 RUN/BIKE displays reproduce under the confirmed populated IF² anchors and
diagnostic HALF_EVEN. Exact quantities retain half-minute sprint segments. Source
precision, operational P authority and V2 compatibility remain unresolved, so no
timed method is activated either. No zone-minute coefficient is changed.

Versioned per-block guidance uses existing `joren-realized-tss-matrix-2` zone ranges
while retaining original source session-focus independently. Rest has no zone or
RPE. No recovery block is forced into the session-focus range; the legacy validator
and historical RPE interpretation are untouched. Public integration is deferred.

The C2 private JSON includes all20 revised swim rows, all original cells, all41
timed calculation/guidance records and both diagnostic swim interpretations.
`joren_c2_draft_revision_registry_v1.json` preserves all61 C1 identities/version1
and proposes20 distinct swim successor IDs/version2. It does not approve a
predecessor mapping, catalog release, operational value or activation.

Every operational accessor rejects unapproved methods. No active catalog, global
coefficient, athlete plan, zone, identity/revision, historical activity, RPE reader,
database migration, progression rule, sport-allocation rule or80/20 rule changed.

## Planner feasibility and multi-week consequences

The [policy analysis](JOREN_BEGINNER_50_30_20_POLICY_ANALYSIS.md) and committed
`benchmarks/joren_c2.py` execute the actual unchanged planner on isolated synthetic
inputs, preserving current restrictions, capacity, schedule and registration rules.
No conflicted swim row enters the deck. The source display grid and hypothetical
64.5 exception are explicit fixture assumptions, never active configuration.

The true zero-history45 target rejects the lightest three-sport64.5 combination.
Its shares are46.82/26.98/26.20%, not50/30/20. A counterfactual64.5 starter produces
three pending occurrences with90 known minutes plus1000m unknown swim duration.
Recovery38.7 and taper22.575 reject those same three sessions. Missing capability,
no availability and restricted zero-history allocation fail closed; all-injured
returns pending rest-only. One date consolidates workouts and warns, without
proving time capacity. Sole BIKE013 exposes the unchanged420min/393.8 fallback
hazard even at target45. A distribution proposal is not a session-suitability cap.

After hypothetical independent complete observations totaling64.5, next target
is70.95; the actual three-session selection remains64.5 with a fit warning. Missing
swim holds64.5; explicit skip yields47.6 and rejects that starter. Week3 holds the
actual selected64.5 after an incomplete second week. No source prescription or CSS
is treated as observed load or actual time. The analysis compares hard budget,
reviewed exception, easier supplied workouts and explicitly approved phased
introduction, with numbers, shares, counts, capacity, multi-week effects and required
approval for each. None is enabled. Single-sport and sparse-week80/20 choices remain
explicit; three easy sessions cannot satisfy exact80/20 per sport.

## Verification

Using the existing project virtualenv, from this worktree's backend:

| Check | Actual final result |
| --- | --- |
| Focused C1+C2 tests | **239 passed**,5.95s |
| Full backend `python -B -m pytest -q -p no:cacheprovider` | **1,252 passed**,151.91s; one existing Starlette/httpx deprecation warning |
| Ruff `python -m ruff check app tests benchmarks/joren_c2.py` | Pass |
| Formatting `python -m ruff format --check app tests benchmarks/joren_c2.py` | Pass,163 files |
| Strict mypy `python -m mypy app tests benchmarks/joren_c2.py` | Pass,163 files; repository strict=true |
| Original C1 dry run | Same61 rows,336 offline UUID references, no errors; original artifact digest unchanged |
| C2 source dry run, identical-output retry | Same exact private artifact; no load in default stdout; source/unknown method/conflict/overwrite rejection tested |
| Actual planner synthetic harness, identical-output retry | Same exact private evidence; no live state changes |
| Custody |24 protected C1 files equal baseline Git blobs byte-for-byte; original artifact and four sources preserved; new original/copy hashes match |
| Diff hygiene | `git diff --check` passes |

The full suite covers OpenAPI/public contracts and recursive private-load leak
checks; historical source/catalog/migration contracts; A3–A9 behavior and exact A9
parity; Realized V2 factor/RPE mapping/version dispatch; registration, correction,
measurement priority, stale/version preconditions, idempotency and safe next-week
holds. Existing tests were not modified or weakened. C2 adds83 focused tests.
An initial source comparison test revealed expected style/XML differences despite
unchanged interval text; the corrected assertion preserves value/type/format parity
and separately retains complete original XML. It does not assert false byte equality.

Git's Windows checkout converted three C1 implementation reports to CRLF in the
fresh worktree. Their exact original LF bytes were restored from the untouched C1
worktree, and a narrow C1 Markdown LF attribute preserves them in future checkouts.
The only C1 content amendment is the requested source-manifest intake addendum;
the original C1 JSON and historical reports remain unchanged.

Mobile code, public contracts and database code are untouched. No unnecessary
TypeScript/mobile changes or checks were made. PostgreSQL/pgTAP/RLS execution is
**DEFERRED BY OWNER — PRE-BETA**, not passed; no tooling was installed and no hosted
database was contacted. Broader full-catalog search timeouts, scientific/release,
device and later C3–C8 integration gates remain open, outside this verified offline
scope. Passing local tests does not close those gates or make full C2 complete.

## Remaining decisions and final status

Required next inputs: six corrected swim prescriptions; original Z3/pace/formula/
normalization/rounding evidence and exact operational P/version authority;
beginner ceiling/exception/progression or easier sources; distribution/intensity
denominators, constraints and infeasibility behavior; long-session individual scope;
catalog release/replacement and V2 compatibility. Activation requires its own
later owner decision and release gates.

All six requested reports, source custody, private deterministic fixtures and
draft registry are delivered. No activation, push, merge, deployment, staging/
production mutation, automatic baseline increase or historical recalculation occurred.

## Local delivery addendum

Exact verified software/source/evidence commit:
`e3d8ae1806e4f11a17b6f5cdeea47ee54dbdc409`, directly based on
`e436285e9f169908a45ff8f34aeed0e003ba6bc2`. The following commit changes only
this report to record that immutable implementation SHA. The final branch-tip
SHA is supplied in the delivery response and resolves with
`git rev-parse feat/joren-three-sport-catalog-c2`.

All three canonical C2 JSON artifacts were compared against their staged Git
blobs byte-for-byte before commit. The new original/custody archive was rehashed
again after commit with the exact expected result. The implementation commit
left the worktree clean. No push, merge, deployment or activation occurred.

WOMBO C2 PARTIAL COMPLETE — SOURCE AND BEGINNER POLICY APPROVALS PENDING
