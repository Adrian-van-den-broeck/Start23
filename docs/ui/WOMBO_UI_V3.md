# Wombo mobile presentation

## Build and rollback

The V3 checkpoint lives on `save/wombo-ui-v3`, based on `afeafa12`. Start Metro from the branch worktree's `mobile` directory. Expo reads `EXPO_PUBLIC_UI_VERSION` when it bundles the client. The Metro transform-cache version includes the flag so a rebuild picks up the selected presentation.

| Build setting | Athlete experience |
| --- | --- |
| Unset or `v2` | Default landscape presentation and its shared supporting screens |
| `v3` | Opt-in pine, orange and grey design across training and supporting flows |
| `v1` | Previous default training interface and the released shared supporting screens |
| Other explicit value | V1 fallback |

To return to V2, unset the flag or set it to `v2` in the mobile build environment and rebuild the bundle. For a local comparison, set the value in the ignored mobile environment file and restart Expo with `npx expo start --clear --dev-client`. Production screens expose no presentation controls. V1 and V2 development builds retain the existing comparison controls. Changing the flag only requires a mobile rebuild.

## Ownership

The V3 module owns its palette, type scale, masthead, cover, session lead, segment chart and gesture components. The existing V2 screens supply the composition points. The build flag selects their visual variants once per bundle. V3 uses the same route adapters, public view models and planning, calendar and activity controllers used by V2. Selection actions send the controller its existing accept/pass transitions. A date drop invokes the same occurrence-specific callback as choosing that date by touch. Moving an approved workout still requires review and confirmation. Returning to an existing route preserves its owner, revision preconditions and retained context.

The released main was used as the integration base. Experimental V6 worktrees remain independent. The modifications cover mobile presentation, its bundling configuration, regression tests and this handoff.

## Design and interactions

| Surface | Presentation |
| --- | --- |
| Sign-in and registration | Track photograph, a single account selector, persistent field labels and inline result feedback |
| Week | The next session has a distinct dark surface. A pending decision gets its own action. Approved workout counts supply the completion strip. Secondary tools form a flat list. |
| Calendar | The date range and week/month controls precede the agenda. Empty known month cells show only the date. Unknown ranges retain a separate state. Full day summaries remain available to assistive technology. |
| Workout selection and placement | Swipe a candidate right to choose it or left to skip it. Buttons perform the same transitions. Hold the placement grip and drag onto a day, slide across the day rail or tap a target. Larger text uses the full-date list. |
| Workout detail | Exact duration, distance and intensity accompany the prescription. An ordered strip compares segments only when all segments have a positive duration or all have a positive distance. The full text sequence remains visible. |
| Activities and feedback | Session measures share a row where space permits. Feedback, correction requests and pending actions keep their qualitative labels. |
| Onboarding, profile, zones, check-in and integrations | Shared header, open form groups, persistent units, visible selection and focus, and status text. Onboarding progress uses the supplied steps. Zone rows retain server-supplied limits and provenance. |

Pine marks primary and selected actions. Orange marks the brand, current onboarding step and contextual emphasis. Warnings and errors retain distinct text and icons. The native system font scales with accessibility preferences. Controls use a 48-point minimum for the shared touch targets. Gesture recognition favours vertical scrolling until a horizontal swipe activates. Cancellation never commits a workout decision. Reduced motion removes decorative travel and stack transitions.

## Dependency decision

