# Phase 0 decision lock

## Status

The architecture and state-semantics portion of Phase 0 is approved.
`phase-3-ruleset-1` approves BR-002, BR-003, BR-004, BR-006, BR-007, BR-008,
and BR-010 calculations. The BR-009 follow-up evidence supplied on 2026-07-26
adds discipline-zone policy in `phase-3-ruleset-2`. Ruleset 1 remains
immutable for historical decisions. The twelve decisions accepted on
2026-08-11 are locked in `phase-3-ruleset-3`; rulesets 1 and 2 remain immutable
for historical records. Ruleset 3 is local-development approved but requires a
named qualified Physiology Rules Review Board approval before production.

## Locked decisions

### Rule precedence

The deterministic engine applies constraints in this order:

1. authentication, ownership, data validity, and confirmed injury exclusions;
2. race taper;
3. recovery week;
4. physiological debt;
5. progressive-load target;
6. time-based intensity distribution and anti-stack placement;
7. athlete availability and scheduling preferences.

Higher rules constrain the input available to lower rules. A lower rule never
restores load or a workout removed by a higher rule. If two rules cannot be
satisfied, the engine returns a pending proposal with a qualitative conflict
instead of silently selecting a result.

This order defines orchestration only. It does not approve any currently
ambiguous formula.

### Automatic and manual changes

- Every system-generated plan, zone, or corrective change is a pending
  proposal.
- Only an authenticated owner may approve a proposal.
- Approval applies exactly one visible proposal against an expected base
  revision.
- A direct athlete calendar move may apply immediately and return qualitative
  soft-boundary warnings.
- A direct edit is rejected when it violates authentication, ownership, schema
  validity, revision concurrency, or a confirmed injury exclusion. Clearing an
  injury is a separate explicit action.
- Chat text cannot approve a proposal in the phase-one MVP.

### Soft boundaries

Performance guidance such as intensity ratio, progressive load, and
anti-stacking is soft for an explicit athlete calendar edit. Generated
schedules must satisfy these rules or return an unsatisfied constraint.
Security, state integrity, canonical-unit validation, and confirmed injury
exclusions are hard validations.

### State machines

Weekly plans:

```text
draft -> pending_approval -> active -> superseded
                         \-> rejected
                         \-> expired
```

Change proposals:

```text
pending -> approved -> applied
        \-> rejected
        \-> expired
```

`approved -> applied` occurs in one database transaction. `approved` is an
auditable transition, not a state in which another request may mutate the
target.

Zone versions:

```text
pending -> active -> superseded
        \-> rejected
        \-> expired
```

An athlete's explicitly confirmed initial manual zone submission may create
the first active version. Every system-derived replacement uses the proposal
state machine.

Activities:

```text
received -> validated -> matched -> awaiting_rpe -> complete
                      \-> unmatched -> awaiting_rpe -> complete
         \-> invalid
```

### Zone-test approval

Approval to schedule or perform a validation test does not authorize a later
zone update. A calculated zone revision is a separate proposal and requires a
separate approval.

### Phase-one activity input

Phase 7 starts with an authenticated canonical activity-summary request.
Direct FIT/TCX upload and wearable-provider imports remain deferred until the
canonical activity workflow is verified. Duplicate submissions use an
idempotency key.

### Expo version

The decision is to upgrade from Expo SDK 54 to SDK 57 before further mobile
implementation. The current `mobile/package.json` still declares SDK 54, so
the upgrade is pending; the existing dashboard is a non-connected design
preview only. Session implementation will keep access tokens in memory and
store refresh/session material using the SDK-compatible `expo-secure-store`
integration when authentication is added to the mobile app.

### Public API and TSS

- The deployed FastAPI base path is `/api/v1`.
- `/health` and `/ready` are unversioned platform probes and are also exposed
  below `/api/v1`.
- Planned and realized TSS are forbidden from every athlete-facing response,
  error, log returned to a client, export, notification, and LLM message.
- No athlete-facing or general support interface may display TSS in the MVP.

## Physiological specification gate

The evidence recorded in
`physiology-formula-specification.md` opens the local calculation gate for every
rule listed in `phase-3-ruleset-3`. Calculations use exact arithmetic and
example, boundary, and invalid-input fixtures.

BR-009 uses attributable versioned soft review ranges: outlying, expired, or
unconfigured values require review instead of hard rejection. Estimated
Karvonen fallback profiles remain explicitly unreviewed. Exact mixed-workout
ties belong to high intensity, and a shared zone boundary belongs to the more
intense zone. Automatic injury-load redistribution is disabled. A new reviewed
ruleset version is required to activate any further physiological policy.
