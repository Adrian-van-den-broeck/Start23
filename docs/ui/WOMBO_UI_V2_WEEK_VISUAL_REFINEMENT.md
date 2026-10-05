# Wombo UI V2 Week / Home visual refinement

Date: 2026-10-05. **Design review only. No runtime implementation.**

The recommendation is one coherent task or session surface, a compact header, and a shared left-aligned rhythm for the supporting rows. The draft state should have an ivory **WeekTaskCard** containing its truthful selection status and existing **Continue choosing** action. It should feel as deliberately composed as an active workout, without inventing workout content or progress.

## 1. Scope and evidence

This review preserves the accepted Slice 2B behavior, shared Planning owner, deterministic public view-models, existing navigation, V1 task fallbacks, Workout Detail return, Calendar fallback and development comparison controls. It does not reopen their architecture. The earlier specifications' future bottom tabs, arbitrary week discovery and broader app redesign are outside this refinement.

Read alongside:

- [V2 specification](WOMBO_UI_V2_SPEC.md), especially Week/Home and visual direction.
- [Screen map](WOMBO_UI_V2_SCREEN_MAP.md), especially Week/Home and its adjacent tasks.
- [Approved tokens](WOMBO_UI_V2_TOKENS.md).
- [Implemented Slice 2B report](../../.worktrees/wombo-ui-v2-week/docs/ui/WOMBO_UI_V2_SLICE_2B_REPORT.md), including its later emulator acceptance section, which supersedes the initial failed attempt.
- [Current MVP roadmap](../implementation/mvp-roadmap.md) and root/mobile instructions.

The implemented screen and components were inspected in `.worktrees/wombo-ui-v2-week`, at review HEAD `7a7259125d2a6a907cf9c175379ae6570aabf71b`. The root checkout does not contain the Slice 2B report or implemented Week components; the accepted worktree is the implementation reference.

### Actual visual evidence

The primary evidence is the actual Android emulator draft capture, **[font-restored.png](../../.worktrees/wombo-ui-v2-week/mobile/.runtime/acceptance-20261005/font-restored.png)**, restored to font scale 1.0. It shows `12 Oct 2026 – 18 Oct 2026`, `Workout selection in progress`, `Continue choosing`, all supporting actions, the disposable goal name and the V1/V2 control. This is an implemented screen, not a generated mockup or the old static Home preview.

Additional inspected captures from the same acceptance directory:

| Capture | What it substantiates |
| --- | --- |
| `after-signin.png` | No-plan composition splits the empty-state title and primary button into separate objects. |
| `week-pending.png` | Pending review also lacks a focus surface; the warning fact and review action are widely separated. |
| `week-active.png` | Forest next-session surface exists, but the tall header and oversized repeated text push supporting content down. This capture is a next-date state, not today's workout. |
| `week-attention-support.png` | Attention and supporting actions repeat the loose vertical pattern below the active session. |
| `root-v1.png` | V1 groups Profile with the brand header, groups tools, and frames the selection task. It provides a useful composition comparison, not a density target. |
| `week-large-text.png` | Draft at 1.3 font scale; labels wrap and the lower content requires scrolling. It does not establish 200% or active-week large-text acceptance. |

These are ignored local acceptance artifacts, not newly committed assets; their links require that local evidence directory. Original PNG dimensions are 1080 × 2280 pixels. Screenshot proportions below are visual observations, not measured dp or physical-device results. No live session, production environment or athlete data was changed for this review.

## 2. Critique of the current screenshot

The palette is already appropriate. The failure is that almost every item has its own large vertical interval and similar typographic emphasis, while very few items share a visible group. Whitespace separates related facts instead of distinguishing sections. A working action inventory therefore reads as an unfinished layout.

