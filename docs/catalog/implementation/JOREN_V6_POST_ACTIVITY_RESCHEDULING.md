# V6 rescheduling after sibling activity registration

2026-11-08. Branch `feat/joren-v6-evidence-safe-rescheduling`.
Accepted base: `1dbe10b1a419c689f189faf077f4178eaa4f6310`.
Final implementation identity and executed-check hashes are recorded in
`evidence-rescheduling/verification.json` after verification.
Delivery review: 2026-11-12. SQL replay and the post-activity workflow were rerun
on that date; the full application/network/build evidence was executed 2026-11-08.

## Implemented behavior

The existing `PATCH /api/v1/planned-workouts/{workout_id}` can move an eligible
unfinished V6 workout after another workout in its confirmed week has been
registered. The unchanged Expo date controller sends the exact physical locator,
reviewed revision and requested date. Python validates the complete frozen week
using the existing source catalog, scheduling/recovery restrictions, availability
and authorized budget. The SQL transaction rechecks ownership, membership,
eligibility, frozen inputs, target evidence, pending state and active revision.

Only the moved target receives a new physical prescription row. Every unrelated
workout remains on its original physical row through an immutable revision
membership. Its stable logical identity, dates, prescription, source, private
planned load and activity references remain unchanged. The operation creates a
new confirmed revision and advances the active pointer by CAS. The original
revision, target row and frozen snapshot remain available as history.

The athlete/week advisory lock, established proposal/revision/plan row-lock order,
revision numbering and `v6_edit_results` receipt remain authoritative. The same
operation returns its immutable result after retries or connection loss. No
approval system or replay ledger was added.

## Real functional example

The disposable PostgreSQL/FastAPI trace creates and confirms the week starting
2026-10-26, records measured RUN activity, and moves BIKE to 2026-11-01. RUN keeps
its original physical ID, recorded date and complete evidence. SWIM also keeps its
physical ID and date. A subsequent SWIM move retains the first moved BIKE row;
registering BIKE uses that exact row even though its originating revision has
already been superseded. With RUN and BIKE now completed, another SWIM move
creates revision 4 while preserving both original activity FKs. An independent
Python process reads the same active calendar, plan and activity history.

See the committed synthetic public HTTP fixture and the independent SQL checks
in [JOREN_V6_ACTIVITY_IDENTITY_REGRESSIONS.md](JOREN_V6_ACTIVITY_IDENTITY_REGRESSIONS.md).

## Persistence and historical compatibility

One forward-only candidate,
`20261108210000_inactive_v6_evidence_memberships.sql`, adds the private immutable
membership representation described in the
[ownership contract](JOREN_V6_EVIDENCE_CARRY_FORWARD_CONTRACT.md). Applied migration
files remain unchanged. There is no backfill, evidence migration, reassignment or
historical load recalculation. All new tables force RLS and deny direct client
and service-role writes; existing security-definer/invoker RPC boundaries remain.

Version-aware plan/calendar/rest-day, registration and planned-history readers
enumerate native plus carried members. Realized processing still resolves the
original physical row and origin revision. The V13 history reader additionally
accepts the exact stored V6 revision/load version pair; it previously omitted V6
weeks. This exposes already stored official planned values to private downstream
readers without calculating new values or changing Realized fallback dispatch.

Activation rejects a successor that drops an evidence-bearing physical member.
A pending proposal created before activity was recorded therefore cannot approve
by cloning away that evidence. Reject the incompatible pending proposal, reload,
and move an unfinished workout. Legacy corrective writers lacking a V6 membership
contract remain explicitly blocked on active V6 plans. Historical non-V6 paths
retain their behavior; all original A5 assertions remain in the SQL suite.

## Unsupported operations and release boundaries

Completed/cancelled targets, targets with any attached activity or explicit
registration event, cross-week/unavailable/unsafe dates, foreign identifiers,
stale revisions and moves with an incompatible pending proposal remain rejected.
No recorded occurrence is moved, cloned, detached or reassigned. A superseded
target physical locator cannot register activity against its replacement.

The automatic selector still adds at most one new workout per goal sport. This
task does not expand weekly workout count or change source phases, ranking,
official `joren-v6-planned-if2-1`, authorized budgets, HIGH policy, swim references,
or measured-data priority. Unsupported Planned/Realized fallback combinations
remain closed. Reference swimming time does not become observed activity time.

V6 remains inactive for production. No push, merge, deployment, hosted connection,
hosted migration or catalog activation is authorized or performed. Scientific,
GoTrue/gateway, actual-device and release gates remain in the
[Dutch register](JOREN_V6_REMAINING_RELEASE_GATES_NL.md).

Implementation commit: `057d88bb41aa8f73c1e1e66b0e7d0059754ca527`.
Evidence reviewed 2026-11-12; the documentation-only successor records the
verification manifest and source hashes. V6 remains inactive.
