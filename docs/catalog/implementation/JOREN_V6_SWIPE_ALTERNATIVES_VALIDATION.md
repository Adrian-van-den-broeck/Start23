# V6 swipe and pending-alternative validation

2026-11-05, Europe/Amsterdam. Actual software path `joren-v6-automatic-selection-1`;
local integration only, not hosted storage/mobile release verification.

## Existing workflow, actual V6 choices

The unchanged authenticated routes are exercised with explicit V6 dependency
injection and the real spawned planning worker:

- `POST /weekly-plans/proposals`: returns a deterministic actual pending week.
- `/weekly-plans/swipe-drafts`: retains existing collecting/placement/submitted
  states and typed current candidate/occurrence, accept/pass, undo/reset, placement
  and submit requests.
- `/weekly-plans/{plan}/pending-workouts/{workout}/alternatives`: returns eligible
  same-sport replacements, validated against the complete resulting week.
- `POST .../edit-proposals`: creates a new pending revision through the existing
  proposal contract. Separate `/change-proposals/{proposal}/approve` is still
  required before athlete activation.

No public DTO or UI is invented. Public responses and errors remain recursively
private-load-free. Production route dependencies still instantiate the legacy
service. The V6 test repository is explicit; current hosted writers reject V6
because they lack its frozen snapshot/CAS contract.

## Whole-week validation and retained state

An initial 45-budget Base proposal selects BIKE-023, RUN-025 and SWIM-021 using
official values. Valid independent single-slot alternatives include RUN-026,
BIKE-022/024 and SWIM-022. They are not individually authorized without the other
workouts: after any replacement the whole week is checked again. Alternatives
that fit the original week may disappear after another retained workout changes.

Pending replacements preserve every unaffected occurrence's identity, template,
date, segments, guidance and source. The changed occurrence keeps its logical ID;
the new immutable revision freezes the new template/method basis. Repeated
templates are handled by occurrence ID, so changing one does not remove its twin.
All retained dates are fixed during replacement validation. Draft undo also keeps
dates belonging to other accepted occurrences, and subsequent completion search
honors those dates through the existing scheduler.

Pending edits use the **frozen authorized week budget and safety caps**, not a
newly grown budget from later history. Confirmed input-fingerprint changes reject
as stale. Current injury/capability/low-only/repeat restrictions still apply.
The complete week must remain below the ceiling and at/below 20% HIGH per sport.
Source phases and the correct frozen BUILD position govern occurrence permission.

Card passes exclude previously passed templates until reset, preserve accepted
cards and never recycle an immediate suggestion merely to force success. Exhaustion
returns `exhausted = true` with retained accepted cards intact. The pending
alternatives endpoint returns an empty list without modifying the existing week
when no safe replacement exists. No invisible approval or automatic acceptance
occurs. Pending alternatives use the same allocation/utilization/UUID ordering
on the full replacement week; explicit back/undo choices remain possible.

## Verified cases

| Case | Actual check |
| --- | --- |
| Initial automatic week | Real HTTP response contains all three selected workouts in a pending revision |
| RUN, BIKE, SWIM independently | Each sport obtains a valid replacement; every resulting week revalidates and remains pending |
| Retained workouts | Other two workouts retain full public snapshots and dates across edits |
| Over-budget / wrong phase / injury / repeat bound | HTTP edit rejects with unchanged stored week and revision |
| HIGH maximum | A mixed SWIM replacement under a 200 test budget rejects because its source HIGH active-time share exceeds 20% |
| BUILD-four occurrence | An otherwise valid low-HIGH-time Z5 BIKE alternative is listed in BUILD four, without requiring Z5 |
| Repeated existing source template | A trusted repeated-occurrence fixture retains the second RUN occurrence byte-for-field after the first is replaced; the public unique-template request rule is not weakened |
| Exhaustion / deterministic reset | Repeated passes do not repeat template suggestions; retained accepts survive exhaustion/reset |
| Undo and dates | An accepted workout's manual date survives undo of another card and the following re-accept/submit |
| Retry | Identical card requests return the same result; pending edits use owner-scoped immutable retry results before stale checks |
| Concurrent edit | Two same-revision requests cannot create two revisions; repository CAS allows one write, with exact retry subsequently returning it |
| Stale requests | Changed proposal/draft revision and already superseded operations reject instead of overwriting |
| Account isolation | Foreign reads reject; equal source choices for two authenticated athletes have disjoint occurrence identities |
| Final confirmation | Submit remains pending; only the separate authenticated approval route applies the proposal |
| Legacy worker ownership | Original A9 background-read, cancellation and admission tests remain unchanged and pass in final verification |

The underlying in-memory storage tests perform owner checks, pending-revision CAS,
proposal expiry, exact frozen payload retention and retry lookup. They do not prove
PostgreSQL transactions, grants/RLS, pgTAP, real-token hosted isolation or device UI.
Those remain explicit activation gates. Actual prescribed-time boundary tests,
source precision and the independent selector oracle are in the full backend set.
