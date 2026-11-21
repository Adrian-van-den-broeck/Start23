# Wombo UI V2 — final token evolution

Date: 2026-10-06. Design values for later implementation; runtime tokens unchanged.

Read with the [final visual system](WOMBO_UI_V2_FINAL_VISUAL_SYSTEM.md). Baseline is [the prior token document](WOMBO_UI_V2_TOKENS.md), cross-checked against the integrated runtime `mobile/src/ui-v2/tokens/{colors,typography,layout,motion,states}.ts`. Keep one typed V2 source; do not change V1 globals or add parallel Tailwind token values.

UNCHANGED means retain the prior value and meaning. MODIFIED means replace the V2 value/usage in a later visual batch. NEW means a missing reusable role. These are resolved implementation recommendations derived from raster mockups, not sampled original design variables. dp for layout, scalable sp for text.

## Colors

| Token | Change | Previous → final | Application |
| --- | --- | --- | --- |
| `background` | MODIFIED | `#F4F2EC` → `#FAFAF6` | Brighter warm off-white canvas seen across mockups. |
| `surface` | UNCHANGED | `#FFFEFA` | Ivory cards and input surfaces. |
| `surface.elevated` | UNCHANGED | `#FFFFFF` | Sheets; optional grid surface. |
| `surface.subtle` | UNCHANGED | `#E9EEE8` | Read-only/disabled and quiet grouping. |
| `primary` | MODIFIED | `#123F39` → `#124D43` | Forest action, selection and identity. |
| `primary.pressed` | UNCHANGED | `#082E2A` | Pressed primary. |
| `primary.soft` | MODIFIED | `#DCEBE3` → `#E7EFE8` | Pale circle, segmented track and secondary fill. |
| `secondary` | MODIFIED | `#DCEBE3` → alias `primary.soft` | One pale green role, not another color. |
| `text` | MODIFIED | `#102B28` → `#071E22` | Strong nearly-black headings and body. |
| `text.muted` | MODIFIED | `#5D706B` → `#526874` | Cool slate supporting copy. |
| `text.inverse` | UNCHANGED | `#FFFEFA` | Primary labels. |
| `border` | MODIFIED | `#D9E0DA` → `#DFE6E1` | Quiet decorative rules only. |
| `border.control` | UNCHANGED | `#70837D` | Accessible input/control edge. Raster mockup's lighter line is not sufficient as sole field boundary. |
| `focus` | MODIFIED | `#123F39` → alias `primary` | Focus ring; inverse ring on forest. |
| `success` / `.soft` | UNCHANGED | `#2D6A52` / `#E4F0E8` | Acknowledged result only. |
| `warning` / `.soft` | UNCHANGED | `#79520E` / `#F8EED6` | Supplied reviewable warning. |
| `destructive` / `.soft` | UNCHANGED | `#A23B2A` / `#FBE5DF` | Error and confirmed destructive operation. |
| `sport.run` / `.soft` | UNCHANGED | `#8F442F` / `#F5E8DF` | Rust run accent, particularly M6. |
| `sport.bike` / `.soft` | UNCHANGED | `#405C45` / `#E6ECE2` | Bike accent where discipline tint is used. |
| `sport.swim` / `.soft` | UNCHANGED | `#285E70` / `#E2EDF0` | Swim accent where discipline tint is used. |
| `scrim` | UNCHANGED | `rgba(16,43,40,0.28)` | Existing modal backdrop, no blur. |
| `landscape.sage` | NEW | `#76A396` | Decorative ridge color only, with asset-layer opacity. |
| `landscape.sun` | NEW | `#FFE3A6` | Decorative sun only; never text or status. |

No new separate colors for hero, profile, calibration, pending or each screen. Info uses primary/text on primary.soft. Pending uses neutral text and explicit wording. Today uses existing warning.soft with text, **without warning semantics**. Selected date uses primary.soft/primary outline. Sport accent never encodes physiological zone or effort.

Translucency is bounded: pale header pills may use the opaque primary.soft default or 92% alpha of that color over canvas, never over live content. Cards, fields, warnings and navigation text area stay opaque. The appearance comes from pale layering and SVG fade, not runtime blur.

