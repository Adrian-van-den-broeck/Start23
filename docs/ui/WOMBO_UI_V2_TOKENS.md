# Wombo V2 design tokens and component rules

Design-only companion to the [specification](WOMBO_UI_V2_SPEC.md). Values are proposed tokens, not edits to `mobile/src/theme/tokens.ts`. Units are dp for layout and scalable sp for type. Light appearance is the defined V2 theme; a new dark theme is not implied.

## 1. Color

Retain the existing warm canvas, ivory surface, forest primary and deep ink. Add clear semantic roles rather than a large new palette.

| Token | Value | Role |
| --- | --- | --- |
| `background` | `#F4F2EC` | App canvas; existing canvas retained |
| `surface` | `#FFFEFA` | Session cards and form surfaces |
| `surface.elevated` | `#FFFFFF` | Sheets and the single lifted object |
| `surface.subtle` | `#E9EEE8` | Quiet inset grouping and disabled fill |
| `primary` | `#123F39` | Primary action, selected controls, occasional Today surface |
| `primary.pressed` | `#082E2A` | Pressed primary fill |
| `primary.soft` | `#DCEBE3` | Selection background and gentle brand grouping |
| `secondary` | `#DCEBE3` | Secondary action fill, with `primary` label; not a second dominant hue |
| `text` | `#102B28` | Titles, body, important values |
| `text.muted` | `#5D706B` | Secondary text; also placeholder text |
| `text.inverse` | `#FFFEFA` | Text on primary forest |
| `border` | `#D9E0DA` | Decorative separators, not sole interactive boundary |
| `border.control` | `#70837D` | Input/control boundary where a boundary is needed |
| `focus` | `#123F39` | 2 dp focus indicator; ivory outer separation on forest |
| `success` | `#2D6A52` | Confirmed success text/icon |
| `success.soft` | `#E4F0E8` | Success background |
| `warning` | `#79520E` | Attention text/icon |
| `warning.soft` | `#F8EED6` | Reviewable warning background |
| `destructive` | `#A23B2A` | Failed action, invalid input, destructive action |
| `destructive.soft` | `#FBE5DF` | Contextual failure background |
| `sport.run` | `#8F442F` | Run marker/icon/text with visible “Lopen” label |
| `sport.run.soft` | `#F5E8DF` | Run icon tile |
| `sport.bike` | `#405C45` | Bike marker/icon/text with visible “Fietsen” label |
| `sport.bike.soft` | `#E6ECE2` | Bike icon tile |
| `sport.swim` | `#285E70` | Swim marker/icon/text with visible “Zwemmen” label |
| `sport.swim.soft` | `#E2EDF0` | Swim icon tile |
| `scrim` | `rgba(16,43,40,0.28)` | Sheet backdrop only; no background blur |

Intensity is separate from sport. Use “Rustig” / “Intensief” from the supplied bucket, with a small neutral or amber treatment. Do not map sport colors or computed gradients to physiological zones. Zone rows retain labels, units and values; five traffic-light colors are unnecessary.

### Contrast policy and checked pairs

Target at least 4.5:1 for all informative text, including small metadata; Wombo does not rely on the large-text exception to make core copy legible. The external reference defines the 4.5:1 normal-text and 3:1 large-text minimums. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

Ratios below are rounded display values from sRGB relative-luminance calculations; acceptance uses the unrounded value. These are token-level checks, not a rendered-screen accessibility audit.

| Foreground / background | Approximate ratio | Approved use |
| --- | --- | --- |
| `text` / `background` | 13.42:1 | Body/title |
| `text.muted` / `background` | 4.70:1 | Supporting text |
| `text.muted` / `surface` | 5.21:1 | Card supporting text |
| `text.inverse` / `primary` | 11.59:1 | Primary button and Today surface |
| `primary` / `primary.soft` | 9.49:1 | Secondary/selected labels |
| `success` / `success.soft` | 5.44:1 | Saved/confirmed |
| `warning` / `warning.soft` | 6.01:1 | Reviewable warning |
| `destructive` / `destructive.soft` | 5.44:1 | Error |
| `sport.run` / `sport.run.soft` | 5.76:1 | Run label |
| `sport.bike` / `sport.bike.soft` | 6.16:1 | Bike label |
| `sport.swim` / `sport.swim.soft` | 6.02:1 | Swim label |
| `border.control` / `surface` | 3.98:1 | Control outline |

