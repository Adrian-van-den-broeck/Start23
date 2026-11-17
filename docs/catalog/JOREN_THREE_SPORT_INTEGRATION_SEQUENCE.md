# Joren three-sport integration sequence — C1–C8

Review date: 2026-11-03, Europe/Amsterdam. REVIEW ONLY; no activation.
Accepted engine: `feat/joren-realized-tss-v2`, exact SHA `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Reused branch `review/joren-new-workout-catalog`; worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
All private load numbers are developer review evidence, never athlete-facing data.

| Source | Original file | Bytes | SHA-256 |
| --- | --- | --- | --- |
| RUN | Looptrainingen_Definitief_Optie1.xlsx | 7198 | dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3 |
| BIKE | Fietstrainingen_Definitief_Optie1.xlsx | 7376 | 5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df |
| SWIM | Zwemtrainingen_Definitief_Optie1.xlsx | 7333 | bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674 |
| SWIM spec | Specificatie Zwem TSS.pdf | 149021 | ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a |

RUN original is in `F:\Projecten Business\Start23\Code\docs\trainings`.
BIKE, SWIM and the swim PDF originals are in
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings`.
All four originals remain byte-identical and at those exact locations. Delivery
is verified; catalog versions and methodological acceptance are separate decisions.

## Status, authority and engineering choices

This is the final **future implementation/migration plan**. None of slicesC1–C8
is implemented by this review. A–F in the Dutch brief must be accepted where they
change source method, training scope or selection intent. Engineering may resolve
lossless parsing, deterministic identity and immutable lineage within those
accepted requirements; it may not fill missing IF anchors, athlete constraints,
CSS scaling or a realized distance ratio. The original nine reports were preserved
before marked updates; the six sport-specific RUN/SWIM findings remain byte-identical.

Proposed technical identity is fully specified and collision-checked against the
available offline current/source projection; final durable uniqueness checks are
a database gate, not a claim about unqueried hosted successor UUIDs:

```python
from uuid import NAMESPACE_URL, uuid5
key = uuid5(NAMESPACE_URL, f"wombo:joren:optie1:{sport}:{source_workout_id}")
id = uuid5(key, f"source-sha256:{workbook_sha256}|template-version:{version}")
```

`sport` is exactly `run`, `bike` or `swim`; `source_workout_id` is the exact original
TR identifier; workbook hash is lowercase64-digit hex; initial proposed template
version1. Registry-controlled later accepted revisions increment version, never
reuse version1 under the same key with different bytes. A formally accepted
logical-predecessor mapping under decisionB must be explicit before reusing any
old key. Default proposal gives all 61 distinct new keys. All 61 keys/IDs are unique
in the offline check; there is no title/suffix conversion or legacy CSV integer
identifier trick. File paths are evidence, not part of identity, so moving a
byte-identical intake does not change its mapping. File hash changes require an
accepted source revision, including regeneration/formatting changes.

| Source example | Proposed stable key | Proposed first template ID |
| --- | --- | --- |
| TR-RUN-001 | d8520c07-aadb-5529-a0c7-6b78cf53ae15 | 9d732bc4-85c9-52f9-a2ce-6caac4b841be |
| TR-BIKE-001 | b2cfa062-b8a8-51be-af35-41054fb4b2a7 | 7b71861a-c2d0-5176-86e0-b338731d9824 |
| TR-SWIM-001 | 9c9e54eb-b2a7-5e02-8aba-d7999909565c | d176d407-a925-53a1-a708-4535237304c7 |

The full deterministic61-row mapping is reproducible from this recipe and the
manifest. Retain explicit mapping rows in the future migration artifact and
assert no UUID/key/version collision before insert. This recipe is an engineering
proposal, not approval that a particular old training is obsolete.

## C1 — Immutable manifest and lossless adapter

Inputs: original four files, exact hashes/bytes above; accepted source release and
replacement policyB. Output: versioned manifest and dry-run normalized candidates,
without changing active selection. Keep the original files read-only.

- Manifest contains catalog release, sport-source and method revisions, original
  filename/hash/byte count, accepted owner/decision reference, all sheet names/
  states/extents, source ID, template mapping and row-level origin. Do not use
  workbook timestamp or “Definitief” as a method version.
- Read OOXML cell value/type, exact numeric lexeme, formula/cache and number format
  separately. Preserve source header spelling/newlines and original row/column
  coordinates. Store original row and ordered raw tokens alongside normalized
  quantities. Any changed source is a new input revision; no resave/recalculation.
