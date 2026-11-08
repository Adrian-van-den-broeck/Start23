# Immutable confirmed V6 workout date moves

8 November 2026. Branch `feat/joren-v6-lifecycle-completion`.
Verified implementation: `bb4ac2c917780740551443380ef6fde7a4db4e09`.

Confirmed scheduled V6 workouts now use the existing
`PATCH /api/v1/planned-workouts/{workout_id}` contract and Expo date-change
controller. The operation creates an immutable `athlete_move` revision and makes
it active under the existing revision precondition. It is an explicit athlete
action, as in the historical move architecture. System planning proposals still
require separate athlete approval. There is no new screen or approval system.

## Identity, validation and persistence

The authenticated resolver accepts an exact physical row or a stable logical
occurrence only in the athlete's active confirmed revision. Python binds plan,
revision ID/number, logical occurrence and physical row before validation. It
reuses complete-week V6 validation with every source template and occurrence fixed,
the original frozen authorized target, stored availability/restrictions and current
controls that can tighten those limits. It changes exactly one fixed date.
Unchanged selection, method, HIGH-time limits, source phases and scheduling rules
are therefore checked by their existing deterministic Python implementation.

The service-only writer uses the existing athlete/week advisory lock and the
proposal ? revision ? plan row-lock order. It compares the exact active revision
and occurrence mapping, current onboarding/input custody and applicable injury
restrictions. Out-of-week/unavailable dates, foreign or tampered identities, stale
revisions and any pending successor reject without a write. A move cannot expire
another pending proposal to win a race.

SQL copies the original revision, ordered workout rows, prescribed segments,
source-bearing frozen payload/input, exact private loads, warnings and Realized V2
planning evidence. Only the selected date and its compatibility timestamp change.
All logical IDs, source/template versions, budgets, restrictions and unrelated
dates stay identical. New physical rows belong to the new revision; the previous
physical rows and prescriptions are never rewritten. Historical revision state may
transition to `superseded`, following the existing revision architecture.

The active pointer changes with CAS in the same transaction. A namespaced hash of
authenticated athlete, submitted occurrence locator, expected revision and target
date uses the existing `v6_edit_results` ledger. The immutable response maps against
the receipt's original revision. Exact retries recover it before active-only
resolution, including when the old physical locator is now historical. A different
move using that superseded physical locator rejects. No second retry ledger exists.

## Evidence and supported context

The real synthetic `TR-BIKE-023` occurrence moved from **29 October to 1 November
2026**, revision 1 ? 2. Revision 3 was subsequently selected by two competing run
moves; exactly one committed. Source prescription equality, immutable old snapshots,
exact private load equality, retained logical IDs and changed physical IDs were
asserted. See [identifiers and source hash](lifecycle-completion/functional-example.json).
A new Python process read the same active calendar. A supported measured activity
then attached to the new physical bike row, preserving the original planned method.

Executed: stale/foreign/outside-week rejection; unavailable-date and same-sport HIGH
spacing rejection through actual routes; rollback after the writer updated the
pointer but before receipt commit; exact repeated move and historical receipt;
synchronized competing moves, move versus pending swipe/edit, move versus
confirmation; rejected/superseded locator rejection; completed snapshot retention;
real PostgREST TCP acknowledgement loss and same-request recovery.

**Fail-closed limitation:** a week with any activity-linked, completed, cancelled
or explicitly registered occurrence cannot currently be copied by this move path.
This includes a scheduled sibling of an already recorded occurrence. Evidence
carry-forward across physical revision rows has no approved contract here. The
operation rejects rather than remapping an existing attachment or manufacturing
new registration evidence. Moving evidence-bearing weeks requires that separate
approved identity/chronology contract. No past-date cutoff or new physiological
safety value was invented.

No planned-load formula or realized fallback was changed. Reference swimming time
remains an estimate and never fills measured actual duration. Unsupported V6
Session-RPE fallback combinations remain unavailable. Production V6 stays disabled.
