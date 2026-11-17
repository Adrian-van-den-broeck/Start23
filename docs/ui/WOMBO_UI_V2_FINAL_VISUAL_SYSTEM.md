# Wombo UI V2 — final visual system

Date: 2026-10-06. Status: final design/implementation mapping; no runtime changes or release approval.

## 1. Authority and handoff

**The six images in [mockups-final](mockups-final/) are the highest-authority visual source.** The 117 images in [reference-screenshots](reference-screenshots/) describe functional content and captured states, not visual acceptance. Never use the sparse V2 scaffolds as the target appearance.

Read this document with [final tokens](WOMBO_UI_V2_FINAL_TOKENS.md), [all-screen mapping](WOMBO_UI_V2_FINAL_SCREEN_MAPPING.md), and [implementation sequence](WOMBO_UI_V2_FINAL_IMPLEMENTATION_SEQUENCE.md). These four documents form one handoff. Exact values below are implementation decisions derived from the mockups, not claims of extracting original design tokens from raster images.

Visual precedence: user mockups → this final system/token/mapping set → older UI guidance only where explicitly retained. Functional precedence: [root instructions](../../AGENTS.md), applicable mobile instructions, [current MVP roadmap](../implementation/mvp-roadmap.md), latest approved decisions, public contracts and current state owners. Screenshots demonstrate behavior but cannot revive a superseded roadmap requirement. Decoration cannot create a field, metric, navigation destination or mutation.

Evidence inspected: all six mockups individually; all 117 functional PNGs in labeled four-image inspection sheets; screenshot index and manifest; the four older visual documents; architecture/dependency documents; root mobile manifest/lock; and the integrated implementation at `.worktrees/wombo-ui-v2-activities/mobile`. The reference index identifies that runtime as `19c23d5`; the root checkout is older. In particular, **the integrated runtime already has a three-destination `TrainingLayout`**. Older statements that bottom navigation and shared controllers do not exist are historical.

## 2. Mockup-by-mockup analysis

M1–M6 are visual references, never fixture data. Device status bars, screenshot dates/times, sample names/values, cropped lower content and raster/anti-aliasing artifacts are not app requirements.

### M1 — Calendar Week

[01-calendar-week.png](mockups-final/01-calendar-week.png)

| Aspect | Observed composition and final rule |
| --- | --- |
| Regions | Back/Profile utility row; mountain band; large calendar title and explanation; Week/Month segment; centered range with arrows and Today; weekday heading; vertical day agenda. |
| Background/header | Warm near-white canvas; several pale green ridges and small warm sun fade behind the title. Header text remains on a light field. |
| Navigation | Back arrow + text; pale Profile pill with person and chevron. No bottom bar is visible in this crop; this is not evidence to remove Calendar's existing tabs. |
| Type | Bold screen title dominates; explanation is supporting; date range is strong; large day numerals beside smaller weekday labels. |
| Surfaces/cards | Pale segmented track; forest selected Week; open agenda on canvas, no large card around every empty day. |
| Icons/CTAs | Circular outlined previous/next; text Today; semantic back/profile icons. All final touch targets >=48 dp. |
| Borders/spacing | Thin horizontal day separators and vertical date rail; small outlined nodes. Broad section gaps, tightly associated weekday/date. Use 24 dp section separation and 16 dp day padding, natural row height. |
| Reusable rule | Range navigator, date rail, segmented control, landscape/title shell, ProfileAction. |
| Screen decoration | Sun position and ridge silhouette; empty-day sample composition. Weekday strip is noninteractive context unless an existing callback supplies interaction. Do not imply time slots or prescribed rest from an empty day. |

### M2 — Calendar Month

[02-calendar-month.png](mockups-final/02-calendar-month.png)

| Aspect | Observed composition and final rule |
| --- | --- |
| Regions | Same utility row/title; Week/Month segment; month range navigation; rounded grid card; selected-date detail card; floating pill navigation. |
| Background/header | Landscape includes a right-side river and trees; broad fade into the page. Reuse the landscape system, not separate artwork per month. |
| Type | Strong title, bold month, medium weekday/date values, large selected-date heading. |
| Surfaces/cards | Ivory grid and detail surfaces; pale cells; subdued outside-month dates. Selected date uses pale green and forest outline; today's warm tint is distinct. |
| Icons/CTAs | Circular arrows; Today link; calendar icons; Activities bars. Selected navigation is forest with ivory icon and label. |
| Borders/spacing | Fine grid lines; subtle card lift; 16 dp between grid/detail. No thick scaffold cell borders. |
| Bottom navigation | Three labeled destinations; fixed visual position above system gesture inset; content must scroll clear of it. Selection follows actual route, not selected date. |
| Reusable rule | CalendarGrid, selected-date list, rounded navigation capsule, distinct today/selected states. |
| Screen decoration | River, tree placement, sample dots/dates. Dot meaning is not specified by the image; final indicators must use actual count/state and visible legend/labels. |

### M3 — Zones

