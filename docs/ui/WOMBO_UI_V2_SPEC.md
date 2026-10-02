# Wombo UI/UX V2 design specification

Status: complete design proposal for later implementation; no runtime authorization.
Date: 2026-10-02.
Functional reference: `fix/pre-ui-beta-blockers` at `6bb3a047139d91c71ac065c35a8af595221b54c5`.

Companion documents:

- [Screen map and screen specifications](WOMBO_UI_V2_SCREEN_MAP.md)
- [Design tokens and component rules](WOMBO_UI_V2_TOKENS.md)

## 1. Scope and evidence

This specification changes presentation and proposes future navigation. It does not change screens, routes, APIs, planning, physiology, persistence, dependencies, or deployments. It does not authorize new product capabilities. Wombo is the athlete-facing name; Start23 remains the repository/domain name. No logo replacement is proposed.

The checkout branch and HEAD matched the supplied baseline during inspection. Existing modified coach code and untracked Garmin, privacy, and user/PDF documents were left untouched. No unpublished regression work was changed. This review used repository source, contracts, tests, and tracked decision documents; it was not an app-running or physical-device visual audit. Dimensions below are design targets, not measured improvements.

### Repository findings

Paths below are relative to the repository root.

| Evidence | Current behavior and V2 implication |
| --- | --- |
| `mobile/app/index.tsx`, `app/(authenticated)/onboarding.tsx` | Authentication enters the onboarding/resume gate, then Planning. Preserve the gate even when Week becomes the home destination. |
| `mobile/app/(authenticated)/_layout.tsx` | Stack navigation and global pending-RPE reminder. No live bottom-tab shell. V2 bottom navigation is a future change requiring route regression coverage. |
| `mobile/src/screens/PlanningScreen.tsx` | Week / Choose / Calendar are internal views. Setup, profile menu, quick actions, revision metadata, warnings, approval and workout editors compete for space. V2 separates tasks while sharing state. |
| `mobile/src/screens/HomeScreen.tsx` | Static design preview, including example start time and nonfunctional tabs. It is not a live feature source. Do not carry its invented time or Coach destination into V2. |
| `mobile/src/components/WeekSchedule.tsx` | Active-plan seven-day move board; dedicated handle, measured row centers, date-button fallback and accessibility moves. Preserve all capabilities. |
| `mobile/src/components/TrainingCalendar.tsx` | Separate approved calendar, Week and Month, local dates, exclusive range end, selected-day Month detail. Two presentations overlap with the move board. |
| `mobile/src/components/WorkoutDetail.tsx`, `src/api/types.ts` | Ordered segments, names, instructions, time/distance, zone/RPE/protocol targets. No structured repeat hierarchy, equipment field or separate session-type field. |
| `mobile/src/lib/workoutPresentation.ts` | Planning-card descriptions deliberately suppress RPE sentences. Keep that default; execution detail carries expected RPE. |
| `mobile/src/screens/ActivityScreen.tsx`, `src/api/client.ts` | Create then HR/RPE; a single inline pending-feedback form, retained create identity/key, refresh on ambiguous feedback failure; current-week RPE correction and explicit activity matching. |
| `mobile/src/screens/OnboardingScreen.tsx`, `ZoneSetupStep.tsx` | Seven persisted steps, previous-month hours for all three sports, five race types, run time/pace alternative, monitor and timezone confirmation, discipline-specific setup, version-aware resume. |
| `mobile/src/screens/ZoneProfileScreen.tsx`, `CalibrationScreen.tsx` | Active/pending/prior values and separate test, threshold and zone decisions; some legacy states remain readable. |
| `mobile/src/screens/CheckInScreen.tsx` | Structured context, blocked dates, fatigue, missed-training reasons, restrictions and external activities; optional extracted context needs confirmation. Keep it discoverable. |
| `mobile/src/screens/ProfileScreen.tsx`, `IntegrationsScreen.tsx`, `PioneerAccessScreen.tsx` | Profile editing, tests, Pioneer redemption and Polar connection/import actions already exist. Garmin runtime does not. |
| `mobile/src/theme/tokens.ts`, `FormField.tsx`, `DurationPicker.tsx`, `ScreenState.tsx`, `StatusPill.tsx`, `MotionPressable.tsx` | Warm canvas/forest identity already works. Many 900-weight labels, generous nested cards, repeated paragraphs, blur and large controls can be refined. |

### Source precedence

Follow [AGENTS.md](../../AGENTS.md), [mobile instructions](../../mobile/AGENTS.md), the [MVP roadmap](../implementation/mvp-roadmap.md), and the latest explicitly approved decisions. The roadmap contains historical phases; they do not reactivate superseded behavior. In particular, consult the [September selection decision](../requirements/joren-workout-selection-phase-2026-09-28.md), its final addendum, and [planning ruleset V2 record](../implementation/joren-planning-ruleset-v2.md) before any later implementation touching presentation of planning states. This document creates no physiological rule.

The [pre-UI stabilization audit](../implementation/pre-ui-beta-stabilization.md) and [V2 backlog](../implementation/ui-v2-backlog.md) ground the UX priorities. The [workout distribution decision](../requirements/workout-distribution-decision.md) remains separate: layout must not enforce a preferred session count, maximum duration, or one session per day.