| Visible problem | Evidence and consequence | Concrete refinement |
| --- | --- | --- |
| Excessive header height | `Wombo · Week`, centered Profile, and the date range occupy three separate bands. In the draft image the main button begins roughly one-third down the screen. | Put title and labeled Profile on one row; put week context directly below. Use content-driven height and intentional 12/16 dp gaps. |
| Detached Profile | Profile appears as a centered standalone text button between brand and week. It looks like another main task. | Trailing header action, minimum 48 dp target; outline person icon plus visible label where available. Preserve the same callback. |
| No draft focus surface | The selection status is below the date; Continue choosing floats separately. There is no object that explains what the athlete is returning to. | Group state, task heading, one short factual line and CTA inside a single ivory task card. |
| Date overwhelms context | Two complete dates including repeated year form a large bold line. | Format the same range compactly, such as `12–18 Oct 2026`; retain both month/year boundaries when necessary and full dates in accessibility. |
| Unrelated-looking support links | Activities/RPE, Check-in, Zones and Prepare week are centered, bold, full-width text buttons without a group heading or common row structure. | One flat Training tools section: aligned labels, restrained outline icons if available, trailing chevrons and separators. |
| Weak section hierarchy | The single divider separates the primary button from View week, but offers little structure to everything below. | Use explicit layers: context, focus, week navigation/progress, attention, tools, goal. Separators only at useful boundaries. |
| View week nearly rivals the primary task | A second broad soft-green button creates another large visual block without contextual grouping. | Keep the same destination as a clear 48 dp navigation row associated with literal week progress when present. |
| Goal stranded at the bottom | `Goal · Disposable V2 development review` is another bold centered action, immediately above development UI. | Separate the quiet Goal label from its supplied name in a left-aligned GoalSummaryRow after training tools. |
| Development chrome competes with product | The floating Tools gear overlaps the header region; the V1/V2 block has similar emphasis to product actions. | Keep the version selector in a clearly separated development footer. Exclude the diagnostic overlay from production-composition judgement and clean comparison captures. |
| Pending-RPE reminder intrudes into system chrome | In these captures the reminder text visually overlaps the status-bar region. | Preserve its global visibility/action, but make a safe-area/inset visual check explicit. Its text must begin below system status content. |

The active capture has a stronger center of gravity, but repeats the workout name in the large heading and the button, renders the entire future-date/count heading at section-title weight, and gives each secondary session another full card. Refine those proportions without dropping names, measures, source descriptions, statuses or independently reachable sessions.

V1 feels more complete because its header, tools and main task are visibly related. V2 should borrow that sense of grouping while retaining the calmer palette, fewer containers and simpler information hierarchy. The catalog replacement character and English `1 workouts` visible in the active capture are separate fidelity/copy observations: do not silently rewrite catalog text; correct singular/plural UI grammar in a later presentation pass.

## 3. Revised hierarchy and composition

### Stable visual order

1. **Existing global pending-RPE reminder, when present:** retain its count, destination and behavior in its existing shell-owned location; ensure readable system insets. Do not manufacture a second Week reminder.
2. **App header:** `Wombo · Week` at screen-title size, labeled Profile aligned at the trailing edge. At narrow widths or large text, let the header wrap into a compact second line aligned to the same gutter.
3. **Week context:** concise locale-formatted Monday–Sunday range. Use the actual loaded/display week; the screenshot's future week must not be called “This week.” No unsupported arrows, picker or return-to-current control.
4. **Dominant surface:** one WeekTaskCard for an existing planning task, or the active NextSession surface. Current blocking/error information remains visible next to the affected action. Do not create a new priority algorithm.
5. **Week navigation:** a flat `View week >` row, with the existing literal completion count immediately above it when supplied. No large progress visualization.
6. **Attention:** show only supplied items not already represented by the main task, retaining warnings, the existing first-two/open-all behavior and exact action targets. Warnings relevant to the focus surface belong immediately beside that surface rather than below unrelated tools.
7. **Training tools:** Activities and RPE, Check-in, My zones, Prepare week, in that order. Prepare remains omitted here only when it is already the main action, as today.
8. **Goal:** one quiet, actionable summary using the existing goal name and confirmation entry.
9. **End spacing:** a modest content inset and the existing bottom safe area. Development controls, if present, follow a separate footer boundary.

