# Joren V6 catalog integration report

2026-11-05, Europe/Amsterdam. Private developer validation; no activation.

## Delivery status and isolation

**WOMBO V6 CATALOG VALIDATION PARTIAL — SOURCE OR PLANNING GAPS REMAIN**

Exact accepted start: `f5831d3cbde04f60053402eb3083a1f1e6ade7a8` on `feat/joren-three-sport-catalog-c2`.
Implementation branch: `feat/joren-v6-catalog`; isolated worktree:
`F:/Projecten Business/Start23/Code/.worktrees/joren-v6-catalog`.
The accepted C2.1 branch was clean at that exact SHA. Main checkout unrelated
changes were retained. The A5/A6 release worktree was clean at
`cd3e2dd438031cfb565858d0a5929e9963f7b31f`; its branch, backend selection and
deployment preparation were not modified. Final delivery commits are recorded
in the local-delivery addendum below after verification.

Applicable root/worktree AGENTS.md and current MVP roadmap were read. No nearer
backend/docs AGENTS.md exists. C1/C2/C2.1 reports, Joren decision records, final
three-sport reconciliation/planning report and C1–C8 sequence were reviewed.
The owner's V6 instruction supersedes the earlier stop-after-C2.1 boundary only
for isolated source intake and validation; it authorizes no active C3–C8 rollout.

`git merge-base --is-ancestor` returned zero for each required ancestry check:

| Component | Exact ancestor |
| --- | --- |
| Realized TSS V2 | cef4d0adfb09f5f1937528a98c594a6442816f20 |
| C1 implementation | 0eb69f54029018e99e8e4d407930a010976f968d |
| C1 accepted delivery | e436285e9f169908a45ff8f34aeed0e003ba6bc2 |
| C2 implementation | e3d8ae1806e4f11a17b6f5cdeea47ee54dbdc409 |
| C2 accepted delivery | ed052211ce413dd045b2e91af0d6a8e59ee534ff |
| C2.1 implementation | 5b6c960cf817dfebc31cffbd6e7f6fc58f2309be |
| C2.1 accepted delivery | f5831d3cbde04f60053402eb3083a1f1e6ade7a8 |
| A3 | b65ea78be1db886586d793f721bb2910ddbc6a41 |
| A4 | 4bb0cdea8f46242018ad8e5d22fa79a706cbf207 |
| A5 | 044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf |
| A6 | 24b27ebd34ccfe662ca57994a736f4f853af8d0b |
| A7 | 75f172d4161f71a763247b04c027fd165901afbd |
| A8 | d0e726dfd291ffde12a459ec430b11fdc5cddc7a |
| A9 | e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6 |

## Supplied source custody

| Sport | Exact supplied file | Bytes | Actual SHA-256 |
| --- | --- | --- | --- |
| RUN | Looptrainingen_Definitief_v6.xlsx | 7731 | `f9efc53405ae80ea06b7c4f45c288d77e0572aabe0309ef17d29336562a5c46c` |
| BIKE | Fietstrainingen_Definitief_v6.xlsx | 7813 | `e291a6e40b193d279e1371032242972f4f940454b544832e04087aec6fec4b95` |
| SWIM | Zwemtrainingen_Definitief_v6.xlsx | 7551 | `acd05e0d02664a09320fc70a4519d518fb0103a34801823d04de1ac929c96348` |

| Sport | Previous rows | V6 rows | Added | Single / mixed |
| --- | --- | --- | --- | --- |
| RUN | 20 | 28 | 8 | 24 / 4 |
| BIKE | 21 | 27 | 6 | 19 / 8 |
| SWIM | 20 | 22 | 2 | 11 / 11 |
| Total | 61 | 77 | 16 | 54 / 23 |

The originals in root `docs/trainings` and archive copies have matching
hashes. Every old source, catalog artifact and historical report remains preserved.
Only new pinned V6 sources/evidence and narrow LF attributes are added under docs.

## Implemented offline foundation

- `workouts/joren_v6.py` extends C1 with pinned schemas, frozen new source records,
  deterministic versioned identities, complete row/cell lineage, immediate-source
  differences, IF² precision experiments and approved-versus-inferred evidence.
- `jobs/joren_v6_dry_run.py` provides hash-verified private immutable output.
  Identical retries are read-only; conflicting output is rejected. Default stdout
  contains only status/count/digest and no private load values.
