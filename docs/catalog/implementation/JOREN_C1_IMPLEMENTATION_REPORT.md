# C1 implementation report

Date: 2026-11-04, Europe/Amsterdam. Approval-independent engineering only.

## Baseline and local delivery

Accepted engine/start SHA: `cef4d0adfb09f5f1937528a98c594a6442816f20`
(`feat/joren-realized-tss-v2`).

Implementation branch: `feat/joren-three-sport-catalog-c1`.
Implementation worktree:
`F:\Projecten Business\Start23\Code\.worktrees\joren-three-sport-catalog-c1`.
The requested branch/worktree already existed clean at the exact accepted SHA;
it was verified and reused. The older root checkout was not used for implementation.
Final verified implementation SHA:
`0eb69f54029018e99e8e4d407930a010976f968d`.
The final documentation-only commit records that exact software/artifact commit;
resolve the delivered branch tip with `git rev-parse feat/joren-three-sport-catalog-c1`.

Read authority: root/worktree AGENTS.md, current MVP roadmap including the realized
V2 amendment, final reconciliation, A–F brief, planning simulation and C1–C8
integration sequence. No more specific backend/docs AGENTS.md applies.
The owner's current instruction authorizes technical C1 despite B remaining open;
all operational approval requirements remain pending.

## Implemented scope

- Archived byte-identical copies of the four hash-verified originals. Original
  locations and source hashes are in [source custody](JOREN_C1_SOURCE_MANIFEST.md).
- Copied all 16 existing review reports into `docs/catalog` without modifying
  their bytes or originals. The review worktree and unrelated root changes remain.
- Added a frozen, versioned private draft manifest and deterministic OOXML adapter
  for RUN 20, BIKE 21 and SWIM 20. Complete cells, exact numeric lexemes, ordered
  events, rest semantics and all aggregate checks are retained.
- Added 61 new provisional UUID5 keys/IDs with offline collision checks and explicit
  lineage. No historical identities or revisions are reused or rewritten.
- Retained raw load, rendered source value, precision, independent references and
  proposed method separately. Operational load remains unavailable for all 61.
- Retained the complete selection proposal as draft data; no metadata is published
  to active selection and TR-BIKE-013 cannot acquire beginner eligibility by default.
- Added a local dry-run command with reproducible private JSON, safe summaries,
  non-overwriting output and separate timing instrumentation.

The immutable generated artifact is `joren_c1_manifest_v1.json`; the detailed
[adapter design](JOREN_C1_ADAPTER_DESIGN.md) explains its private boundary and event
union. [Validation evidence](JOREN_C1_VALIDATION_RESULTS.md) records actual checks,
including full backend regression and open integration gates.

## Approval and remaining slices

The manifest status is **DRAFT — SOURCE VALIDATED, METHODOLOGY NOT APPROVED**.
All sources remain unaccepted for operational selection. A–F are open; neither
structure validation nor matching arithmetic is treated as scientific acceptance.

| Slice | Remaining dependency |
| --- | --- |
| C2 | Actual A/E approvals, operational method/version/precision and compatibility; IF² remains inactive and Z3 undefined |
| C3 | Accepted B release/replacement policy and C2 method; production template/rest/guidance/snapshot contracts and immutable persistence |
| C4 | C/D selection, capability, individual scope, repeat and block-guidance acceptance; seven-hour beginner hold |
| C5 | E planned distance-load/time-coverage/rest scope; no CSS scaling or inferred duration; new realization policy requires separate science |
| C6 | Explicit accepted planned-method/V2 compatibility and frozen occurrence lineage; retain A3–A9, measurement hierarchy, weekly completeness and stale-safe approval |
| C7 | Approved cross-sport/multi-week scenarios; separate bounded investigation of the eight automatic-search diagnostic timeouts |
| C8 | Forward-only database implementation, durable identity/revision constraints, deferred pre-beta PostgreSQL/pgTAP/RLS checks, release/scientific sign-off and rollback |

C2 has not started. No actual A/E approval was supplied. No new method or rule,
athlete duration cap, sport multiplier, feature flag or training coefficient was
chosen. No selection algorithm optimization was made. Parser timings do not
resolve the eight planner diagnostic timeouts.

## Explicit operational boundary

No active catalog changes, approved athlete occurrences, plan/zone changes,
migration application, database connection, production/staging changes, push,
merge or deployment. No PostgreSQL, Docker, Podman or psql was installed.
PostgreSQL/pgTAP is **DEFERRED BY OWNER — PRE-BETA**, not passed. No API/mobile or
database contract is changed by C1; corresponding runtime/release gates belong
to later approved integration. This report claims only the verified offline C1
foundation, not completion of the three-sport integration or release readiness.

## Local delivery addendum

The exact final software/source/artifact SHA is
`0eb69f54029018e99e8e4d407930a010976f968d`, based directly on
`cef4d0adfb09f5f1937528a98c594a6442816f20`. The following commit changes only this
report and validation documentation to record the immutable SHA and custody checks.
All source reports/originals and the canonical artifact were also checked against
their staged Git blobs, confirming byte preservation under the recorded attributes.
Local source/software checks pass; the implementation worktree is delivered clean.
No push, merge, deployment or production/staging change occurred.