This order is visual grouping of existing output. The existing `mainAction`, session list, `empty`, attention filtering and action locks remain authoritative. A draft and a pending proposal can coexist; the design must not substitute a new guessed action for the callback already selected by the model.

### Status treatment

Show a state once prominently within its relevant group. For task-only states, place the existing status at the top of WeekTaskCard, directly below the week context; do not repeat it as an unrelated paragraph above the card. For an active schedule, keep the approved/active-plus-pending label adjacent to the week range, followed by the session surface.

Use `label` typography and words; a small icon may supplement them. Draft and placement use neutral/brand treatment, not warning amber merely because they are unfinished. Pending uses neutral `Proposal awaiting review`; amber is reserved for actual supplied warnings. Active may have a small success check with its explicit state. Avoid large status pills, step trackers and repeated “not approved” badges.

### Supporting rows and goal

Training tools are one flat list on warm canvas, not a grid of cards. Each row has at least 48 dp height, a left label, optional 20 dp semantic icon and trailing chevron. Use the same text start and separator inset for every row. The entire row activates one existing callback; do not add nested buttons or a second focus target for the chevron.

GoalSummaryRow sits 16 dp after the tool list, below one decorative separator. It contains `Goal` in muted supporting type and the exact supplied name in card-title type, with a trailing chevron. Allow the name to wrap. It invokes the existing goal-achievement confirmation flow; do not relabel it as an edit screen or make tapping it confirm achievement. Show no race countdown, race date, target time or goal progress: Week currently receives only `goalName`. Omit the row when the name is absent, as today.

## 4. State-specific compositions

The following are presentation recipes for existing output, not new domain states or a replacement state machine. All retain the shared header, View week, tools, goal when supplied, Profile, pending-RPE reminder and development control.

### A. No plan loaded

Use an ivory WeekTaskCard: existing `No week loaded yet` status, `Prepare your training week` heading, and forest `Prepare week` button inside the card. Merge the current detached empty-state card and button visually. No illustration, empty workout slots or example workout. The displayed current-week context does not promise that preparation generates that week: the existing preparation flow still owns its generation dates. Do not add “Create this week now” copy.

Keep View week accessible even without a loaded plan. No completion count or duplicate Prepare row. A failed initial read is not this state.

### B. Draft / workout selection in progress — primary review state

**Dominant surface: ivory WeekTaskCard, not a blank workout hero and not a standalone button.**

- State: existing `Workout selection in progress`.
- Heading: `Choose your workouts` / `Kies je trainingen`.
- Supporting sentence: existing factual unfinished-selection message (`Your workout choices are not finished` / `Je trainingskeuzes zijn nog niet afgerond`).
- CTA: existing `Continue choosing` / `Verder kiezen`, full-width forest button inside the surface.

The selected date range remains immediately above it. This creates a composed task with a clear next step using facts already available. Do not assert “saved,” “almost ready,” a time to finish, or “step 2 of 4.” No selected/target count, progress bar or sport breakdown: the current Week view-model exposes none of those draft values. Their presence in the separate V1 selection screen does not authorize copying them into Week.

Keep the separate Prepare week entry in Training tools: today its callback resumes an existing draft rather than discarding it. Styling must not imply that this entry starts a fresh plan. The main task's duplicate draft attention row stays filtered out; real warnings remain visible.

### C. Placement incomplete

Use the same ivory task silhouette with `Dates still to confirm`, heading `Confirm your training dates` / `Bevestig je trainingsdatums`, and the existing continuation CTA. A short line may explain that date placement is unfinished, without inventing a remaining count.

The currently implemented CTA is still `Continue choosing`, dispatching the draft action. Preserve that callback and label for this refinement; the surrounding heading gives the missing context. Automatic/manual placement, undo/back and submission remain in the unchanged V1 task. Do not add date chips, placement controls or an approval button on Home.

