# Slice 2C evidence index

These are original native PNG captures and UIAutomator XML, not generated mockups. All new Week captures are **local component fixtures** on the existing `emulator-5554`, not live authenticated plans. The one historical `slice2b-accepted-draft-reference.png` is the original accepted live Slice 2B capture; it retains the old diagnostic overlay and shell reminder.

See [the report](../../WOMBO_UI_V2_SLICE_2C_REPORT.md) for acceptance limits, ownership, software results and the refused staging mutation. [fixture-host.tsx.txt](fixture-host.tsx.txt) records the temporary development-only host inputs, including exact public fixture source and no-op product callbacks. It is plain-text evidence; the corresponding runtime route was removed. Existing UI-version/language controls used their normal local preference mechanism.

- `slice2c-before-clean-B/E` and `slice2c-after-clean-B/E`: controlled native comparisons, original 1080×2280 px viewport, density 440, font scale 1.0, English, same public model/goal.
- `slice2c-after-clean-A` through `H`: all eight documented fixture states at the same original viewport/font. Supplied warnings remain in D/E/F/G/H; draft B/C uses the neutral reference selection input.
- `slice2c-development-v1/v2`: reachable existing preference controls after native taps, V2 restored; XML carries selected state. These prove preference controls, not authenticated root switching.
- `slice2c-rpe-inset-fixture`: count-one text and the owning shell's wrapper/styles; no live activity count or navigation claim.
- `slice2c-width-{width}-font-{scale}-{language}-{state}` and `-end`: six profiles below, B/E each at top and end of scroll, long goal and second-session name. Original viewport/font restored afterwards.
- `live-before-ui-state.json`, `live-after-ui-state.json`: nonsecret normal-app observations, signed out with requested V2 before and after; no planning owner while signed out.
- `verification.json`: final runtime commit, exact final test counts and per-suite pass results. No credentials, full public API responses or test actor identity are included.
- `screenshots.json`: capture kind, emulator configuration and PNG/XML SHA256 provenance.

| Width | Font scale | Locale | Draft top | Draft end |
| --- | --- | --- | --- | --- |
| 320 dp | 1.0 | NL | [Top](slice2c-width-320-font-1.0-nl-B.png) | [End](slice2c-width-320-font-1.0-nl-B-end.png) |
| 320 dp | 2.0 | EN | [Top](slice2c-width-320-font-2.0-en-B.png) | [End](slice2c-width-320-font-2.0-en-B-end.png) |
| 360 dp | 1.0 | NL | [Top](slice2c-width-360-font-1.0-nl-B.png) | [End](slice2c-width-360-font-1.0-nl-B-end.png) |
| 360 dp | 2.0 | EN | [Top](slice2c-width-360-font-2.0-en-B.png) | [End](slice2c-width-360-font-2.0-en-B-end.png) |
| 412 dp | 1.0 | EN | [Top](slice2c-width-412-font-1.0-en-B.png) | [End](slice2c-width-412-font-1.0-en-B-end.png) |
| 412 dp | 2.0 | NL | [Top](slice2c-width-412-font-2.0-nl-B.png) | [End](slice2c-width-412-font-2.0-nl-B-end.png) |

Each profile also includes corresponding E/`E-end` files. Widths use an Android display-size override at the original 2.75 density, with height 2280 px retained. These are practical emulator profiles, not physical devices or every language/width/font combination. Native configuration changes can restart React; only captures whose expected fixture/locale was reverified were retained.

Cross-month/year formatting is test evidence, not a native screenshot claim. Full TalkBack traversal, real authenticated shell insets and live call-count/return checks remain open. Partially scrolled-off content at a scroll viewport edge is distinct from a fixed-height card/action clipping; no all-content-in-one-viewport promise is made.
