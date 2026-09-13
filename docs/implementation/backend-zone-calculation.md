# Backend zone calculation, field tests, and Week-1 calibration

Status: `current Phase 13/14 contract implemented locally; database and device
runtime gates remain`

Updated: 2026-09-13

This is the current implementation record for the reviewed calibration files in
`docs/trainings`. The approved Phase 13 ruleset is authoritative when older
Phase 8.5 behavior conflicts with this document.

## Current setup routes

Setup discovery is discipline-scoped:

| Discipline | Selectable routes |
| --- | --- |
| Run | known values, Week-1 calibration |
| Bike | known values, Week-1 calibration |
| Swim | known values, reviewed CSS field test, Week-1 calibration |

Run and bike field tests are deliberately absent from both the discovery API
and mobile UI because their current planning/execution contract is not complete.
Historical protocol rows remain readable and retain their original provenance;
they are not silently reinterpreted. `rpe_only` is likewise historical only and
cannot satisfy current onboarding.

The route is only resumable setup intent. A `discipline_zone_setups` row, a
threshold estimate, or a pending zone profile never counts as ready. Current
readiness requires an active profile for every discipline required by the
athlete's race.

## Current calibration lifecycle

The current path is:

```text
prescribed reviewed protocol
  -> immutable owner-scoped observations
  -> deterministic Phase 13 threshold estimate
  -> deterministic Zone 1-5 calculation
  -> threshold confirmation creates a pending zone/profile proposal
  -> athlete approval with an exact base-version precondition
  -> stale-safe activation
```

Nothing in evaluation or threshold confirmation activates a zone profile.
Changed retries conflict; identical retries return the existing result. A stale
approval cannot replace a newer active profile.

For the first mandatory calibration block, the evaluator requires completion,
sufficient data quality, stable execution, and an integer block RPE from 1
through 10. Run and bike additionally require same-block average heart rate.
Swim requires elapsed time and distance and converts that observation to seconds
per 100 metres. The versioned `phase-13-joren-ruleset-1` anchors calculate the
threshold, apply canonical half-up rounding, and calculate five adjacent zones.
Run/bike estimates below 140 bpm retain the warning
`calculated_threshold_unusually_low`.

Current successful submaximal evaluations use:

```text
status = threshold_estimated
threshold_status = estimated
zone_status = pending_athlete_confirmation
requires_athlete_confirmation = true
ruleset_version = phase-13-joren-ruleset-1
```

Persisted calculated profiles distinguish a submaximal estimate with
`source_quality=submaximal_calibration_estimate`. They never claim the stronger
`reviewed_field_threshold` provenance used for a reviewed field-test result.
The earlier `provisionally_calibrated` value remains accepted only when reading
historical evaluations.

## Protocol registry

| Protocol | Current discovery | Successful result |
| --- | --- | --- |
| `start23_run_threshold_30min_v1` | suppressed | historical reviewed field-test definition |
| `start23_bike_ftp_30min_v1` | suppressed | historical reviewed field-test definition |
| `start23_bike_fthr_20min_v1` | suppressed | historical reviewed field-test definition |
| `start23_swim_css_400_200_v1` | selectable | pending CSS threshold and zones |
| `start23_week1_run_calibration_v1` | selectable | pending HR threshold and run zones |
| `start23_week1_bike_calibration_v1` | selectable | pending HR threshold and bike zones |
| `start23_week1_swim_calibration_v1` | selectable | pending pace/CSS threshold and swim zones |

The Python registry is parity-tested against the committed index and seven CSV
files. The mobile/API flow is covered end to end for the selectable run, bike,
and swim calibration protocols, including source provenance, pending approval,
and the below-140 warning.

## API contract

All routes are authenticated below `/api/v1`:

| Method and route | Behavior |
| --- | --- |
| `GET /onboarding/zone-options/{discipline}` | Returns only executable routes for that discipline. |
| `PUT /onboarding/disciplines/{discipline}/setup` | Saves owner-derived resumable intent; does not establish readiness. |
| `GET /calibration/protocols/{discipline}` | Returns only current selectable protocol definitions. |
| `POST /calibration/observations` | Saves one immutable, retry-idempotent observation. |
| `POST /calibration/evaluate` | Runs deterministic evaluation and persists its attributable result. |
| `POST /calibration/evaluations/{evaluation_id}/threshold/confirm` | Records the threshold decision and creates/replays a pending zone proposal. |
| `POST /change-proposals/{proposal_id}/approve` | Performs owner-scoped stale-safe activation. |
| `POST /change-proposals/{proposal_id}/reject` | Rejects the pending proposal without changing the active base. |

Canonical units are BPM, watts, seconds per kilometre, seconds per 100 metres,
metres, and seconds. Athlete identity always comes from a verified access token;
public requests and responses contain no TSS or private-load values.

## Persistence and security

The original Phase 8.5 tables retain immutable observations and evaluations.
The final Phase 13/14 R6-entry audit migration adds the truthful submaximal
source label and validates that its evaluation, discipline, protocol, ruleset,
and exact calculated profiles agree. The previous persistence function is
renamed and loses all external execution; a service-only wrapper preserves its
locking/idempotency behavior while closing the provenance bypass.

## Verification gates

Local Python domain/API/repository/contract tests and React Native
component/transport tests cover the implemented lifecycle. The new migration
and rollback-only pgTAP suite still require execution against a disposable or
linked PostgreSQL runtime, followed by real-token two-user isolation and
physical-device checks. These are R6/release gates; this remediation does not
start or complete R6.