The following physical Android gates remain open and unchanged: activity plus HR/RPE save; delayed-response retry; Month/Week; drag/drop behavior and performance; workout detail. This task neither executes nor closes them.

## 2. Visual direction: a personal endurance coach

Use warm paper-like backgrounds, forest-green actions, strong readable type, and restrained rounded surfaces. The screen should feel composed around a training decision. Athletic character comes from clear session numbers, orderly sequences, and confident spacing, not imagery, aggressive slogans, glowing gradients or decorative charts.

Use one dominant focus surface per screen, with flat supporting sections. Most of Week is warm canvas; today's session may use forest green with ivory text. Keep the main action equally legible when a warning takes precedence. Sport color appears in a small icon tile or leading marker, never as the entire screen theme. No photos, raster asset generation, new font download, glass panels, repeated heavy shadows, rings, points, streaks or social feed are needed.

At standard font size, the first viewport should answer what, when, how hard, and next action. Detailed execution instructions belong in workout detail; rationale and provenance remain available where useful. Mandatory protocol instructions, decision consequences, current blocking errors, and missing required inputs must not be hidden as optional help.

Dutch is the primary copy reference here; preserve the existing Dutch/English language preference and translate all new labels together. Use sentence case and direct verbs. Prefer “Bekijk training”, “Kies dagen”, “Controleer week”, “Zones bevestigen”. Avoid “deterministisch evalueren”, raw revision/status identifiers, repeated “Jij houdt de controle” banners and technical dates in normal content.

## 3. Information architecture

Propose three labeled bottom destinations: **Week**, **Kalender**, **Activiteiten**. Keep **Profiel** as a labeled avatar/header action on each root destination, with an equivalent accessible button. No Coach tab, separate Home tab, or persistent Choose tab.

| Destination | Owns | Does not duplicate |
| --- | --- | --- |
| Week | Current context, today's/next sessions, explicit next action, compact week progress and attention queue; entry to creation, selection, approval and check-in | No second complete seven-day schedule below the hero |
| Calendar | Canonical seven-day schedule and Month overview; detail and same-week moves for the active plan | No separate calendar hidden inside a second Planning tab |
| Activities | Recorded activity history, add activity, pending HR/RPE and supported correction/matching | Planned workouts remain Calendar's responsibility |
| Profile | Athlete data, training setup, connections, account, language, Pioneer | No second workout history or week editor |

Week's preview and Calendar serve different jobs: immediate action versus full date placement. Tapping “Bekijk week” opens the same week in Calendar. Week preview shows only today's sessions, or the next scheduled date if none today, plus compact totals. Multiple workouts on one date remain independently identifiable; date-only data provides no execution order. Say “Vandaag · 2 trainingen”, not “Eerst lopen, daarna zwemmen”. For a future date say “Volgende trainingsdag”; do not invent a start time.

Creation → selection → placement → pending review are task screens under Week. Calendar Week and Month are modes of one destination with one date anchor. An explicitly labeled proposal review may reuse the schedule component, but it is not merged into the approved calendar feed. Calendar's public response has workouts/rest days without per-plan approval metadata; use loaded plan/proposal context for pending review. If that context is absent, do not infer a pending or approved revision from a workout's `scheduled` status.

Preserve existing entry routes as compatibility paths during later migration. Authentication, onboarding upgrade/resume, `/tests` and `/calibration`, profile, zones, check-in, integrations, activities and Pioneer remain reachable. A back action returns to the actual origin and selected date/scroll context; direct entry without history falls back to Week. One task sheet at a time. Close a sheet before opening another destination, preserving the existing deferred-dismiss pattern.

## 4. Week / Home composition

Use this priority order for presentation, without creating a new domain readiness algorithm:

1. Week range and server-backed state (“Deze week · 28 sep–4 okt”, “Goedgekeurd”, “Voorstel”). Current-week default; clear previous/next and return-to-current controls.
2. A blocking prerequisite for the attempted action, if returned by existing state. Otherwise today's/next session is the dominant surface. Pending review is a compact attention row while an active week exists; if no active week exists it becomes the main action.
3. Today's sessions or the next training date; sport, name, duration or distance, supplied intensity and “Bekijk training”. Secondary siblings use compact rows.
4. Week progress: `completed` planned occurrences / non-cancelled planned occurrences, only with an identified active revision. Display literal counts, never a fitness/adherence score. Unmatched activities do not silently complete a planned workout. Pending RPE remains a separate count.
5. Attention rows: resume draft, pending approval, calibration/zone confirmation, saved activity needing feedback, check-in. Show known items, not guessed due dates. Keep all available through “Aandachtspunten” if more than two; display total count.
6. Supporting actions: “Bekijk week”, “Activiteit toevoegen”, “Volgende week voorbereiden”, and a compact race-goal link. Goal-achieved/maintenance action lives in the goal summary and retains explicit confirmation.

Never show a completed/selected count as evidence that the server's week-combination warning is resolved. Show “Week vraagt aandacht” alongside the relevant proposal. An approved empty/rest-only plan is a legitimate state: show supplied rest reason and supporting activity/check-in access. An empty unplanned date says “Geen training gepland”, not “Rust voorgeschreven”. An empty query result is not proof that the athlete has no plan if loading failed.