- Parse timed RUN/BIKE as ordered `Nm Zk`/`Ns Zk` with exact Decimal/canonical
  seconds; convert30s to.5min and sum before rounding. Parse SWIM `Nm Zk` as
  meters and `Ns Rust` as an unzoned stationary-rest event. Full-token consumption,
  positive measures, totals and every zone subtotal must agree. No inferred warm-
  up/cooldown, unprovided rest, distance or Z3 IF value.
- Proposed canonical event union separates a swimming distance block and a
  stationary rest with positive seconds/no distance/no zone/no RPE. Preserve
  original sequence positions. P 50/D61 diagnostic textual folding is not this
  production adapter. Source swimming distance and unknown swimming duration
  remain separate fields.
- Reject duplicate/version-colliding IDs, unsupported syntax, nonfinite values,
  missing units/methods and unexplained numerical discrepancies. Quarantine row
  issues with private evidence; athlete errors/logs must not expose load values.
- Do not pipe these rows into the old CSV generator: its split-token ID parsing,
  integer TSS conversion, different headers/segment columns and missing rest
  representation are incompatible. Add one explicit adapter using existing
  domain/repository patterns; do not create a parallel training engine.

Acceptance: all 61 rows reproduce original values/ordered events; format/formula
presence is attributable; original files unchanged; import retry on identical
manifest emits the same IDs/payload; a changed accepted revision is never an
unconditional overwrite. The dry-run adapter performs no migration/activation.

## C2 — Approved planned source methods and precision

Blocked on A and the planned swimming scope in E. Resolve the exact authority
between raw stored source P and independently calculated operational P before
creating any operative load row. Retain both; never overwrite the original.

- RUN/BIKE H remains hypothetical until accepted: populated zone IF candidates
  .55/.75/.98/1.15, run multiplier1.15/cycling1.00 once, divide60 last. Z3 has no
  evidence and must reject any future populated Z3 under this proposed method.
  Do not dispatch the inactive per-score sRPE formula or change zone coefficients.
- SWIM uses explicit published per 100m constants .98/1.44/1.98/2.40/2.70, rest0;
  do not multiply .90 again. CSS1:55 is a reference, not an athlete converter.
- Recommended operational arithmetic if A is accepted: exact decimal inputs,
  versioned50-significant-digit HALF_EVEN divide-last policy, no intermediate
  quantization; retain the context result and source numerator/denominator as
  relevant. Original source display grid remains separate, with accepted
  one-decimal source rounding for RUN/BIKE. SWIM's source file has no tie to
  identify its general one-decimal rounding mode; choose/document that boundary
  explicitly rather than attributing it to the PDF.
- Private evidence stores source raw P, display format/result, exact derived P,
  accepted operational P, method/version, constants/multiplier, numeric policy
  and acceptance reference. Neither retained P nor a historically overloaded
  occurrence label may be described as an independent zone recomputation.

Acceptance fixtures include BIKE 00130.25→30.2 vs HALF_UP30.3, BIKE 010281.25→281.2,
BIKE 004 raw residue and H84.375/current 72, RUN 00986.25→86.2 and raw017 residue,
SWIM 010 exact28.44/stored28.4, and per 100mZ1 .98 versus raw-pace.975. No historical
private load is recalculated to pass these fixtures. A new method/version label
is a proposal until accepted and supported; unknown combinations stay unavailable.

## C3 — Versioned templates and full ordered structures

Create immutable new templates/successors only afterC1/C2 decisions, using the
explicitB mapping. Extend existing typed internal catalog/snapshot contracts to
retain source session-focus RPE, versioned per-block guidance, typed rest events,
optional planned time and distance, plus original/private load provenance. Do not
weaken the invariant by falsely placing hard focus RPE on recovery blocks.
Old stored catalog/protocol/plan snapshots retain legacy interpretation/readers.
New template guidance dispatches the accepted new mapping; never globally redefine
historical RPE 3 or calibration rules. Any public additive guidance fields require
typed Pydantic/OpenAPI and strict mobile contract work in that future slice;
private planned-load evidence must remain server-private. No UI redesign is implied.

