# Wombo UI V2 Slice 2C — Week / Home visual refinement

Date: 2026-10-05. Presentation implementation and software verification complete. Native component-fixture comparison improved the approved hierarchy. Final authenticated emulator visual acceptance is pending; local integration has **not** been promoted.

## Prerequisite, source and branch

The final acceptance section of [Slice 2B](WOMBO_UI_V2_SLICE_2B_REPORT.md) declares `WOMBO UI V2 SLICE 2B COMPLETE — EMULATOR ACCEPTED, PHYSICAL DEVICE GATES REMAIN`. Its accepted branch/head was verified before edits. The previously reported auth problem had been resolved by that acceptance follow-up; no unresolved functional defect was carried into this slice. The accepted **190 tests / 36 suites** were rerun successfully before changes, including Slice 1 Workout Detail, controller, mapper and boundary regressions.

Root/mobile instructions, current MVP roadmap, [primary refinement contract](WOMBO_UI_V2_WEEK_VISUAL_REFINEMENT.md), V2 specification, screen map and tokens were read. The primary contract was supplied in the root checkout and copied byte-for-byte into this branch: SHA256 `B2F66F8848428953EB6D6B27795F72C7F804176F53CF02DD8D1620B9EB783F0B`. Its historical worktree-relative evidence links describe its original root-checkout location; this report links the archived reference directly.

| Item | Value |
| --- | --- |
| Accepted starting Slice 2B SHA | `7a7259125d2a6a907cf9c175379ae6570aabf71b` |
| Dedicated branch | `feat/wombo-ui-v2-week-refinement`, created from that exact SHA |
| Isolated worktree | `F:\Projecten Business\Start23\Code\.worktrees\wombo-ui-v2-week` |
| Final runtime/source SHA | `d96701fed3a61faa091e10ad0470ba8756dc5dbc` |
| Final delivery SHA | Report/evidence-only commit containing this file; resolve with `git log -1 --format=%H -- docs/ui/WOMBO_UI_V2_SLICE_2C_REPORT.md`. Exact SHA is also supplied in the delivery response. |
| Local integration | **Not promoted**: `feat/wombo-ui-v2` remains `7a7259125d2a6a907cf9c175379ae6570aabf71b` |
| Prior Week branch | `feat/wombo-ui-v2-week` remains at the accepted starting SHA |

Small local commits preserve previous history:

1. `c7683863e19c215480e864ebf4d4027e0f73d015` — Week presentation compositions and focused tests.
2. `791de438a6887247593fe36738e03e37ef360503` — Week hierarchy, bilingual copy, accessibility and regression coverage.
3. `d96701fed3a61faa091e10ad0470ba8756dc5dbc` — independently scoped shell reminder safe-area correction and tests.
4. Report/evidence commit — this report, unchanged primary contract and review evidence only.

## Visual changes and scope

The old composition separated brand, centered Profile, large repeated dates, status and CTA into unrelated bands. Supporting actions were centered; View week looked like another primary block; Goal and development controls competed with production content. Active sessions repeated oversized date/name/measure text and gave each sibling another card.

| Composition | Result |
| --- | --- |
| Header / WeekContext | Trailing labeled Profile with the existing callback, compact locale-aware range; clean stacked header at large text. Same displayed dates, full weekday/day/month/year accessible range; cross-month/year preserved. |
| New WeekTaskCard | Receives resolved presentation strings/action. One ivory radius-20 surface, 24 dp padding, related status/section-title/support and existing 52 dp CTA; no shadow, fixed height or state-selection logic. |
| NextSession | One forest focus with Today and actual count, or Next training day and supplied date/count inside. Section-title source name, one numeric supplied measure, subordinate second measure, existing effort/status/description. Short visible CTA retains full source name in its accessible label. |
| Same-day siblings | Flat separated rows, preserving every supplied field and independent exact occurrence action. Source order remains unchanged; no execution-order claim. |
| New QuickActionRow | One whole-row action with text/chevron, minimum 48 dp, existing disabled/busy semantics, natural wrapping and token focus outline. Used for View week, Profile and ordered tools; no nested chevron control. |
| New GoalSummaryRow | Muted Goal label and exact supplied name at card-title weight, natural wrapping, full accessible name and unchanged confirmation callback. Omitted without a name. |
| AttentionRow | Aligned fact/action, stacking at narrow width or large text. Amber only for an existing warning. Existing filtering, busy lock and show-more behavior retained. Task warnings sit directly below the task. |
| Development footer | Existing controls after production content, separator and 24 dp separation. No footer container/space in non-development rendering; fail-closed production V1 unchanged. |
| Copy / Button | Required NL/EN strings through LanguageProvider; singular workout/progress copy corrected. Button accepts an optional full accessible label with its previous default and press protection intact. No source catalog text correction. |