Recalculate any additional pair used during implementation. Do not use muted text on a tinted surface without checking it; prefer `text`. Do not put amber highlight/yellow text on white. Decorative `border` is deliberately subtle and cannot communicate focus, error or selection alone. Disabled controls use explicit state plus `text` or `text.muted` on `surface.subtle`, not a blanket 45% opacity on the entire control. If custom focus sits on forest, use an ivory outline with separation.

## 2. Typography

Use the native system sans-serif stack for the first slices: no new font package or download. Weight and composition establish the identity. Reserve bold for hierarchy rather than making every label heavy.

| Token | Size / line height | Weight | Use |
| --- | --- | --- | --- |
| `display` | 32 / 38 | 700 | Auth welcome or single Today emphasis; at most once per screen |
| `screenTitle` | 28 / 34 | 700 | Screen purpose |
| `sectionTitle` | 20 / 26 | 600 | Day/group headings |
| `cardTitle` | 18 / 24 | 600 | Session name |
| `body` | 16 / 24 | 400 | Instructions and form values |
| `supporting` | 14 / 20 | 400 | Units, dates, purpose, help |
| `caption` | 12 / 16 | 500 | Short nonessential metadata only |
| `label` | 14 / 20 | 600 | Persistent field labels, state labels |
| `button` | 16 / 22 | 600 | Action labels |
| `numeric` | 28 / 34 | 600 | One key duration/distance statistic |
| `numeric.compact` | 20 / 26 | 600 | Counts and sequence measures |

Use tabular digits where supported for duration, pace and changing counts. Normal letter spacing; no decorative uppercase headings or condensed athletic type. Keep units adjacent and spoken. Dates and pace must never be smaller than supporting text. Keep critical warnings at body/supporting size. Allow full titles in detail and wrapping titles in schedule; list truncation must have an accessible full name and detail destination.

At larger accessibility sizes, line heights scale, cards grow, chips wrap and two-column forms become single-column. No maximum font-scale clamp. Do not force a primary button label into one line. Preserve semantic reading order when visual groups stack.

## 3. Spacing, layout and radii

Spacing scale: **4, 8, 12, 16, 24, 32, 48 dp**. Use 4 for icon/text association, 8 within compact metadata, 12 within control groups, 16 card padding/gutters, 24 between sections, 32 for major separation and 48 only for intentional empty-state spacing. Avoid 48 dp padding around routine forms.

Phone gutter: 16 dp; wider/tablet layouts may use 24 dp and a centered reading width of 600 dp. No dashboard columns on narrow phones. Cards use 16 dp padding; the singular focus card can use 20–24 dp. Seven-day agenda has a 48 dp date column, 12 dp gap and flexible content. Section heights follow content, including multiple sessions.

Radius hierarchy: **8 dp** small icon tile/inset, **12 dp** fields/buttons, **20 dp** cards, **28 dp** sheet top corners, **999 dp** compact status pills/selected day. Rounded controls must still look actionable. Do not wrap every section in a pill or put a rounded card inside another rounded card.

Primary button minimum height: 52 dp. Other buttons, icon hit targets and interactive rows: minimum 48 dp. Field minimum height: 52 dp plus persistent label. Tabs: 56 dp minimum above bottom safe area; each destination has icon + label and a full-width target. Bottom task action area: 12 dp top, 16 dp horizontal, 12 dp plus safe-area bottom; add equivalent content inset so it never covers the last item. With large text/keyboard, allow it to grow or enter normal flow.

A 7 × 48 dp control row needs 336 dp before gaps. Availability wraps when it does not fit. Month uses the explicit alternate layout from the main specification. Hit slop must not create overlap with another action.

## 4. Surfaces

| Surface | Appearance | When to use |
| --- | --- | --- |
| Flat section | Canvas, heading and spacing; optional divider | Profile groups, week summary, day groups, zone rows, instructions |
| Card | Ivory surface, radius 20, no shadow by default | A selectable session or focused activity summary |
| Focus card | Forest or ivory with clear hierarchy; one per screen | Today/next task, not every workout |
| Elevated card | White, radius 20, Android elevation target 2; optional shadow opacity .08, offset 0/2, blur radius 8 | Dragged object only or one floating summary where necessary |
| Sheet | White, top radius 28, scrim; elevation target 6, shadow opacity .12, offset 0/4, blur radius 16 | Bounded date/action choices and contextual help |