Total time must be qualified when any workout is distance-only: “Tijdsduur bekend: …” with distance-based swims separately. Do not add estimated swim time or combine meters and minutes into a training score. The existing public time-intensity breakdown may appear under “Weekdetails”, with its time basis stated; it is not private load or an 80/20 coaching verdict.

### Structural wireframe: active week

```text
Wombo                                  Profiel
Deze week                  < 28 sep–4 okt >
Goedgekeurd

[ Vandaag · supplied sport              ]
[ supplied workout name                 ]
[ supplied duration/distance · intensity ]
[ Bekijk training                       ]
Additional sessions today, if present

Deze week          [completed] / [planned] afgerond
Bekijk week >

Feedback nodig · [count]          Aanvullen >
Supporting actions

Week              Kalender             Activiteiten
```

Numbers and workout wording in design previews must come from clearly labeled public fixtures. This wireframe intentionally supplies no prescription.

## 5. Compact availability and week creation

Open a focused full-page task from Week. Header: “Wanneer kun je trainen?” and a locale-formatted Monday–Sunday range. Tapping the range opens a date/week chooser; selection still resolves to the existing Monday/date-only input. Retain typed date fallback without making ISO the main display.

Use a checkbox weekday selector with weekday, date and a check mark. At 392 dp width, 16 dp margins allow seven 48 dp targets with 4 dp gaps. Below that width use four then three wrapping cells, in Monday–Sunday reading order; at large font use a two-column or vertical list. Never shrink touch targets to keep seven columns. No horizontal scroll hiding Sunday.

The summary says “3 dagen beschikbaar”, never “3 trainingen”. Keep one short line visible: “Meerdere trainingen op één dag zijn mogelijk.” Selection is forest fill, ivory label, check mark and spoken checked state. The selector is not a workout-count control.

Place explicit “Gebruik dagen van vorige week” below the selector. Show what was reused when available; do not silently preselect or guess absent prior data. Existing defaults may be displayed as editable choices, never as confirmed facts. Preserve server validation and current defaults during presentation migration.

“Blessures en beperkingen” is an expandable summary, always visible with its current state; expand automatically when relevant input or an error exists. Existing voluntary bike/swim alternatives appear only in the applicable injury context. Never opt in on behalf of the athlete or claim they guarantee a safe plan. Preserve every baseline injury input and opt-in.

Bottom action: “Maak weekvoorstel” using the existing action and its actual returned draft/plan state. Disabled with “Kies minimaal één dag” when required. A selected single day is not rejected for aesthetic reasons. Any placement/spacing rejection remains authoritative. Keep content above keyboard and safe-area inset, and let the page scroll at large text sizes.

## 6. Proposal cards and selection

One current candidate, a compact accepted-count row, and visible **Overslaan / Kiezen** buttons. The candidate is authoritative; V2 does not browse unreturned alternatives or synthesize replacements. Use occurrence identity: repeated copies of the same template are legitimate distinct selections.

Card hierarchy: sport name/icon → source workout name → duration **or** distance plus supplied whole-session intensity → short source-purpose text → “Opbouw bekijken”. “Kalibratie” and zone-evidence contribution are distinct supplied signals; avoid a large CAL logo and repeated explanation.

The public model has no dedicated session-type or purpose field. Preserve the source name and brief existing filtered description; do not classify a workout from a guessed word match or invent a training benefit. A separate session-type line is shown only when explicitly conveyed by reviewed source content; otherwise omit it. Truncated text must be readable in full in detail. Do not ask an LLM to shorten prescriptions.

Expected RPE is supplied, but the baseline deliberately excludes RPE guidance from planning cards. V2 keeps the quick decision card free of an extra RPE line by default. Show supplied expected RPE in execution detail and relevant calibration/feedback context. Promoting it to every selection card is a product choice (D2), not required for this slice. Intensity remains the supplied whole-session bucket; segments may contain different targets.

| Visual state | Treatment and action |
| --- | --- |
| Candidate/alternative | Warm surface, plain border only where interactive grouping needs it; “Alternatief” in pending replacement context; details action available |
| Chosen locally, request in flight | Check outline plus “Keuze opslaan…”; lock repeated submission; do not increment confirmed count yet |
| Accepted in server draft | Check mark and “Gekozen”; compact occurrence row in “Gekozen trainingen”; not “Goedgekeurd” |
| Approved in active plan | “Gepland”/“Goedgekeurd” from plan context; ordinary execution card, no accept/pass controls |
| Unavailable | Short supplied reason and next step; disabled action with explanation; do not render missing candidates as selectable gray cards |
| Loading | One fixed-structure candidate skeleton; preserve accepted summary; avoid fake stacked cards and target counts |
| Failed/stale | Preserve last known selection; inline retry/refresh; restore candidate position and reconcile before another decision |

Swipe may remain as an optional shortcut: horizontal translation, no rotation/oversized stamps, quiet side labels “Overslaan”/“Kiezen”, and the same request lifecycle as buttons. Gesture thresholds and physiology are outside this design. Provide Undo only when `can_undo`, and “Overgeslagen opnieuw bekijken” only when applicable. Exhaustion explains those available actions; it is not successful completion.

Placement retains both automatic spread and explicit per-occurrence dates. Present automatic spread as primary, “Zelf dagen kiezen” as secondary disclosure. Manual placement lists occurrences once with a date chooser; dates allow multiple occurrences. Preserve undo/back to choosing, complete-layout validation, warnings, submit and pending review. Manual selection cannot accidentally approve the week.