[03-zones.png](mockups-final/03-zones.png)

| Aspect | Observed composition and final rule |
| --- | --- |
| Regions | Back/centered WOMBO/subtitle/exit; mountain band; ivory profile hero; discipline heading; stacked discipline cards. |
| Background/header | Airy warm canvas; mountain band beneath utility header; first card intersects the faded artwork area. |
| Type | Bold wordmark; small eyebrow; large hero title; clear body explanation; prominent discipline heading and sport titles. |
| Surfaces/cards | Hero contains profile circle and copy, divider, two metric groups. Sport card contains icon/title/status, route row, information row, full-width CTA. |
| Icons | Forest outline person, swim, bike, document, location and info within pale circles. Icon is supplementary to text. |
| CTA/borders | Forest rounded route/value CTA, arrow at end; fine separators between facts; soft shadow outside large ivory cards. |
| Spacing/navigation | 24 dp between major groups; 16 dp card interior groups. Scroll all disciplines. No bottom nav shown; preserve the actual secondary-route shell. Exit keeps its existing sign-out meaning. |
| Reusable rule | HeroCard composition, MetricRow, discipline card, InfoRow, StatusChip, icon circles. |
| Screen decoration | Particular mountains; “3” and “Los / Plan gekoppeld” are sample presentation. Use actual existing discipline/association context. Never reinterpret “Los” as a subscription tier. Numeric-free cards do not authorize new RPE-only onboarding. |

### M4 — Profile / Onboarding

[04-profile-onboarding.png](mockups-final/04-profile-onboarding.png)

| Aspect | Observed composition and final rule |
| --- | --- |
| Regions | Back/wordmark/subtitle/exit; mountain band; progress capsule; large step heading and explanation; one ivory form card; submit at card bottom. |
| Background/header | Most expansive ridge treatment; fade behind progress/title. Form is opaque and readable. |
| Type | Strong “Jouw basis”; bold persistent field labels; optional qualifier lighter but readable; large input values; smaller helpers and units. |
| Surfaces/cards | Ivory outer form; light fields with fine outline and modest radius; pale leading icon discs; separated unit suffix area. |
| Icons/CTA | Person/date/heart symbols; forest full-width save button with arrow. Do not turn the leading icon into a separate action. |
| Dividers/spacing | No separator between every field; 24 dp field-group gap, 8 dp label-to-field, 4 dp field-to-help. Button 24 dp after last helper. |
| Navigation | No root bar in this onboarding composition; existing step/gate behavior wins. Back must not bypass required setup. |
| Reusable rule | FormField anatomy, FormCard composition, StepProgress, branded secondary header. |
| Screen decoration | Seven pictured dots are progress decoration, not seven navigation buttons. Use actual current step/total. Profile reuse of this form must not fabricate onboarding progress; omit progress outside a genuine step flow. Sample birth date/HR are not defaults. |

### M5 — Workout selection

[05-workout-selection.png](mockups-final/05-workout-selection.png)

| Aspect | Observed composition and final rule |
| --- | --- |
| Regions | Back/Profile; landscape; large task title; candidate card; skipped-count divider; Undo/reset controls. |
| Background/header | Same pale ridges; artwork stops at first content card. Development subtitle is diagnostic content, not brand typography or production copy. |
| Type | Display task title; bold source workout name; readable duration/effort; subordinate source description. |
| Card anatomy | Large pale sport circle alongside sport chip/title; duration and effort in two fact groups; description; primary Choose; pale full-width Skip. |
| Icon/CTA anatomy | Actual runner silhouette, clock, ascending bars, forward arrow; undo/list icons on secondary controls. Forest is concentrated on Choose. |
| Borders/spacing | Restrained exterior shadow; no heavy card border; thin divider through skipped-count section; secondary controls have light outlines. Use 16 dp internal grouping, 24 dp before footer controls. |
| Navigation | Focused task, no bottom bar shown. Existing task locks and return behavior remain; do not introduce swipe-only operation. |
| Reusable rule | WorkoutSummary candidate composition, MetricRow, Button variants, two secondary actions which stack when needed. |
| Screen decoration | Example catalog code/time/effort, exact mountain crop and diagnostic line. No fake deck layers, inferred target count or progress gauge. |

### M6 — Activities

[06-activities.png](mockups-final/06-activities.png)

| Aspect | Observed composition and final rule |
| --- | --- |
| Regions | Large title/Profile; mountain header; prominent add action; Recent heading; activity card; back affordance; selected Activities navigation. |
| Background/header | Landscape/trees, with a dark landscape inset in prominent forest actions. This is a bounded decorative variant, not a chart. |
| Type | Display root title, bold section title, sport chip, date, clear metrics, strong feedback heading, full RPE explanation. |
| Card anatomy | Sport icon/chip/date; divider; duration/source rows; divider; execution/RPE/HR; pale information inset; conditional correction CTA. |
| Icons | Run uses rust-on-peach circle; other facts use forest-on-pale-green circles. Overflow dots appear but supply no product capability. |
| CTA/borders | Wide forest Add with ivory plus circle; correction forest with arrow; soft card shadow and internal separators. |
| Spacing/navigation | Natural-height card; 16 dp groups, 24 dp sections; root bar is rounded with strong selected pill and readable inactive destinations. Card count is unbounded. |
| Reusable rule | ActivitySummary with fact rows, Notice inset, action banner, bottom navigation. |
| Screen decoration | Trees inside actions and single example activity. Omit overflow control unless an existing action menu is evidenced; no edit/delete/share behavior may be inferred. |