### D. Pending proposal, without an active workout surface

Ivory WeekTaskCard: `Proposal awaiting review`, heading `Review your week` / `Controleer je week`, short existing confirmation fact, forest `Review proposal` CTA when supplied as the main action. A real warning becomes a compact amber attention row directly below the card, with its existing review action and explanation destination.

Do not show proposal workouts as today's session, planned progress or committed dates. Review opens the precise existing proposal; the Home CTA must never say or perform Approve. If a simultaneous draft means the existing model selects draft continuation, retain that main action and show proposal review as its existing attention item.

### E. Active week with today's workout

The forest NextSession surface dominates. Put `Today` and actual same-day count in a restrained contextual line inside it; sport label/marker, source name, one primary supplied measure, other supplied measure if present, effort/status, existing description and View workout follow in that order. Use `sectionTitle` for the workout name rather than a second screen title, and `numeric` for the main measure.

Keep the visible CTA short (`View workout` / `Bekijk training`), with the full name in its accessible label. Maintain the exact occurrence target. Additional same-day sessions become flat compact rows beneath the focus card, each retaining its source name, measures, effort/status, supplied description and independent detail action. The source order does not imply execution order. Never hide siblings in a carousel or “first workout” narrative.

Then show literal completed/planned counts and View week together. Existing draft/proposal/warning attention follows, except focus-related blocking facts stay beside the focus surface.

### F. Active week without a workout today, with a next training date

Use the same forest session surface with `Next training day` and the actual localized date. Break the long current heading into label, date and a compact count; do not style all three as one large sentence. The screenshot's `Wednesday 14 October` remains the actual source date, never an invented time.

If `empty` also supplies today's approved rest or restriction-rest message, retain that message as a quiet adjacent line. A blank date alone does not mean prescribed rest. Do not use “Today” for the future workout, predict a later week or fetch another plan to fill space. Literal progress, siblings and supporting rows follow the active pattern.

### G. Active week plus pending proposal

Keep authoritative active sessions as the dominant surface and active completion counts intact. Week context explicitly identifies the approved week plus a proposal awaiting review. Put the separate proposal AttentionRow directly beneath the active focus/progress group, retaining its review callback; show actual warnings distinctly.

Do not present two competing hero cards or merge proposed sessions into the active list. Pending alone is not a warning severity. If no active session is available and the existing main action is Review proposal, an ivory task card can carry that action while the approved context/rest message remains explicit. If the existing action is draft continuation, preserve it and keep proposal review in attention. Styling follows current output, not a new priority policy.

### H. Rest-only approved week

One modest ivory rest surface with the supplied `Rest in your approved week` or restriction-rest wording, approved context and no fake workout metric. Its height follows its text; do not give it the height of a populated workout hero. Retain any simultaneous supplied continuation/review action and warnings in their appropriate task/attention treatment.

Keep Activities/RPE, Check-in, Zones, Prepare week, View week and goal available. If the model supplies `0 of 0 planned workouts completed`, preserve it as quiet literal text in the week-navigation group; do not turn it into a percentage, ring, success award or “100% complete.” Unknown counts remain omitted. Never manufacture recovery advice, injury interpretation or an exercise recommendation.

### Additional states that must survive the visual pass

Loading uses the existing static skeleton and loading announcement; no fake plan claims. Failed/stale reads retain known context and inline uncertainty, with only existing actions and locks. Rejected, expired and unavailable states retain their literal status and existing planning entry in the ivory task treatment. An active week with no future sessions says the existing no-upcoming-workout message, not rest-only. Do not invent a retry or refresh operation. Missing optional content collapses naturally without reserved card-sized holes.

## 5. Annotated textual wireframe — draft

This wireframe uses the actual screenshot's week and existing draft action. Bracketed notes are design annotations, not athlete copy. Goal text is a placeholder for the exact supplied name. No bottom tabs are proposed.