For an existing pending plan, use one selected session plus “Alternatieven bekijken” in place of permanently open carousels for every slot. Preserve replace and conditional remove (`can_remove`), busy locking, updated revision and warnings. No arbitrary delete control on an active plan.

## 7. Week approval and state language

Separate review from collection: header “Controleer je week”, range, “Voorstel”, seven-day proposal schedule, supplied warnings, short public explanation, then “Week goedkeuren” and “Afwijzen”. The bottom action remains visible; it is not automatic, a swipe, or disguised as Next. “Later” returns without changing state. No extra confirmation dialog is necessary when the page already clearly states this consequence.

Use the latest proposal identity and revision. Refresh/stale recovery shows “Je week is gewijzigd. Bekijk de nieuwste versie voordat je bevestigt.” Never silently replay an approval against new content. Superseded/rejected/expired versions remain visibly inactive and cannot look ready to approve. New proposal preparation follows the existing operation.

Warnings that require athlete review are visible before approval; long background rationale can expand. The count “alle trainingen gekozen” is separate from “combinatie vraagt aandacht”. A rest-only proposal receives the same explicit approval semantics. Plan approval, test assignment approval, threshold confirmation, and zone confirmation remain different decisions.

## 8. Workout detail: the session sequence

Make detail a full-height reading surface with a visible back/close action and origin preservation. Avoid a small sheet containing another scrollable card stack. At the top: sport, source name, status/date where known, supplied duration or distance, whole-session intensity, expected RPE. Then an ordered sequence on one flat surface with a thin vertical rail and sequence markers. Text remains dominant; no waveform that implies invented power/pace.

| Source | Presentation rule |
| --- | --- |
| Workout `name`, `description` | Name in full; short description near header, longer description expandable without rewriting its meaning |
| Workout/segment `duration_minutes`, `distance_meters` | Duration when supplied; distance when duration absent; both may appear in detail if both supplied. Never calculate duration from CSS, pace, distance or assumed effort. |
| `segments[].sequence`, `name` | Source order and name; do not rename phases or insert warm-up/cool-down when absent |
| `instructions` | Source text with wrapping and preserved meaningful breaks. Execution instructions visible by default; no generated technique or safety advice. |
| `zone_target` | “Zone [value]”; no derived bpm/pace unless explicitly supplied for that execution context |
| `rpe_target`, then `protocol_target`, then `expected_rpe` | Preserve baseline target precedence after zone target. Show supplied range/value, not a guessed zone conversion. Additional supplied detail must be clearly labeled, never override the primary target. |
| `is_swim_technique` | Quiet “Techniek” label; instructions still own technique specifics |
| Repetitions, interval recovery, equipment | No dedicated fields in planned segments. Show only explicit source name/instruction text. No free-text parsing into invented repeat groups, additional rows or equipment checklist. |
| `rpe_zones` | Optional “RPE-uitleg” disclosure using supplied labels; do not substitute this for active physiological zones |

The visual sequence can read Warm-up → Main set → Recovery → Cool-down only when the source contains those segments. A repeat block stays in its source instruction unless a future approved structured field exists. No proportional bar heights: units differ and some durations are absent.

For distance-driven swims the hero is distance, the sequence is distance/targets/instructions, and duration is omitted. Missing segments show “Geen verdere opbouw beschikbaar” with supplied summary, not an empty execution plan disguised as complete. A cancelled or historical workout retains its supplied snapshot; never repaint targets from current zones.

This presentation support does not change candidate eligibility. The current planning-ruleset record excludes distance-only swims from new-plan target fitting where no approved planned-duration/load projection exists. V2 must display such source, historical or recorded data faithfully when supplied, but must not force those workouts into a new selection or invent duration to make them eligible.

Execution-critical text remains expanded. Optional description/rationale and RPE reference can collapse. Provide “Activiteit toevoegen” only where the existing activity flow can use a selected workout; this is logging, not starting a live tracker. V2 adds no GPS, stopwatch, interval player or completion mutation.

## 9. One calendar, two modes

**Week is primary:** seven vertically stacked day sections, Monday–Sunday, each with a small date column and naturally growing session rows. This is readable on Android and can hold zero, one or many workouts. Show all seven days, including distinct blank dates and supplied rest days. No fixed-height row, clipped last card, or seven narrow workout columns.

The active-plan move board and approved calendar should eventually use the same `WeekAgenda` presentation. Calendar range loading and planning mutation remain separate states. Historical weeks may be read-only; move affordances appear only when the existing active-plan context and same-week operation are available. No invented cross-week move, time scheduling or intra-day sequencing.

**Month is orientation:** a Monday-first 7-column grid, selected/today treatment, sport indicators and session count. Show all sessions for the selected date below, with full details links. Avoid tiny repeated workout titles inside date cells. At widths where 48 dp targets do not fit, use an accessible horizontal grid viewport with preserved target sizes and a visible “Dag kiezen” list alternative; never use overlapping hit areas. At large font, the list alternative is primary while Month navigation remains available. “Week” opens the selected date's week; “Vandaag” returns to today. Month is retained, not removed.

Pending review uses an explicitly labeled proposal mode backed by the known proposal, separate from approved range results. Week/Home links to that review when relevant. Do not overlay tentative workouts onto the approved calendar as if committed; a future combined overlay would need a product/contract decision. Use the same visual rows so athletes learn one schedule language.