Existing Text/Card/Button/Divider/tokens are reused. Page gutter 16 dp, focus padding 24 dp, primary radius 12/minimum 52 dp and row minimum 48 dp are unchanged approved values. Related gaps use 4/8/12/16 dp; major groups and development separation use 24 dp. Goal flows after tools without a flexible bottom spacer. No arbitrary new colors, icon/font dependency, artwork, metric, progress percentage or new product capability was added.

## Emulator evidence and visual judgement

The existing `emulator-5554` / API 35 / `com.adrivdbs.wombo` development client was reused. Original viewport was **1080 × 2280 px**, density **440 dpi**, approximately **393 dp** wide, font scale **1.0**. Metro **8082** served this worktree's `mobile` project with the normal expo-router entry. Its existing process was restarted once on the same port with cache clear because route discovery did not recognize the temporary review host. No second emulator, additional Metro on another port, rebuild or reinstall was performed. The root checkout's unrelated server/work was left intact.

The actual app began signed out with Auth visible and requested UI **V2**. Registry/source and passing tests confirm effective **Week + Workout Detail V2**, Calendar/planning tasks **V1**, production **V1**. [Before UI state](evidence/slice2c/live-before-ui-state.json) and [restored UI state](evidence/slice2c/live-after-ui-state.json) contain only nonsecret observations. No live authenticated Week existed to capture before edits.

All new Week screenshots below are **native emulator component fixtures**, not live authenticated planning. The temporary local review route used the existing public typed test fixtures and unchanged `weekHomeViewModel`; production actions were no-ops, with no controller/provider or API mutations. Exact host input provenance is archived as [plain text](evidence/slice2c/fixture-host.tsx.txt). That route was removed before the final full suite and is absent from the deliverable runtime. Language was restored to NL, requested UI to V2, viewport/font to original values; normal Auth is visible again. The diagnostic Tools overlay was hidden using its existing developer-menu toggle for clean comparisons.

| Direct comparison | Before | After |
| --- | --- | --- |
| Historical accepted draft — actual live Slice 2B reference | [Accepted original](evidence/slice2c/slice2b-accepted-draft-reference.png) | [Refined draft fixture](evidence/slice2c/slice2c-after-clean-B.png) |
| Controlled draft — same native emulator, viewport, font, locale, public model and goal | [Accepted presentation fixture](evidence/slice2c/slice2c-before-clean-B.png) | [Refined presentation fixture](evidence/slice2c/slice2c-after-clean-B.png) |
| Controlled active today + two same-date sessions | [Accepted presentation fixture](evidence/slice2c/slice2c-before-clean-E.png) | [Refined presentation fixture](evidence/slice2c/slice2c-after-clean-E.png) |

For controlled BEFORE captures, only the four accepted Week presentation files were temporarily loaded from the exact starting commit and then byte-restored; the model/controller stayed unchanged. The controlled draft uses the reference's week range, neutral selection state and supplied goal text. It intentionally excludes shell reminder/diagnostic chrome so the composition comparison is consistent. The historical original includes both; it is not represented as a new controlled live capture.