## 3. Global language A–T

| Area | Final reusable rule |
| --- | --- |
| A Canvas | `background` warm off-white; opaque ivory data/form cards. No app-wide photo, dark theme, noise texture or blue sci-fi glow. |
| B Landscape | One decorative header asset; full-width bleed with bounded height/fade. Detailed rules below. |
| C Header | Root: large title and pale Profile pill. Task: back row then large task title. Profile/Zones: centered WOMBO + subtitle between existing back/exit actions. Header height follows content. |
| D Typography | Strong 36/42 display, 30/36 screen, 24/30 section, 22/28 card hierarchy; body 16/24. Use final token weights; no universal bold body. |
| E Icons | Typed semantic vector wrapper; consistent outline UI set plus three coherent sport assets. No emoji, initials or text arrows. |
| F Icon containers | Pale circle: 40 dp field/metric, 48 dp row/sport, 64 dp hero sport; respective 20/24/32 dp artwork. Circle is decoration unless the whole control is an action. |
| G Cards | Ivory radius 20; 16 dp normal padding, 24 dp hero/form padding at reference width; restrained soft lift. Distinct workout, activity and task anatomy, not one schema-driven mega-card. |
| H Primary buttons | Forest, ivory 18/24 semibold label, radius 16, min 56 dp; full width in forms/tasks; optional trailing ArrowRight, no decorative badge. |
| I Secondary | Pale green fill/forest label, min 52 dp; outline variant for Undo/reset and dismissal. Text rows remain >=48 dp. Skip/reject are not error-red by default. |
| J Lists | 48 dp icon column + 12 dp gap + flexible label/helper + 24 dp chevron; min 64 dp when icon circle exists; 12 dp vertical padding. Divider begins at text inset. No fixed row height. |
| K Segments | Pale capsule, 4 dp inset, forest selected segment; min 48 dp individual target. Exclusive mode semantics. At large text stack labeled options inside a rounded container. |
| L Fields | Persistent label, optional qualifier, light outlined input, optional icon disc, unit suffix, helper/error beneath. See forms section. |
| M Status | Natural-width soft capsule, 12 dp horizontal/4 dp vertical padding; label + optional 16 dp state icon; wraps. A noninteractive chip is not a button. Pending uses neutral green, not success or danger. |
| N Warning/info | `Notice` tone variants: pale amber warning, pale green info, pale red error, pale green success with explicit icon/title/body/action. No color-only severity. |
| O Navigation | Existing Week/Calendar/Activities routes, equal targets, ivory capsule with forest selected pill. No new destination, unread count or settings tab. |
| P Sports | Forest icons in selection/zones; discipline accent in activity history and compact sport badges. Run rust, bike green, swim blue. Sport label always present; intensity remains a separate supplied field. |
| Q Spacing | 4/8 associations; 12 control gaps; 16 card groups; 24 sections; 32 title/major transitions; 48 only deliberate empty-state space. Never stretch content to fill a screenshot. |
| R Borders/shadows | 1 dp decorative separators, 1 dp accessible field boundary, 2 dp selected/focus outline; one subtle shadow level for cards, stronger only for sheet/lift. No shadow on every field. |
| S Safe areas | Safe-area provider once; system status/navigation insets are not copied image pixels. Background may bleed; controls never sit under OS UI. |
| T Long screens | One scroll owner; all content grows; header artwork scrolls away; use existing virtualized activity list. End content clears measured footer + inset. No nested same-direction scroll/card carousel for ordinary content. |

## 4. Landscape system

Implement later as a small local SVG component/asset family using `react-native-svg`: **HeaderLandscape** and **ActionLandscape**. HeaderLandscape has a ridges-only default and an optional right-side trees/river layer; these share paths/palette. ActionLandscape reuses the foreground ridge/tree paths, not a second generated illustration. No remote URLs, random procedural mountains or dozens of React Native Views. No new image-generation task is required by this document.

Use an original 393 × 180 viewBox as the composition basis. Three broad ridge paths plus one foreground layer, one small sun and a vertical fade are sufficient. Preserve soft atmospheric depth; do not trace every raster blur edge. Trees/river must be a single grouped decorative layer. No weather, elevation, route, progress or time-of-day semantics.