In approved context: sport label + name, duration/distance, intensity, completed/cancelled state and detail action. In proposal context: a visible “Voorstel” label and applicable replace/remove controls. A rest day has the supplied reason; no motivational instruction is manufactured. Rest and workout records returned together must remain visible for review, not silently reconciled by the UI.

## 10. Drag and date moves

The dedicated handle remains. A 48 dp hit target holds a quiet grip icon and accessible “Verplaats [name]”. The card body opens detail and scrolls normally. Keep a visible “Verplaatsen” action for touch, switch and TalkBack users; date selection is functionally equivalent.

| Stage | Visual feedback | Integrity rule |
| --- | --- | --- |
| Pickup | Immediate 1.02 scale at most, small elevation, origin placeholder, optional single light haptic | No mutation on pickup; honor reduced motion |
| Hover | Target day border and label “Naar woensdag 30 sep”; visible placeholder within that day | Highlight means intended target, not physiologically valid |
| Known unavailable target | Unavailable symbol/text where already known; no green validity promise | No client spacing calculation or new restriction |
| Drop/checking | “Verplaatsing controleren…” on the occurrence; preserve committed origin identity | Existing complete-layout validation and exact active revision |
| Reviewable warning | One contextual panel with qualitative warning, Cancel and existing confirmation action | Confirmation cannot override a server conflict |
| Server rejection/stale | Smooth 160–200 ms return, inline explanation at origin, date picker remains accessible | No committed visual move; refresh on stale state |
| Success | Place at returned date, quiet confirmation and spoken announcement | Only authoritative successful result changes schedule |
| Cancel/interruption | Return to origin and restore focus | No request if no change; no lost workout |

No cross-month drag, artificial spacing gaps, new target-date constraints or autonomous rearrangement. Long weeks must remain usable by date picker even when drag scrolling is difficult. Exact gesture hit testing and performance need later physical-device verification; this design does not claim to resolve that gate.

## 11. Zones, calibration and tests

Use a three-sport overview with independent statuses; selecting a sport opens its values and next action. Do not imply the entire athlete is confirmed when only one sport is ready.

| Sport | Primary numeric representation, only if supplied and visible |
| --- | --- |
| Run | Pace in `m:ss min/km` and/or heart rate in bpm; distinct labeled sections for pace and HR boundaries; preserve supplied bound ordering and open endpoints |
| Bike | Heart-rate ranges in bpm and/or power ranges in W plus FTP where supplied; no speed-as-zone substitution |
| Swim | CSS/swim pace in explicit `sec/100 m` for this baseline, with distance-based protocol structure; clock-format `m:ss /100 m` can be a later formatting choice after decimal precision is specified |

RPE remains a distinct supplied guide, not a numeric HR/power/pace substitute. Numeric values hidden by `values_hidden`/visibility remain hidden, including accessibility labels. Never produce ranges from percentages or contemporary profiles. Open boundaries are “tot …” / “vanaf …”; null is not zero. Historical profiles carry date/version/source in a history disclosure and retain their original meaning.

| Athlete-facing state | Meaning and next action |
| --- | --- |
| Instellen nodig | Required setup absent; “Instellen” uses allowed routes |
| Kalibratie klaarzetten / uitvoeren | Setup/assignment exists but no qualifying result; show actual protocol/task status |
| Gekalibreerd · nog bevestigen | A qualifying returned result exists; not active zones and not a universal new backend state |
| Voorstel · bevestiging nodig | Pending threshold or zone proposal; name the exact decision and show supplied values |
| Bevestigd · actief | Active profile returned; display source date, pending replacement separately if present |
| Meer gegevens nodig / historisch | Incomplete or legacy evidence; preserve actual state and reason; do not promise automatic Week-2 evaluation |

“Calibrated” and “confirmed” must never be synonyms. Render status from the actual evaluation, decision and profile fields, not from a local linear wizard approximation.

Setup routes: known values, supported field test, or current submaximal calibration. Keep source selection, guidance choices, optional entered five-zone boundaries and swim pool length. Do not offer a new RPE-only route. Protocol execution opens directly to instructions and feedback, with the existing **“Stop if you feel pain”** warning visible before instructions. Preserve every required observation, including mandatory-block HR for applicable run/bike protocols, swim repetition/rest measurements where requested, session/block RPE, completion/interruption and quality fields. Optional blocks remain explicitly optional; do not require warm-up HR if the existing protocol does not.

Result review preserves threshold confirmation then separate pending-zone confirmation. Test scheduling preserves standalone/in-plan capability flags and separate approvals. Integrated CSS remains unavailable where unsupported. Calibration is never inferred from a normal activity save.

## 12. Activity and HR/RPE continuity

Activities opens a history list and an attention row, rather than the full registration form above history. “Activiteit toevoegen” enters one page. Planned selection uses a searchable/scrollable existing-choice surface with a persistent “Extra training” option and supported external activities. Searching is local presentation of loaded choices, not a new search API. Selected sport and editable planned measurements are suggestions, never labeled as sensor observations.

Show actual local start date/time and confirmed timezone, duration and optional whole-meter distance. Preserve the existing timestamp and athlete timezone semantics; calendar dates and activity instants are not interchangeable. Missing confirmed timezone routes to existing setup. Swim may be saved with measured distance and no duration. No fabricated elapsed time or unobserved zone minutes.