```text
[system status area — text must not overlap]
[existing global pending-RPE reminder, when present]

Wombo · Week                          Profile >   [1]
12–18 Oct 2026                                    [2]

╭──────────────────────────────────────────────╮
│ Workout selection in progress               │   [3]
│ Choose your workouts                        │
│ Your workout choices are not finished.      │
│                                            │
│ [          Continue choosing             ] │   [4]
╰──────────────────────────────────────────────╯
[actual warning row here only when supplied]      [5]

View week                                      > [6]

Training tools                                   [7]
  Activities and RPE                           >
  ─────────────────────────────────────────────
  Check-in                                     >
  ─────────────────────────────────────────────
  My zones                                     >
  ─────────────────────────────────────────────
  Prepare week                                 >

────────────────────────────────────────────────
Goal                                             [8]
[exact supplied goal name, wrapping]            >

[16 dp content end + existing safe-area handling]
[development build only: separated V1/V2 footer] [9]
```

1. Header shares a baseline and 16 dp page gutter; Profile retains visible text and a minimum 48 dp target. It wraps below only when necessary.
2. Quiet supporting-size date text; full dates remain accessible. The card's state is visibly associated with this week and not repeated above it.
3. Ivory, radius 20, 24 dp padding. Status uses label; heading uses sectionTitle; supporting copy uses supporting. No nested card or shadow.
4. Forest primary, radius 12, minimum 52 dp; 16 dp above CTA. The strongest fill belongs to the action. Busy/disabled behavior remains unchanged.
5. No warning in the supplied draft capture: render no empty attention container. If present, preserve its fact and existing action.
6. Clearly actionable 48 dp row, 12 dp after the focus group. It is subordinate to Continue choosing without looking like unstyled text.
7. Section heading and flat rows establish a shared structure; 8 dp heading-to-list, no 24 dp gaps between routine rows. Icons are optional and must use available approved assets.
8. Goal is part of the content rhythm, separated from development controls. It is not a floating footer or a decorative quote.
9. Development controls remain reachable in normal scroll flow with their current requested/effective-state wording and disabled semantics. No production space is reserved for them.

## 6. Annotated textual wireframe — active week

Structural placeholders below are existing public values, not sample prescriptions. This illustrates state E; state F replaces Today with Next training day and its actual date.

```text
[system status + existing RPE reminder when present]

Wombo · Week                          Profile >
[actual week range]
Approved                                          [1]

╭────────────────── forest ────────────────────╮
│ Today · [actual same-day session count]      │   [2]
│ [small sport marker] [supplied sport]        │
│ [exact source workout name, wrapping]       │
│ [supplied primary duration OR distance]     │   [3]
│ [other measure if supplied]                 │
│ [supplied effort] · [workout status]         │
│ [existing source description if supplied]   │
│ [              View workout              ] │   [4]
╰──────────────────────────────────────────────╯
[same-day sibling: full source summary]         > [5]
[additional same-day sibling, when present]     >

[completed] of [planned] workouts completed        [6]
View week                                      >

Attention · [existing displayed count]             [7]
[supplied fact]             [existing action]   >
[up to two initially; existing show-all control]

Training tools
  Activities and RPE                           >
  Check-in                                     >
  My zones                                     >
  Prepare week                                 >
────────────────────────────────────────────────
Goal
[exact supplied goal name]                     >
[content end / safe area; optional dev footer]
```

1. Approved refers to the identified active revision, not to a workout's scheduled status. In G, retain explicit pending-proposal context as well.
2. This date context belongs to the hero, reducing the current oversized heading outside it. Count wording must handle singular/plural in both languages.
3. One measure gets numeric emphasis. Both supplied measures remain visible and distinct; absent duration never becomes zero or an estimated swim duration.
4. Use the existing soft-green secondary button with forest label on the forest surface. No nested forest button, repeated full title in visible CTA, or pale muted body text on forest.
5. Compact means less framing and smaller hierarchy, not dropped information or fixed-height clipping. Each occurrence remains independently reachable.
6. Body/supporting text, no graphic. Week navigation remains next to it. The count is neither feedback completion nor physiological readiness.
7. Omit the heading/group if no items survive existing filtering. Keep actual warnings visible; do not repeat the global RPE reminder or invent check-in/zone due badges.