The draft AFTER visibly groups status, heading, factual support and CTA into one object. Profile/date now occupy a compact header region; View week is a row; the four tools have common alignment/dividers; Goal follows without filler. At default text the task, View week and beginning of tools are visible before scrolling. The added factual task text makes the focus surface larger than the old isolated button; the improvement is hierarchy and distribution of space, not a claim that all content requires less total height. [Separate footer evidence](evidence/slice2c/slice2c-development-v2.png) proves controls remain reachable.

The active AFTER moves temporal context inside one forest hero, reduces source-name emphasis, isolates duration from distance and replaces the second card with a flat sibling. Literal progress remains immediately above View week; attention remains below focus/navigation. [Future-date fixture](evidence/slice2c/slice2c-after-clean-F.png) also shows accurate localized date and singular `1 workout`. These images visibly improve grouping and intention against the primary contract, but **do not close the actual authenticated shell/return acceptance gate**.

### State and width coverage

| State | Native fixture evidence | Component/behavior tests |
| --- | --- | --- |
| A — no plan | [A](evidence/slice2c/slice2c-after-clean-A.png) | Same prepare callback, single prepare entry, no fabricated session |
| B — draft / selection | [B](evidence/slice2c/slice2c-after-clean-B.png) | Existing draft action, factual copy, no draft metric |
| C — placement incomplete | [C](evidence/slice2c/slice2c-after-clean-C.png) | Same continuation action; placement remains V1 |
| D — pending | [D](evidence/slice2c/slice2c-after-clean-D.png) | Review action; supplied warning adjacent; pending itself neutral |
| E — active + today | [E](evidence/slice2c/slice2c-after-clean-E.png) | Same occurrence IDs/fields; one hero, independent flat sibling |
| F — active + next date | [F](evidence/slice2c/slice2c-after-clean-F.png) | Supplied date, singular count/progress |
| G — active + pending | [G](evidence/slice2c/slice2c-after-clean-G.png) | Active hero remains active; neutral review attention, warning separate |
| H — rest-only approved | [H](evidence/slice2c/slice2c-after-clean-H.png) | Existing rest and literal progress, no sample workout |

A–H composition tests run in **both NL and EN**. Loading/failed reads retain existing tests and visible handling; rejected/expired and no future session have preserved/new action and empty-message coverage. Active + draft + pending without a future session explicitly retains the model's draft priority. No state machine was added.

Native width/text captures cover six practical profiles, each with draft and active fixtures, long supplied goal/workout names, top and end-of-scroll PNG/XML: **320 dp NL 100%, 320 dp EN 200%, 360 dp NL 100%, 360 dp EN 200%, 412 dp EN 100%, 412 dp NL 200%**. This is not a claim of the full Cartesian matrix. See the [evidence index](evidence/slice2c/README.md) and [screenshot provenance](evidence/slice2c/screenshots.json).

At 200%, the full header/Profile, growing card/buttons and final goal/developer actions were checked. The native check exposed vertical title shrinking; the final layout stacks without wrapping/shrinking the column. Scrolling is necessary and accepted. End screenshots naturally contain partially scrolled-off rows at the viewport boundary. Both-locale cross-month/year formatting and full accessible ranges were checked by tests; these dates were not additionally captured natively. Attention stacking has focused width/font tests. Full TalkBack traversal and every intermediate long-workout/warning scroll position remain acceptance gates, rather than being inferred from top/end screenshots.

## Shell reminder ownership and open live gate

The global reminder is owned by `mobile/app/(authenticated)/_layout.tsx`, outside Week. The only runtime change there is a top-edge SafeAreaView around the existing reminder. Its list-activities effect, count/copy, haptic, destination `/activities` and state logic are unchanged. No Week RPE attention item was introduced; no inset container is rendered when the count is zero.

Three owner-level tests verify count 1/2, exact destination, one activities read across a visual rerender, and no wrapper for zero count. [Native reminder evidence](evidence/slice2c/slice2c-rpe-inset-fixture.png) uses the owning wrapper/styles and existing localized count-one text, showing text below system chrome. It is an **equivalent inset fixture with a no-op action**, not the real authenticated shell. Actual shell visibility/tap/return and combined insets remain open.