Saving leads within the same task surface to the stored activity's HR/RPE form. No modal stack, second create, or concurrent feedback copies. Header: “Activiteit opgeslagen · gevoel toevoegen” only once create is confirmed. HR field explains that it is the measured session average; RPE asks how this session felt. Manual HR remains supported without linking a provider. Preserve optional HR in ordinary feedback and mandatory protocol HR where required; do not globalize one rule to all screens.

Use all ten existing discipline-specific textual RPE choices, unchanged, as vertical radio-like action rows. No unlabeled number slider, emoji scale, or five-category replacement. The baseline saves on RPE tap: retain that interaction and say “Kies je gevoel om op te slaan” before the choices. Enter HR before choosing RPE. A future select-then-Save variant is a separate interaction decision (D3); it must not silently appear in this preservation slice.

| State | Presentation and allowed next step |
| --- | --- |
| Editing | Inputs with persistent labels; no success state |
| Create in flight | “Activiteit opslaan…”; repeated save locked; retain entered values and logical submission identity |
| Create acknowledged, refresh failed | “Activiteit opgeslagen. Gegevens opnieuw laden.”; refresh existing activity, do not create another |
| Outcome unknown/delayed | “Opslaan nog niet bevestigd. Controleer de status.”; existing reconcile/retry flow, same submission; do not claim failure or offer a fresh duplicate |
| Awaiting RPE | One saved-activity summary, HR field and exact textual choices; next create remains blocked as in baseline |
| Feedback in flight | Selected row “Gevoel opslaan…” and input lock; same activity identity |
| Feedback retry/already stored | Refresh/reconcile existing state; show returned stored value if complete; no extra evaluation or success assumption |
| Complete | Quiet check, “Opgeslagen”, returned qualitative result and Back to Week/Activities |
| Correctable current-week feedback | “Gevoel corrigeren” opens supported correction; retain eligibility and stale-safe checks |

Unmatched imported activities require explicit confirmation of a suggested planned match before the supported operation; never auto-match. A correction proposal links to review only when accessible through existing state, and remains pending. Qualitative results (“Herstelsignaal”, “Zwaarder dan gepland”) do not become a diagnosis or automatic zone change.

## 13. Goal and onboarding principles

Goal setup is a race task, not a menu of unsupported fitness aspirations. Keep run, bike, swim, triathlon and duathlon, required race name/date/distances/total target time, optional split times and focus. Place the locked personal-goal capability in a quiet “Komt later” disclosure, without an editable form or implied availability date.

For run only, label a two-choice control **“Beschrijf je doel met: Eindtijd / Tempo”** and explain once “Twee manieren om hetzelfde doel in te vullen.” Show only one editable target representation. Pace uses min:sec per km. Preserve the existing conversion to total target seconds using entered distance and existing rounding. Show the converted total as a read-only preview in pace mode. Changing distance updates that preview; do not add a second independently editable goal. Preserve entered values when switching in the same form; the selected mode is the submission source. Do not promise persistence of preferred input mode, since the contract stores total time.

For multi-sport races, show one distance row per required discipline and optional time disclosure, plus total finish time. Do not split duathlon into invented repeated legs, require all split times, allocate a remainder to transitions, or infer missing splits. Preserve the existing check that supplied component times do not exceed total; any new transition model or allocation is a product decision.

Onboarding keeps all seven server steps and checkpoints. Visually group them into “Jij” (profile, monitor, timezone), “Training” (history, goal, zones), “Controle” (review), with a compact truthful current-step label and progress disclosure. Grouping does not batch writes, skip confirmations, reorder server steps, or claim a fixed time to finish.

Retain optional names, required birth/resting-HR data as defined by existing readiness, explicit monitor prerequisite, confirmed timezone with device suggestion/manual fallback, previous-month average hours/week for swim/bike/run (explicit zero distinct from blank), required race and discipline setup, and separate zone approvals. Do not resurrect weight, height, experience or historical two-month frequency collection. No default invented physiological inputs. Resume and upgrades show only server-required missing work and preserve existing completion/version semantics. Completion opens Week directly, without a celebratory interstitial.

## 14. Profile and connections

Use grouped flat rows: **Athlete profile**, **Training setup**, **Connections**, **Account**, **App**. Profile summary opens existing editable fields; setup links to goal/history/zones/tests and confirmed operational settings through their supported flows. Language uses the existing preference. Sign out moves to Account rather than appearing on every task header. Pioneer access remains under Account, with existing redeem/active states.

Connections contains the existing Polar provider page: connect/reconnect, returned status, last import when present, 7/14/30-day import choice, import progress/failure and allowed retry, refresh, disconnect with its existing retained-data explanation, and imported activities. No fabricated live-sync guarantee or missing timestamps.

Reserve a provider-row pattern for future Garmin. The specification does not expose a functioning Garmin button, invent authorization permissions, promise imports, or edit the preserved Garmin design document. A public “Coming later” row is optional product communication; default to no public Garmin row until approved. Account recovery, deletion, notifications, subscription and security settings without existing flows are not fabricated to fill sections.

## 15. Error, empty and loading language