## Typography

Use the native system sans, standard width, normal letter spacing, scalable line heights; explicit weights below. No font download is required. The raster mockups do not identify a font, so do not assert a match to a proprietary family. At most one display-level content heading per screen; centered WOMBO uses screenTitle weight, not a second huge hero.

| Token | Change | Previous size/line/weight → final | Use |
| --- | --- | --- | --- |
| `display` | MODIFIED | 32/38/700 → **36/42/800** | M4/M5 task emphasis or M6 root title. |
| `screenTitle` | MODIFIED | 28/34/700 → **30/36/800** | Calendar/root purpose, branded wordmark. |
| `sectionTitle` | MODIFIED | 20/26/600 → **24/30/700** | Recent, disciplines, task-card heading. |
| `cardTitle` | MODIFIED | 18/24/600 → **22/28/700** | Full candidate/workout/sport name. Compact list title uses body with 600 weight. |
| `body` | UNCHANGED | **16/24/400** | Instructions, form values, source content. |
| `supporting` | UNCHANGED | **14/20/400** | Date, help, source metadata, never smaller for crucial values. |
| `caption` | UNCHANGED | **12/16/500** | Nonessential eyebrow only. |
| `label` | MODIFIED | 14/20/600 → **16/22/600** | Persistent form/status label. Compact chip can use supporting with 600. |
| `button` | MODIFIED | 16/22/600 → **18/24/600** | Primary and secondary task CTA. |
| `numeric` | UNCHANGED | **28/34/600** | Primary measure; tabular digits. |
| `numeric.compact` | UNCHANGED | **20/26/600** | Secondary count/date; tabular digits. |
| `navigationLabel` | NEW | **14/20/600** | All three tab labels; always visible and scalable. |

No fixed line counts on critical headings, instructions or actions. Do not use `adjustsFontSizeToFit` to force screenshot proportions. Short uppercase eyebrow such as M3's profile label is allowed at caption size with 1 sp tracking; long titles and status text remain sentence case. Units stay adjacent and accessible. All weight changes must render on both target platforms; do not simulate bold with multiple text layers.

## Spacing and radii

| Role | Change | Final |
| --- | --- | --- |
| Spacing scale | UNCHANGED | 4, 8, 12, 16, 24, 32, 48 dp; do not add a per-screen spacing scale. |
| Phone gutter | UNCHANGED | 16 dp at all four specified widths. |
| Wider gutter / reading width | UNCHANGED | 24 dp / max 600 dp. |
| Standard card padding | UNCHANGED | 16 dp. |
| Focus card padding | UNCHANGED | 24 dp at >=393 dp and default font; 16 dp below or at large text. |
| Form padding | NEW role, existing value | Alias focus padding, not new numeric token. |
| Section separation | UNCHANGED | 24 dp; major heading transition 32 dp. |
| Field group separation | NEW role, existing value | 24 dp from end of help/error to next label; label→field 8, field→help 4. |
| `radius.inset` | UNCHANGED | 8 dp for small inset details. |
| `radius.control` | UNCHANGED | 12 dp fields/date choices. |
| `radius.button` | NEW | 16 dp buttons; separates field radius from softer CTA. |
| `radius.card` | UNCHANGED | 20 dp. |
| `radius.sheet` | UNCHANGED | 28 dp top corners. |
| `radius.pill` | UNCHANGED | 999 dp nav selection, profile capsule, segments/status; circles use equal measured sides. |

Avoid card-in-card inflation: only an info/feedback inset or selected/pending value group may have a secondary tinted surface inside a card. Ordered workout blocks and zone rows use separators/rail, not a separate elevated card for each line.

## Borders and shadows

| Role | Change | Final |
| --- | --- | --- |
| Decorative line | UNCHANGED width; modified color | 1 dp `border`; not an interaction boundary. |
| Control edge | UNCHANGED | 1 dp `border.control`; selected/focus 2 dp primary without layout shift. |
| Card shadow | MODIFIED usage | Formerly absent except lifted object; now large ivory cards may use one soft level: black/forest shadow opacity .06, offset 0/3, radius 12; Android elevation target 2. |
| Floating nav shadow | NEW usage, shared level | Same card shadow; no second stacked shadow on selected segment. |
| Sheet/lift shadow | UNCHANGED | Opacity .12, offset 0/4, radius 16; Android elevation target 6. |
| List/field/icon-circle shadow | UNCHANGED absence | None. |

