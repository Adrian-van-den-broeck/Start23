# Durable optional athlete frequency preferences

13 November 2026. Accepted source: [policy approval](JOREN_V6_REAL_FREQUENCY_APPROVAL.md).
V6 remains inactive and disconnected from normal application startup.

The existing profile and onboarding review render the same small card:
**Gewenste sessies per week (optioneel)**. It displays current goal sports,
starts without prefilled counts and does not add an onboarding prerequisite.
All existing history, heart-rate-monitor, confirmed-timezone, race and zone
requirements remain unchanged. Empty input is `null`; zero is an explicit
request for no new sessions. The existing technical envelope is 0–24 per sport,
at most 24 requested together; this is not a physiological maximum.

Authenticated operations are `GET` and `PUT /api/v1/me/frequency-preferences`.
PUT accepts only an expected revision, UUID operation ID and the three nullable
preferences. It accepts no owner, maximum or review evidence. The verified
token resolves to the existing opaque athlete identity. SQL serializes writes
and compares the expected revision. Reusing an operation ID with different
content rejects; repeating a committed save returns its original metadata.

`private.frequency_preferences` is append-only and separate from training history
and all load storage. Revisions preserve values, the original confirmation actor
and timestamp, recording time, operation ID, invalidation reference and sports
requiring reconfirmation. A system invalidation retains earlier confirmation
provenance; it never invents confirmation when no preference existed. A fresh
explicit save reconfirms the preference. Clearing values revokes them through a
new revision. Direct table access and mutation are denied; forced RLS remains enabled.

The card shows saved revision/values, loading and read retry, validation, explicit
save status and conflicts. An ambiguous write retains its exact operation ID and
payload while editing is locked, supporting safe retry or authoritative read-back.
Account keys discard late old-account responses; token rotation retains input.
No preference or authorization data is added to SecureStore.

Preferences affect future newly generated proposals, including an explicit new
request in the current week. They do not edit an active plan. Old pending context
becomes stale instead of silently reshuffling. Each resulting plan remains pending
until the existing separate athlete approval.

The server freezes original P separately from the effective `SessionFrequency`.
With valid M, its soft target is `min(P,M)`; without P, existing default request
semantics remain. Without extra authority, automatic generation retains the safe
one-new-session-per-goal-sport envelope. Retained occurrences are not retroactively
capped at one. P=0 does not delete an existing confirmed occurrence.

Public proposal presentation contains only requested P and actual proposed counts,
with a qualitative partial explanation. It exposes no maximum, reviewer, medical
evidence or private load. Incomplete search explicitly says no new proposal was
stored and is distinct from an exhaustively infeasible selection. Runtime error
code validation now admits version digits, so `v6_search_incomplete` reaches its
safe Dutch explanation instead of being discarded.

See [verification](JOREN_V6_FREQUENCY_VERIFICATION.md) for executed component,
transport, strict TypeScript, SQL and privacy checks.
