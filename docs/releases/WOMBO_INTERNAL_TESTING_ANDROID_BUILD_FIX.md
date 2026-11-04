# Android native build remediation

2026-11-04. Start `f5831d3cbde04f60053402eb3083a1f1e6ade7a8` plus preserved audit overlay; final software `8f75140169e074111e868d48bcf67e82aed8f899`.

## Isolation and diagnosis

The previous attempt compiled from a long worktree path and a junction to another worktree's node_modules. It reported CMake object-path warnings and Ninja `build.ninja still dirty after 100 tries` in screens/worklets. Those observations do not establish an incompatible dependency.

This task created a new private short dependency workspace `F:/wmbo-rc-1104`, then a separate native verification workspace `F:/wmbo-native-1104`. Both were newly created after confirming they did not exist. No old project, asset, worktree, global package, Android SDK or generated cache was deleted. The remediation worktree uses a dependency junction to the first workspace; native compilation uses the second workspace's own fresh locked install, generated Android tree and native caches. Expo/React Native/native module versions are unchanged.

`scripts/verify-wombo-android-release.ps1` reproduces source selection and isolation. It refuses an existing target or drive root, requires a short absolute path and existing SDK, enumerates Git tracked/unignored mobile files, rejects credentials/env files/path escapes, copies exact bytes and writes SHA-256 source hashes. It installs the committed lock without lifecycle scripts, runs Expo prebuild without dependency updates, then local offline arm64 release compilation. There is no cloud command or signing-credential lookup in this script.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-wombo-android-release.ps1 -BuildRoot F:\wombo-native-next
```

Use a new dedicated target each time; the script never cleans an existing workspace. This is local compilation with the installed SDK/JDK/Gradle cache, production API URL and a conspicuous placeholder publishable key. The generated default local signing identity is not the established Play upload key. `app.json`, `eas.json`, package identity `com.adrivdbs.wombo`, version `1.0.0` and native dependency versions are preserved.

## Verification result

**PASS: clean local arm64 release compilation in 7m29s (836 tasks executed).** After the last recovery guards/tests were synchronized, the exact final source rebuilt successfully in **1m27s** (26 executed, 810 up-to-date). All **285 copied mobile files** were hash-checked against the final remediation tree.

AAB: `F:/wmbo-native-1104/mobile/android/app/build/outputs/bundle/release/app-release.aab`, 32,545,847 bytes, SHA-256 `47640a8152f2c50282ac37a335256bec0fe1c93f86bf1bad6b1e718e5acef370`. ZIP integrity passes; merged release manifest and AAB manifest bytes identify `com.adrivdbs.wombo`, versionName `1.0.0`. Local versionCode is **1**, not the EAS remote counter, and cannot be used as the next store update.

`jarsigner -verify` exits 0: jar verified, with expected self-signed/untrusted-chain/no-timestamp warnings. Certificate owner is **Android Debug**, SHA-256 `FA:C6:17:45:DC:09:03:78:6F:B9:ED:E6:2A:96:2B:39:9F:73:48:F0:BB:6F:89:9B:83:32:66:75:91:03:3B:9C`; this is not the historical Play upload identity.

The HBC contains the configured production API URL and the explicit placeholder auth key, with no r6-staging string. A raw binary secret-prefix pattern spans contiguous Hermes strings; the source-map contents show only Supabase's prefix-validation markers and no long secret-key pattern. This heuristic was not presented as a leaked credential or as complete secret verification. Application credential scans and privacy tests provide separate evidence. The artifact remains **verification-only, not distributable**.

The short-path build passed the screens/worklets steps that previously failed, without native dependency changes. This supports a path/cache/environment explanation; separate path versus cache causality was not experimentally isolated. A success here does not verify physical-device behavior, other Android ABIs, Play upload-certificate match or real authentication. Final exact-source synchronization and artifact fingerprints are recorded in remediation evidence.

## EAS verification route — requires owner approval, not started

After all release blockers are cleared and the owner approves the potentially billable cloud build, from the exact committed candidate's mobile directory:

```powershell
npx --yes eas-cli@23.2.0 build:version:get --platform android --profile wombo --json --non-interactive
npx --yes eas-cli@23.2.0 build --platform android --profile wombo --wait --json --non-interactive
```

Use the existing `wombo` profile only, no auto-submit. It selects EAS production environment, existing remote signing, remote versionCode and auto-increment; the store default is AAB. Verify the returned exact build ID/source SHA, package, version/code, signing certificate and actual production public configuration before considering it distributable. Counter currently 23 does not prove a published build 23; re-read immediately before approval.

No cloud build, credential rotation, app installation, submission or publication occurred. A local verification AAB, if produced, must never be submitted with placeholder configuration/default local signing. The intended submission track remains `internal`, with the existing owner/Joren tester list unchanged.

Official workflow reference: [Expo local build limitations](https://docs.expo.dev/build-reference/local-builds/) and [Android submission](https://docs.expo.dev/submit/android/). This task uses direct local Gradle on Windows; it does not claim Windows EAS local-build parity.
