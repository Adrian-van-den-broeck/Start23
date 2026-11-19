# Wombo mobile presentation

## Build and rollback

The current app lives on the main checkout based on `afeafa12`. Start Metro from its `mobile` directory. Expo reads `EXPO_PUBLIC_UI_VERSION` when it bundles the client. The Metro transform-cache version includes the flag so that rebuilding with a fallback setting also replaces previously inlined presentation choices.

| Build setting | Athlete experience |
| --- | --- |
| Unset or `v3` | Current pine, orange and grey design across training and supporting flows |
| `v2` | Previous landscape presentation and its shared supporting screens |
| `v1` | Previous default training interface and the released shared supporting screens |
| Other explicit value | V1 fallback |

To roll back the entire redesign, set the desired fallback value in the mobile build environment, rebuild the mobile bundle and distribute it through the existing release process. For a local comparison, set the value in the ignored mobile environment file and restart Expo with `npx expo start --clear --dev-client`. Production screens expose no presentation controls. Explicit V1 and V2 development builds retain the existing comparison controls. The flag carries no athlete preference or credentials. A rollback requires no data migration, backend release, or change to a saved draft.

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

Strict TypeScript, including unused-local and unused-parameter checks, passed. Each of the V3, V2 and V1 configurations passed 629 mobile tests across 70 suites. The backend suite passed 778 tests, including athlete-facing contract and private-load checks.

The shipping V3 source exported Android and iOS Hermes bundles and a web bundle. The temporary QA route was absent from all three outputs. A consecutive V1, V2 and V3 build using the same transform cache produced the intended inlined flag in both the route provider and design selection. Each exported web app rendered its password field. The V3 build displayed the track cover, and both fallback builds displayed their released sign-in presentation. The offline Expo compatibility check reported the installed dependencies up to date against the locally available SDK metadata.

## Interaction and frame checks

The Android API 35 Pixel 4 emulator exercised workout detail, month paging, choosing and skipping a candidate, a long-press drag onto Thursday 8 October, and profile navigation. The placement callback returned the expected ISO date, shown at the bottom of the QA capture. [Android workout detail](evidence/v3/android-detail.png) | [Android date drop](evidence/v3/android-placement.png)

Web pointer tests exercised both swipe directions, cancelled input, vertical scrolling and choosing a date. The sign-in and supporting screens were also inspected at mobile widths from 320 to 430 CSS pixels.

The calendar keeps its agenda mounted during paging, reuses locale date formatters and leaves vertical scrolling to the native scroll view. The following Android frame samples used three pairs of 350 ms vertical swipes across the month calendar. Measurements come from Android `dumpsys gfxinfo` on an Expo development client at 1080 x 2280.

| Calendar sample | Rendered frames | Frames flagged as janky | Median | 95th percentile |
| --- | ---: | ---: | ---: | ---: |
| Initial implementation, debug JS, SwiftShader | 195 | 94 (48%) | 48 ms | 77 ms |
| Final implementation, minified production-mode JS, SwiftShader | 115 | 84 (73%) | 57 ms | 150 ms |
| Final implementation, minified production-mode JS, host NVIDIA GPU | 44 | 29 (66%) | 65 ms | 150 ms |

All three emulator samples missed the 16.7 ms frame budget. They establish a release gate for calendar scrolling. Repeat the same interactions on representative iOS and Android hardware with signed release builds, including VoiceOver/TalkBack, large text, reduced motion, and both warm and cold navigation. An iOS simulator and physical devices were unavailable in this Windows environment.

## Cover asset

[Optimised track photograph](../../mobile/assets/wombo-track.jpg). Generated using the built-in ImageGen tool, then encoded as a local JPEG.

> Premium sports editorial photograph for Wombo triathlon app, landscape 3:2. Oblique high angle over an outdoor running track in deep evergreen rubber with clean thin ivory lane markings curving in graceful arcs. One small real female athlete wearing a vivid burnt orange race vest and dark shorts running at the far right third of frame, long angled shadow in early morning light. Camera far enough away that entire athlete fits comfortably within central half of frame height. Left half mostly quiet dark green rubber, premium analog film texture. Realistic, restrained, sharp graphic composition, no lettering, no numbers, no text, no logos, no typography.
