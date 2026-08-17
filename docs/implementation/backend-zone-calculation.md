# Backend zone calculation, field tests, and Week-1 calibration

Status: `Phase 8.5 backend and Expo functional cores implemented locally;
planner, database, device, dependency, and production gates remain`

Date: 2026-08-13

This document is the decision and implementation record for the backend phase
between the structured weekly check-in (Phase 8) and the first wearable
integration (Phase 9). It is the authoritative roadmap reference for the
reviewed files in
`docs/trainings/START23_test_en_kalibratie_CSVs_v1_APPROVED.zip`.

## Outcome

The backend now supports four explicit setup routes per discipline:

1. `known_values`: self-reported thresholds and optional complete Zone 1-5
   profiles;
2. `field_test`: one reviewed, versioned field-test protocol;
3. `calibration_week`: a conservative, submaximal Week-1 protocol;
4. `rpe_only`: training without thresholds or zones.

The canonical perceived-exertion field is RPE on an integer 1-10 scale. TSE in
the supplied product text means this same perceived-exertion input in this
flow; it is not a second physiological measure.

Empty optional boundary arrays are valid when the athlete supplies only a
threshold, selects a field test, selects calibration, or explicitly chooses
RPE-only. RPE-only is a configured onboarding route and does not create a fake
zone profile.

## Locked safety boundary

The approved CSV bundle defines field-test threshold formulas, but it does not
define a complete deterministic Zone 1-5 model for CSS, FTP, bike threshold
heart rate, run LTHR, or run threshold pace. In particular it contains no
complete set of:

- percentage or offset bands for every metric;
- canonical rounding for every pace-derived boundary;
- boundary ownership after rounding;
- minimum evidence and reviewer metadata for the Zone 1-5 model.

Consequently, this phase can produce a pending threshold estimate but cannot
create calculated Zone 1-5 boundaries. A valid field-test response uses:

```text
status = threshold_estimated
threshold_status = threshold_estimated
zone_status = pending_protocol
review_status = pending_athlete_confirmation
reason_codes = [zone_model_not_approved]
```

No active zone version is created or changed. This is intentional fail-closed
behavior, not a missing default. Athlete-entered complete boundaries continue
to use the existing manual validation and approval lifecycle.

Submaximal Week-1 calibration can return `provisionally_calibrated` when the
required block/session RPE and objective same-block measurements exist. It
returns `rpe_only` when the workout is complete but sensors are absent. It
never returns CSS, FTP, bike threshold heart rate, LTHR, or run threshold pace.

## Reviewed protocol registry

| Protocol | Discipline | Successful maximum result | Deterministic formula |
|---|---|---|---|
| `start23_run_threshold_30min_v1` | Run | `threshold_estimated` | Run threshold pace is the whole-second average pace of the valid 30-minute segment. Optional LTHR is the rounded average heart rate over minutes 10-30 when HR completeness is sufficient. |
| `start23_bike_ftp_30min_v1` | Bike | `threshold_estimated` | `round_half_up(average_power_last_20min_watts * 0.95)` after the explicit 30-minute test with a calibrated source and at least 95% completeness. |
| `start23_bike_fthr_20min_v1` | Bike | `threshold_estimated` | Rounded average heart rate over the complete valid 20-minute bike segment with at least 95% completeness. |
| `start23_swim_css_400_200_v1` | Swim | `threshold_estimated` | `(time_400m_seconds - time_200m_seconds) / 2`, with 25/50 m pool, freestyle, no equipment, valid recovery, and a faster 200 m pace. |
| `start23_week1_run_calibration_v1` | Run | `provisionally_calibrated` | Preserve same-block RPE, heart rate, and/or pace observations; no threshold conversion. |
| `start23_week1_bike_calibration_v1` | Bike | `provisionally_calibrated` | Preserve same-block RPE, heart rate, and/or power observations; no threshold conversion. |
| `start23_week1_swim_calibration_v1` | Swim | `provisionally_calibrated` | Compute repetition pace as `elapsed_seconds / distance_meters * 100`; do not call it CSS. |

The Python registry is parity-tested against every protocol and segment in the
committed approved index and seven CSV files. The ZIP named in the original
decision record is absent from the repository, so the test reads those source
files directly. A fixture change therefore still fails tests until the
versioned code contract is deliberately updated.

### Pace rounding

Canonical run pace and CSS are whole seconds. The supplied field-test files do
not state how a fractional run threshold pace or fractional CSS result must be
rounded. These cases return `insufficient_protocol` with
`pace_rounding_rule_not_approved`; the backend does not silently choose a
rounding convention. The explicitly stated FTP and heart-rate `round()` rules
use deterministic decimal round-half-up.

## Data and quality rules

Every observation belongs to one verified athlete, activity, protocol, and
segment. The athlete identity is derived from the verified access token and is
not accepted in the request model.

Evaluation requires the non-optional protocol segments, completion state,
segment duration or distance, block RPE, session RPE, and protocol-specific
quality signals. Objective measurements used for calibration come from the
same main block as `reported_block_rpe`. Missing session RPE blocks evaluation
but does not block persistence of the activity or immutable observations.

The following principles are implemented and tested:

