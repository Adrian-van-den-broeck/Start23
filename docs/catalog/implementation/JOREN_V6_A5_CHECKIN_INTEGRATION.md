# V6 integration with authoritative A5 check-ins

8 November 2026, Europe/Amsterdam. Branch `feat/joren-v6-lifecycle-completion`.
Accepted base `31a8ed0cfad831780b405030121817df50e8fa2c`.
Verified implementation: `bb4ac2c917780740551443380ef6fde7a4db4e09`.

V6 generation now uses the existing A5 creation, attachment, recovery and
athlete-decision lifecycle. The default application remains historical; V6 is
available only through the existing isolated test dependency seam. All 77 source
revisions remain INACTIVE. No hosted connection, migration or activation occurred.

## Transaction boundary

Forward-only migration `20261108180000_inactive_v6_lifecycle_completion.sql`
adds version dispatch inside `create_weekly_plan_proposal_v3`, after its existing
owner/check-in lock and authoritative attachment/orphan recovery checks. Legacy
requests execute the original v3 body. V6 requests call the private snapshot
writer and the same `attach_checkin_plan_proposal` before the transaction commits.
The public V6 entry point routes check-in writes through A5; service callers have
no execute grant on the extracted private writer. There is no new check-in table,
approval state machine or replay ledger.

The service-only context reader additionally returns the exact confirmed context
revision and fingerprint. Python freezes these with the complete context payload.
The writer locks and compares that owned confirmed context, check-in week/timezone,
initial request/fingerprint/current input, frozen athlete/week scope and registration
evidence. Existing onboarding eligibility triggers remain enabled. Immutable source,
method and budget checks are retained. Any attachment failure aborts the plan,
revision, workouts, loads, snapshots and proposal together.

The existing owner-scoped A5 replay reader dispatches V6 plans to the logical/
physical mobile projection. It still reads the original attached proposal and its
current terminal state. Repeated generation never regenerates a rejected, expired
or applied attachment. Pending edits may expire that original proposal; replay
returns the expired original rather than silently substituting a successor.
Separate approval of the current pending successor remains necessary.

`install_local_v6` now injects V6 planning into the existing check-in controller.
Its small presentation subclass adds the exact immutable source prescription to
A5 responses; orchestration and state transitions remain in `CheckInService`.
No default startup dependency or mobile generation switch was added.

## Reopened context confirmation

A real PostgreSQL guard test exposed an inherited inconsistency with the approved
A3 save-new-revision contract: confirming a new draft while an older context was
confirmed violated `one_confirmed_context_per_checkin`. The same forward migration
corrects the existing confirmation RPC after its owner/CAS/fingerprint/restriction
checks: it supersedes the previous confirmed context before confirming the new one,
within the existing check-in row lock and transaction. Its original payload,
revision and confirmation timestamp remain intact. The constraint now permits that
timestamp on a superseded context. No migration transforms an existing row.

The V6 writer also requires the confirmed context revision to equal the check-in's
current revision; a newer unconfirmed draft cannot authorize planning from its
older confirmed context. Actual SQL tests verify both stale-draft rejection and
successful explicit reconfirmation with exact historical provenance preservation.
This fixes an existing intended transition; it adds no new state or approval path.
Historical plan creation, attachments and terminal replay retain all original A5
assertions. See [executed guard results](lifecycle-completion/context-guards.json).

## Executed examples and compatibility

Eligible synthetic athletes completed onboarding using the normal
`complete_current_onboarding` RPC with all required history, goals, zones, monitor
and timezone inputs. Actual FastAPI check-in/context/confirmation routes then
produced automatically selected V6 pending weeks in real PostgreSQL transactions.
See [the exact synthetic example](lifecycle-completion/functional-example.json).

Executed: attachment-trigger failure and complete rollback; committed creation
with withheld acknowledgement and exact replay; two requests synchronized before
persistence converging on one attachment; foreign-owner denial; explicit approval
and active calendar read; rejection replay; original attachment remaining expired
after a pending edit; normal source prescription recovery.

A separate loopback PostgREST 16.5 test closed the real client TCP socket after
creation committed, before response headers. The same check-in recovered its
original proposal. The corresponding move also passed this test:
[network results](lifecycle-completion/socket-loss.json).

Historical A5 SQL passed all 29 original assertions using only the previously
reviewed onboarding/32-character-input-fingerprint overlay. The original SQL file,
fixture proposal and protected A5/A6 branch were not changed. The overlay remains
an isolated execution choice, not permanent adoption. The deliberately uncorrected
original still has its documented synthetic prerequisite failure. No production
eligibility, constraint or original A5 assertion was weakened.

All A3?A9 and Realized V2 backend regressions run in the full suite. The complete
local SQL suite and inherited V6 restart/concurrency/activity probes also pass.
See [transaction evidence](JOREN_V6_LIFECYCLE_TRANSACTION_TESTS.md) for commands,
counts, boundaries and hashes. GoTrue, the complete Supabase gateway and real
device testing remain independent release gates.
