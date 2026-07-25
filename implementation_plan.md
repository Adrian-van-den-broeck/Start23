The repository is still at a pre-implementation stage. The architecture constraints are coherent, but the business specification contains several blocking contradictions—especially around user approval, “soft” safety limits, automatic calendar changes, and zone upgrades. These should be resolved before backend or database work begins.

No files were created or modified. No dependencies were installed, and no migrations were executed. Git status remained unchanged.

## 1. Current repository state

Sources inspected: [AGENTS.md](</F:/Projecten Business/Start23/Code/AGENTS.md>), [START23 concept.docx](</F:/Projecten Business/Start23/Code/docs/START23 concept.docx>), [Start23_Systeemoverzicht_BR.pdf](</F:/Projecten Business/Start23/Code/docs/Start23_Systeemoverzicht_BR.pdf>), and the complete relevant contents of [mobile](</F:/Projecten Business/Start23/Code/mobile>).

| Area | State |
|---|---|
| Git | Branch `main`, aligned with `origin/main`. Only `README.md` is tracked. `AGENTS.md`, `/docs`, and `/mobile` are untracked. |
| Root | `README.md` contains only the Start23 heading. There is no root `package.json` or root `package-lock.json`, despite the IDE tab shown in the prompt. |
| Backend | `/backend` exists but is empty. No Python project, FastAPI app, tests, migrations, Supabase configuration, Railway configuration, or environment example exists. |
| Documentation | A Word concept document and a 20-page PDF contain substantially the same BR-001–BR-010 and UC-01–UC-05 specification. The PDF preserves formulas that are image objects in the Word source. |
| Mobile | Stock Expo starter with one placeholder screen in [App.tsx](</F:/Projecten Business/Start23/Code/mobile/App.tsx>). |
| Mobile versions | Expo `~54.0.36`, React `19.1.0`, React Native `0.81.5`, TypeScript `~5.9.2`. Strict TypeScript is enabled. |
| Mobile functionality | No navigation, authentication, Supabase client, API client, state management, domain models, forms, tests, or Start23 UI. |
| Local state | `node_modules` exists with 643 locked packages. `.expo` cache exists and is ignored. Recent logs show Expo CLI `57.0.10` and an Expo Go compatibility error. |
| Version inconsistency | `mobile/AGENTS.md` requires Expo SDK 57 documentation before coding, while the project itself is on SDK 54. The intended upgrade path must be decided first. |

## 2. Functional domains

The requirements imply these bounded functional domains inside one modular monolith:

1. **Identity and athlete profile**
   Supabase Auth identity, biometrics, motivation, preferences, timezone, and onboarding state.

2. **Goals, races, and macrocycles**
   SMART goals, A/B/C priority, race events, macrocycle generation, mesocycles, taper periods, and non-race objectives.

3. **Training zones and calibration**
   Discipline-specific swim CSS, cycling FTP/heart-rate thresholds, running threshold pace/LTHR, manual values, tests, and fallback values.

4. **Workout catalog**
   Curated workout templates, discipline, phase tags, duration, expected RPE, intensity bucket, compatibility requirements, and internal precomputed planned TSS.

5. **Weekly planning and calendar**
   Weekly budgets, workout deck, selection, scheduling, rest days, anti-stack validation, plan revisions, warnings, and approval.

6. **Deterministic physiology**
   Internal TSS calculations, 80/20 distribution, progression, physiological debt, recovery weeks, tapering, fatigue matching, and injury redistribution.

7. **Activity ingestion and execution**
   FIT/TCX ingestion, wearable summaries, telemetry parsing, matching an activity to a planned workout, realized TSS, and completion status.

8. **RPE and feedback loop**
   Post-workout RPE, match-matrix classification, fatigue warnings, and proposed micro-adjustments.

9. **Weekly check-in and athlete context**
   Availability, blocked days, missed-training reasons, injuries, fatigue, agenda stress, and proposed next-week planning.

