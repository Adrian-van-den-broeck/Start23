# Multi-session swipe, persistence and evidence preservation

12 November 2026. Existing A3–A9, A5 attachment, revision CAS, immutable edit
receipts and evidence-safe memberships remain the authority. No migration,
approval state machine, new table, replay ledger or public schema is introduced.

## Durable occurrence identity

Repeated templates retain different logical occurrence IDs. Service generation
namespaces these by athlete/week; explicit retained IDs survive extension.
The selector rejects incomplete, duplicate or colliding supplied IDs. Every
persisted occurrence has its own physical planned-workout row, exact source
revision, prescription, method and date. The existing ordinal map distinguishes
duplicate source templates from duplicate physical rows.

The new private frequency controls and `selection_version` live inside the
existing frozen snapshot. `frozen_controls` restores them after restart, with
backward defaults for old snapshots. `effective_controls` retains stored requests
and provenance; current ceilings can tighten them, including ceilings introduced
after an older snapshot. A later maximum or target cannot expand the frozen
generation request during replacement. Public requests cannot supply controls.

## Swipe and dates

The concrete adapter limitation was `_load_swipe_draft_context`: retained dates
were keyed by template. Two accepted instances of the same template could not
retain distinct placements in that map. It now transports retained logical IDs
and dates by occurrence, through the same complete-week scheduler. The scheduler
already allowed multiple workouts on one date and enforced existing anti-stack
rules; no recovery rule needed weakening.

Pending alternatives replace only the chosen occurrence's template. Its logical
ID and date remain; all unrelated logical IDs, dates, source prescriptions and
selection are retained. The full resulting week is revalidated for count,
repetition, official budget, HIGH time, capability and placement. Empty/exhausted
alternatives perform no write. A pending revision remains pending until a separate
explicit athlete approval. Immutable pending revisions allocate new physical rows
under the accepted existing persistence contract; this is not activity cloning.

New HTTP coverage accepts five cards including a duplicate RUN template, gives
the RUN occurrences different dates, undoes/reaccepts a card, retains both RUN
dates, submits a manually placed pending proposal, and checks public privacy.

## Real PostgreSQL trace

`scripts.verify_v6_multi_session` uses normal onboarding completion, approved
hours/budget calculation and real FastAPI routes with a spawned planner and
independent psql transactions. Its explicit fixture overlay supplies 35 historical
minutes per sport and TEST_ONLY 2/2/1 frequency. The normal resolver authorizes
100.1 official units; no private budget override bypasses SQL evidence checks.

Executed on PostgreSQL 17.11 with all 62 migrations:

- A failed A5 attachment rolls back every plan, revision, occurrence and snapshot.
- Lost creation acknowledgement replays one exact five-occurrence attachment.
  Foreign-owner access is denied; pending workouts remain absent from Calendar.
- Two original RUN-025 instances have separate logical and physical IDs.
  Swiping RUN-B preserves RUN-A and unrelated dates/prescriptions. Exact retry
  returns the original edit result; stale/expired locators reject. A5 replay keeps
  the original expired attachment after the pending successor, as before.
- Separate approval activates all five mappings with their source/method data.
- Registering RUN-A and BIKE-A uses each exact physical FK with measured zone
  minutes. Moving unfinished RUN-B and BIKE-B preserves completed rows and all
  activity/measurement/registration/calculation evidence byte-for-byte.
- A late edit-receipt failure rolls back pointer and row changes. Lost move
  acknowledgement recovers the exact original receipt. Old physical locators
  reject rather than redirecting activity or a different move to a replacement.
- Concurrent moves commit once. Duplicate check-in generations converge on one
  attachment. Two concurrent swipes commit one successor and reject the stale
  competitor. Move-versus-swipe and move-versus-confirmation remain serialized
  by existing locks/CAS. Rejection replay preserves terminal attachment state.
- A fresh Python process and an actual PostgreSQL stop/start restore exact
  five-occurrence Calendar mappings. Independent queries find zero orphaned
  activity FKs, missing active memberships, duplicate logical/physical memberships
  or duplicate activity attachments; the evidence hash survives database restart.

An additional loopback PostgREST 16.5 proxy test really closes the TCP socket
after PostgreSQL commits, before headers reach the client. Both A5 creation and
unfinished RUN-B movement after RUN-A completion recover their exact results.
Both upstream transactions return 200; no activity evidence changes. This test
uses local synthetic signed claims, not GoTrue sessions or a hosted gateway.

Completed/cancelled/activity-linked/explicitly registered targets, incompatible
pending proposals, cross-week/unavailable/unsafe moves, foreign accounts and
stale revisions retain their existing fail-closed restrictions. Native plus
carried membership remains a single physical occurrence per active week.

## Mobile boundary

The recorded [public fixture](../../../mobile/src/features/planning/v6-multi-session-http.test-fixture.json)
is checked for private fields before export. Component/controller tests render
five separate Calendar cards, open five exact physical activity targets, preserve
completed RUN-A while moving RUN-B, and restore repeated-template pending versus
active state on restart. Session, transport and SecureStore are simulated. These
are real application components using real SQL/HTTP output, not device tests.