Automatic approval review rejected the existing staging acceptance helper **before execution**: it would create a hosted test account and perform onboarding, calibration and zone confirmation, without sufficiently explicit trusted authorization for those external mutations/destination. No actor was created and no hosted domain state changed. Component fixtures allowed the local work to finish without bypassing that rejection. To close the live gate, explicitly authorize one disposable **start23-dev** acceptance actor using the existing flow, followed by sign-out, global session revocation and deletion of that exact actor; or provide an already authorized existing staging session. No credentials are requested for this report.

## Functional, privacy and software verification

| Gate | Result / evidence |
| --- | --- |
| Shared controller / owner | **Zero diff** in all `src/features/planning`, planning screen, mapper/utils, ownership or boundary code. PlanningOwner remains the sole `usePlanningController` caller. |
| Action / state parity | Existing owner/controller/Week-boundary tests remain unchanged and pass. Main action, draft/candidate/occurrence IDs, proposal ID/revision, active revision, availability, placement, warnings, V1 task destinations, goal confirmation, Calendar fallback and Detail origin/scroll coverage retained. New presentation tests dispatch the same action/occurrence and Profile/Activities/Check-in/Zones/goal callbacks. |
| Duplicate effects | Existing tests prove one bootstrap/owner, no visual-rerender/bootstrap duplication, locked mutations, one Calendar range effect, no Detail-triggered refetch and no UI-version bootstrap. No controller changes. New shell test verifies no extra reminder read on visual rerender. Live call-count audit was not rerun. |
| V1 / Slice 1 | V1 screen/theme, Detail defaults/boundary, production registry and task/Calendar fallbacks have no diff; their existing regression suites pass. Native footer taps changed requested V1 then V2 with selected semantics, but this fixture does not mount the real V1 planning root. |
| Recursive privacy | Full-suite recursive source privacy test and existing mapper poison-field tests pass. No unknown API-response spread into component props, hidden values, source-name rewrite, log/analytics addition or privacy-sensitive accessibility label. Archived fixture XML also checked recursively. |
| Focused new/presentation checks | Latest focused run: **44 tests / 6 suites passed**, no skipped tests/snapshots. |
| Final full mobile | **231 tests / 41 suites passed**, zero failures/skips/snapshots, after temporary runtime-route removal. Baseline coverage retained; **41 added tests / 5 added suites**. [Exact suite/count evidence](evidence/slice2c/verification.json). |
| Strict TypeScript | `tsc --noEmit` passed on the cleaned final runtime. |
| Unused code | `tsc --noEmit --noUnusedLocals --noUnusedParameters` passed on the cleaned final runtime. |
| Formatting / diff | Installed TypeScript formatter applied only to changed TS/TSX files; `git diff --check` passed. No tests weakened, skipped or replaced to pass. Existing ActivityScreen FlashList act warnings remain unrelated passing-test output. |
| Packages / native / backend | **No package/lockfile, native build, backend/API/contracts, database/migration/RLS or physiology diff.** Backend/Ruff/mypy/OpenAPI/database checks were not rerun because those layers did not change. |

## Remaining gates and delivery boundary

Final emulator acceptance requires the live authenticated Week draft/active comparison with the actual shell reminder and callbacks/return paths, including combined safe areas. The visible component-fixture improvements and green tests alone do not close it. Physical-device inset/layout, large-text, TalkBack reading order/duplicate announcements, focus/scroll returns and reduced-motion checks remain open from earlier slices. No physical-device acceptance is claimed.

Local `feat/wombo-ui-v2` remains at the accepted Slice 2B SHA until those gates pass. **Main remains `fb56c51d983564c652d83fc15e02b039e9063d3f`, untouched and unpushed. No push, production deployment or production access.** Original dirty root-workspace changes were not modified. No Calendar V2 or later slice was started.

WOMBO UI V2 SLICE 2C COMPLETE — VISUAL ACCEPTANCE PENDING