Complex tasks—workout execution detail, calibration, onboarding, activity entry—use full-height pages rather than nested sheets. A sheet has one scrolling owner, a title, visible close/back, safe-area padding, accessible focus containment and Android back dismissal. At large text it can become full-height. Dismissal never approves or saves implicitly. Unsaved transient values follow existing form behavior; no claim of new cross-restart local draft persistence.

## 5. Buttons and form controls

| Component | Default | Selected / error / busy rules |
| --- | --- | --- |
| Primary button | Forest, ivory label, radius 12, 52 dp minimum | Pressed deep forest; loading retains width and text plus spinner; no duplicate submissions |
| Secondary button | Soft green fill, forest label | Selected semantics only when it is truly a selection control |
| Tertiary button | Text on canvas, 48 dp target | For help/back/details; underline or clear row chevron where link-like |
| Destructive button | Destructive label or solid destructive fill with ivory label in final confirmation | Name consequence; red is not used for Skip or ordinary decline |
| Icon button | 20–24 dp icon centered in 48 dp target | Accessible verb/object label; selected/disabled/busy state explicit |
| Disabled/loading | Subtle solid fill and readable label; reason adjacent if not self-evident | Never spinner alone, opacity-only state or “saved” before acknowledgment |
| Text input | Persistent 14 sp label, 16 sp text, white fill, control border, radius 12 | Focus 2 dp outline without layout shift; error icon/message below; optional label explicit |
| Segmented control | Bounded exclusive modes, minimum 48 dp segments | Forest selected segment plus text and checked/selected state; wrap/stack at large text |
| Chips | Discrete multiple-choice categories with 48 dp hit target | Check mark and fill when selected; no color-only distinction |
| Weekday selector | Weekday/date with checkbox semantics | Check, solid selected fill, natural wrap; show available-day count, never workout count |
| Numeric input | Unit in label/suffix; appropriate keyboard; locale-aware display | Blank is not zero; preserve accepted decimal rules and existing validation bounds |
| Time input | Compact `hh : mm : ss` entry with separately labeled fields or existing picker presented compactly | Preserve null versus zero and existing seconds precision; optional clear action |
| Run pace | `min : sec` with `min/km` label, formatting example on focus/help | Preserve existing parser/formatting; no decimal-minute ambiguity |
| Date/time choice | Locale date/time button plus accessible typed fallback | Week date and actual activity instant use different labels; no silent timezone assumption |
| RPE choices | Ten full discipline-specific descriptions with canonical number | Exact text and mapping; selected check and saved/in-flight status; no slider |

No slider is needed in the baseline V2 flows. Discrete RPE, precise HR, pace, dates and duration are poorly served by sliders. Future use requires a genuinely approximate continuous value and accessible exact-value alternative; this document invents none.

## 6. Signature Wombo components

| Component | Composition and distinguishing feature | Variants |
| --- | --- | --- |
| `WeekContext` | Quiet date range, one state label, previous/next/current actions | Active, proposal, no plan, stale |
| `NextSession` | Source sport/name, one key measure, effort and clear detail action | Single, same-day siblings, next date, rest/no scheduled workout |
| `WorkoutSummary` | Small sport tile, source title, metric/effort line, optional purpose, status | Candidate, accepted draft, planned, complete, cancelled, unavailable |
| `SessionSequence` | Vertical rail with ordered source segments; measure/target then instructions | Time-based, distance-based, mixed, missing detail |
| `WeekAgenda` | Seven natural-height date sections and consistent session rows | Approved read-only, active movable, proposal review |
| `AvailabilityDays` | Explicit Monday–Sunday checks with wrapping and selected count | New choice, explicit reuse, validation |
| `AttentionRow` | Short fact + affected object + verb | Feedback, approval, zones, check-in, warning |
| `RpeChoices` | Canonical number with exact sport-specific description | Save-on-tap, in flight, stored, eligible correction |
| `ZoneTable` | Five labeled rows where supplied, separate units per metric | Active, pending, hidden, historical; no computed color scale |
| `SaveStatus` | Stable text near action with subtle status icon | Saving, confirmed, refresh needed, outcome unknown, retry, complete |