The lockfile and native dependency graph are unchanged. The existing Expo Router stack supplies navigation, Gesture Handler 2.32 and Reanimated 4.5.1 handle continuous input on the UI thread, and Worklets schedules the final callback. Expo Haptics confirms completed gesture choices. The existing Gorhom sheet and FlashList remain in their established roles. Lucide and react-native-svg provide the icons. The two proportional strips use ordinary native layout. Their size and data do not justify a second drawing engine or chart package. [Expo SDK 57 Reanimated reference](https://docs.expo.dev/versions/v57.0.0/sdk/reanimated/) | [Expo SDK 57 Skia reference](https://docs.expo.dev/versions/v57.0.0/sdk/skia/)

## Visual verification

The sign-in and registration captures use the Expo app entry. Training captures render the actual screens with local QA fixtures. Dates and workout examples in the screenshots are fixtures. The preview route and data are excluded from the shipping app. The emulator uses a development client, whose floating tool button can appear in Android captures.

[Sign-in](evidence/v3/sign-in.png) | [Week](evidence/v3/week.png) | [Calendar](evidence/v3/calendar.png) | [Activities](evidence/v3/activities.png) | [Profile at 320 px](evidence/v3/profile-320.png) | [Registration at 320 px](evidence/v3/registration-320.png) | [Android Week](evidence/v3/android-week.png) | [Android Calendar](evidence/v3/android-calendar.png)

## Build and regression results

The original checkpoint passed 629 mobile tests across 70 suites for each of V3, V2 and V1. After changing the default, strict TypeScript and unused-code checks passed, and both unset (V2) and explicit V3 passed all 635 mobile tests across 71 suites. The initial unset run had one navigation timeout during native compilation. That test passed on its own with the default timeout, and the full rerun passed with a 15-second runner timeout. The backend suite passed all 778 tests, including athlete-facing contract and private-load checks.

The shipping V3 source exported Android and iOS Hermes bundles and a web bundle. The temporary QA route was absent from all three outputs. A consecutive V1, V2 and V3 build using the same transform cache produced the intended inlined flag in both the route provider and design selection. Each exported web app rendered its password field. The V3 build displayed the track cover, and both fallback builds displayed their released sign-in presentation. The offline Expo compatibility check reported the installed dependencies up to date against the locally available SDK metadata.

## Interaction and frame checks

The Android API 35 Pixel 4 emulator exercised workout detail, month paging, choosing and skipping a candidate, a long-press drag onto Thursday 8 October, and profile navigation. The placement callback returned the expected ISO date, shown at the bottom of the QA capture. [Android workout detail](evidence/v3/android-detail.png) | [Android date drop](evidence/v3/android-placement.png)

Web pointer tests exercised both swipe directions, cancelled input, vertical scrolling and choosing a date. The sign-in and supporting screens were also inspected at mobile widths from 320 to 430 CSS pixels.

The calendar keeps its agenda mounted during paging, reuses locale date formatters and leaves vertical scrolling to the native scroll view.

### Earlier development-client samples

These Android samples used three pairs of 350 ms vertical swipes across the month calendar. Measurements came from Android `dumpsys gfxinfo` on an Expo development client at 1080 x 2280.

| Calendar sample | Rendered frames | Frames flagged as janky | Median | 95th percentile |
| --- | ---: | ---: | ---: | ---: |
| Initial implementation, debug JS, SwiftShader | 195 | 94 (48%) | 48 ms | 77 ms |
| Final implementation, minified production-mode JS, SwiftShader | 115 | 84 (73%) | 57 ms | 150 ms |
| Final implementation, minified production-mode JS, host NVIDIA GPU | 44 | 29 (66%) | 65 ms | 150 ms |

All three samples missed the 16.7 ms frame budget and used different build or renderer settings.

### Matched Android release benchmark

The two local, non-debuggable Gradle `release` APKs run the same fixture entry and real month calendar from this branch. The only APK archive entry that differs is the Hermes bundle with the baked-in `EXPO_PUBLIC_UI_VERSION`. The APKs were built for x86_64 and signed with the development key for local installation. The fixture fixes the October 2026 date range, selected day, six workout occurrences and one rest day. It bypasses sign-in and uses no network requests. The QA entry is outside the shipping router.

Both APKs used the same API 35 Pixel 4 emulator at 1080 × 2280, 60 Hz, 440 dpi and font scale 1.0, with the NVIDIA host renderer. Six runs alternated direction and balanced version order (V2, V3, V3, V2, V2, V3). Each run warmed up with two swipe pairs, then recorded three pairs of 350 ms vertical swipes at x=540 between y=440 and y=1800. The measurement reset `gfxinfo` per swipe and pooled valid, unflagged frames. Frame time is `FrameCompleted - IntendedVsync`, and p95 uses nearest rank. [Android frame statistics documentation](https://developer.android.com/tools/dumpsys#ui-performance)

| Presentation | Frames | Median | p95 |
| --- | ---: | ---: | ---: |
| V2 | 1,111 | 17.43 ms | 25.91 ms |
| V3 | 1,093 | 17.38 ms | 18.85 ms |

V3's pooled median was essentially flat (−0.05 ms) and its p95 fell by 7.06 ms. Per-run p95 ranged from 18.85 to 27.52 ms for V2 and from 18.77 to 18.92 ms for V3. Emulator variability and the fixture workload limit the result to this comparison.

The untraced frame data showed a shorter V3 p95 from render sync to buffer swap (2.97 vs. 4.80 ms) and from buffer swap to frame completion (13.74 vs. 17.76 ms). The median for the latter stage was 0.83 ms longer in V3. Individual stage percentiles use different frames and cannot be added to reconstruct the end-to-end p95.

Separate Android system traces recorded graphics, view, input and scheduler activity using the same swipe sequence. V2/V3 p95 was 9.01/9.21 ms for UI-thread `Choreographer#doFrame`, 18.21/18.32 ms for RenderThread `DrawFrames`, and 0.59/0.50 ms for `ReactScrollView.onScrollChanged`. The traced UI-thread median rose from 6.89 to 7.70 ms. These stage differences did not translate into a pooled scroll regression. The follow-up implementation commit was limited to the build selector and its test. The local raw frame dumps, traces, fixture and capture script are under `.tmp/v3-calendar` in the workspace.

### Open release checks

- Physical Android and iOS release hardware. Repeat the scroll comparison and confirm swipe, drag-and-drop, tap alternatives, large text, reduced motion, and TalkBack or VoiceOver with warm and cold navigation.
- Native iOS build and runtime. The Windows workstation has no Xcode or iOS simulator.
- Authenticated release flow. The fixture starts directly at the calendar, so real-token sign-in, owner-scoped data, pending review, and stale-safe plan transitions still need release-runtime evidence.

## Cover asset

[Optimised track photograph](../../mobile/assets/wombo-track.jpg). Generated using the built-in ImageGen tool, then encoded as a local JPEG.

> Premium sports editorial photograph for Wombo triathlon app, landscape 3:2. Oblique high angle over an outdoor running track in deep evergreen rubber with clean thin ivory lane markings curving in graceful arcs. One small real female athlete wearing a vivid burnt orange race vest and dark shorts running at the far right third of frame, long angled shadow in early morning light. Camera far enough away that entire athlete fits comfortably within central half of frame height. Left half mostly quiet dark green rubber, premium analog film texture. Realistic, restrained, sharp graphic composition, no lettering, no numbers, no text, no logos, no typography.