10. **Change proposals and approval**
    Pending plan revisions, pending zone revisions, approval/rejection, stale-proposal protection, and audit history.

11. **LLM coach**
    Structured-context extraction and user-friendly explanation only. It must not calculate physiology or apply changes.

12. **External integrations**
    Garmin, Strava, Apple Health, Supabase Storage, provider webhooks, OAuth token management, and idempotent imports.

13. **Progress evaluation**
    Multi-week efficiency analysis, test recommendations, and pending zone-update proposals.

## 3. Proposed FastAPI modular-monolith structure

```text
backend/
├── pyproject.toml
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── errors.py
│   │   └── logging.py
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── rls_context.py
│   ├── modules/
│   │   ├── profiles/
│   │   ├── onboarding/
│   │   ├── goals/
│   │   ├── zones/
│   │   ├── workouts/
│   │   ├── planning/
│   │   ├── physiology/
│   │   ├── activities/
│   │   ├── checkins/
│   │   ├── proposals/
│   │   ├── integrations/
│   │   └── coach/
│   ├── jobs/
│   │   ├── weekly_planning.py
│   │   └── zone_evaluation.py
│   └── api/
│       ├── dependencies.py
│       └── router.py
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

Each functional module should contain only the components it needs, typically:

```text
router.py       Thin FastAPI endpoints
schemas.py      Explicit Pydantic request/public-response models
models.py       Persistence models
repository.py   Database access
service.py      Application orchestration
domain.py       Pure deterministic rules and value objects
```

Key dependency rules:

- Routers call application services; they do not perform calculations.
- `physiology` is pure Python and has no FastAPI, database, LLM, or provider dependencies.
- Planning calls deterministic physiology functions and persists their results.
- Integrations translate provider formats into canonical activity input.
- The coach receives deterministic outcomes and sanitized qualitative facts.
- The coach may create a context candidate or pending proposal, but never invoke approval or mutation.
- Scheduled commands reuse the same services and codebase. A Railway cron entrypoint can invoke them without introducing Celery, Redis, or another service architecture.
- All client-facing endpoints use explicit response models. ORM objects must never be serialized directly.

## 4. Proposed database entities and relationships

Use Supabase Auth for identity, PostgreSQL for domain state, and private Supabase Storage buckets for FIT/TCX and telemetry files.

| Group | Entities | Relationships and purpose |
|---|---|---|
| Identity | `auth.users`, `athlete_profiles` | One Auth user has one athlete profile. Store date of birth rather than a permanently stale age if legally acceptable. |
| Onboarding | `training_history_entries`, `onboarding_sessions` | Profile has multiple discipline/category history entries and one or more resumable onboarding sessions. |
| Goals | `goals`, `race_events` | Athlete has multiple A/B/C goals. A goal may optionally reference a race event; non-race goals remain possible. |
| Periodization | `macrocycles`, `mesocycles` | Goal has macrocycles; macrocycle has ordered mesocycles; mesocycle has weekly plans. |
| Zones | `zone_profile_versions`, `zone_metrics` | Athlete has versioned zone profiles per discipline. Exactly one version is active; proposed versions remain pending. |
| Context | `injuries`, `availability_blocks`, `athlete_state` | Discipline injuries, blocked dates, and fatigue/context flags belong to the athlete. |
| Catalog | `workout_templates`, `workout_segments`, `workout_tags` | Templates contain segments and classification tags. Planned TSS is server-internal. |
| Planning | `weekly_plans`, `plan_revisions`, `planned_workouts`, `plan_warnings` | A week has one active plan and potentially multiple pending revisions. Revisions contain scheduled workouts and warnings. |
| Execution | `activities`, `activity_metrics`, `activity_files` | An activity optionally matches a planned workout. Raw files live in private Storage; summaries remain in PostgreSQL. |
| Integrations | `provider_connections`, `webhook_receipts`, `import_runs` | Connections belong to users. Webhook receipts enforce provider event idempotency. Tokens remain server-only. |
| Check-ins | `weekly_checkins`, `context_candidates`, `coach_messages` | LLM extraction first produces a candidate; confirmed context can then feed deterministic planning. |
| Approval | `change_proposals` | References a typed plan revision, zone version, or test-scheduling revision. Tracks pending/approved/rejected/expired status. |
| Audit | `decision_runs` | Records rule-set version, input hash, qualitative outcome, warnings, and proposal reference for reproducibility. |

Primary relationship chain:

```text
auth.users
  └── athlete_profiles
      ├── goals ── macrocycles ── mesocycles ── weekly_plans
      │                                         └── plan_revisions
      │                                             └── planned_workouts
      │                                                 └── activities
      ├── zone_profile_versions
      ├── provider_connections
      ├── weekly_checkins
      └── change_proposals
