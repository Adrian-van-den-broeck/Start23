# V6 evidence-safe revision membership contract

2026-11-08. Accepted base: `1dbe10b1a419c689f189faf077f4178eaa4f6310`.
Branch: `feat/joren-v6-evidence-safe-rescheduling`.

## Authority and scope before schema changes

The owner's current instruction authorizes the conservative product behavior:
move an eligible unfinished occurrence while retaining completed/registered
siblings and their exact physical evidence references. It does not authorize
measurement cloning, activity reassignment, physiology changes or production use.
This contract records that product authorization; scientific and release review
remain separate. The representation below is implemented and verified locally;
hosted adoption of the migration candidate still requires release authorization.

## Existing authoritative ownership

`weekly_plans` owns the athlete/week and active revision CAS pointer.
`plan_revisions` is an immutable prescribed snapshot apart from its allowed state
transitions. `planned_workouts.id` is the exact physical activity/registration FK;
its `revision_id` identifies its originating immutable revision.
`v6_occurrence_snapshots` binds this row to a stable logical occurrence, source
revision and order. Its physical primary key cannot represent sharing across later
revisions. Activities, observed loads, calculation revisions and registration events
retain that exact physical FK. Realized V2's original approved-workout basis records
its original physical/source/revision identity, including superseded revisions.

Today plan/calendar/planned-load/expected-registration readers enumerate physical
rows by originating revision. Simply cloning a completed row would lose its valid
activity relationship; changing the activity FK or origin revision would rewrite
history. Neither representation satisfies the user's contract.

## Adopted local representation and migration candidate

Add a private immutable membership table for a later V6 move revision referencing
an unchanged physical row and the exact parent revision membership. Keep the
original occurrence map, physical rows and all evidence tables unchanged. Enforce
athlete, plan/week, stable logical ID, ordering and confirmed-parent ownership
through owner-composite foreign keys and a guarded append-only writer.

A new date-move revision copies only its eligible target to a new physical row.
Every unrelated sibling remains the SAME physical row, source, prescription and
date; membership references do not duplicate completion or measured data. A later
move refers directly to the same original physical row rather than chaining aliases
or manufacturing new activity evidence. The active read projection combines native
rows and explicit memberships exactly once. The physical origin revision stays
independent from its active membership revision.

| Identity/reference | Meaning after a later move |
| --- | --- |
| Weekly plan and active revision | The exact athlete/week and CAS-selected current schedule |
| Logical occurrence ID | Unchanged workout identity across revisions |
| Physical workout ID | Original prescription/evidence record; changes only for the moved eligible target |
| Physical row `revision_id` | Immutable originating revision, including when superseded |
| Revision membership | Current or historical week includes that original physical record |
| Activity/measurement/registration FK | Original physical workout, never a membership alias or replacement clone |
| Frozen source and load method | Original source/method versions; no reinterpretation |

The internal read projection supplies a virtual membership revision for week
enumeration. It does not change `planned_workouts.revision_id` in storage. Activity
processing and registration CAS use the original physical origin. Status changes
from normal authorized registration remain canonical on the original row; its
historical prescription, source, date and evidence are not rewritten. Historical
week views may therefore show later canonical completion, as before this task.

The membership table has dual owner keys, five foreign keys, forced RLS, immutable
update/delete guards and no direct authenticated/service-role grants. Insert
guards bind exact parent/child plan, athlete, logical ID, ordinal and physical row.
Native and carried maps cannot overlap regardless of insert order. Account-delete
cascades retain the established immutable-evidence cascade behavior.

Activity/registration eligibility must resolve active membership under the existing
plan lock. Processing and realized-calculation provenance continue to resolve the
original physical row. Expected weekly occurrence IDs are the effective physical
members, so an original activity counts once. Pending or legacy operations that
would drop recorded physical members must fail closed. No new approval system or
retry ledger is introduced.

## Rejected targets and concurrent operations

A target with any activity, completed/cancelled status or explicit registration
history remains immovable. Only same-week available dates passing the existing
complete-week deterministic validator are eligible. The existing athlete/week
advisory lock, proposal/revision/plan lock order, active CAS and immutable retry
receipt apply. Activity and registration writes serialize through that plan lock:
a target registration winning first blocks the move; a move winning first makes
registration against the superseded target fail. Sibling registration may complete
without reassignment because its physical row remains an active member.

No historical row or evidence is backfilled or recalculated. No physiological
threshold, method compatibility or selector scope changes are authorized. The
current automatic selector still adds at most one new workout per goal sport.

## Verification and remaining decisions

The real SQL/HTTP traces preserve one and then two completed siblings across
successive moves, including registration on a previously carried scheduled row.
They also preserve an activity-linked sibling awaiting feedback, inject a late
transaction failure, race transitions, reject invalid writes and reload from a
new process. Original evidence tables are independently compared; evidence is
never copied or transferred. See
[JOREN_V6_ACTIVITY_IDENTITY_REGRESSIONS.md](JOREN_V6_ACTIVITY_IDENTITY_REGRESSIONS.md)
and the exact checks, hashes and implementation SHA in
`evidence-rescheduling/verification.json`.

No additional physiological decision is needed for this conservative identity
representation. Moving a recorded target, approving a replacement that discards
recorded members, cross-week rescheduling and legacy V6 corrective generation
remain unsupported. Scientific acceptance, official fallback compatibility,
hosted migration/release authorization and catalog activation remain independent
decisions; none is claimed by these tests.

Implementation commit: `057d88bb41aa8f73c1e1e66b0e7d0059754ca527`.
Evidence reviewed 2026-11-12; the documentation-only successor records the
verification manifest and source hashes. V6 remains inactive.