Prepared migration artifact must list exact source IDs/keys/versions, fields,
ordered segment/rest rows and private load records. No title merge, numerical
suffix alias, historical template deletion or regeneration of approved plans.
Validate full structure/field parity between dry-run payload, Python and durable
rows. Mixed sessions remain mixed even where a focus label isZ5.

## C4 — Approved selection metadata

Blocked onC/D in the brief. Materialized61-row proposal is in the final
reconciliation. Low single-zone Z1/Z2 proposes base/build/recovery/taper; mixed
Z3+ proposes high/build, with Z5 limited to existing position 4 filtering. RUN/BIKE
requires confirmed HR capability, SWIM pace/CSS; no new HR/swim conversion.
Record auto/swipe/explicit-only flags and repeats distinctly, not from a title.
The seven-hour row is held from automatic beginner use pending explicit individual
scope; no other new physiological duration/availability threshold is invented.

Keep current target coefficients, recovery/taper factors, high budgets, at most24
automatic occurrences, separate occurrence UUIDs, date availability, run72h and
bike/swim48h high spacing, injury recipient/cap/consent rules and fatigue/illness
precedence. If approved metadata cannot satisfy a target, preserve fail-closed/
qualitative warning behavior; do not scale a source workout or edit the formulas
just to fit it. Athlete date availability currently supplies no minute budget;
adding one would need an explicit separate input/rule specification.

## C5 — Distance-swimming planned P, only if E accepted

The actual planner **does not fundamentally require T for load fit and date
placement**: existing snapshots allow distance-only SWIM, scheduling uses dates,
and the time distribution already excludes unknown durations with a warning.
D61 demonstrates this in memory. The active source projection currently removes
P deliberately; it is not an accidental numerical mismatch to bypass globally.

Minimum necessary production changes are:

1. Add explicit accepted distance-load method/version and private lineage through
   existing catalog repository/model/snapshot/occurrence persistence. The present
   Python template/snapshot carries P but not a complete per-template load-origin
   method/version; do not rely on the current generic planning-revision label to
   encode a new distance calculation honestly.
2. Change `with_current_load`/catalog projection only for the explicitly accepted
   method/version to preserve valid distance P, while leaving T=None. Unsupported
   distance sources remain unavailable. Do not infer T from published CSS/paces.
3. ImplementC3's lossless rest representation and D's per-block guidance, without
   fake Z1/meter/minute values. Keep total swimming meters, rest seconds and
   unknown active/elapsed planned duration separate.
4. Retain a typed internal completeness marker for planned time/intensity coverage.
   Existing distance warning can communicate the qualitative boundary;0 known
   minutes/0% in an all-swim week must not be represented as full zero-duration/
   intensity evidence. DecideE's consumer scope: if complete all-sport time ratio
   is required, withhold that conclusion/selection or require independently
   prescribed time; never silently use a reference pace to fill the denominator.
5. Preserve actual completion semantics: observed minutes may yield supported
   actual load; distance source P and rest text do not prove execution. Identified
   wall rest is0 in the source method, but active-versus-elapsed actual duration
   and complete-rest evidence need an approved policy before partial coverage is
   upgraded. No new mean-HR/CSS/provider/pace conversion is introduced.

No new distance-ratio realization method is part of this minimum plan. If desired,
commission a separate scientific specification rather than swapping meters into
A/T. Current duration V2 stays unavailable for these source swims with missing T.

## C6 — V2 interoperability and weekly completeness

Keep `E=P*A*F/T` and the exact approved factor,50-digit policy and measurement
hierarchy. Snapshot original exact plan/revision/occurrence/template/source/P/T/
zone/method/version and source manifest; corrections reuse that basis. A new
planned-method compatibility table must be explicitly accepted. The existing
approved retained-timed-source occurrence convention may be reused only with
honest immutable origin and explicit accepted compatibility; otherwise support
a named new combination or fail closed. Never relabel historical unsupported
source-method/version rows or give distance swims fake T to pass dispatch.

Observed/partial/approved mean-HR results retain precedence; no RPE addition or
multiplication into measurements. Whole-session mixed matrix remains excluded;
A≠T math remains retained but automatically withheld by the current reliability
policy. Explicit actual-duration confirmation and canonical integer Session-RPE
remain mandatory. Expected session focus never confirms actual interval execution.