```

TSS should be isolated in server-only columns or preferably a non-exposed database schema:

- Template planned TSS.
- Planned-workout TSS snapshot.
- Weekly planned TSS.
- Activity realized TSS.
- Weekly realized TSS and physiological debt.

None of these fields should exist in public Pydantic response types, LLM-facing conversational payloads, client logs, or error messages.

Approval should be optimistic and atomic: a proposal records the base plan/zone revision. Approval fails if that base revision is no longer current, preventing a stale proposal from overwriting newer user changes.

## 5. BR-001 through BR-010 mapping

| Rule | Owning module(s) | Implementation responsibility |
|---|---|---|
| BR-001 Autonomy | `proposals`, `planning`, `zones` | System-generated critical changes become versioned pending proposals. Only an authenticated owner can approve. Applying a proposal is atomic and audited. |
| BR-002 Soft boundaries | `physiology`, `planning` | Calculate overshoot and intensity debt deterministically; store warnings and internal debt. User calendar edits remain possible unless requirements explicitly redefine an exception. |
| BR-003 80/20 | `physiology`, `goals`, `workouts` | Classify workout minutes into low/high buckets, select the goal-specific target ratio, and return qualitative compliance/warnings. |
| BR-004 10% progression | `physiology`, `planning` | Pure functions calculate next-week internal load from the prior plan, realized load, recovery state, and CTL fallback. |
| BR-005 Hidden TSS | `api`, `activities`, `planning`, `coach` | Separate internal and public schemas. Add contract tests that fail if any planned/realized TSS field appears in mobile responses. |
| BR-006 Anti-stack | `planning`, `physiology` | Initial scheduling respects 72-hour run and 48-hour bike/swim spacing. Manual user edits return warnings and record violations. |
| BR-007 4+1 | `goals`, `physiology`, `planning` | Periodization assigns mesocycle week numbers and calculates the week-five recovery proposal. |
| BR-008 Tapering | `goals`, `physiology`, `planning` | Race priority and date determine taper windows and internal volume caps. Priority ordering with recovery and injury rules must be specified. |
| BR-009 Zone management | `zones`, `physiology` | Discipline-specific validated value objects, units, ranges, versioning, fallback status, and pending upgrades. |
| BR-010 Injury redistribution | `checkins`, `physiology`, `planning`, `proposals` | Confirm injury context, remove affected-discipline workouts from a proposed revision, redistribute internally using the coefficient, then await approval. |

## 6. UC-01 through UC-05 endpoint mapping

The paths are proposed API contracts, not implemented routes. Public responses must omit all TSS values.

| Use case | Proposed endpoints |
|---|---|
| UC-01 Onboarding | `GET/PATCH /v1/me/profile`; `PUT /v1/me/training-history`; `POST/PUT /v1/me/goals`; `PUT /v1/me/zones/{discipline}`; `POST /v1/onboarding/complete`; `POST /v1/integrations/{provider}/oauth/start`; provider OAuth callback endpoint. |
| UC-02 Weekly planning | `POST /v1/weekly-plans/proposals`; `GET /v1/weekly-plans/{id}/deck`; `PUT /v1/weekly-plans/{id}/selections`; `POST /v1/weekly-plans/{id}/schedule-proposals`; `PATCH /v1/planned-workouts/{id}` for explicit user edits; `GET /v1/calendar`; proposal approve/reject endpoints. |
| UC-03 Execution | Provider-specific webhook endpoints; `POST /v1/activity-imports` for direct FIT/TCX import; `GET /v1/activities/pending-rpe`; `PUT /v1/activities/{id}/rpe`; `GET /v1/activities/{id}`; resulting plan-correction proposal retrieval and approval. |
| UC-04 Weekly check-in | `POST /v1/checkins`; `POST /v1/checkins/{id}/messages`; `PUT /v1/checkins/{id}/context-confirmation`; `POST /v1/checkins/{id}/plan-proposals`; proposal approve/reject endpoints. |
| UC-05 Zone evaluation | Internal scheduled command, not a mobile endpoint; `GET /v1/change-proposals?kind=zone_update`; `GET /v1/change-proposals?kind=validation_test`; standard approve/reject endpoints. Test activity ingestion returns through UC-03. |

Recommended approval contract:

```text
POST /v1/change-proposals/{proposal_id}/approve
POST /v1/change-proposals/{proposal_id}/reject
```

The backend derives the owner from the verified access token. These endpoints must not accept an authoritative `user_id` from the client.

## 7. Security boundaries

### Expo client

- May contain only public configuration such as the API base URL, Supabase URL, and publishable/anon key.
- Must never contain the service-role key, database password, provider client secret, or LLM key.
- Authenticates through Supabase Auth and sends the access token to FastAPI.
- Stores session material in an appropriate secure native store once the Expo version is settled.
- Receives only public schedule/activity DTOs without TSS.
- Does not write critical tables directly through Supabase.
- Uploads sensitive files only through authenticated or short-lived signed upload flows.

### FastAPI

- Verifies Supabase access tokens using the project issuer/signing configuration, including signature, expiry, issuer, audience, and subject. Supabase documents JWKS-based verification and the role of the `sub` claim in its [JWT guidance](https://supabase.com/docs/guides/auth/jwts).
- Derives the athlete ID exclusively from the verified `sub`.
- Owns every physiological formula and planning decision.
- Owns all proposal creation, validation, and approval transitions.
- Keeps provider secrets, database credentials, service-role keys, and LLM keys in Railway environment variables.
- Verifies webhook signatures and applies idempotency using provider event IDs.
- Sends the LLM only sanitized context and deterministic outcomes; the LLM receives no mutation capability.
- Uses explicit Pydantic response models and response-contract tests to prevent TSS leakage.

### Supabase

- Auth is the identity authority.
- PostgreSQL is persistence, not the location of physiological business logic.
- RLS must be enabled on every user-owned table with ownership based on `auth.uid()`. Supabase recommends explicit authenticated ownership policies and warns that exposed-schema tables require RLS in its [RLS documentation](https://supabase.com/docs/guides/database/postgres/row-level-security).
- Server-only schemas should not be exposed through the Data API.
- Raw activity files and GPS/telemetry belong in private Storage buckets with ownership policies or short-lived signed access. Supabase Storage uses RLS, while service keys bypass it entirely, so service-key use must remain narrowly server-side ([Storage access control](https://supabase.com/docs/guides/storage/security/access-control)).
- OAuth refresh tokens and internal TSS data should not be readable by the authenticated client role.
- If the backend uses a role that bypasses RLS, application-level ownership checks become the only guard. Prefer a database access design that preserves RLS context, and reserve bypass credentials for narrowly scoped webhook or maintenance operations.

## 8. MVP phase 1

A credible first MVP should be a narrow end-to-end planning loop:

- Supabase Auth and authenticated FastAPI requests.
- Athlete profile and resumable onboarding.
- One primary race-oriented A goal; B/C goals can be stored but need not drive planning initially.
- Swim, bike, and run training history.
- Manual zone entry plus clearly flagged fallback zones, once formulas and validation ranges are approved.
- A small curated workout catalog rather than the claimed 500+ workouts.
- Internal planned TSS and public TSS-free workout views.
- Deterministic weekly planning with:
  - baseline ratio,
  - progression,
  - 4+1 periodization,
  - taper for an A race,
  - anti-stack warnings,
  - structured availability,
  - structured injury exclusion.
- A pending plan-revision and explicit approval workflow.
- Calendar display and explicit user drag/reschedule actions.
- Activity completion, RPE collection, and a limited objective activity-summary or direct FIT/TCX import path.
- Pending corrective plan proposals after overshoot/fatigue.
- Comprehensive unit tests for all included physiological rules.
- Contract tests proving that planned and realized TSS never cross the client API boundary.

A structured check-in form should precede the LLM. This gives the deterministic engine a testable input contract before natural-language extraction is added.

## 9. Features to defer explicitly

- Multiple wearable integrations at once. Select one provider only after feasibility review.
- Full Apple Health/Garmin/Strava parity.
- Automatic multi-week zone upgrades and UC-05 batch analysis.
- LLM-led onboarding or unrestricted conversational coaching.
- Gamification, XP, and Pacing Points.
- A 500+ workout library; start with a reviewed representative catalog.
- “Other endurance sports” and “other sports” load modelling.
- Non-race goals such as muscle gain and weight loss until their planning rules are specified and clinically reviewed.
- Fasted-training recommendations.
- Advanced swimrun-specific redistribution.
- Automatic provider-based 30-day historical calibration.
- Rich GPS maps and long-term raw telemetry analytics.
- Push notifications and background mobile synchronization.
- Social, sharing, coach, or multi-athlete functionality.
- Admin dashboards and content-management interfaces.
- Any microservice, Redis, Celery, TimescaleDB, Kubernetes, or distributed event infrastructure.

## 10. Ambiguities and contradictions requiring resolution

| Topic | Requirement conflict or gap |
|---|---|
| Automatic calendar mutation | BR-001 requires pending changes, while UC-03 says heavy workouts are automatically downgraded, blocked, or converted. Later text again asks for approval. The exact pre-approval state must be defined. |
| Soft boundaries | BR-002 says limits never block; UC-02 removes high-intensity workouts from the deck, UC-03 temporarily blocks them, and BR-007 calls recovery mandatory. Define whether these are recommendations, generation constraints, or user-facing prohibitions. |
| Zone approval | UC-05 says zones are overwritten after a test, but BR-001 prohibits independent zone changes. Decide whether test consent authorizes the future value or whether a second explicit approval is required. |
| Threshold gaps | “Perfect” is ±10%, BR-002 discusses >10% volume overshoot, and UC-03 defines overshoot at >15%. Behavior from 110% through 115%, including exact boundaries, is undefined. |
| Physiological debt | “Structurally” exceeding limits is not defined. Debt carry-over, minimum next-week load, negative results, rounding, and debt expiry are unspecified. |
| CTL | BR-004 refers both to four active weeks and a conventional 42-day baseline. The formula, weighting, missing-data behavior, and definition of an active week are absent. |
| Rule precedence | No priority is defined when recovery week, taper, injury redistribution, debt correction, availability, and anti-stack rules collide. |
| TSS formulas | Normalized Power calculation is missing; `IFHR` and `IFpace` are undefined; units for duration, pace, CSS, and heart rate are unclear. The displayed swim formula may invert the effect of faster pace. |
| Planned TSS | Workouts have precomputed pTSS, but the system may shorten, downgrade, or personalize them. Define whether it selects another immutable template or recalculates a modified workout. |
| TSS-to-time conversion | UC-02 converts a TSS target to weekly minutes, but no algorithm maps a discrete workout catalog to both a TSS budget and a time-based 80/20 ratio. |
| Ratio logic | The heading mentions a “30/70 rule” that is never defined. Swimrun is called more defensive at 75/25 even though that raises high intensity above 20%. |
| Non-race goals | The product supports weight loss and general fitness, but macrocycle generation assumes an A race and race date. |
| Initial capacity | Start load is defined as all sport hours × 40, but Week 1 also says there is no mathematical start cap. “Other sports” are both collected and declared unnecessary for MVP. |
| Fallback zones | FTP estimates use binary sex-based constants without validation ranges or handling for other users. The scientific and product-policy basis needs review. |
| Injury behavior | Severity, duration, recovery/clearance, multiple injured disciplines, and when redistribution is unsafe are unspecified. Automatically moving load after an injury requires clinical review. |
| RPE | Expected RPE ranges per workout are not modelled. A “mandatory” popup may also conflict with autonomy unless it is dismissible. |
| Activity matching | Matching tolerances, duplicate imports, extra activities, bricks/multisport sessions, edited provider activities, and late-arriving webhooks are undefined. |
| Zone evaluation | Cycling improvement thresholds, minimum sample counts, data-quality rules, run interval comparability, outlier handling, and the actual upgraded zone values are missing. |
| Calendar time | Generation is Monday 00:01 UTC, but athlete timezone and daylight-saving behavior are not defined. |
| State machines | `draft`, `planned`, `pending`, `active`, `completed`, rejected, expired, and superseded states are used inconsistently or not defined. |
| TSS secrecy boundary | Clarify whether TSS is forbidden only from mobile responses or from every user-visible surface, including chat text, exports, notifications, errors, and support tools. The safest interpretation is every user-facing channel. |
| Integration feasibility | Provider-specific OAuth, webhook, file-access, rate-limit, and approval requirements are not documented. |
| Health-data governance | Consent, retention, account deletion, export, GPS sensitivity, LLM data processing, audit retention, and incident handling are absent. |
| Expo version | The app is SDK 54, its nested instruction targets SDK 57, and local CLI/cache state is already version 57. Upgrade versus pinning must be decided before mobile work. |

## Proposed implementation sequence

1. **Requirements lock**
   Resolve the approval state machine, rule precedence, thresholds, TSS formulas/units, zone-upgrade approval, MVP provider, and Expo version.

2. **Backend foundation**
   Add the FastAPI package, configuration, health endpoint, lint/type/test setup, Railway entrypoint, and no domain behavior.

3. **Authentication and isolation**
   Implement JWT verification, authenticated request context, initial Supabase schema, RLS policies, and security tests.

4. **Pure physiology package**
   Implement one BR at a time as deterministic functions with boundary, unit, and property-based tests. No routes or LLM.

5. **Profiles, goals, and zones**
   Add onboarding persistence, manual/fallback zone versions, validation, and public TSS-free schemas.

6. **Workout catalog**
   Introduce a small reviewed catalog with internal pTSS, expected RPE, discipline, phase, and intensity classifications.

7. **Planning and approval**
   Generate pending weekly plan revisions, validate BR-002/003/004/006/007/008/010, expose the workout deck, and apply only approved revisions.

8. **Activity and RPE vertical slice**
   Ingest one supported activity format, calculate internal realized load, collect RPE, classify the match, and create pending correction proposals.

9. **Structured weekly check-in**
   Support blocked days, fatigue, injuries, and missed-training reasons without an LLM.

10. **One wearable integration**
    Add one provider adapter, webhook verification, idempotency, and private file storage.

11. **LLM coach**
    Add schema-constrained context extraction and explanations over deterministic results, with no direct mutation path.

12. **Progress evaluation**
    Implement UC-05 only after its statistical thresholds and approval semantics are fully specified.