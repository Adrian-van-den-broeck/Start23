# Wombo UI V2 Slice 3A: read-only Calendar

Date: 2026-10-05. Visual status: **PROVISIONAL FUNCTIONAL SCAFFOLD**.
Week, Month and selected-date details are implemented and functionally verified.
The presentation is a readable reference for later user mockups, not final art
direction. Slice 2C's former visual acceptance gate did not block this work.

## Provenance and scope

- Exact clean starting SHA: `43a365b91ceaab2fc030e1ab2bd04f61bcf0964c`.
- Before editing, reran the prerequisite: **231 tests / 41 suites passed**,
  strict TypeScript and unused-code passed; recursive privacy was included.
- Branch: `feat/wombo-ui-v2-calendar-readonly`, created from that exact SHA.
- Reused worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-ui-v2-week`.
- Shared-state commit: `7ed9995`.
- Final runtime implementation SHA: `7ec453276f715b2062fa752125d496816755df76`.
- Final delivery SHA is the documentation commit containing this report:
  `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_3A_REPORT.md`.
- Read root/mobile AGENTS, current MVP roadmap, V2 spec, screen map,
  implementation plan, architecture and Slice 2A/2B reports. Their information
  architecture informed the scaffold; the user's latest functional strategy
  controls presentation scope. No additional Astra design pass was requested.

Only mobile Calendar presentation, its shared navigation seam, loaded-range
metadata, localized copy and regression tests changed. Package/lockfile changes:
**NONE**. Backend/API/DTO/database/schema changes: **NONE**. Planning mutation
controller, routes, native configuration, accepted detail implementation and
V1 styles/pending editor/draft presentation remain unchanged. No drag handles,
move components, rescheduling, timeline, start time, bottom tabs or new dependency.

## One Calendar owner and shared context

`mobile/src/features/calendar/useCalendarController.ts` remains the sole
Calendar read owner, instantiated once by the existing PlanningOwner in
PlanningFlowProvider. It owns workouts, rest days, loading and request sequence,
and uses its existing shared safe-error callback. The only state addition is the
successful response's `from_date` / exclusive `to_date` provenance, committed
inside the existing latest-request guard. No second error/request state or client.

One active-range effect in PlanningBoundary is above both presentations.
CalendarScreen, WeekAgenda, DayHeader, MonthGrid and calendarViewModel contain no
API call or fetch effect. `useCalendarNavigation` owns only mode, anchor and
selection. V1 TrainingCalendar consumes this same controlled navigation; its
standalone compatibility wrapper is not mounted by the Planning host and owns
no API client/controller. The pre-existing Activities calendar lookup is outside
this flow and was not changed. Source audit, boundary tests and native owner
inspection confirm a single mounted PlanningOwner and mutually exclusive views.

Calendar loading remains independent of planning mutation busy. Opening/ranging
Calendar sets calendarLoading only. Existing provider coverage explicitly runs
a pending planning mutation and overlapping Calendar reads, showing that each
completion changes only its own loading state. No planning mutation code changed.

The implementation registry is exactly `workoutDetail`, `week`, `calendar`.
Activities, planning tasks, Profile, onboarding, zones/calibration and other
unimplemented slices continue to V1. Non-development forced-V1 behavior remains
unchanged and is tested explicitly for Calendar.

## Week and Month behavior

| Surface/state | Implemented behavior and evidence |
| --- | --- |
| Week | Full Monday-Sunday range and seven natural-height date sections; Sunday and multiple independent occurrences remain reachable. |
| Workouts | Sport, exact supplied source name, supplied duration/distance, intensity and status, filtered source description and individual detail action. Returned order and occurrence IDs are retained; no scheduled-status proposal inference. |
| Empty/rest | Successfully empty dates say no workout planned. Returned rest records show their supplied reason. Rest-only and rest plus workout are distinct; all returned rest records survive the adapter. |
| Month | Monday-first 28/35/42-cell orientation grid, adjacent-month dates, count, sport/rest markers, selected state and separate visible/accessibility Today state. Full workout names belong in the selected-date list. |
| Selection | Full-date heading, readable workout/rest list below grid, and selected-date-to-Week action. Selecting a loaded date causes no read. |
| Navigation | Previous/next week or month; Today uses the existing local date convention. Month-to-Week anchors the selected date, including adjacent-month dates. Month movement uses the first of the target month, avoiding January-31 skips. |
| Responsive | When seven >=48 dp targets do not fit, or fontScale exceeds 1.2, a full-width accessible natural-height date list becomes primary. No overlapping hit slop or compressed targets. |
| Initial loading/error | Explicit loading, unknown-range copy, safe error and retry; unknown dates never masquerade as successful empty dates. |
| Retained range | Failed/delayed new ranges retain the successful response and its actual date provenance; clearly labelled last-loaded records are separate from unknown requested dates. No old workouts relabelled onto new dates. |

Thin pure adapters allowlist public fields, group exact date strings, retain
source order and calculate calendar cells. They infer no training meaning,
recovery, duration, private load, validity or rest prescription. Date-only parsing
uses local noon and existing addDays/isoDate helpers, preserving local dates,
Monday-Sunday weeks, DST/month/year boundaries, locale formatting and exclusive
API ends. No plan date is parsed through UTC.

Existing V2 Text, Button, Divider, SportIndicator and tokens supply provisional
structure. Button's optional accessibility role enables exclusive mode tabs
without changing its existing default role or duplicate-press protection.

## Races, detail and fallback

Focused tests explicitly issue A then B and complete A last. Latest B remains
displayed for both old success and old failure. An old finally cannot clear
current loading; latest failure retains last successful records/range. Existing
provider coverage also preserves newer failure against late old success.
Rerender adds no read; rapid Week/Month integration tests retain the latest range.

Calendar resolves a selected ID against the exact loaded calendarWorkouts array
and passes that existing object to the accepted WorkoutDetailBoundary. No detail
implementation or detail fetch was added. The Calendar remains mounted beneath
the modal. Mode/anchor/selected date live above V1/V2 and detail; scroll positions
are retained per presentation/mode/range. Origin remains the original Week/V1
Planning entry during detail comparisons and safe Calendar switching.

Integration tests cover Week and Month detail, Android modal Back, V1/V2 detail
comparison, Calendar comparison, exact object identity, range/date/scroll return,
zero extra reads and zero mutations. A separate test covers Calendar entered
from V1, compared as V2, then returned to its V1 origin. Only one Calendar view
mounts at a time; neither comparison nor detail remounts its range owner.

## Software verification

| Gate | Exact result |
| --- | --- |
| Focused Calendar/planning/Week/detail/privacy | **119 tests / 16 suites passed** |
| Full mobile | **259 tests / 45 suites passed**, zero snapshots |
| New test count | **28 new tests**, four new suites, relative to 231 / 41 prerequisite |
| Strict TypeScript | `npm run typecheck` passed |
| Unused-code | `npm run check:unused` passed |
| Privacy | Recursive source privacy, public-adapter poison fields and archived rendered/accessibility/public-response scans passed |
| Formatting/diff | Installed TypeScript formatter on changed/new source; unrelated V1 formatting restored; `git diff --check` passed |
| Protected scope | Planning controller/API/DTO/backend/database/packages unchanged; V1 style block/editor/draft presentation byte parity verified |

Week coverage includes seven dates/Sunday, zero/one/multiple sessions, source
identity, rest-only, rest plus workout, statuses and exact detail callbacks.
Month coverage includes Monday alignment, boundaries, adjacent cells, Today,
selection, counts, selected empty/populated lists and narrow/large-font fallback.
Planning-controller, warning, provider, Week refinement, V1/V2 Detail and
transport regressions also passed in the full suite. Superseded registry and
Calendar-entry descriptions were updated for the now implemented Calendar;
existing mutation assertions were retained. No skipped or weakened tests.

Evidence: ignored `mobile/.runtime/slice3a/` contains prerequisite/full/focused
Jest JSON/logs, typecheck/unused logs, software-verification.json and
emulator-verification.json. No backend suite rerun was needed for this purely
mobile read-only slice.

## Authenticated Android verification

Reused `emulator-5554`, API 35, `com.adrivdbs.wombo`. Verified existing Metro
8082's manifest projectRoot points to this worktree's mobile directory. No
emulator startup, native rebuild or reinstall. Native computer-use pipe remained
unavailable after retry/reinitialization; the existing ADB UI helper used fresh
UI trees and observed bounds, normal taps, scroll and Back.

Staging API: `https://r6-api-r6-staging.up.railway.app`; Supabase start23-dev:
`https://isfumhgqphieoayqahjv.supabase.co`. Normal Auth sign-in and supported
onboarding/calibration/zone confirmation calls prepared the owned athlete.
Existing UI creation/selection/automatic placement/submission/explicit approval
produced two genuine run occurrences on Sunday 2026-10-18 and six supplied
planned-rest dates. Calendar data was approved authoritative range data.