Retain exact expected occurrence sets, distinct repeats, explicit skip versus
unknown, pending feedback, partial/unavailable state, known subtotal versus nullable
usable total, and separate volume/intensity/reference gates. A source P cannot
be copied into a completion as actual load. Recompute prospective weekly evidence
only under the accepted dispatch/version, preserve prior append-only calculations,
and keep stale evidence preconditions/idempotency for pending approval/corrections.
Storage/selection toggles and hosted readiness gates stay unchanged until allowed.

## C7 — Cross-sport and multi-week regression

Port the review fixture matrix into durable tests around the accepted adapter and
methods; do not bless exploratory assumptions automatically. Include all 61 rows,
seconds/rests, the 38 structural/29 timed distinctions, unsupported methods, planned
and actual time/distance, the six A–F numerical examples, all phase positions,
zero-history three-sport composition, single-sport beginners, long-session scope,
limited/one/no-date availability, repeats, candidate shortage, injury/caps/consent,
high spacing, full and partial taper, measured/estimated/unknown/skipped/pending
completion and mixed incomplete weeks. Verify consecutive prospective weeks plus
historical inputs/output/intermediate fingerprints without reinterpreting history.

Repeat automatic cases that exceeded the 8s review budget under uncontended,
bounded-process instrumentation. Explicit build witnesses prove capacity but not
search completion or a production latency bound. Record accepted operational
precision because finer/repeating load grids change search-state cardinality.
Any later search optimization must preserve exact outputs/tie-breaks/constraints,
keep the existing process worker behavior and have its own reviewed parity tests;
no optimization is implemented here.

## C8 — History, privacy, database and release gates

Use forward-only migrations after accepted inputs; never edit an applied one.
Prepare, review and later execute the minimum immutable manifest/source/segment/
private-load/occurrence evidence changes. Source and technical identities have
unique constraints; exact method/precision records remain private. Idempotent
manifest application either returns the existing identical artifact or rejects a
conflict, never last-write-wins. Existing ownership, RLS, narrow grants, append-only
audits and account-deletion conventions remain intact. Do not weaken them to make
the import pass. Secrets never enter mobile, docs, payloads or logs.

At **OWNER-DEFERRED PRE-BETA** run PostgreSQL/pgTAP fresh/upgrade replay,
function/trigger compilation, source/private-load parity, actual numeric storage,
RLS/grants/owner isolation, migration constraints, concurrency/idempotency, stale
plan/zone approval and correction readers. No tooling is installed and no hosted
operation is run by this review. Static contracts are not these execution gates.
Run relevant backend, Ruff/format, strict mypy, OpenAPI/recursive private-load leak,
strict TypeScript/mobile and real-token/device checks for the implementation.
Complete qualified scientific/release gates for exact new method scope.

Final artifact forF includes accepted catalog/hash/version set, all 61 immutable
rows and their selection scope, test/performance evidence, unresolved exclusions,
activation/rollback instructions and accountable sign-off. Cutover changes future
selection only. Historical approved plans, actual/realized loads and RPE meanings
remain unchanged; pending proposals keep their frozen evidence/preconditions and
cannot silently resnapshot under the new catalog. Rollback reselects the previous
accepted version for future plans and retains readers/corrections for any new
records already created. Never delete or rewrite those records to roll back.

## Current review handoff

Seven new requested reports and marked updates to the three existing combined/
plan reports are the intended changes. All originals and six source-specific
RUN/SWIM reports are preserved. No C1–C8 application code, adapter, migration or
activation is implemented. A–F remain unanswered. Simulation capacity/performance/
time-coverage limitations are explicit, not waived by passing tests.

Reproduction of the focused test command is recorded in
[JOREN_THREE_SPORT_PLANNING_SIMULATION.md](JOREN_THREE_SPORT_PLANNING_SIMULATION.md)
and the scratch verification log; the 439-test result is an actual rerun at the
accepted source SHA. Existing complete v2 implementation results remain attributed
to their original report, not rerun claims for this documentation-only task.

Verification for this final review: **439 focused backend tests passed**, one
existing Starlette/httpx deprecation warning, 46.45 seconds. Tests cover catalog/
source/repository/static migration contracts, actual planning, repeat coverage,
RPE zones, Realized V2/context/completeness, OpenAPI/privacy and exact A 9 parity.
No test/application/API/coefficient/SQL change was made. Previous running/swimming
results remain historical evidence. PostgreSQL/pgTAP is **DEFERRED BY OWNER —
PRE-BETA**; no tooling was installed and no database was contacted or migrated.
No push, merge, deployment or production/staging mutation occurred.