- `benchmarks/joren_v6.py` projects all 77 rows only in explicit offline hypothetical
  simulations, calls the real unchanged planner, records safety/coverage outcomes
  and separates bounded automatic timeouts from actual returned results.
- The new tests cover all rows, revision diffs/lineage, source hashes, already
  corrected swims, source RPE, exact arithmetic/precision, collisions, immutability,
  decimal-context isolation, 45-budget beginner witnesses, mixed active-time
  accounting, missing swim time, injury/capability/availability and weekly evidence.

Existing runtime catalog, source projection, selection functions, zone coefficients,
Realized V2 methods, API/mobile models, settings and SQL are unchanged. No active
application module imports V6; only the explicit job, benchmark and tests do.
Operational P remains null and accessors reject unapproved source methods.
No SQL migration is generated or applied. No live database/client/network is used.

## Findings and remaining gates

All 77 structures pass: 54 single/23 mixed; all 16 lighter additions are real
source rows. Existing value changes are 20 titles, one focus and six approved
ordered blocks. All 55 other existing prescriptions and all 61 raw P values match
their immediate parent. Six swim rows are already corrected, with original rest
and zero-load semantics. All 77 IF² candidate displays match; exact reference
seconds differ for precisely SWIM-011–014. Z3 IF, swim reference precision and
authoritative operational P remain unapproved.

The 43.1 one-per-sport beginner witness fits actual target 45 and is pending only.
The 29.3 minimum is below budget but rejected by the actual target-fit predicate.
There are 33 low-zone one-each combinations under 45; none is made a default.
50/30/20 is now an approved triathlon planned-P **target**, and the independent
20% high-active-time maximum has no required high minimum. Swimming time remains
UNVERIFIED, even for all-Z2. Current selector integration, athlete suitability,
long-session limits and automatic search performance remain gaps.

40 final simulations return 14 hypothetical pending drafts and eight fail-closed
outcomes, with 18 bounded diagnostic timeouts across four explicitly different
catalog modes. All eight old timeout slots reproduce; six V6 automatic cases
time out. Smaller catalog arithmetic does not establish automatic readiness.
The reports distinguish exact source-grid fits, target-nearest results, pending
state, safe warnings, policy rejection, unverified time and diagnostic timeouts.

The accepted v2 fixtures supersede preliminary v1 diagnostics, which lacked
explicit returning-athlete flags and are retained for traceability. The final
independent v3 repeat, after all test/typecheck processes finished, reproduces
all 40 v2 outcome payloads exactly. No v1 performance result is promoted to a
final source/planning conclusion. v3 timing metadata correctly distinguishes
serial workers from uncontrolled host load; the earlier metadata label overstated
host control and is not evidence of an idle-host measurement.

## Deliverable reports

1. [Complete source diff](JOREN_V6_SOURCE_DIFF.md)
2. [All 77 workout validations](JOREN_V6_77_WORKOUT_VALIDATION.md)
3. [IF² precision reconciliation](JOREN_V6_IF2_RECONCILIATION.md)
4. [Actual-planner simulations](JOREN_V6_BEGINNER_PLANNING_SIMULATION.md)
5. This integration report
6. [Remaining decisions in Dutch](JOREN_V6_REMAINING_DECISIONS_NL.md)

## Verification

Existing project virtualenv, this worktree's backend cwd; no dependency installs.

| Check | Result |
| --- | --- |
| All V6 focused tests | 96 passed; includes all 77 rows |
| Full backend `python -B -m pytest -q -p no:cacheprovider` | **1,378 passed**, 148.97s; one existing Starlette/httpx deprecation warning |
| Ruff `python -m ruff check app tests benchmarks/joren_c2.py benchmarks/joren_v6.py` | PASS |
| Formatting with same paths | PASS; 170 files |
| Strict mypy with same paths | PASS; 170 source files, strict=true |
| C1 dry run | 61 rows, no errors; digest 3c149c9096dd568156eab0246f7f6c679fc6ac98416b073a798c7bde3b68bc85 unchanged |
| C2.1 correction dry run | 20 valid derived rows; digest a850a745e2170a3024f00ca201116880f8ba66de46d73e6b40ef8dbd380a948a unchanged |
| V6 dry-run immutable retry | 77 rows; identical canonical manifest bytes and digest |
| Final independent planner repeat | All 40 outcome payloads equal v2; same 18 timeouts; separate v3 wall timings |
| Source custody / prior artifacts | All 36 pre-existing catalog source/report/artifact files byte-identical to accepted C2.1 worktree; V6 originals equal pinned copies |
| Git diff hygiene and staged-byte checks | Final results in delivery addendum |
| PostgreSQL/pgTAP/RLS execution | DEFERRED BY OWNER — PRE-BETA; not run; no database access |
| Mobile/TypeScript | Not applicable to this offline-only change; no mobile/public contract changes |