Feedback belongs nearest the affected object. Use destructive red for failed/invalid actions, amber for reviewable attention, neutral status for waiting, and green only for confirmed success. Keep ordinary app navigation usable while one region loads. No raw HTTP codes, rule IDs, revision IDs, internal errors, private load or TSS in screens, accessibility, toasts, logs or analytics.

| Condition | Example athlete copy | Action / constraint |
| --- | --- | --- |
| Week combination warning | “Deze week vraagt aandacht. Controleer de gekozen combinatie.” | Review supplied warning; never claim swipes/count are incomplete |
| Availability conflict | “Deze datum valt buiten je beschikbare dagen.” | Choose date / return to supported availability flow |
| Spacing rejection | “Deze verplaatsing kan niet. Kies een andere dag.” | Show approved qualitative reason; no new hour calculations |
| Stale proposal | “Je week is gewijzigd. Bekijk de nieuwste versie.” | Refresh and review; no silent reapproval |
| Calibration incomplete | “Er ontbreken gegevens voor dit resultaat.” | Name supplied missing observation; retain recorded data |
| No candidate | “Geen nieuwe keuzes beschikbaar.” | Undo/reset passed only if allowed |
| No approved plan | “Je week staat nog niet klaar.” | Resume known draft/review, else create |
| No recorded activity | “Nog geen activiteiten.” | Add activity; no ghost chart |
| Calendar load failed | “Deze periode kon niet worden geladen.” | Retry this range; never show failure as an empty week |
| Ambiguous save | “Opslaan nog niet bevestigd.” | Reconcile/retry existing operation |
| Unknown error | “Dit lukte niet. Probeer opnieuw.” | Preserve context; only safe public detail; no stack trace |

Copy is a presentation proposal; preserve supplied error severity and available actions. Do not hide blockers in collapsed help. Validation is shown after interaction/submission, with a summary linking to the first invalid field for long forms. A successful mutation plus failed refresh must be distinguished from a failed mutation.

First load uses static skeletons matching the real layout; refresh retains clearly identified last-known content, with actions gated by existing validity rules. Avoid full-page spinner replacement except authentication/resume where content cannot yet be trusted. Announce status once, not every render. No indefinite reassuring animation when an error has occurred.

## 16. Accessibility, motion and Android performance

Concrete dimensions, contrast pairs, controls and motion timings are defined in [Tokens](WOMBO_UI_V2_TOKENS.md). Minimum interaction target is 48 × 48 dp, with actual nonoverlapping layout space. Text scales; rows grow; no fixed-height cards or hidden final lines. At 200% text, labels wrap and action bars become stacked/in-flow where necessary. Support TalkBack order, checked/selected/busy/disabled states, focus restoration and meaningful units. Swipe and drag always have explicit button equivalents.

Motion explains object movement and acknowledgment, never server truth. Keep transitions short and interruptible, one focused animation at a time, no perpetual shimmer, parallax, spinning statistics or confetti. Reduced motion replaces spatial transitions with immediate state changes or brief opacity. Haptics are optional and never the only feedback.

Use one scrolling owner per screen. Calendar has seven natural-height day sections or one bounded Month grid plus selected-day detail; it must not render two full calendars. Activity history remains virtualized. Do not mount every alternative carousel or all historical zone profiles at once. Long instructions remain readable without numerous elevated wrappers. No blur-dependent bottom bar; one drag shadow or sheet elevation is enough. Date-range loading preserves latest-request protection. Public result data can be formatted, but no client physiological calculations are introduced.

Later performance review must measure a mid-range physical Android device: pickup response, scroll/drag frames, large-font layout, Month↔Week rapid navigation, network loading isolation and no content clipping. These are future verification gates, not claimed outcomes.

## 17. Reversible V1 → V2 migration

Future presentation modules may map to the requested boundary:

| Proposed location | Responsibility |
| --- | --- |
| `mobile/src/ui-v2/tokens/` | Semantic colors, typography, dimensions and states |
| `mobile/src/ui-v2/primitives/` | Text, button, icon, field, surface, sheet frame |
| `mobile/src/ui-v2/components/` | WeekContext, NextSession, WorkoutSummary, SessionSequence, WeekAgenda, AvailabilityDays, AttentionRow, RpeChoices, ZoneTable, SaveStatus |
| `mobile/src/ui-v2/screens/` | Presentational compositions from the screen map |
| `mobile/src/ui-v2/motion/` | Restrained transitions and reduced-motion policy |

Do not build these directories now. Shared business/domain hooks and API clients remain authoritative; do not copy mutation logic into a second V2 implementation. The UI-version choice must be reversible without a database migration, new physiological version, loss of pending work or duplicate submission. Never mount both versions' mutating effects at once. Switching UI must not reset draft occurrence identity, proposal revision, activity retry identity or onboarding state. If the future boundary cannot preserve an in-flight task, complete/reconcile it before changing presentation.

