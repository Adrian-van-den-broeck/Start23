# Private weekly frequency authorization and revocation

13 November 2026. Policy `joren-v6-real-athlete-frequency-policy-1`.
One new forward-only candidate migration is added; the 62 inherited migrations,
templates, formulas and historical calculations remain unchanged.

`private.frequency_decisions` stores immutable revisions for exact opaque athlete,
sport and local Monday week. Each carries the confirmed IANA timezone, explicit
maximum, policy, reviewer and database-login operator references, original
designation reference, dated evidence period and source/completeness/context/
capability/phase/rationale/review identifiers, reviewed/decided/recorded times,
week expiry, status, predecessor and lifecycle reference. Only the latest revision
for that exact key can be current. Replacement explicitly identifies its
predecessor and expected revision; earlier authorized rows remain historical,
not another current authorization. Suspended/revoked decisions cannot reactivate.

The internal boundary is
`private.register_frequency_decision(integer,jsonb)`. It requires both membership
in the NOLOGIN `v6_frequency_registrar` role and an enabled, separately designated
`session_user` in `private.frequency_reviewers`. The request's reviewer must match
that designation. Application/anonymous/authenticated roles have no execute grant
or decision-table mutation grant. User-editable JWT metadata cannot designate an
operator. No HTTP administration portal or automatic enrollment is introduced.

**No real reviewer/operator is configured. Real issuance therefore remains
unavailable.** An administrator must first receive the actual designation and
identify the genuine database login, reviewer and permission evidence. Each
numerical athlete maximum and its evidence require a separate real review.
No placeholders, professional credentials, signed approvals or individual maxima
are manufactured. The policy approval is not any of these operational facts.
`TEST_ONLY` is rejected by the real registration boundary and resolver.

The request document contains `id`, `athlete_id`, `sport`, `week_start`, `timezone`,
`maximum`, `policy_version`, `reviewer_reference`, `evidence`, `reviewed_at`,
`decided_at`, `status`, `predecessor_id` and `lifecycle_reference`. Evidence requires
explicit `period_from`/`period_to` and the reference fields listed above. There
is no default observation duration, medical threshold, inferred readiness,
progression step or maximum derived from hours, load, availability or activity count.
Expiry is the following Monday in the confirmed timezone, never automatic renewal.

The pure Python resolver distinguishes persisted absence from a failed read.
Malformed/unavailable reads fail closed. Valid M caps the complete planner week,
including retained/completed members once. P remains separate and is only a soft
target; M=0 permits no new sessions. Retained members above a tightened M cause
a conflict, never deletion. Unmatched or ambiguously linked activities block
expansion; no synthetic occurrence or undocumented session definition is created.
Resolving such a context requires review and a supported complete-week mapping.

Saved relevant check-in injury/illness reports and changed active restrictions
invalidate authority. Explicit `POST /api/v1/me/frequency-preferences/interruption`
also supports injury for a named sport, illness for all sports, and an explicitly
reported training interruption. Missing registrations alone do not diagnose one.
Goal, active capability, timezone or assessment-source changes invalidate affected
review grounds. Disabling/changing reviewer designation also suspends its decisions.
The preference remains visible and is marked for reconfirmation. Recovery or time
passing never restores the old maximum. No illness-duration or medical-clearance
rule is invented; the physiological/recovery resolver is unchanged.

The frozen V6 controls retain exact preference and authorization revisions,
original P, assessment-source fingerprint and current lifecycle facts. They
participate in generation/context fingerprints; the established onboarding input
fingerprint remains its original contract. Pending replacement cannot expand the
frozen request. Restoring an old snapshot cannot revive a revoked permission.

Database triggers revalidate private context at snapshot insertion, draft commit
and pending-to-active transition. Draft metadata is in a private companion table,
not in the public draft or a new replay ledger. Frequency locking occurs after
existing plan/check-in locks. Invalidation/registration never lock those source
rows in reverse order. A volatile current-context read after waiting observes
committed invalidation, including expiration while waiting. Existing A5 attachment,
revision CAS, rollback, memberships and separate approval remain the authorities.

Historical creation/edit/move/approval receipts retain their existing identity.
A5 replays before generation; edits/moves read the existing immutable receipt
before current-state checks. Submitted swipe recovery reads the original proposal's
explicit target revision through its existing draft locator. None of these reads
grants a new operation after invalidation. New writes and later approval revalidate.

The restricted `create_v6_frequency_swipe_proposal` wrapper binds proposal creation
and the existing submitted-draft locator atomically. A late draft-write failure
rolls back the proposal and snapshot. A committed retry reads the same locator
before current-context checks; it cannot use the old receipt for a new operation.
It introduces neither a second approval state machine nor another replay ledger.

The ungranted NOLOGIN `v6_frequency_test_executor` exists only for explicit legacy
synthetic harness permissions. It is not a real reviewer or an issuance route.
The isolated historical five-session test grants it temporarily to local test
roles; the grants are revoked before real-path verification/closure. Normal startup
never installs the loopback/test-only V6 dependency seam.

The remaining operational positive-issuance gate and evidence boundaries are
explicit in [verification](JOREN_V6_FREQUENCY_VERIFICATION.md).