The full backend suite includes existing planner, Realized TSS V2, physiology,
OpenAPI/public-contract and recursive private-load leak regressions. No historical
tests were modified or weakened. Local passing tests cannot close scientific,
database, time-coverage, automatic-search, athlete/device or release gates.

## Reproduction and immutable evidence

From this worktree's backend:

```text
python -B -m app.jobs.joren_v6_dry_run --dry-run --private-output NEW_PRIVATE_MANIFEST
python -B -m benchmarks.joren_v6 --private-output NEW_PRIVATE_PROBES --timings NEW_PRIVATE_TIMINGS
```

The second command reproduces final v2 fixtures (archived final repeat v3); timings are deliberately separate
and timeout outcomes may vary with host load. Private artifacts are never API payloads.
The exact manifest retains all row-level UUIDs/versions, originals, revisions,
method/precision candidates, null operational P and source/approval status.

| Private artifact | SHA-256 |
| --- | --- |
| joren_v6_manifest_v1.json | a99df3ffde3c75015606a84e0139506d2a44dd5f19030fcf55139958c5f12aba |
| joren_v6_planner_probes_v3.json | b6310b56476f1b20475292bef6a431ebf995a4e2019eb698667916752b5a9839 |
| joren_v6_planner_timings_v3.json | 3f9d9f40e13d525911bf53c0e3c3f5d932820a65370097636c4218213417ef95 |

## Local delivery and explicit boundary

Final verified implementation SHA: recorded after local commit in the delivery
addendum. A following documentation-only commit records that immutable SHA;
its branch-tip SHA is supplied in the final delivery response because a commit
cannot contain its own hash. Resolve it with `git rev-parse feat/joren-v6-catalog`.

**Active application/catalog behavior is unchanged.** No activation, push, merge,
deployment, migration, publish, production/staging access or historical
recalculation occurred. A5/A6 release branch/worktree and its backend selection
and deployment preparation were not modified.

WOMBO V6 CATALOG VALIDATION PARTIAL — SOURCE OR PLANNING GAPS REMAIN

Verification and immutable delivery commits: [integration report](JOREN_V6_CATALOG_INTEGRATION_REPORT.md).

## Local delivery addendum

Exact verified software/source/evidence commit:
`99adc4ef89baebfbaf28a54a193177c35a2655b8`, direct child of accepted start
`f5831d3cbde04f60053402eb3083a1f1e6ade7a8`.
The following documentation-only commit records that immutable implementation
SHA; its own final branch-tip SHA is supplied in the delivery response.

Final staged diff hygiene passed. All 16 newly staged reports/source archives/
private JSON artifacts were compared to their index blobs byte-for-byte and
matched. All 36 pre-existing catalog source/report/artifact files equal their
accepted C2.1 worktree copies byte-for-byte; their historical Git blobs remain
unchanged. Fresh Windows checkout line-ending differences were restored from
those copies, with narrow LF attributes for the three accepted LF reports.
The original correction report retains its historical mixed line endings.
All three V6 original/custody SHA-256 values were reverified unchanged.

The six reports have valid local links. Full backend: 1,378 passed; focused V6:
96 passed; Ruff/format/strict mypy passed. The final independent 40-case planner
repeat equals the preceding corrected fixture run exactly, including the eight
historical and six V6 timeout slots. No timeout or safety constraint changed.

The A5/A6 release worktree remains clean at
`cd3e2dd438031cfb565858d0a5929e9963f7b31f`; backend selection and deployment
preparation are untouched. Active application/catalog behavior remains unchanged.
PostgreSQL/pgTAP remains owner-deferred. No push, merge, deployment, migration,
publish, catalog activation or historical recalculation occurred.

WOMBO V6 CATALOG VALIDATION PARTIAL — SOURCE OR PLANNING GAPS REMAIN