- RPE must be an integer from 1 through 10;
- running and cycling threshold heart rate are different metric kinds;
- FTP is never derived from heart rate, weight, sex, or a W/kg constant;
- CSS is never derived from a normal swim or RPE;
- LTHR is never extrapolated from an easy run;
- submaximal calibration never produces a threshold;
- a duplicate identical observation is idempotent;
- a changed retry for the same activity/protocol/segment conflicts rather than
  rewriting history;
- public request/response models and the new public tables contain no TSS or
  private-load fields.

## Biometric heart-rate fallback

The existing active fallback remains Tanaka HRmax plus Karvonen heart-rate
reserve:

```text
HRmax = 208 - 0.7 * age
target HR = resting HR + (HRmax - resting HR) * intensity fraction
```

The backend now also contains the explicitly requested deterministic
`220 - age` plus resting-heart-rate Karvonen calculation as
`calculate_age_220_karvonen_fallback`. It is labeled with ruleset
`start23-age-220-karvonen-v1`, source `estimated`, validation state
`unreviewed`, and `requires_confirmation=true`.

The alternative is deliberately not the default onboarding persistence route.
Persisting it as an athlete-facing selectable profile still needs a reviewed
provenance column/RPC contract and the already recorded clinical/privacy gate.
It must never be used to infer FTP, CSS, run threshold pace, or a clinically
measured maximum heart rate.

## API contract

All routes are authenticated and live below `/api/v1`:

| Method and route | Behavior |
|---|---|
| `GET /onboarding/zone-options` | Returns the four setup routes. |
| `PUT /onboarding/disciplines/{discipline}/setup` | Saves an owner-derived, resumable setup route. |
| `GET /calibration/protocols/{discipline}` | Returns active protocol segments and RPE targets. |
| `POST /calibration/observations` | Saves one immutable, retry-idempotent segment observation. |
| `POST /calibration/evaluate` | Runs deterministic evaluation over owned observations and persists the result through a service-only RPC. |
| `GET /calibration/status` | Returns only the caller's setup and evaluation state. |

Input models use canonical units:

- heart rate: BPM;
- power: watts;
- run pace: seconds per kilometre;
- swim pace/CSS: seconds per 100 metres;
- distance: metres;
- duration: seconds.

## Persistence and security

Forward migration
`20260813170000_phase_8_5_zone_calibration.sql` adds:

- `discipline_zone_setups`;
- `calibration_observations`;
- `calibration_evaluations`;
- owner-scoped setup and observation RPCs using `SECURITY INVOKER`;
- a narrow service-only evaluation persistence RPC;
- forced RLS, explicit Data API grants, ownership indexes, and direct-write
  guards;
- immutable observation and evaluation triggers;
- planning-input snapshots containing discipline setup routes;
- onboarding completion based on either an active manual/fallback zone profile
  or an explicit safe setup route for every discipline.

The generated evaluation RPC is not executable by `authenticated` or `anon`.
This prevents a client from persisting forged threshold results. The service
role can perform only the bounded RPC and receives no new direct table grant.

## Historical training and load

Reported training minutes remain context for frequency, experience, and safe
planning. No `reported hours * 40` or equivalent Start-TSS formula was added.
The calibration engine does not read or reconstruct private planned/realized
TSS and does not use RPE to manufacture CSS, FTP, LTHR, or pace.

## Implementation actions

- Added the pure protocol registry and evaluator in
  `backend/app/modules/calibration/domain.py`.
- Added strict public schemas, thin routes, application service, and Supabase
  repository in `backend/app/modules/calibration/`.
- Registered the module in the FastAPI modular monolith and lifecycle.
- Added the forward-only migration and rollback-only pgTAP suite.
- Added domain, fixture-parity, repository, API, owner-isolation, idempotency,
  and OpenAPI/privacy tests.
- Extended onboarding state with explicit discipline setup records.
- Added the optional pure `(220 - age)` Karvonen alternative without making an
  unsupported validation claim.
- Added strict-TypeScript mobile setup for all four routes, including partial
  known thresholds, optional athlete-entered boundaries, reviewed field-test
  selection, calibration guidance selection, swim pool length, and RPE-only.
- Added a mobile protocol/feedback/result flow that first creates an owned
  canonical activity, records canonical session RPE, writes immutable segment
  observations, and then calls deterministic evaluation. Threshold results
  explicitly explain that no active Zone 1-5 profile was created.
- Aligned the Expo SDK 57 patch set and verified 21/21 Expo Doctor checks plus
  strict TypeScript.

## Remaining gates

The following work is not silently treated as complete:

1. approve a full per-metric Zone 1-5 conversion model, including pace
   rounding and boundary ownership after rounding;
2. define an approved internal planned-load treatment, connect calibration
   protocols to zone-independent planned-workout DTOs, and add normal Week-1
   planner selection (the current regular workout DTO assumes a zone number);
3. add threshold-result approve/reject semantics only when an approved zone
   model can create a real pending zone version;
4. exercise the implemented mobile setup, protocol, feedback, and result flow
   in Android/iOS development builds;
5. resolve the remaining npm dependency advisories through an
   upstream-compatible SDK 57 patch or separately reviewed SDK upgrade rather
   than the audit tool's incompatible downgrade proposal;
6. run the migration, pgTAP, database advisors, and two-real-token tests when a
   PostgreSQL/Docker or hosted development runtime is available;
7. record named qualified production review and, for biometric alternatives,
   privacy/legal review.

Until gate 1 is satisfied, `zone_status=pending_protocol` is the correct final
state for a valid field-test threshold estimate.