## 7. Component refinement

| Component | Assessment and focused recommendation | Behavior boundary |
| --- | --- | --- |
| `WeekContext` | Refine date hierarchy and natural wrapping. Keep range associated with one state presentation; compose task status into the adjacent task card where appropriate. | Same dates/state/localization source. No week discovery, current-week inference or new controls. |
| `NextSession` | Keep forest focus; bring temporal context inside; reduce title to sectionTitle, isolate one primary measure, shorten visible CTA. Present siblings as flat rows. | Preserve all current summary information, exact IDs, source order, rest-message coexistence and detail return. |
| `AttentionRow` | Replace loose paragraph + centered button with fact and explicit trailing verb in one aligned row; stack at large text. Use warning fill only for actual warning items. | Same supplied items, filtering, actions, busy locks and show-all behavior. No synthesized due tasks. |
| `WorkoutSummary` | Its visual vocabulary is appropriate; no global redesign needed. A compact Week-only presentation may reuse its type/measure patterns for sibling summaries. | Do not change accepted Workout Detail defaults or add a new summary mapper. Preserve RPE-description suppression and every public source field currently shown. |
| `Button` | Existing primary/secondary token treatments work. The main problem is using centered tertiary buttons for every supporting destination. Use purpose-built rows for those destinations; allow concise visible workout CTA with full accessible object name. | Keep duplicate-press protection, busy/disabled labels, focus and callbacks. Do not globally restyle all tertiary buttons for this screen. |
| `Card` | Existing ivory/radius/no-shadow primitive is adequate. Give the singular focus card 24 dp padding; ordinary card remains 16 dp. | No global radius/palette change, invented elevation or nested cards. |
| `WeekTaskCard` — small new presentational composition | Justified because draft, placement, preparation and review currently render disconnected status/title/action pieces. Accept supplied text, existing button/action and optional existing message content. | No data fetching, state selection, draft ownership, progress derivation or mutation code. |
| `QuickActionRow` — small new presentational composition | Shared aligned text/icon/chevron pattern for View week and tools; controls surface density without shrinking targets. | One existing action, correct accessibility/disabled state, no navigation registration. |
| `GoalSummaryRow` — small new presentational composition | Separates the quiet label from the real goal name and confirmation affordance. | Existing `goalName` and `onGoal` only. No goal status computation. |
| `SectionHeader` | Optional local text pattern, not a necessary new abstraction. | Reuse existing Text unless repetition justifies extraction. |

Prefer Week-local composition changes over edits that propagate into accepted V1 screens or Workout Detail. The names above do not authorize a new domain/state abstraction or changes to the shared controller.

## 8. Spacing, typography and surfaces

Use the approved tokens exactly. The dimensional recommendations below are future layout targets, not claims that a revised screen was rendered or measured.