| Property | Final rule |
| --- | --- |
| Placement | Roots, selection, Zones/Profile and first/current onboarding step header; optional compact form header. Never repeat between sections on one long page. |
| Size | Standard visible art 140 dp; absolute maximum 180 dp excluding system inset. Compact form/secondary variant 96 dp. No minimum screen-height percentage. |
| Fade | First ridge begins below utility controls. Last 56 dp fades fully to canvas; content can overlap only this faded region. Behind text use a canvas veil that keeps effective colored artwork <=12% opacity. |
| Layer opacity | Asset internal ridge layers .10/.16/.22/.28 in forest/sage; sun .40 using decorative warm tint. If using precolored light paths, do not apply these alphas twice. |
| Header interaction | Text/controls remain normal layout siblings above art; art absolute, clipped, pointerEvents none. Utility row is opaque/light enough for contrast. No sticky art, parallax, collapsing-title animation or touch capture. |
| Card overlap | First opaque card may begin in final 24 dp of fade. No negative margin over required text, warning or progress. Actual content height determines card position. |
| Variants | Ridges default for Week/selection/profile; trees/river for Calendar/Activities. No per-sport color landscape and no asset chosen from training metrics. |
| Dark action inset | At most one action banner per viewport uses ActionLandscape; rightmost 35% only, <=.12 effective contrast against forest; keep label/icon region plain. In M6 choose Add as decorated banner; correction may be solid forest. |
| Narrow/large text | At <360 dp or text scale >=1.5 use compact 96 dp art; center crop, never distort. If title wraps, art remains bounded and ends before text needs extra height. Large type grows normally. |
| Do not show | Workout execution block body, numeric zone tables, RPE choice list, warning/error panel, busy skeleton, modal choice list or native keyboard area. Errors never get extra decorative space before the reason. |
| Accessibility/performance | Exclude the whole art subtree from accessibility; no label, role or focus. Static, no animation, no haptic response. Contrast must pass with artwork on; opaque canvas is fallback if SVG fails. |

## 5. Icons and dependency audit

Both `mobile/package.json` / lock and the integrated runtime manifest/lock were inspected. Neither resolves `lucide-react-native`, `react-native-svg` or `@expo/vector-icons`. The optional SVG peer mention in the lock is **not** an installed renderer. `expo-font` 57.0.4 is transitive, not an adopted custom typeface. Current `SportIndicator` is text with a colored border; `TrainingLayout` uses text-only tabs. These are implementation gaps, not final icon designs.

