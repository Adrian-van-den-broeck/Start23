# Wombo UI V2 dependency decisions

Date: 2026-10-02. Baseline: `6bb3a047139d91c71ac065c35a8af595221b54c5`.
Documentation only: no installs, removals, upgrades or build/config changes.
Read with the [architecture](WOMBO_UI_V2_ARCHITECTURE.md) and
[implementation plan](WOMBO_UI_V2_IMPLEMENTATION_PLAN.md).

## 1. Exact repository audit

Versions below were read from `mobile/package.json`, `package-lock.json`, local
`node_modules/*/package.json` and Expo's local `bundledNativeModules.json`.
Lock and installed versions matched for every listed installed dependency.
Declared ranges are not mistaken for exact resolved versions. Expo is
**SDK 57: 57.0.24**, React **19.2.3**, React Native **0.86.3**. Retain them.
The SDK 57 reference pairs RN 0.86 with React 19.2.3; installed packages remain
the exact starting point, not permission to upgrade to latest releases.
[Expo SDK 57 reference](https://docs.expo.dev/versions/v57.0.0/).

| Dependency | Declared / locked & installed | Why / existing alternative | Compatibility and risk | Decision |
| --- | --- | --- | --- | --- |
| `nativewind` | `^4.2.6` / **4.2.6** | Already configured, not a proposed new adoption. V2 can use typed StyleSheet tokens | Existing Babel/Metro interop applies even without utility classes; repository records function-valued Pressable styles being lost | Retain stable v4; utility-first V2 conversion optional, not recommended initially |
| `tailwindcss` (dev) | `^3.4.19` / **3.4.19** | Supports existing NativeWind build; not a V2 runtime requirement | NativeWind 4.2.6 peer is >3.3.0; keep current build config | Retain; do not migrate to Tailwind 4/NativeWind 5 prerelease |
| `react-native-css-interop` (transitive) | not direct / **0.2.6** | NativeWind interop, already present | Cross-cutting styling behavior; a removal/upgrade can affect V1 | Do not add directly or change |
| `react-native-reanimated` | `4.5.1` / **4.5.1** | UI-thread timings, restrained transitions, later gestures; RN Animated already serves V1 | SDK 57 local mapping and published reference recommend 4.5.1; local peer RN 0.83-0.86 and Worklets 0.10.x. Native/JS version mismatch or extra Babel plugin is a risk | Essential existing motion engine; reuse, no upgrade |
| `react-native-worklets` | `0.10.1` / **0.10.1** | Required by installed Reanimated, not an independent UI abstraction | Local Expo mapping/peers match; must stay paired with Reanimated | Essential existing runtime; no change |
| `react-native-gesture-handler` | `~2.32.0` / **2.32.0** | Existing sheet root and later swipe/drag; V1 PanResponder can remain | SDK 57 expected ~2.32.0; root already installed. Native gesture arbitration/scroll regressions need device testing | Reuse; essential for existing sheet runtime, optional in first read-only slice |
| `@gorhom/bottom-sheet` | `^5.2.14` / **5.2.14** | Existing profile sheet and provider. Bounded date/help choices later, RN Modal already handles full-height detail | Not Expo-managed. Installed peers accept GH >=2.16.1 and Reanimated >=3.16.0 or >=4.0.0-. Published overview still mentions v1-3: peer acceptance is not Android proof | Reuse only as needed; optional for detail, no new sheet library |
| `react-native-reanimated-carousel` | `^5.1.1` / **5.1.1** | Existing pending alternatives; Astra needs one focused alternatives surface, not permanent carousels | Installed peers accept current RN/GH/Reanimated/Worklets. Parallax/spring presentation and mounting many alternatives are V2 risks | Retain for V1; not essential to V2, do not replace with another carousel |
| `@shopify/flash-list` | `2.0.2` / **2.0.2** | Already virtualizes ActivityScreen; FlatList/SectionList sufficient for bounded agendas | Matches local Expo SDK mapping. Recycling requires row identity/state discipline, no outer ScrollView | Reuse for activity history; no extra list framework |
| `react-native-safe-area-context` | `~5.7.0` / **5.7.0** | Existing safe-area provider and footer/keyboard layout | Matches Expo SDK mapping; double insets/obscured actions are layout risks | Essential existing infrastructure |
| `expo-router` | `~57.0.22` / **57.0.22** | Existing file routing, Stack; JavaScript Tabs can supply approved navigation | SDK aligned; route groups/typed routes/back behavior require tests, not new routing dependency | Essential; retain, no experimental navigator |
| `react-native-screens` | `~4.26.0` / **4.26.2** | Existing native navigation runtime | Installed patch within local Expo range; navigator remount can lose local task state | Retain |
| `react-native-pager-view` | `8.0.2` / **8.0.2** | Already present; no baseline V2 requirement | SDK mapping matches; unnecessary paged onboarding would change approved step flow | Retain; no new V2 use by default |
| `expo-haptics` | `~57.0.3` / **57.0.3** | Existing optional selection/completion signals | SDK mapping matches; catch failures, no per-frame vibration, accessibility must not rely on it | Optional reuse |
| `expo-blur` | `~57.0.3` / **57.0.3** | Installed V1 reminder; V2 spec uses solid surfaces/scrim | SDK mapping matches, but Android blur cost has no V2 UX justification | Retain V1 dependency; no new V2 blur |
| `expo-linear-gradient` | `~57.0.2` / **57.0.2** | Installed; V2 requires no decorative gradients | SDK mapping matches; visual/runtime inflation without required use | Retain; no new V2 gradient |
| `lucide-react-native` | not declared, **absent** from lock and installation | Astra's coherent outline icon family; no installed icon library provides it | Requires SVG renderer; new JS package + native renderer, icon API/license/bundle/peers require a small reviewed dependency slice | Optional for architectural/detail proof; recommended for final approved icon implementation, subject to gate below |
| `react-native-svg` | not declared, **absent** | Renderer for Lucide/vector icons; native text cannot render the approved glyphs | Local SDK 57 mapping and versioned docs recommend **15.15.4**. Adding native code requires rebuilding the development client | Conditional essential only if Lucide/SVG implementation chosen; exact target 15.15.4, recheck at installation |
| `@expo/vector-icons` | not declared, **absent**, not even a resolved transitive | Expo mapping advertises ^15.0.2 but it is not available in this checkout; Lucide is the approved direction | Would introduce another family/font assets instead of supplying Lucide | Do not add as an unrequested icon-family replacement |
| `@supabase/supabase-js` | `2.110.8` / **2.110.8** | Shared authenticated session only; backend owns domain data | Existing singleton/storage flow; no V2-specific Supabase clients, SDK upgrades or direct data queries | Essential shared baseline; unchanged |
| `expo-secure-store` | `~57.0.4` / **57.0.4** | Existing refresh token, language and latest plan/draft storage | SDK mapping matches; do not persist UI preference here or clear identity on toggle | Shared baseline; unchanged |
| `expo-localization` | `~57.0.2` / **57.0.2** | Existing Dutch/English preference/locale | SDK mapping matches; V2 needs localized copy in both languages | Reuse |
| `expo-constants` | `~57.0.16` / **57.0.19** | Existing build identity/config; not a new flag service | Installed patch is the local Expo expected ~57.0.19; declared range accepts it | Retain; no silent package-range cleanup |

Other installed Expo packages remain: dev-client **57.0.19**, linking
**57.0.10**, splash-screen **57.0.9**, status-bar **57.0.1**. Web dependencies
remain react-dom **19.2.3**, react-native-web **0.21.2**, URL polyfill **4.0.0**.
No changes are proposed to them. Strict TypeScript **6.0.3**, Jest **29.7.0**,
jest-expo **57.0.5** and React Native Testing Library **14.0.1** are the existing
test toolchain; no new test framework is necessary.

## 2. Styling decision: extend StyleSheet, retain NativeWind

This is **not** a NativeWind installation decision: the repository already has
stable 4.2.6 with Tailwind 3.4.19, nativewind-env declarations, global CSS,
Babel preset/JSX interop and withNativeWind Metro config. Audited live screens
mainly use StyleSheet rather than utility classes; `src/theme/tokens.ts` and
Tailwind have overlapping definitions, including a different old accent.

Use semantic TypeScript V2 tokens and StyleSheet initially. This keeps font
scaling, exact dp values, motion and state styles explicit and isolates V1
without touching bundler configuration. Do not remove NativeWind: V1 depends
on its configured interop, and removing it is unrelated risk. Avoid dual token
sources. If future repeated utility use warrants aliases, derive prefixed V2
Tailwind names from the same values, with parity tests and concrete Pressable
styles. Do not convert V1 styles or add utility classes to hundreds of screens.

The current NativeWind installation guide documents the same Babel/Metro
integration and advertises v5 as RC. There is no repository-specific need to
adopt that prerelease. Retaining installed stable v4 is the smallest choice;
upstream setup alone does not certify this app's interop on devices.
[NativeWind installation](https://www.nativewind.dev/docs/getting-started/installation).

## 3. Compatibility evidence and package gates

Reanimated 4.5.1 and Worklets 0.10.1 match local peer constraints and Expo SDK
57 mapping; the official table also supports RN 0.86 with Reanimated 4.5.x.
Keep the existing Expo Babel preset rather than adding a duplicate worklets
plugin. Runtime compatibility remains a development-client/device check.
[Expo Reanimated](https://docs.expo.dev/versions/v57.0.0/sdk/reanimated/),
[Reanimated compatibility](https://docs.swmansion.com/react-native-reanimated/docs/guides/compatibility/).

Gesture Handler's versioned Expo recommendation is ~2.32.0. The existing root
already satisfies its root-view integration; do not add another root around
each V2 screen. Bottom-sheet's installed peers accept the current runtime,
but its public overview's older compatibility wording is insufficient to close
Android accessibility/keyboard/reduced-motion verification.
[Expo Gesture Handler](https://docs.expo.dev/versions/v57.0.0/sdk/gesture-handler/),
[Gorhom overview and dependencies](https://gorhom.dev/react-native-bottom-sheet/).

For icons, use named imports of the approved Lucide outline family behind a
small typed `Icon` wrapper; review actual sport glyphs with visible text.
SVG **15.15.4** is the versioned Expo recommendation. No SVG transformer or
runtime icon-name scanner is needed for component imports.
[Lucide React Native](https://lucide.dev/guide/react-native),
[Lucide getting started](https://lucide.dev/guide/react-native/getting-started),
[Expo SVG](https://docs.expo.dev/versions/v57.0.0/sdk/svg/).

**Unresolved package pin, not a UX decision:** Lucide has no existing current
version in this repo. Its official guide supports the library choice, but an
exact stable npm release/payload was not verified (the registry read failed).
Do not invent a version or use `latest` in the committed manifest. A later
small package slice must select and record an exact stable Lucide release,
check React 19.2.3/RN 0.86.3/SVG 15.15.4 peer compatibility and licensing,
update the lockfile and rebuild/test the Android client. No Lucide v0/v1 API
assumption may leak into screen code before that pin is resolved.

The first read-only architecture slice can prove Text, Card and labeled
Button without icons; it must not introduce emoji or initials to imitate the
approved icon system. Full visual icon acceptance and IconButton usage wait
for the dependency gate. This defers one asset implementation, not Astra's
visual direction.

For any later package change: review only that manifest/lock diff, run strict
TypeScript/mobile tests, Expo alignment diagnostics and Android native build
smoke. Do not use `--force`, upgrade Expo, or install remote feature-flag,
state-management, UI-kit, font, blur, chart or calendar packages to unblock UI
work. Keep existing packages even if V2 does not use them until V1 is retired
in a separately approved cleanup.

No compatibility diagnostic, build, security audit or device test was run by
this documentation task. File/version/peer inspection and external reference
checks are evidence for this plan, not a runtime certification.