| Region | Recommendation |
| --- | --- |
| Page | `background` warm canvas `#F4F2EC`; 16 dp phone gutters; 24 dp on wider layouts with existing 600 dp reading width. One scrolling content owner. |
| Header | Screen-title 28/34, weight 700; Profile button 16/22, weight 600, minimum 48 dp. 12 dp to week context. No display-sized brand plus another display-sized task title. |
| Week/date | Supporting 14/20 for range; label 14/20 for status. 4–8 dp between related lines; 16 dp to the focus surface. Dates never use caption size. |
| Task focus | Ivory `surface` `#FFFEFA`, radius 20, padding 24. Label → heading gap 8; heading → supporting gap 8; supporting → CTA gap 16. Heading sectionTitle 20/26, weight 600. |
| Session focus | `primary` forest `#123F39`, inverse ivory text, radius 20, padding 24. Internal gaps 8/12/16 by relationship; source title 20/26, measure 28/34, supporting copy 14/20. |
| State | Text first; at most a compact accent/icon. Neutral state text uses deep ink `#102B28`. Approved success can use approved success token. No filled amber label for ordinary draft/pending state. |
| Main button | Forest + inverse label, radius 12, 52 dp minimum; 16/22 weight 600. Natural growth for wrapped labels. Deep-forest pressed state, existing explicit busy/disabled treatment. |
| View week / tool rows | Minimum 48 dp; 12 dp vertical padding where content needs it; icon-to-label gap 12. Body 16/24 or button 16/22 for action label, one consistent choice per list. Natural height at large text. |
| Group separation | 12 dp focus-to-navigation, 24 dp navigation/attention-to-tools, 8 dp heading-to-first row, 16 dp tools-to-goal. No universal 24 dp gap around every element. |
| Separators | Existing `Divider` using `border` `#D9E0DA` inside flat row groups or before goal/dev footer. Align to text inset within lists. Do not surround every surface with rules. |
| Goal | Muted 14/20 label on canvas, exact name 18/24 weight 600, 4 dp between them. No forest fill, race-photo background or extra pill. |
| End spacing | 16 dp after final production content plus existing bottom safe-area handling, counted once. No flex spacer that pins goal to the bottom; no footer-sized blank reserve for hypothetical tabs. |
| Development footer | Separator and 24 dp separation from production content; clear supporting label; retain V1/V2 48 dp targets and actual state. Footer grows/scrolls at large text. |

Use `primary.soft`/`secondary` only for the focus-session button, genuine selection or restrained press feedback. Supporting tools do not each need a tint. Sport colors belong on small sport markers/tiles with text; no sport color in a draft without a supplied sport. Use approved outline icons only if available without a new dependency; a text-and-chevron row is an acceptable complete design. Never substitute emoji or letter circles.

Use `text.muted` only on its approved canvas/ivory backgrounds. Forest content uses inverse text; warning text uses warning-soft fill when grouping is needed. Decorative separators are not sufficient control/focus boundaries. Keep approved 2 dp focus treatment and contrast requirements. New foreground/background combinations require checking during implementation.

At 320 dp width or 200% text, rows and headers wrap and cards grow. No fixed-height focus card, single-line primary-label constraint, font-scale clamp or truncation of status/warnings. More scrolling is preferable to removing information. A default-size draft screen should reveal the primary task and View week before the first scroll, with training tools beginning in that viewport on the reference emulator; do not make “everything fits on one screen” a universal requirement.

## 9. What stays visually simple

- One dominant focus surface. All other structure comes from alignment, type, spacing and a few dividers.
- One literal week context; no seven-day mini-calendar duplicating Calendar.
- One filled primary task CTA, or one forest active-session hero with its subordinate soft button.
- One flat tool list; no card grid and no description paragraph under every tool.
- One small goal summary using only its supplied name.
- Attention appears only for existing facts. Do not fill an empty queue with reassurance or educational cards.
- Native system typography, warm canvas, restrained sport accents and existing motion. No new font, hero artwork or decorative animation.

## 10. What must not be added or changed

No readiness score, training/private load, TSS, adherence score, streak, achievement, completion ring, social feature, AI chat, invented schedule time, goal countdown, generated coaching advice, new backend data or speculative workout. No fabricated selected count or draft completion percentage. No claim that selection resolves a physiological warning.

No bottom-tab shell, new route, replacement Calendar, discovery arrows, new shared planning owner, new state abstraction, duplicated API calls or mutation logic. No approval from Home, implicit plan activation, changed prepare/resume semantics or guessed reconciliation of active and pending content. Keep version checks, idempotency, existing locks and confirmations intact.

Do not replace the global pending-RPE reminder with an inferred Week item or silently remove it. The old screen map's future tab-count proposal is outside scope. The Tools overlay is diagnostic chrome, not Profile or a production action. No developer control should dictate production spacing; preserve current development-only eligibility and the existing non-development V1 policy.

## 11. Implementation acceptance checklist

