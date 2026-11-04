# WOMBO runtime decoder fix and signed-build preparation

2026-11-04. Review baseline `abcc800d594e9e46784148cc799c51834daed329`. This supersedes the runtime decoder's unresolved status in the earlier remediation triage; historical reports remain unchanged. **The runtime source fix is implemented and tested. Release/signing/hosted gates remain open.**

Final verified source: `5e990ccb831f03926ea35b722eaa4ec4493bcdbe`. The vendor directory pins LF line endings with its own `.gitattributes`; a fresh Git index checkout reproduces both recorded source hashes on Windows.

## Exact targeted change

The reachable Android chain was `expo-router@57.0.22 → query-string@7.1.3 → decode-uri-component@0.2.2`, with malformed externally supplied URL input as a plausible DoS entry point. Upstream 0.5.1 fixes the decoder algorithm, but publishes an ESM default export while the current query-string consumer uses a synchronous CommonJS callable. A blind major override could break navigation.

The candidate vendors the official MIT-licensed 0.5.1 source and mechanically changes **only export packaging**: strict-mode prefix, default function export to `module.exports`, assignment terminator. No algorithm change, new URL-size policy, router fork, Expo upgrade or native dependency upgrade. The local package is explicitly versioned `0.5.1+wombo.cjs.1`; this is a WOMBO packaging adaptation, not a claimed upstream CJS release. Maintenance of this vendored copy is now a project responsibility; replace it when the approved toolchain supports the upstream module directly.

`mobile/vendor/decode-uri-component/PROVENANCE.json` retains tar URL, npm integrity, upstream/adapted SHA-256 and the three changes. `upstream-index.mjs` is the exact upstream source and LICENSE is retained. `package.json` uses a direct `file:vendor/decode-uri-component` dependency plus an npm override reference, so all existing transitive consumers resolve the same local package. The lockfile changes only decoder resolution and its local package entry; the previously accepted security pins remain.

Upstream tar SHA-256: `68747a955bbb6a700d758155cf5ff15595c0dfa38504d385abdb249c688bfb15`.

Upstream source SHA-256: `6a86ac891edf15c5efa0841ebb31935e3669d58b98318b57d7b08a4530317cb0`.

Adapted source SHA-256: `621c20e0d371040b29c70e507b1b8c5f9d60145580bb86679f2e13ec3196cca2`.