Recommend **lucide-react-native + Expo-aligned react-native-svg** in a later dedicated foundation batch. SVG serves icons and landscape, making the dependency worthwhile. Local SDK 57 `bundledNativeModules.json` specifies SVG **15.15.4**; recheck the installed SDK mapping before installation. Retain Expo/React/RN versions. Lucide provides named, typed components with adjustable stroke/size. Use static named imports behind a semantic `Icon` wrapper; do not load all icons through dynamic name lookup. [Lucide React Native documentation](https://lucide.dev/guide/react-native). Expo documents SVG primitives and SDK-compatible installation. [Expo SVG documentation](https://docs.expo.dev/versions/latest/sdk/svg/). The latest web page does not override this repository's SDK pin.

Exact Lucide version remains a dependency-lock gate: select a stable version, verify its exports/peers/license, commit an exact pin and lock in that later batch, rebuild the development client, then compare actual rendered glyphs. No package was installed here. No second icon-font library, SVG transformer or UI kit is required.

| Semantic key | Final artwork choice | Use |
| --- | --- | --- |
| profile | UserRound-style outline person; filled profile silhouette variant only for ProfileAction | Header/form/person circle |
| back / forward / chevron | ArrowLeft / ArrowRight / ChevronRight; ChevronLeft for range | Navigation/actions; never literal text arrows |
| week / calendar | CalendarDays / Calendar | Distinct tab shapes and date field |
| activities / intensity | ChartNoAxesColumnIncreasing-style ascending bars | History tab / supplied effort; static symbol, never magnitude-driven |
| run | Local 24-unit running-person SVG: head circle, leaning torso, bent arms, split stride, rounded strokes | Match recognisable runner in M5/M6; footprints are not an adequate final runner substitute |
| bike | Local 24-unit rider-and-bicycle SVG, same stroke weight as runner | Match M3 rider; plain Lucide Bike exists but depicts a bicycle, so is only a fallback pending asset review |
| swim | Local 24-unit swimmer/wave SVG: head, arm arc, two wave strokes | Match M3; never a pool-ladder pictogram as the sole sport cue |
| clock | Clock | Duration/date-time |
| heart rate | HeartPulse | HR form/metric; not physiological diagnosis |
| document | FileText | Source/result/plan context |
| info / warning | Info / TriangleAlert | Notice tone, always with words |
| location | MapPin | Existing route/context row only; no GPS permission or map feature |
| undo / list | Undo2 / List | Existing undo/reset-passed |
| add / logout / goal | Plus / LogOut / Flag | Existing Add, sign out, goal destination |
| check / close / refresh | Check / X / RefreshCw | State, dismissal, existing refresh |

Names describe intended glyphs; confirm exact package export spellings at the chosen pin. Three local sport icons are a deliberate coherent extension behind the same wrapper, not three libraries. All use 24-unit viewboxes, round caps/joins and a 2-unit stroke; enlarge geometrically for hero circles. Selected UI state primarily changes container/fill, not the entire icon style. Decorative duplicates are inaccessible; icon-only buttons have localized verb/object labels. Provider logos remain authorized provider assets.

## 6. Smallest component family and repository boundaries

Paths below are inside the integrated runtime's `mobile/src/ui-v2`, unless stated otherwise. Reuse the existing primitives, components, view models and state owners. Names in the left column are implementation boundaries, not instructions to create every example component named in the task.

| Boundary | Repository decision | Visual contract |
| --- | --- | --- |
| `Screen` + new `AppBackground` / `LandscapeHeader` | Extend `primitives/Screen`; two background compositions share assets | Insets, scroll ownership, bounded landscape, no data decisions. |
| `AppHeader` with `ProfileAction` | New shared composition replacing repeated screen JSX | Root/task/brand variants; literal title/back/exit callbacks; wraps. ProfileAction is a header slot, not another navigation owner. |
| `BottomNavigation` | Extract/restyle presentation in existing `navigation/TrainingLayout.tsx` | Existing tab events, locks, selection, detail footprint and measured height retained. No second navigator/provider. |
| `Text`, `Button`, `Input`, `Card`, `Divider`, `Skeleton` | Evolve existing primitives | Typed final tokens; Primary/Secondary are Button variants; SurfaceCard/HeroCard are Card compositions. Do not duplicate primitives under new names. |
| `Icon` + `IconTile` | New typed vector and circle primitive | Size/tone only; no data-fetch or inferred sport. |
| `InfoRow` / existing `QuickActionRow` | One fact-row anatomy, one actionable row anatomy | Leading icon, wrapping text/value, optional existing action; no nested pressables. MetricRow is layout of fact rows, not new domain class. |
| `Notice` / `AttentionRow` | Shared visual tone primitive; retain attention filtering/action behavior | Info/warning/error/success; existing AttentionRow composes Notice with exact item/action. No independent WarningCard and InfoCard logic. |
| `StatusChip`, `SegmentedControl`, `ChoiceRow` | Small state/control primitives | Display-only chip; exclusive mode control; checked radio/checkbox row with real state. Do not use button styling to infer selection. |
| `FormField` / `StepProgress` | Compose V2 Input, Text, IconTile; reuse existing field/picker parsers | Label, unit, help/error, optional icon; actual step/total only. |
| `SportIndicator` | Evolve existing component | Sport SVG + visible sport name; circle/chip variants; neutral or discipline tone. |
| `WorkoutSummary` / `NextSession` | Restyle existing compositions | Candidate hero, scheduled summary and same-day compact variants; all receive existing view-model fields. NextSession owns only temporal presentation. |
| `WeekTaskCard`, `WeekContext`, `GoalSummaryRow` | Retain existing compositions | Task/status/action grouping; exact range; actual goal label/callback only. |
| `SessionSequence` | Retain existing composition | Ordered numbered rail/blocks with explicit measures, targets and instructions; no inferred intervals. |
| `ActivitySummary` | Retain; separate from WorkoutSummary | Recorded instant/source, actual measures, execution feedback, HR, coverage Notice, capability-gated correction. |
| `WeekAgenda`, `DayHeader`, `MonthGrid` | Retain; DayRow is agenda layout, not a new scheduler | Full seven dates, natural-height siblings, selected-day detail, accessible compact-calendar alternative. |
| `RpeChoices` / `RpeIndicator` | Retain canonical choice data and tap-save behavior | Number + exact sport-specific description; full-width rows; pending/saved states separate. |
| Zone profile composition + `ZoneTable` | Add when migrating current ZoneProfileScreen | Sport/title/state, current/pending/history sections, value/unit rows with visibility guards. No giant generic proposal/card abstraction. |
| Proposal review composition | Keep `ProposalReviewScreens` | WeekTaskCard + WorkoutSummary + Notice + explicit decisions. No separate data-owning ProposalCard needed. |

SectionHeader is a Text style/layout recipe. FormCard is Card containing fields. HeroCard is Card with focus padding and leading icon; not a new generic component with dozens of optional props. Extract repeated layout only after two real uses. No new controller/state library; no physiology or API work hidden in this migration.

### Concrete card recipes

**Workout candidate:** 24 dp padding at reference width; 64 dp sport circle / 16 dp gap / flexible sport chip and 22/28 title; 16 dp below; duration and effort fact groups with 16 dp gap and thin divider; 16 dp source description; 24 dp Choose then 12 dp Skip. Detail entry remains wherever the current candidate offers it. At <360 dp the sport header stacks; facts wrap; all content survives.

**Scheduled/next workout:** ivory card using same header, 48 dp circle, date/state line, primary measure 28/34, other supplied metrics 16/24, effort and source copy, forest detail action. Same-day siblings use ivory summary rows/cards with 16 dp padding and individual detail action. This replaces the old mandatory full-forest NextSession body: forest belongs primarily to CTA surfaces in the new mockups.

**Activity:** 16 dp padding, 48 dp sport circle next to sport/date, divider 16 dp below; 40 dp metric icon circles and full values; execution/RPE block after next divider; conditional HR; pale inset Notice with 16 dp padding; correction action 16 dp below only if eligible. Do not force all activities to the same height.

**Task/proposal hero:** ivory focus card, status label, 24/30 task title, existing explanation, primary action. Warnings are separate Notice immediately adjacent to the affected group, not absorbed into a green success chip. Active/pending sections have distinct headings and stay independently legible.

**Zone discipline:** 48 dp icon, sport title/status; route InfoRow; active table if visible, pending block with decision controls if present, history below; source/version retained; full-width route/value action. Numeric-free state replaces table with actual explanatory Notice, not blank zero rows.

## 7. Forms from M4

| Part/state | Final treatment and contract |
| --- | --- |
| Label | Persistent 16/22 weight 600 above field; append localized “(optioneel)” using muted normal weight. Required status follows actual contract, not whether the mockup included an asterisk. |
| Field | min 56 dp, radius 12, opaque surface; 1 dp `border.control`. 12 dp horizontal padding; optional 40 dp leading circle + 12 dp gap. Value 16/24. Multiline starts at 112 dp and grows. |
| Unit | Suffix in subtle fill with 1 dp divider; 12 dp side padding. Unit also belongs in accessible label. At narrow widths move unit into label, keep identical meaning. |
| Helper | 14/20 below at 4 dp; aligns with input text when practical. Essential required instructions never rely on placeholder. |
| Focus | Stable 2 dp forest ring reserved inside/outside without moving text; ivory separation on dark controls. |
| Validation/error | Destructive boundary + icon + localized 14/20 message below; retain input. Long forms show error summary and focus first invalid field. No new numeric bounds. |
| Disabled/read-only | Subtle solid fill, readable text, explicit reason if not obvious; no global opacity. Read-only value is not announced as editable. |
| Busy | Existing submit lock, text + spinner with stable layout. Busy is not success. Unknown write outcome remains unconfirmed until existing reconciliation. |
| Submit | Forest 56 dp minimum, full width, grows for labels; 24 dp after last helper. Normal flow by default; measured sticky footer only where current task supports it. |

| Flow | Fields and adaptations which must survive |
| --- | --- |
| Profile/onboarding | Optional first/last names; birth date and resting HR; monitor confirmation; explicit timezone; previous-month hours/week for all three disciplines; goal; zone setup; review. Keep seven persisted steps and upgrade/resume; no weight/height/experience fields. |
| Activity entry | Planned versus deliberate extra choice; sport; actual timestamp with timezone; duration; optional distance; existing external/matching controls when supplied. Save creates activity; subsequent HR/RPE remains its distinct existing operation. |
| Goal | Five supported race types, name/date, discipline distances, total time, optional split times/focus; run time/pace mode retains existing parser/conversion. No new leg/transition allocation. |
| Calibration | Only protocol-returned observation controls: run/bike observation HR and RPE; swim measured time/distance/RPE as required. Completion/interruption, required versus optional blocks and current eligibility remain unchanged. |
| Known zones | Existing source choice, discipline threshold fields/units, optional explicit five-boundary override; blank remains missing. Values form a pending proposal; never activate on save. |
| Check-in | Week, optional context/extraction, blocked days, fatigue, missed-training reasons, each discipline restriction/advice, external sport/time/duration/flags/review acknowledgment. Save context, confirm context and request proposal stay separate. |

Do not move all fields into sheets to mimic the short mockup. Use one form card per meaningful section, a full page for long tasks, and the existing duration picker with accessible large targets. No slider for RPE or precise physiology inputs. No date picker dependency merely to restyle a field.

## 8. Responsive and accessibility rules

| Viewport | Default text | 200% text |
| --- | --- | --- |
| 320 dp | 16 dp gutter, 288 dp content; card padding 16; header actions on separate row; candidate header/facts stack; nav icon above wrapping label; Month uses date-list alternative. | Same font scaling, no clamp; single-column forms/facts/choices; compact art; headings wrap; CTA normal flow; navigation can grow to two label lines. |
| 360 dp | 16 dp gutter, 328 dp content; 16 dp card padding; two fact groups only if contents fit; vertical icon/label nav; Month date-list alternative. | Single-column information; full-width radio/date rows; no dense grid, clipped unit or horizontal-only choice. |
| ~393 dp | 16 dp gutter, 361 dp content; 24 dp hero/form padding, 16 dp ordinary card; reference composition. Horizontal icon/label nav only when all labels fit their thirds. | 16 dp card padding; reflow utility header, chips, facts and buttons; compact art; Month date list. |
| 412 dp | 16 dp gutter, 380 dp content; reference card padding; horizontal nav if measured fit. No extra dashboard column. | Same reflow rules; vertical nav labels if needed; date list instead of seven narrow cells. |

At widths above phone layouts retain centered 600 dp reading width with 24 dp outer gutters; landscape can bleed beyond it. Never reduce the typography token or `maxFontSizeMultiplier` to preserve a single line. Use natural text height, not captured PNG proportions.

**Month grid feasibility:** seven real 48 dp targets need 336 dp. At 393 dp, 361 dp content minus 8 dp grid padding each side leaves 345 dp, sufficient for seven ~49 dp cells; use no intercell gaps. At 360/320 dp it does not fit. For content width <352 dp or text scale >=1.5, retain Month mode/range/selection but render all month dates as chronological full-width date rows grouped by week, with full date, current/today label, actual count and rest status; selected-date details follow the selected group. This is a layout alternative over identical date callbacks, not a new agenda data source. Outside-month dates retain the current range/callback semantics. No overlapping hit-slop trick.

Month indicators: forest outline + pale fill + selected semantics for selected date; warm tint + explicit Today text in date detail/accessible label for today; if both, combine outline and Today label. Number/count/rest labels remain available; a dot can supplement, never replace essential count or state. Do not render tiny letters as the sole sport key.

Every interactive target >=48 × 48 dp, including circular arrows, duration controls, choice cells and close. Logical reading order: header → status/context → object/fields → warning → actions → navigation. Mark headings, tabs, radio/checkbox state, busy/disabled and error messages accurately. Avoid nested accessible card/action duplication. Artwork and decorative icons are excluded. Return focus to origin; announce save result once; preserve full names, instructions, warnings and units with no critical truncation.

All informative text must reach 4.5:1; controls/focus >=3:1. Check composited artwork, not only isolated token values. Reduced motion uses immediate transitions/brief opacity; no landscape movement, shimmer or bounce. Existing functional animations/gesture alternatives and cancellation remain. No new data in accessibility labels, logs or analytics; private training load and hidden zone values stay absent everywhere.

Navigation sits in a layout footer, visually floating with margins, rather than overlaying the final card. If existing absolute composition remains, reserve its actual measured height plus safe-area inset and 16 dp end gap, counted once. Existing detail footprint/navigation locks must remain. With keyboard, retain current route behavior and scroll the focused field and submit clear of it; do not invent navigation on keyboard dismissal. Global feedback reminder lives below top safe area and above page content, expands with text and pushes the header down.

## 9. Mockup versus functional conflicts

| Conflict | Visual reference | Functional truth | Implementation rule |
| --- | --- | --- | --- |
| Sparse scaffold versus composed cards | All M1–M6 | Scaffolds already implement states | Replace visual treatment; do not keep flat text-only styling as “parity.” |
| No Week/Home mockup | M5/M6/M3 supply reusable parts | Week has state-selected task/session/attention | Use explicit Week recipe in mapping; do not invent a seventh source image. |
| One candidate/activity | M5/M6 | Same templates can recur; history/same-day workouts can be many | Natural lists keyed by occurrence/activity, never deduplicate by title/template. |
| Missing duration | M5 duration; M6 duration | Distance-only workout can omit time | Show distance; remove clock/time block, never estimate swim duration. |
| Extra metrics absent from mockup | M6 | Activity may have distance, pace, HR and coverage | Add InfoRows for supplied fields, grow card; never drop them to match height. |
| Missing HR | M6 has 140 bpm | HR can be absent; required observation is contextual | Omit nonexistent history value; keep appropriate feedback field/helper. No 0 bpm. |
| Overflow dots | M6 | No evidenced activity menu in reference flow | Omit dots and target until real capability exists; no invented delete/share. |
| Correction button on every sample | M6 | Current-week eligibility/locks govern correction | Conditional action only; blocked Add remains readable with feedback prerequisite. |
| Hero association/count | M3 | Existing public context can supply discipline count and plan association | Use those exact fields; omit unavailable group. Do not infer subscription or physiological readiness. |
| RPE-guided numeric-free zones | M3 | Readable existing Bike/Swim state; new RPE-only setup is unavailable | Show actual state, retain approved current setup paths; no new route. |
| Step 1 on profile reuse | M4 | Profile editor is not necessarily an onboarding step | Progress only with actual step model; do not announce “1 of 7” on unrelated edit. |
| Back on onboarding | M4 | Completion/upgrade gate cannot be bypassed | Render only currently valid back/exit action; no new skip. |
| Exit label | M3/M4 “Uit” | Existing action is sign out | Preserve callback; accessible localized “Afmelden”; no close/disable interpretation. |
| No warning in sample | M5/M6 | Public warning/error may coexist with task or saved activity | Insert full Notice near affected action; do not hide under decoration. |
| Pending versus approved | Sample schedule appearance | Choosing, placement, pending proposal and active plan differ | Explicit labels; separate active/pending sections; approval only through existing confirmation. |
| Rest versus empty | M1 empty rows | Explicit planned rest differs from no scheduled workout | Preserve rest label/reason and supplied sibling coexistence; never infer rest. |
| Calendar dot ambiguity | M2 | Counts, selected/today/rest/sport have distinct meanings | Count/labels/accessible date detail retain meaning; no readiness/completion dots invented. |
| Narrow seven-column calendar | M2 | Real 48 dp targets and 200% text required | Use the width-triggered month date-list layout above. |
| Cropped bottom content | M2/M3/M4 | Last card/actions remain reachable | Scroll clear of bar/keyboard; no fixed screenshot-height card. |
| Bottom nav absent in crops | M1/M3/M4/M5 | Integrated shell has existing route/task visibility and locks | Restyle that shell; absence in a crop is not routing authorization. |
| Development UI subtitle | M5 and functional images | Development-only diagnostic control | Retain eligibility/locks in diagnostic footer; never production hero copy. |
| Mojibake/source text | Functional catalog captures | Encoding artifacts are not intentional design | Do not copy replacement glyph styling; preserve source data and separately report upstream text defect, without silently rewriting prescriptions. |
| Stronger font than old docs | All mockups | No supplied original font file/name | Use resolved system-font hierarchy below; no asserted font identity or unlicensed asset. |
| Landscape in CTA | M6 | Button still conveys one existing action | Decorative bounded inset only; no data visualization or hit target. |
| Settings/goal confirmation | No source image | No implemented consumer screen in index | Component recipe only; behavior/navigation unresolved, no route creation. |
| Completed check-in | Missing capture | Staging mismatch prevents proposal result | Do not show success from confirmed context; unresolved success reference remains open. |

## 10. Old documents: preserve, but prevent visual regression

The old files remain unmodified. This table is the explicit supersession record; future tasks must read it before treating their wireframes as visual instructions.

| Older document/portion | Functionally still authoritative where consistent with latest decisions | Visually superseded |
| --- | --- | --- |
| `WOMBO_UI_V2_SPEC.md` §§1,3–15,17–19 | Public-data fidelity, explicit actions, state separation, parser precision, pending/revision/idempotency, privacy and accessibility constraints. Older capability claims must be checked against current index/roadmap. | §2 “not imagery,” flat-supporting-section dominance, no repeated soft card shadows; §4 forest session hero and sparse wireframe; §§6,12,14 card/form hierarchy; §16 one-shadow restriction; §17 old rollout order. Final mockups/recipes replace these. |
| `WOMBO_UI_V2_SCREEN_MAP.md` journey and screen descriptions | Actual supported fields, actions, optional/absent values, errors, task origin and separate confirmations. | All composition/typographic/card/navigation appearance instructions where this handoff differs; flat-profile-only presentation, compact sparse headers, old three-group onboarding visuals. |
| `WOMBO_UI_V2_TOKENS.md` §§1–10 | Semantic roles, numeric precision, label/selection semantics, canonical RPE, >=48 dp, contrast, text scaling, reduced motion. | Exact values explicitly MODIFIED in final tokens; shadow default, optional final icons, smaller type hierarchy, flat dominant surfaces. UNCHANGED values are enumerated, not blanket discarded. |
| `WOMBO_UI_V2_WEEK_VISUAL_REFINEMENT.md` state/action analysis | Existing Week source fields, state priority, actual warnings, occurrence identity, no invented data, callbacks/locks and preservation of reminder. | §§5–9 textual wireframes as appearance, mandatory forest NextSession, flat tools, no hero artwork, text-chevron acceptable as final icon treatment, fixed old-token requirement. Its “no bottom-tab shell” scope restriction does not erase the subsequently integrated TrainingLayout or current mockup appearance. |

Also update interpretation of architecture/dependency documents: their separation of presentation/state still applies, but read current integrated source rather than re-extracting already existing controllers. “No new V2 gradient” yields to SVG landscape fades; blur remains unnecessary. Earlier proposed goal-achieved UI is not proof of an implemented consumer flow. The latest screenshot index leaves that destination unresolved.

## 11. Resolved defaults and remaining gates

Resolved visual defaults: system sans hierarchy, warm off-white/ivory palette, forest actions, outline UI icons with local sport extensions, two reusable landscape assets, 15 screen families, responsive month list alternative, existing navigation semantics. Implementers should not invent another visual direction.

Open asset verification: exact original font/artwork files were not supplied; the specified system-font and SVG reconstruction are the working design. Actual SVG path craft and exact Lucide pin belong to foundation review, with side-by-side mockup comparison. Do not call those runtime assets delivered by this document.

Open product/reference questions: completed check-in after staging upgrade mismatch; scope/navigation of standalone Settings; goal-achievement consumer confirmation. No behavior is defined for these gaps. Linked integration history and executable calibration/result captures are additional uncaptured variants, not among the three claimed missing requested states. Public fields/actions in those flows must be source-verified when implemented; use existing patterns without fabricated results.

This deliverable does not close emulator, 200% text, TalkBack, physical-device, backend or release gates. Verification performed for these documents is recorded in the implementation sequence.
