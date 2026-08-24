# Phase 0-7 requirements audit

Audit date: 2026-08-13  
Audit scope: current workspace state, including uncommitted files  

Update 2026-08-24: the product owner confirmed completion of qualified
physiological production review for the active rules and
`start23-zone-model-1.0`. References below to that review being blocked describe
the original audit-date state and are superseded; other audit findings remain
historical unless separately updated.
Source documents:

- `docs/Start23_Systeemoverzicht_BR.pdf` (20 pages)
- `docs/START23 concept.docx`

Primary comparison targets:

- `docs/requirements/phase-0-7-decision-register.md`
- `docs/requirements/phase-0-decision-lock.md`
- `docs/requirements/physiology-formula-specification.md`
- `docs/requirements/business-rule-traceability.md`
- `docs/implementation/mvp-roadmap.md`
- architecture, migration, API, backend, mobile, SQL, and test artifacts

## Executive conclusion

The Phase 0-7 documentation and code do **not** yet include or correctly implement
all requirements from the two source documents.

The repository has a substantial and well-tested MVP foundation, but it is not
source-complete. Some differences are deliberate, safety-improving MVP decisions;
others are accepted-but-undelivered work; and several are actual documentation or
implementation defects.

The most important findings are:

1. BR-003 currently derives a workout bucket from dominant interval duration,
   while amended decision 1 makes the training catalog's explicit `Emmer
   (80/20)` authoritative;
2. the first weekly plan uses the cheapest eligible catalog items instead of
   decision 42's reviewed standard Week-1 selection personalized by known
   CSS/zones or the safe unknown-zone calibration route;
3. blocking all goal disciplines still returns an error; decision 36 now assigns
   the required pending, TSS-free rest-only revision to Phase 8;
4. the accepted retrospective mesocycle rule is not used by application
   planning; decision 43 now unambiguously makes a race date the cycle anchor;
5. athlete-facing workout movement, explicit public rest days, selection-aware
   deck filtering, and an athlete-local weekly trigger are now accepted Phase 8
   work but are not implemented;
6. the available 160-row training export has not been reviewed/imported for
   taper eligibility and contains no explicit taper marker; and
7. several support documents contain obsolete status or rule statements.

The root `README.md` test credentials are fake, non-production examples. Their
presence is a narrowly scoped, explicitly accepted risk under decision 35, not
an unresolved leaked-secret finding. Real or privileged credentials remain
prohibited.

## Audit method and limitations

- All 20 PDF pages were rendered and visually inspected. The document covers the
  overview and actors (pages 2-3), BR-001 through BR-010 (pages 4-8), UC-01
  (pages 9-12), UC-02 (pages 12-14), UC-03 (pages 14-16), UC-04 (pages 16-17),
  UC-05 (pages 17-19), integrations/examples (page 19), and the overshoot example
  (page 20).
- The DOCX was read from its complete OOXML body, including all paragraphs and
  tables. Its vocabulary overlaps the PDF extraction by 98.33%; the PDF also
  preserves the formula images from the DOCX. The two files are treated as
  equivalent requirement sources, not as two independently versioned specs.
- The current workspace was reviewed rather than only committed `HEAD` because
  most Phase 4-7 implementation files are currently untracked or modified.
- Verification performed:
  - backend: `235 passed`;
  - Ruff: passed;
  - strict mypy: passed;
  - mobile strict TypeScript: passed.
- SQL migration presence and pgTAP definitions were inspected. No local
  PostgreSQL/Docker pgTAP run was available. Phase 6 hosted verification and
  Phase 7's lack of hosted verification are taken from the repository records;
  this audit did not independently connect to the hosted Supabase project.

Status meanings used below:

- **Implemented**: present in the current application path and covered by tests.
- **Partial**: important parts exist, but the source or accepted decision is not
  fully delivered.
- **Deferred**: intentionally assigned to a later roadmap phase.
- **Missing**: absent from both the applicable roadmap delivery and code.
- **Incorrect**: code or documentation conflicts with the latest accepted rule.

## Phase-by-phase result

| Phase | Intended result | Audit result | Main qualification |
|---|---|---|---|
| 0 | Lock contradictions, formulas, states, precedence, TSS boundary, and MVP input | **Partial / inconsistent** | Strong decision set, but partial-race alignment is simultaneously open and approved; recurring activities are both open and later resolved; older lock text contains stale implementation status. |
| 1 | FastAPI foundation, configuration, probes, Railway packaging, CI | **Implemented locally** | Code and checks exist. Railway has not been deployed. The "no credentials committed" gate is violated by the root README. |
| 2 | Verified identity and row isolation | **Partial** | JWT identity and profile/RLS schema exist. The roadmap still says FastAPI profile persistence is pending even though Phase 4 implements it. Full real-token FastAPI verification remains open. |
| 3 | Pure deterministic physiology | **Partial / one incorrect rule path** | Pure modules and broad tests exist. BR-003 aggregate arithmetic conflicts with the latest decision register; retrospective mesocycle logic is not used by runtime planning. The production-review blocker recorded on the audit date was closed by the 2026-08-24 confirmation. |
| 3.5 | Expo SDK 57 development-build transition | **Implemented for Android** | Package versions and TypeScript agree with SDK 57. iOS signing/device validation remains open. The Phase 0 lock still says SDK 54 is current. |
| 4 | Onboarding, goal, history, and zones | **Partial** | Profile, triathlon history, one A-race goal, manual zones, unreviewed HR fallback, and resumability exist. Refined threshold/self-test/calibration flows, physiology-sex fallback, source initial-capacity behavior, other-sport context, and backward macroplanning do not. |
| 5 | Workout catalog and private planned load | **Implemented for narrowed catalog** | Eight immutable versions across seven logical templates are represented after Phase 6. The 500+ library is explicitly deferred. Multi-discipline taper coverage is incomplete. |
| 6 | Pending weekly planning, approval, deck, scheduling, warnings, calendar | **Partial** | Backend proposal/approval and calendar paths are strong. Mobile rescheduling, smart-rest records, live selection-aware deck filtering, scheduled weekly generation, and runtime retrospective race alignment are missing. All-disciplines-blocked handling is incorrect. |
| 7 | Canonical activity, RPE, private realized load, limited corrections | **Implemented locally, partial against accepted amendments** | Canonical summaries and pending corrections exist. Current-week RPE correction is not implemented; hosted migration/RLS verification and Android E2E remain open. The app does not force a global RPE prompt on open. |

## Complete source-requirement coverage matrix

This matrix groups every material requirement family in the source documents.
It distinguishes an intentional roadmap narrowing from an accidental omission.

### Product, actors, and global boundaries

| ID | Source requirement | Roadmap/code status | Result |
|---|---|---|---|
| SYS-01 | Race and non-race goals, including weight loss, muscle gain, and general fitness | Race-oriented A goal exists; non-race rules are Phase 12 | **Deferred / partial product** |
| SYS-02 | Athlete, deterministic AI Engine, LLM Coach, and modular wearable platforms | Athlete/backend exist; LLM is Phase 10; wearable is Phase 9 | **Deferred / partial system** |
| SYS-03 | LLM extracts context and explains, but does not make physiological decisions or mutate plans/zones | Enforced architecturally; no LLM mutation path exists | **Implemented boundary** |
| SYS-04 | Wearable data supplies FIT/TCX and telemetry through modular integrations | Phase 9 | **Deferred** |
| SYS-05 | Athlete retains final authority | Pending proposals and explicit approval exist | **Implemented for plan/zone/correction paths** |
| SYS-06 | Planned and realized TSS never reach the athlete UI | Private tables, Pydantic mapping, OpenAPI/recursive tests exist | **Implemented for current surfaces** |

### BR-001 through BR-010

| Rule | Result | Evidence-based qualification |
|---|---|---|
| BR-001 autonomy | **Implemented for current critical paths** | Generated plans, zone replacements, and activity corrections remain pending. Direct athlete moves are the approved immediate exception. |
| BR-002 soft boundaries/debt | **Partial** | Pure volume and intensity debt plus pending correction exist. Richer correction/replacement behavior remains open. |
| BR-003 time-based 80/20 | **Incorrect catalog-source implementation** | Current code derives the bucket from interval dominance. Decision 1 makes the imported training's explicit `Emmer (80/20)` authoritative for its full duration; interval zones remain for execution/private TSS. |
| BR-004 progression | **Partial** | Deterministic progression and 42-day fallback exist. Decision 42's standard Week-1 selection and the accepted four-complete-week zero-restart rule do not. |
| BR-005 hidden TSS | **Implemented for current API/database surfaces** | Public schemas and mobile types omit the numbers; private load records and contract tests exist. Future coach/export/notification surfaces remain gates. |
| BR-006 anti-stack | **Implemented in backend** | Generated scheduling enforces 72/48 elapsed hours; direct moves return warnings. The mobile app cannot currently perform the documented move. |
| BR-007 4+1 cycle | **Partial** | Pure forward/retrospective functions exist; application planning uses only forward count. Decision 43 requires backward alignment from every race date and a week-1 start for non-race goals. |
| BR-008 taper | **Partial** | Pure A/B/C calculations exist, but the available 160-row training export has no explicit taper marker and has not been reviewed/imported for complete triathlon taper coverage. |
| BR-009 zones | **Partial** | Canonical metrics, soft review, boundaries, versioning, and unreviewed fallback exist. Standard Week-1 calibration plus TSE feedback is accepted, but the TSE scale/RPE relationship and deterministic conversion to CSS/zones are not specified or implemented. |
| BR-010 injury restrictions | **Partial / incorrect all-blocked path** | Zero automatic redistribution and discipline exclusion are correct. Durable restriction lifecycle is Phase 8. All goal disciplines blocked currently errors instead of producing rest. |

### UC-01 onboarding and baseline

| ID | Source requirement | Result |
|---|---|---|
| UC01-01 | Age, height, weight, resting HR, sex, and motivation | **Partial**: DOB/height/weight/resting HR/motivation exist; optional physiology-sex decision is not implemented. |
| UC01-02 | SMART A/B/C goals | **Partial**: one A-race goal exists. Decision 43 requires explicit race/event versus non-race goal selection; non-race execution is Phase 12. |
| UC01-03 | Swim, bike, run, other endurance, and other sport history | **Partial**: only swim/bike/run are accepted. Weekly outside activities are assigned to Phase 8. |
| UC01-04 | Initial capacity `sum(hours) * 40` | **Explicitly superseded by decision 42**: use a reviewed standard Week-1 selection, personalized by known CSS/zones or the safe calibration route. Runtime's cheapest-catalog bootstrap is still not that final behavior. |
| UC01-05 | Week 1 as dynamic calibration and immediate RPE-based correction | **Partial**: decision 5 uses planned/realized calibration context plus TSE feedback for a pending zone proposal, but the reviewed conversion protocol and workflow do not exist. |
| UC01-06 | Generate macroplanning backward from the A-race with 4+1 and two taper weeks | **Partial**: decision 43 locks race-date anchoring, but runtime planning does not call the retrospective helper and no macrocycle/mesocycle persistence exists. |
| UC01-07 | Per-discipline manual, test, or fallback setup | **Partial**: manual and HR fallback exist; test/calibration flow does not. |
| UC01-08 | Tanaka/Karvonen and estimated FTP fallback | **Superseded/partial**: current code uses Tanaka/Karvonen for bike/run; accepted 2026-08-13 decision replaces this with an optional physiology-sex HRmax route and expressly forbids sex-based FTP estimation. |
| UC01-09 | OAuth and 30-day historical sync/recalibration | **Deferred to Phase 9**. |
| UC01-10 | Completion creates first WeeklyPlan and opens the deck | **Partial**: completion queues an `initial_plan_request`; the athlete separately opens planning and triggers proposal generation. |

### UC-02 weekly planning

| ID | Source requirement | Result |
|---|---|---|
| UC02-01 | Monday 00:01 automatic transition or post-check-in trigger | **Missing**: only request-driven plan generation exists; no scheduled job/command exists. |
| UC02-02 | Build/recovery/taper target calculation | **Partial**: calculations exist, subject to baseline, alignment, and catalog gaps. |
| UC02-03 | Time-based low/high budget | **Incorrect for mixed-workout aggregation** due to BR-003 issue. |
| UC02-04 | Deck filtered by phase, injury, and zone capability | **Implemented**. |
| UC02-05 | 500+ workouts | **Explicitly deferred**; narrowed reviewed catalog is intentional. |
| UC02-06 | Swipe/drag workouts onto chosen calendar days | **Partial**: checkbox selection and auto-schedule exist; no swipe/drag day placement exists in mobile. |
| UC02-07 | Recalculate budget and live-filter the remaining deck after each selection | **Missing**. |
| UC02-08 | Deterministic auto-planner | **Implemented** for the narrowed catalog and availability model. |
| UC02-09 | Anti-stack validation and soft warning on athlete edits | **Implemented in backend**. |
| UC02-10 | Persist and display `smart_rest_day` for empty days | **Missing**. |
| UC02-11 | TSS-free WeeklyPlan, workouts, and calendar | **Implemented**. |

### UC-03 activity execution and feedback

| ID | Source requirement | Result |
|---|---|---|
| UC03-01 | Provider webhook and FIT/TCX parser | **Deferred to Phase 9** under the locked canonical-summary MVP decision. |
| UC03-02 | Power/hr/pace realized-TSS formulas from telemetry | **Deferred/replaced for MVP** by deterministic RPE-times-duration private load. |
| UC03-03 | Immediate mandatory RPE popup when opening the app | **Partial**: pending RPE appears only on the activity screen; app open defaults to onboarding. Dismissal policy is still open. |
| UC03-04 | Perfect/overshoot/hidden-fatigue match matrix | **Implemented for the canonical-summary proxy**. |
| UC03-05 | Corrective plan changes remain pending | **Implemented**; current policy cancels eligible future high-intensity work only. |
| UC03-06 | Activity/RPE and qualitative outcome without TSS | **Implemented**. |

### UC-04 weekly evaluation

| ID | Source requirement | Result |
|---|---|---|
| UC04-01 | Weekly check-in over prior activity/RPE and missed work | **Deferred to Phase 8**. |
| UC04-02 | LLM conversation/explanation | **Deferred to Phase 10**. |
| UC04-03 | Schema-constrained extraction of blocked days, injury, and stress | **Structured form in Phase 8; LLM extraction in Phase 10**. |
| UC04-04 | Durable injury/availability context, source, expiry, and weekly review | **Deferred to Phase 8**. |
| UC04-05 | Present and approve the new weekly calendar | **Plan approval exists; check-in orchestration is deferred**. |

### UC-05 progress and zone evaluation

| ID | Source requirement | Result |
|---|---|---|
| UC05-01 | Week-5 batch evaluation of four build weeks | **Deferred to Phase 11**. |
| UC05-02 | Cycling efficiency triggers FTP-test proposal | **Deferred; thresholds/protocol unapproved**. |
| UC05-03 | Running efficiency comparison with >=2% trigger | **Deferred; statistical protocol unapproved**. |
| UC05-04 | Swim top-quartile long-interval CSS detection | **Deferred; statistical protocol unapproved**. |
| UC05-05 | Separate approval for test scheduling and later zone change | **Decision and proposal architecture implemented; evaluation flow deferred**. |
| UC05-06 | Field-test/calibration proposal for fallback users | **Accepted but not implemented**. |

### Integrations, examples, and non-core features

| ID | Source requirement | Result |
|---|---|---|
| INT-01 | Garmin, Strava, or Apple Health integration | **Deferred; first provider not selected**. |
| INT-02 | FIT parser and raw telemetry/file storage | **Deferred to Phase 9**. |
| INT-03 | OpenAI/Gemini wrapper | **Credential plumbing only; provider behavior deferred to Phase 10**. |
| EX-01 | Representative swim/bike/run workouts | **Implemented as a small reviewed catalog**, though not with the source example load numbers. |
| EX-02 | 500+ workout catalog | **Explicitly deferred**. |
| EX-03 | XP and Pacing Points | **Explicitly deferred**. |
| EX-04 | 600/680 overshoot and next-week correction example | **Implemented in pure tests**. |

## Detailed findings and required corrections

### F-01 - Risk accepted - fake test credentials in tracked README

`README.md:2-10` contains two email/password examples. The owner has confirmed
that they are fake, non-production values used only for testing and explicitly
accepted their presence in the repository. Decision 35 records this narrow
exception.

Earlier documentation contains broader wording:

- `docs/implementation/mvp-roadmap.md:98` (no secrets committed);
- `docs/implementation/mvp-roadmap.md:618` (credentials handed off outside the
  repository);
- `docs/implementation/database-migrations.md:59` (no test credential stored in
  the repository).

The accepted examples are not secrets, so the no-secret rule remains intact.
No removal, rotation, or product-code change is required on the stated facts.
The acceptance becomes invalid if either value is ever reused for a production,
privileged, or real-data account.

### F-02 - High - BR-003 aggregate arithmetic implements the wrong source of truth

The available `Trainingen START23.v01` export contains 160 training rows. Every
row has an explicit `Emmer (80/20)` (`73` rows in `80%`, `87` in `20%`) plus
separate interval `Tijd`/`Afstand` and `Zone` fields. Amended decision 1 now
defines the intended separation:

- `Emmer = 20%` places the complete workout duration in the intensive weekly
  bucket;
- `Emmer = 80%` places the complete workout duration in the quieter weekly
  bucket; and
- the individual interval zones remain the source for execution and private
  per-interval TSS, not for overwriting the declared emmer.

The implementation does not import that authoritative field. It derives and
validates a workout bucket from dominant segment duration:

- `backend/app/modules/physiology/intensity.py:126-147`;
- `backend/tests/physiology/test_debt_and_intensity.py:183-195` explicitly locks
  this behavior;
- `backend/app/modules/planning/domain.py:747-824` uses that aggregate for plan
  percentages and minutes.

The full-catalog import, validation, planning arithmetic, tests, and plan
responses must be changed together later. No code was changed in this
documentation pass.

### F-03 - High - accepted standard Week-1 selection is not implemented

The source onboarding flow defines initial capacity as all reported sport hours
multiplied by 40. The planning input snapshot carries training history, but
`PlanningService._context_values` does not use it
(`backend/app/modules/planning/service.py:113-140`). The first-plan target is the
sum of the cheapest eligible catalog item per uninjured discipline
(`backend/app/modules/planning/domain.py:663-714`).

Decision 42 now explicitly supersedes the `hours * 40` Week-1 formula. Week 1
uses a reviewed standard Start23 training selection. Known CSS/thresholds and
zones personalize the prescribed difficulty within those trainings; unknown
values follow the safe calibration route and may create only a pending zone
proposal. Training history remains context/safety input. The current
cheapest-catalog bootstrap is not yet this accepted final behavior.

### F-04 - High - accepted Phase 8 rest-only behavior is not implemented

The accepted BR-010 specification says all blocked disciplines produce rest and
zero redistribution (`physiology-formula-specification.md:231-243`). The pure
injury test covers that analytical result, but application planning raises
`all_disciplines_injured` and generates no rest proposal
(`backend/app/modules/planning/domain.py:656-661`).

Decision 36 now explicitly requires the application path to create a safe,
TSS-free, pending rest-only revision, with athlete confirmation before
activation. A normal planning error is not the specified result. Delivery is
assigned to Phase 8 and remains unimplemented.

### F-05 - High - accepted goal-type and race-date alignment is unused

- Decision 43 requires the athlete to distinguish a dated race/event from a
  non-race personal goal.
- Every dated race always anchors backward cycle alignment; a non-race goal
  begins at cycle week 1 and uses separate Phase 12 rules.
- Pure code implements and tests it
  (`backend/app/modules/physiology/recovery.py:49-62`).
- Runtime planning ignores it and uses `len(prior_loads) + 1` with the forward
  cycle (`backend/app/modules/planning/domain.py:241-257`).

This leaves UC-01's backward macroplan generation and the goal-type choice
undelivered. Runtime planning must later use the race date rather than prior-plan
count and persist stable cycle identity where needed. Weight loss and other
non-race planning remain Phase 12 work and must not silently reuse race rules.

### F-06 - High - accepted athlete-facing rescheduling is not implemented

The backend has `PATCH /planned-workouts/{workout_id}` and enforces the accepted
same-week boundary. The MVP outcome and Phase-one inclusion promise schedule or
move behavior (`mvp-roadmap.md:31` and `mvp-roadmap.md:897`). The mobile API
client has no corresponding method, and `PlanningScreen.tsx:570-628` only
supports deck checkbox selection and read-only calendar cards.

Decision 37 assigns an athlete-facing move/reschedule action to Phase 8. It must
carry the expected revision, preserve the accepted same-local-week boundary,
reject stale changes, and show qualitative warnings without exposing TSS. The
backend boundary exists; the mobile flow does not.

### F-07 - Medium - accepted public rest-day representation is absent

UC-02 requires every intentionally empty day to be distinguishable as a rest day
in persistence and UI. Repository-wide code has no public rest-day model or
event; the planner only enforces a maximum number of consecutive empty days.
Decision 38 assigns explicit TSS-free API and mobile-calendar representation to
Phase 8. It is not implemented.

### F-08 - Medium - accepted selection-aware deck recalculation is absent

The source requires remaining high-intensity cards to disappear when the
selected high bucket is filled. Current deck eligibility filters phase, goal,
injury, fallback, and zone requirements, while mobile selection is local
checkbox state. There is no selection-aware remaining-budget deck endpoint or
recalculation. Decision 39 requires server-authoritative recalculation against
the exact selection and expected revision in Phase 8; the precise endpoint or
response shape remains an implementation choice. Public output must stay
qualitative and TSS-free.

### F-09 - Medium - accepted athlete-local weekly trigger is absent

The source defines Monday 00:01 UTC or post-check-in generation. The repository
has request-driven plan generation only and no scheduled application command.
Decision 40 replaces blind UTC behavior with idempotent athlete-local
Monday-Sunday semantics and a compatible post-check-in trigger. Phase 8 owns
delivery; it is not implemented.

### F-10 - Medium - accepted zone-onboarding flow remains undelivered

Decision 5 now clarifies the unknown-zone route: the athlete performs standard,
safely executable calibration training through the training plan and enters a
TSE feeling score afterwards. The prescribed training, eligible realized
measurements, and TSE feedback together may produce only a pending CSS/zone
proposal.

The checked `Start23_Fysiologische_TSS_Logica.pdf` contains fixed IF values for
Zones 1-5 and the private TSS/sTSS formulas per interval. It does **not** contain
a TSE-to-CSS, TSE-to-FTP, TSE-to-LTHR, pace, or Zone 1-5 conversion. TSE is also
not defined elsewhere in the repository or related explicitly to the existing
RPE 1-10 field. Therefore the UI/workflow can be specified, but the numerical
zone engine cannot be implemented safely until that deterministic mapping,
scale, required realized measurements, and review metadata are supplied.

The mobile intake now exposes the three expected pistes before showing any
fields: manual known values, automatic calibration/test, and biometric
fallback. Manual entry works, and the existing heart-rate fallback works for
bike/run. Calibration and swim cold-start are visible but safely unavailable.

Remaining gaps are:

- no per-discipline "threshold known?" pre-question;
- no threshold-only submission;
- no reviewed deterministic boundary derivation;
- no zone-independent Week-1 calibration workout;
- no pending initial threshold/zone proposal.

Current `ManualZoneSubmission` requires five boundaries
(`backend/app/modules/onboarding/schemas.py:177-187`). This is truthful roadmap
debt, not a hidden implementation.

### F-11 - Medium - accepted 2026-08-13 amendments not implemented

The decision register and roadmap correctly identify these gaps:

- optional physiology-sex HRmax route (decision 9);
- achieved-goal maintenance state (decision 29);
- recurring outside-activity confirmation and pre-scheduled extra sport
  (decisions 30-31; Phase 8);
- current-local-week RPE correction with audit trail (decision 32);
- exact four-complete-week restart after a zero week (decision 34);
- pending rest-only revision when every goal discipline is blocked (decision
  36);
- mobile same-week movement with revision preconditions and warnings (decision
  37);
- explicit public rest days, selection-aware deck recalculation, and
  athlete-local weekly generation (decisions 38-40);
- existing-catalog taper review, eligibility, validation, and import (decision
  41);
- standard Week-1 selection/personalization (decision 42);
- race/event versus non-race goal selection and race-date alignment (decision
  43); and
- persistent non-blocking app-open feedback reminder (decision 44).

These should not be described as ruleset-3 behavior until a new ruleset,
migrations, APIs, mobile flows, and tests exist.

### F-12 - Medium - accepted app-open feedback reminder is not implemented

`App.tsx:18-69` defaults authenticated users to onboarding and does not check for
pending RPE. The RPE list exists only after navigating to `ActivityScreen`.
Decision 44 requires a prominent but non-blocking app-open reminder that remains
visible until the required RPE/TSE is entered or an explicit terminal state is
recorded, and deep-links to the activity. This is assigned to Phase 8 and is not
implemented.

### F-13 - Medium - available training catalog has not been assessed for taper

The available `Trainingen START23.v01` export contains 160 trainings: 60 swim,
50 bike, and 50 run. It has training type, target event, emmer, RPE, and interval
zone fields, but no explicit `taper` or `afbouw` marker. The small runtime catalog
still fails closed for a complete triathlon taper.

Decision 41 therefore requires Phase 8 to review the existing rows first,
define and approve taper eligibility, validate/import suitable rows, and run a
complete A-race triathlon taper fixture. It no longer assumes that additional
training rows must be supplied. No training or import was implemented in this
documentation pass.

### F-14 - Medium - phase and decision documents contain stale statements

The following statements should be corrected or clearly marked historical:

| Document | Wrong or stale statement |
|---|---|
| `README.md` and credential-handling statements | Decision 35 accepts the fake, non-production README examples. Broader wording elsewhere must not misclassify them as leaked secrets, while the prohibition on real credentials remains. |
| `implementation_plan.md:1-18` | Says the repo is pre-implementation, backend empty, and mobile a stock starter. It also retains the old active 0.8 BR-010 redistribution mapping at line 187. |
| `backend/README.md:14-20` | Says no activity ingestion/realized-load orchestration and describes ruleset 2, despite Phase 7 and ruleset 3 code. |
| `phase-0-decision-lock.md:115-120` | Says mobile still declares SDK 54 and the SDK 57 upgrade is pending. |
| `phase-0-7-decision-register.md` | The recurring-activity and taper delivery items were previously worded as undecided; decisions 30 and 41 now make them accepted Phase 8 work. |
| `domain-model.md:10-14` | Says Phase 6 is local/not applied, while migration records say it is hosted and verified. |
| `domain-model.md:291-292` | Calls the active-revision composite foreign key deferred, although the Phase 6 migration creates it. |
| `domain-model.md:506-507` and `api-contracts.md:334` | Call RPE permanently immutable, superseded by decision 32's current-week correction window. These must be labelled current implementation, not current policy. |
| `security-model.md:10-13` | Says Phase 6 has not been applied. |
| `business-rule-traceability.md:589` | Requires cycling speed zone input, directly contradicting the accepted decision, the same document's line 616, and the code. |
| `business-rule-traceability.md:119-120` | Says hosted Phase 6 verification is pending, while the roadmap records 30/30 hosted pgTAP and two-session isolation. |
| `Vereisten.md:2-4` | Still presents the Phase 3 formula gate as draft without a prominent superseded/historical label. |
| `mvp-roadmap.md:104-108` and current-status lines 941-943 | Say FastAPI profile persistence is pending, though onboarding profile endpoints/repository code exist. Only the remaining hosted real-token E2E gate should be described as pending. |

### F-15 - Medium - no complete maintained source-to-delivery trace exists

`business-rule-traceability.md` covers BR-001 through BR-010, but not every UC
step, actor/integration requirement, later accepted decision, or source example.
The decision register records decisions rather than complete requirements. The
roadmap records phases but does not explicitly disposition every source item.

This makes omissions such as initial-capacity calculation, public rest days,
live deck filtering, global RPE prompt, and the weekly trigger easy to miss,
even when later decisions assign them to a roadmap phase.
Maintain a trace table equivalent to the coverage matrix in this report with:

- stable requirement ID;
- source section/page;
- controlling decision/ruleset;
- roadmap phase or explicit exclusion;
- code owner;
- migration/API/mobile artifacts;
- test evidence;
- delivery and hosted-verification status.

## Roadmap/source differences that are correctly handled

These differences should **not** be treated as implementation bugs:

1. **Automatic plan/zone mutation was removed.** Source UC-03/UC-05 wording
   conflicts with BR-001. Current pending proposal behavior is the correct
   safety interpretation.
2. **Automatic 0.8 injury redistribution is disabled.** The accepted MVP policy
   removes blocked-discipline load and redistributes zero. The code is correct
   for one/two blocked disciplines; the all-blocked application result remains
   an accepted Phase 8 delivery gap.
3. **Phase 7 uses canonical summaries instead of FIT/TCX/provider ingestion.**
   This is a locked Phase 0 scope decision; raw import is Phase 9.
4. **The catalog is small instead of 500+.** This is an explicit, sensible MVP
   deferral and the immutable/private-load implementation is verified locally.
5. **LLM coaching is absent from Phases 0-7.** The deterministic structured
   check-in is Phase 8 and constrained LLM integration is Phase 10.
6. **UC-05 automatic upgrades are absent.** The roadmap correctly requires
   reviewed statistical thresholds and separate approvals before Phase 11.
7. **Non-race plan generation is absent.** It is explicitly assigned to Phase
   12 rather than silently using race rules.

## Recommended correction order

1. Replace segment-dominance bucket derivation with authoritative imported
   `Emmer (80/20)` behavior across catalog validation, planning, tests, and
   public duration summaries.
2. Deliver the accepted standard Week-1 known-zone/calibration routes and make
   race dates, rather than prior-plan count, anchor race cycle alignment.
3. Deliver the accepted Phase 8 rest-only and revision-safe mobile rescheduling
   flows.
4. Deliver explicit public rest days, selection-aware deck recalculation, and
   idempotent athlete-local weekly generation in Phase 8.
5. Reconcile stale documentation and mark historical documents as superseded.
6. Define and review the missing TSE/RPE scale and deterministic
   training/measurement-to-CSS/zone conversion, then complete the Phase 4/8
   calibration route.
7. Review taper eligibility in the available 160-row training export, validate
   and import eligible rows, and run a full triathlon taper fixture.
8. Deliver decision 44's persistent, non-blocking app-open RPE/TSE reminder.
9. Apply and verify Phase 7 in hosted development with pgTAP, real-token
   isolation, advisors, and Android end-to-end execution before calling it
   hosted-verified.

F-01 requires no corrective action while the documented test-only assumptions
remain true.