Verified V2 Week -> View week -> Calendar Week; all seven days, Sunday, both
workouts and supplied rest; Calendar Month; select Sunday; real workout detail;
Android Back/Close to Calendar; rapid mode changes; next/previous month; Today;
selected-date-to-Week; safe Calendar V1/V2 comparison. Plain presentation was
readable, no control overlap, all content reachable by normal scrolling.

Native Week detail returned at **725.4545288085938 dp**, same week/date/range.
Native Month detail returned at **432 dp**, same October mode, selected
2026-10-18 and `2026-09-28` through exclusive `2026-11-02` range. Native owner
snapshots show one PlanningOwner. Week detail and Calendar V1/V2 comparison
recorded **zero extra API reads**; Month detail also had no intervening read.
After Calendar entry all observed application requests were GETs; no moves or
other mutation was issued by Calendar. Unique request IDs prevent duplicated
CDP events from inflating counts.

Some CDP response bodies were unavailable; request method/path/status evidence
remained available. A separate supported authenticated Calendar GET archived
the public response for privacy/source comparison. No credentials, headers,
Auth responses or tokens were recorded by the network observer.

All 35 normal Month date targets measured >=48 dp in the archived native tree.
At **320 dp** width and separately **200%** system text, Month used the date-list
fallback. Its last adjacent-month date and selected rest/details/action remained
reachable; controls wrapped without overlapping. Android's font configuration
restart returned through normal saved-plan restoration; cross-OS-restart Calendar
transient context is not claimed. Original **1080x2280 / density 440 / font 1.0**
was restored, and normal app sign-out settled to AuthProvider sessionPresent=false.