Sources: [upstream source](https://github.com/SamVerschueren/decode-uri-component/blob/main/index.js), [malformed-input advisory](https://github.com/advisories/GHSA-qr28-fpjm-wq7f), [earlier decoder advisory](https://github.com/advisories/GHSA-vcc3-ghjq-m6fr). The immutable source and hashes in this repository, rather than a moving main branch, identify the reviewed code.

## Verification

- Fresh isolated `npm ci --ignore-scripts --no-audit --no-fund`: 952 packages installed with the revised lockfile. No global software change or force audit fix.
- `node mobile/scripts/verify-decoder-security.cjs`: verifies hashes, reverses the export-only transformation byte-for-byte, loads the actual query-string consumer, tests Unicode/emoji/malformed encodings and decodes a 100,000-run adversarial input in a child process with a 10-second limit. PASS.
- Ten URL-decoding regression cases, including no recursive percent rescanning and query round trip: PASS. Full mobile suite **933 tests / 85 suites** PASS; strict TypeScript and unused-code checks PASS.
- Android Metro/Hermes export with source maps: PASS. The map resolves the runtime decoder to `vendor/decode-uri-component/index.cjs`; hashes are recorded in `evidence/a5-a6/verification.json`. No vulnerable 0.2.2 decoder appears as another map source. Bundle inclusion is stronger evidence than npm's count alone, but is not a real-device native-link test.
- EAS wombo profile now explicitly declares `distribution: store`, Android `buildType: app-bundle`, `credentialsSource: remote`, retaining production environment and remote auto-increment. Validated offline against cached EAS CLI 23.2.0's profile schema. Submit profile remains **internal**. No signing material or tester setting changed.

The local dependency junction required sandbox permission to write its isolated cache; the initial denied cache creation was rerun with authorized filesystem access and export passed. Export uses a placeholder public key and is **verification-only**, not an installable signed release. The earlier native arm64 AAB predates this change and was debug-signed; it cannot validate this exact candidate's signature or substitute for the next EAS build. No signed release AAB was produced in this task.

`npm audit --omit=dev`: **0 critical, 3 high, 31 moderate, 6 low** (40 package/aggregate findings). The bundled decoder/query-string/router high chain is removed. Remaining high packages are image-size 1.2.1 (Metro build asset parsing), zod 3.25.76 (CLI validation), and the aggregate @expo/cli 57.0.26 entry. These are build-tool exposures, not automatically acceptable risks. Prior evidence found vulnerable image-size/Zod functionality absent from the Android map; tool inputs and build integrity still matter. Their fixes change major/API contracts outside the current consumer families. Keep the earlier precise triage and obtain an owner/security-reviewed fix or exception naming candidate/advisories, trusted inputs, isolated build controls, accountable reviewer, expiry and patch trigger. **No critical/high risk was accepted.** Moderate/low findings remain recorded, not declared harmless. Audits do not independently inspect vendored code; provenance/algorithm verification is essential.

## EAS/Play identities and owner-only commands

Known existing Expo project: `57a06d4f-7405-432b-9b63-a3753c1ebf88`, owner `adrivdbs-team`. Package must remain **com.adrivdbs.wombo**, visible version **1.0.0**. Earlier authorized read evidence: completed store build `0b1a3606-7476-4607-b4c7-a37e763249c0`, versionCode 22, source `ee229a9ac2b8de56a6b5bf69026921eab0ab5b56`; remote counter 23. These are historical EAS observations, **not proof of a Play publication**. Current distributed Internal Testing version, installed versions, release status and upload-certificate match remain UNKNOWN. Counter must be read again; do not hardcode 24 or reset it.

Before any billable build: owner verifies existing Play app/package, current Internal Testing release and greatest used versionCode, existing upload certificate and owner/Joren access without modifying testers. Compare EAS's existing remote keystore certificate to Play **upload** certificate; Play's app-signing certificate can differ legitimately. Do not generate/rotate credentials. Confirm existing remote credentials are used or stop.

On the exact committed mobile candidate, owner reviews EAS production environment variable names/values locally. Required public names are **EXPO_PUBLIC_API_BASE_URL** (`https://start23-production.up.railway.app`), **EXPO_PUBLIC_SUPABASE_URL** (verified actual project, not merely the source default) and **EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY** (that project's genuine public key). `EXPO_PUBLIC_API_URL` and `...ANON_KEY` are not the application's configured names. No server-only key may enter the build. Verify no local .env/staging URL overrides production inputs. Do not upload placeholder exports or local credentials files.

Read-only identity checks, using an existing authorized EAS session from `mobile/`:

```powershell
eas whoami
eas project:info
eas build:list --platform android --limit 5 --json --non-interactive
eas build:version:get --platform android --profile wombo --non-interactive
```

If unauthorized, stop and let the owner choose dashboard access/login separately; do not auto-login. Confirm archive includes the new vendor directory and excludes credentials, generated native caches and runtime artifacts. Recheck EAS production variables and existing signing through the owner dashboard without printing secrets.

**Only after explicit authorization for a potentially billable signed cloud verification build**, with all relevant security/identity/backend gates satisfied:

```powershell
eas build --platform android --profile wombo --non-interactive
```

Do not add auto-submit. Inspect the resulting immutable build ID: exact committed source, effective production variables, package, 1.0.0 version, newly incremented code greater than existing Play codes, release AAB and existing upload certificate. Download and validate the actual AAB (bundletool validate/manifest and `jarsigner -verify -verbose -certs`, certificate fingerprint comparison). These checks are **not yet performed**. A completed EAS build alone is not publication.

After successful backend/device/signing review and **separate explicit submission approval**, target only the existing Internal Testing configuration and the inspected build ID:

```powershell
eas submit --platform android --profile wombo --id <VERIFIED_NEW_BUILD_ID> --non-interactive
```

No other track or tester change is part of this procedure. Android rollback requires a higher versionCode with the same package/upload signing and a compatible backend. See the A5/A6 runbook for backend/config rollback, which must retain all forward schema and historical data.

No EAS cloud build, credential rotation, submission, publication, production configuration change or backend deployment was executed.