These names are implementation mapping suggestions, not new files or public API schemas. Components receive existing public data and actions. They never own physiological rules or silently infer missing state.

## 7. Feedback primitives

Inline validation: concise error immediately below the field, invalid state for accessibility, entered value retained. Warning: amber icon/title and brief consequence; associated with the relevant proposal/session. Error: destructive icon/title plus next action; no all-screen red banner for a local issue. Success: check and persistent textual state near the affected object, not only a disappearing toast. Empty: one sentence, one relevant action, no large illustration. Skeleton: static neutral blocks shaped like actual content; hide fake content from screen readers and announce one loading status.

Long warnings may expand supporting explanation, but the reason and next action remain visible. Saved state persists after animation. An unavailable action keeps a readable reason instead of a mysterious disabled button. No invented countdowns, loading percentages or claims that an ambiguous network result has failed.

## 8. Iconography

Recommend **Lucide outline** as the coherent family for future V2 assets, using 24 dp view boxes, approximately 2 dp stroke and rounded ends. Its published guide describes a consistent vector family and platform packages; this is an asset recommendation, not package-install approval. [Lucide guide](https://lucide.dev/guide/).

Use semantic icons for week, calendar, activity history, person, run, bike, swim, check, warning, close, chevrons and drag grip. Exact sport glyph selection should be visually reviewed within that family; pair each sport with text, even if the symbol is imperfect. Provider logos remain provider identity assets rather than a second UI icon set. No emoji, decorative stars, initial-letter circles masquerading as icons, or heavy filled icons mixed with thin outlines.

Use 20 dp inline, 24 dp navigation/action. Purely decorative icons are excluded from the accessibility tree. Icon-only actions always have a localized label. State icons supplement words, never replace them. Do not replace clear headings with a row of unexplained pictograms.

## 9. Motion

| Interaction | Proposed timing / motion | Reduced-motion alternative |
| --- | --- | --- |
| Press | 90 ms fill/opacity feedback; no whole-screen scale | Immediate fill |
| Candidate arrival | 160 ms opacity + at most 8 dp translation | Immediate/80 ms opacity |
| Choose/pass | 180 ms restrained lateral departure; no rotation | Immediate state replacement with saving label |
| Change week | 160 ms crossfade after state selection | Immediate heading/state update |
| Expand supporting detail | 180 ms height/opacity where stable | Immediate layout |
| Drag pickup | 100 ms to at most 1.02 scale and single elevation | Outline + origin/target labels |
| Drag return/rejection | 180 ms ease-out return | Immediate origin restoration |
| Drop success | 140 ms settle; no bounce | Immediate authoritative placement |
| Success | 120 ms check fade; state label remains | Immediate check/text |
| Sheet | 220 ms vertical transition, 160 ms exit | Immediate sheet + scrim |
| Loading to content | 140 ms opacity, stable dimensions | Immediate content |

Use ease-out for entry and ease-in for exit; no overshoot or elastic bounce. These are visual durations, not network timeouts, safety delays or gesture activation thresholds. Haptic selection may accompany selection/pickup and one completion; no vibration on every drag pixel or repeated retry. Respect system reduced-motion settings and preserve functional feedback without haptics.

## 10. Accessibility verification targets

Use at least 48 × 48 dp focusable touch targets, following Android's published guidance. [Android touch target guidance](https://support.google.com/accessibility/android/answer/7101858?hl=en).

Later visual QA must cover 320, 360 and 412 dp widths, system default and 200% text, Dutch and English, keyboard shown, gesture navigation safe area and TalkBack. There must be no cropped weekday, overlap, clipped last workout, inaccessible horizontal-only operation or obscured Save button. Screen readers announce full date, sport, workout name, measure, state and available action without duplicate announcements from nested elements.

Checkbox/radio/tab semantics reflect actual multiple/exclusive selection. Screen transitions focus the heading; sheet dismissal restores the trigger; rejected moves return focus to the moved occurrence; save errors focus/announce the relevant message without stealing focus repeatedly. Status is expressed in text and shape as well as color. History uses its original versioned values. Accessibility descriptions never contain hidden zone values or private training-load data.