| Order | Slice and rationale | Acceptance gate |
| --- | --- | --- |
| 1 — first V2 slice | Tokens, WorkoutSummary and full-height WorkoutDetail at existing Week/Calendar entry points. High value, mostly read-only, no route change. | Exact source fidelity, distance-only swims, mixed segments, absent fields, TalkBack/large text, origin return, no private values; original physical detail gate still open until exercised |
| 2 — second slice | Week/Home hierarchy and read-only Calendar Week/Month presentation inside the existing navigation. Use shared summary/agenda, keep move logic isolated. | No duplicate full schedules, seven days/multiple sessions/rest, state provenance, latest range wins, public totals truthful |
| 3 | Navigation shell, Profile/Connections organization and reachability. | Auth/onboarding gate, compatibility paths, back restoration, all existing actions including Pioneer/tests/check-in reachable |
| 4 | Availability, selection, manual/automatic placement, pending editing and approval; then move affordances. | Accept/pass/undo/reset, repeated occurrences, warnings, stale approval, conditional removal, same-week server rejection and rollback preserved |
| 5 | Activities and HR/RPE continuity, supported corrections and matching. | Create/refresh/feedback partial success, delayed response and retry, no duplicate writes or lost pending feedback; physical gate required |
| 6 — last | Goal/onboarding forms, zone setup, calibration execution/results, test scheduling and structured check-in. | All required fields, legacy/versioned resume, current/previous profiles and distinct approvals preserved |

Highest regression risks: activity create-plus-feedback recovery; proposal/revision transitions; drag and pending-warning confirmation; calibration/test/zone approvals; onboarding upgrade/resume and separate writes; calendar request races. Visual changes alone cannot close those risks.

For later implementation, run strict TypeScript and applicable mobile interaction/navigation/privacy tests for each slice. Cross-stack, OpenAPI, backend, mypy/Ruff and database/RLS checks become required if those layers are separately authorized and touched. Do not weaken tests to match an unapproved interaction or reinterpret old records. This documentation-only task calls for document/source consistency, links, contrast arithmetic and diff scope checks, not runtime suite claims.

## 18. Product decisions and design risks

| ID | Decision or unresolved boundary | Safe design default |
| --- | --- | --- |
| D1 | Final endorsement of three bottom destinations and secondary Profile | This is the recommended navigation proposal; retain existing routes until a later approved navigation slice |
| D2 | Whether expected RPE should be promoted onto quick selection cards despite current deliberate suppression | Keep it in workout detail/calibration context; no change to physiological meaning |
| D3 | Whether RPE choice should select then require Save, rather than existing tap-to-save | Preserve tap-to-save with explicit copy; no new API/confirmation semantics |
| D4 | Session frequency, historical-frequency input, maximum session length or distribution preference | Use returned count/composition; no new cap, one-per-day implication or training allocation |
| D5 | Multi-discipline pace inputs, triathlon transitions, duathlon legs or missing split allocation | Existing distances, optional split times, total time only |
| D6 | Rich structured repeats/recoveries, equipment or session-type taxonomy absent from current snapshots | Render explicit source text, omit unsupported structure; any contract expansion is separate work |
| D7 | A combined pending/approved calendar overlay across arbitrary periods | Separate proposal review from approved Calendar; no inferred provenance |
| D8 | New password recovery/security/account controls, Garmin visibility/runtime, new preference persistence | Expose existing capabilities only; reserve extensible row patterns |
| D9 | Historical RPE-only/Week-2 wording or ongoing automated zone improvement | Show truthful historical state and current server-required setup; no future promise or reactivation |

These decisions do not block creating this design specification. They block only the specific later behavior that exceeds the stated defaults. Existing physiological review, provider and release gates remain outside UI design.

Main UX risks and mitigations:

- Progressive disclosure can hide important conditions: expose blocker/warning titles, affected object and actionable consequence; collapse only supporting explanation.
- A strong Today card can obscure a second session: show same-date count and sibling rows; do not create a false execution order.
- Chosen versus approved can be confused: use different literal labels and keep explicit review/approval.
- Calendar unification can lose move capability or pending provenance: share visual components while preserving source-specific actions and context.
- Compact weekday/month controls can become inaccessible: use responsive wrapping/list alternatives and real 48 dp targets.
- Fewer paragraphs can make immediate RPE saving surprising: retain the explicit save-on-choice instruction and visible save status.
- A progress count can imply coaching compliance: label it as recorded planned-session completion only; keep unmatched activities and feedback separate.
- Legacy state labels can promise unsupported automatic evaluation: identify historical data and use existing setup/review paths.

## 19. Design acceptance checklist

- Every major screen has purpose, information, action, hierarchy, components, disclosure, states and accessibility in the companion screen map.
- A first-time athlete can distinguish setup, choosing, pending approval and active training without reading technical metadata.
- Every existing baseline operation has a destination; no runtime capability is removed by consolidating views.
- All examples derive from public source fields or are explicit structural placeholders; no invented prescriptions, start times, zone bounds or swim durations.
- Pending state, server validation, revision preconditions, idempotency and separate confirmations remain intact.
- No private-load metric appears in athlete-facing designs, including hidden accessible text.
- Design tokens are specific; relevant contrast pairs are checked mathematically, with device rendering still a future gate.
- All changes in this task are the three new Markdown documents. No application, backend, route, API, package, deployment or preserved work is modified.

### Documentation verification record

On 2026-10-02, local checks passed for relative document links, trailing whitespace, balanced code fences, and the nine required handoff dimensions across all 19 screen specifications. The documented contrast pairs were calculated from the proposed sRGB colors and meet their stated text/control thresholds. Git status retained the same pre-existing modified/untracked work, with only these three design documents added by this task. No runtime suites, emulator, physical device, hosted API or deployment checks were run; this record establishes document consistency only.