Accessibility fundamentals: full localized date/count/sport/rest/Today labels,
selected state, exclusive Week/Month roles, heading order, full source names,
spoken supplied measures, natural text growth and >=48 dp targets. Physical
TalkBack, focus-return/device acceptance and other release gates remain open.
No physical TalkBack acceptance or final visual acceptance is claimed.

## Functional reference screenshots and fixture cleanup

**19 PNGs** with fresh companion XML under ignored `mobile/.runtime/slice3a/`:

- `week-home.png`, `week-mode.png` (includes real rest dates),
  `week-sunday-multiple.png`, `week-sunday-second-reachable.png`.
- `week-detail-open.png`, `week-detail-returned.png`.
- `month-mode.png`, `month-selected-details.png`, `month-selected-empty.png`,
  `month-detail-open.png`, `month-detail-returned.png`.
- `next-month.png`, `today-week-empty.png`, `calendar-v2-return.png`.
- `month-narrow-list.png`, `month-large-text.png`,
  `month-large-text-list-end.png`, `month-large-text-selected-rest.png`.
- `final-signedout.png`.

These are **FUNCTIONAL REFERENCE SCREENSHOTS**, suitable for later mockups.
Rest plus workout is covered by supplied test fixtures; it was not fabricated
in staging. Literal replacement characters in some catalog names remain intact.

Two sequential owned disposable athletes were created and deleted. The first
used the original one-athlete authorization. A wrong optional diagnostic route
in the ignored helper returned 404 and triggered guarded cleanup before Calendar
verification. The user was told exactly what happened and explicitly authorized
**one replacement athlete**; no replacement was created before that reply. The
helper was corrected so optional snapshot failure does not terminate review.

For **each** actor: one creation, one deletion, global session revocation,
ownership-checked purpose/identity, admin GET **404**, zero matching own users.
Proof: `first-slice3a-authenticated-cleanup.json` and
`slice3a-authenticated-cleanup.json`; actor markers contain no credentials.
Generated credentials stayed temporary in helper memory and were discarded.
No session injection, direct domain-row writes or real-user access/modification.
The final app is signed out; helpers/observer are stopped.

Main remains `fb56c51d983564c652d83fc15e02b039e9063d3f`, untouched/unpushed.
Slice 2C branch remains at its exact prerequisite SHA; integration remains
`7a7259125d2a6a907cf9c175379ae6570aabf71b`. Original dirty checkout and unrelated
coach/Garmin/privacy/PDF/deployment work were untouched. No push, merge,
deployment or production access. Physical release gates remain open.

WOMBO UI V2 SLICE 3A COMPLETE — FUNCTIONAL CALENDAR SCAFFOLD ACCEPTED