These are gates for a later authorized presentation change, not tests passed by this design review.

### Visual evidence and hierarchy

- [ ] Capture the implemented refinement at the same emulator size/font scale as `font-restored.png`, with the same draft content where feasible; compare actual output against this primary evidence.
- [ ] Capture all A–H states using known public fixtures or an authorized existing test flow. Clearly label fixture evidence; do not claim live coverage where none exists.
- [ ] Draft has one coherent ivory focus surface with status, task heading and Continue choosing; it reads as intentional even without a workout hero.
- [ ] Profile is visibly part of the header, the date is subordinate, and the first task no longer starts after three oversized header bands.
- [ ] View week, training tools and goal have distinct roles and consistent left alignment. No centered stack of unrelated links remains.
- [ ] Goal follows content naturally and remains separate from development UI; no filler region pushes it down.
- [ ] Active week has one forest hero, accurate date context, readable measures and independently reachable same-date siblings. No repeated full workout title in visible button copy.
- [ ] Pending review and approved training remain visually distinct. Actual warnings remain visible and actionable.
- [ ] Screenshot with diagnostic overlay closed demonstrates clean composition; a separate development capture demonstrates reachable V1/V2 controls.
- [ ] Pending-RPE reminder remains visible/actionable and no longer overlaps system status content. Verify actual shell insets; do not claim this is solved by Week-only padding if it is shell-owned.

### Information, actions and accessibility

- [ ] Preserve Week context, every current plan state, continuation/preparation/review actions, View week, Activities/RPE, Check-in, Zones, Prepare week, goal confirmation, Profile and V1/V2 behavior.
- [ ] Preserve all currently displayed workout fields and literal progress values; missing values stay absent. No derived duration or invented draft metric appears.
- [ ] Verify no-plan display dates do not imply a changed generation week; preparation still enters the existing V1 flow.
- [ ] Verify placement continuation and draft/pending coexistence dispatch the same existing actions. Do not swap action priority for aesthetic convenience.
- [ ] Goal tap still opens explicit confirmation, never directly changes goal state.
- [ ] English and Dutch at 320, 360 and 412 dp; default and 200% text; long goal/workout names; singular/plural; cross-month/year week ranges.
- [ ] Minimum 48 dp targets, primary minimum 52 dp; rows grow; no overlapping hit areas, clipped warning or hidden final action.
- [ ] TalkBack reads week/state, source workout identity/units, literal counts, actionable rows and disabled/busy states in visual order without duplicate nested announcements.
- [ ] Existing return/focus/scroll behavior holds for Detail, Calendar, Profile and V1 planning tasks. Reduced motion remains supported.
- [ ] Contrast/focus checks use approved token pairs, including inverse content on forest; status meaning never depends on color alone.

### Engineering and verification boundaries

- [ ] Changes stay in authorized presentation/copy scope. Shared controller, API/contracts, planning behavior, navigation architecture and accepted Detail defaults remain intact.
- [ ] Run strict TypeScript, unused checks, applicable Week/view-model/boundary/interaction tests and recursive public-data privacy checks. Run the full mobile suite for later runtime acceptance; retain the accepted 190-test baseline coverage.
- [ ] Recheck no duplicate reads and no changed mutation/return semantics through existing regression coverage and focused emulator comparisons where relevant.
- [ ] Keep existing physical-device, TalkBack, large-text and inset gates open until actually executed. An emulator screenshot does not close physical acceptance.
- [ ] If a required gate cannot run, record it explicitly rather than declaring the implementation accepted.

### Verification of this design-only deliverable

Reviewed actual emulator screenshots, the requested documents, current roadmap constraints and implemented Week/component/view-model source. Recommendations use existing public information and approved tokens. Only this Markdown file was added by this task; pre-existing workspace changes and the accepted implementation worktree were left untouched. Runtime tests were not rerun because no runtime code changed. The report's 190 passing mobile tests are inherited acceptance evidence, not a new test result. No runtime or physical-device gate is closed by this document.