Platform shadow renderings are approximate equivalents; compare visual softness, not pixel-identical blur. Use a thin ivory/nav boundary where needed; avoid shadow plus dark border on every card.

## Icons, controls and navigation metrics

| Role | Change | Final |
| --- | --- | --- |
| Inline icon | UNCHANGED | 20 dp (16 dp only noninteractive state glyph). |
| Action/nav icon | UNCHANGED | 24 dp. |
| Hero sport icon | NEW | 32 dp. |
| Stroke | UNCHANGED | 2 units in a 24-unit viewBox, rounded caps/joins. |
| Icon discs | NEW | 40 dp field/metric, 48 dp row/sport, 64 dp focus sport. Pale circles replace old square/letter/scaffold markers. |
| Icon-to-text gap | UNCHANGED value | 12 dp normal; 8 dp navigation; 16 dp hero. |
| Minimum touch target | UNCHANGED | 48 × 48 dp, nonoverlapping. |
| Primary CTA | MODIFIED | Min 52 → **56 dp**; padding horizontal 16, vertical 16; height grows. |
| Secondary CTA | MODIFIED | Min 48 → **52 dp**; same label scale; grows. |
| Field min height | MODIFIED | 52 → **56 dp**, excluding external label/help. |
| Icon button | UNCHANGED | 48 dp actual target; artwork 24 dp. |
| Segmented track | NEW metric | 4 dp inset, min 56 dp overall, each segment >=48 dp. |
| ActionRow min height | MODIFIED composition | 64 dp with 48 dp disc; grows with 12 dp vertical padding/content. Plain text row remains >=48 dp. |
| Bottom nav | MODIFIED | Old min 56 rectangular strip → capsule min 64 dp content height, 4 dp internal padding, 12 dp outer horizontal margins, 8 dp above safe-area bottom. |
| Nav destinations | MODIFIED | Equal thirds, min 56 dp high; horizontal icon+label at default text only when all fit; otherwise icon above label with 4 dp gap. Selection fills entire rounded destination. |
| Nav reserve | MODIFIED | Actual measured bar + outer vertical spacing + bottom safe-area inset, once. Prefer footer in layout flow. |
| Task action inset | UNCHANGED | 12 dp top, 16 horizontal, 12 + safe-area bottom if sticky; normal-flow actions have no extra fixed reserve. |
| Header utility target | NEW metric | min 48 dp; Profile pill horizontal padding 16, icon gap 8, chevron 20. |
| Artwork | NEW | 140 dp normal, 96 compact, max 180; final 56 dp fade. |

Navigation horizontal fit is measured using localized text at current font scale. At 320/360 dp or 200% text, use icon-above-label consistently for all three. Wrap long labels, allow bar height to grow and remeasure; never remove inactive labels or shrink their fonts. No unsupported counts/badges.

## Motion retained

UNCHANGED: prior motion tokens and reduced-motion behavior. Press 90 ms fill, content arrival 160 ms / <=8 dp, choice departure 180 ms, sheet 220 ms in / 160 ms out, success 120 ms fade. These are presentation durations, never request timers. NEW landscapes are static. No CTA shimmer, animated sun, parallax, pulsing status or continuous gradient.

## Contrast acceptance

Checks use WCAG relative luminance arithmetic, without rounding before comparison. Require >=4.5:1 informative text and >=3:1 control/focus edges. Decorative borders/sun are deliberately exempt because they carry no information. Calculate source values rather than relying on the old document's ratios after palette changes.

Required pairs: text and muted on background/surface; primary on primary.soft; inverse on primary and primary.pressed; info text on primary.soft; success/warning/destructive on their soft fills; each sport text on its soft fill; border.control on surface; inverse focus on primary. Every listed pair is checked in the documentation verification record. Rendered/translucent/landscape contrast remains a later emulator gate. If a compound background fails, add an opaque surface/veil; do not weaken the contrast target.
