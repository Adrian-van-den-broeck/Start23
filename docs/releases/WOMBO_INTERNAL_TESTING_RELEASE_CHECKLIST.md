# WOMBO Internal Testing release checklist and commands

2026-11-04. **NO-GO — do not execute build/submission/deployment commands below yet.** Exact audited cumulative base: `f5831d3cbde04f60053402eb3083a1f1e6ade7a8`. Prepared branch: `release/wombo-internal-testing-audit-20261104`. Mobile overlay is uncommitted; the source manifest in the readiness report identifies it. There is no final approved release commit.

## Gates before approval

- [x] Root/mobile instructions, relevant roadmap/specification and cumulative ancestry inspected; UI V2 inclusion verified.
- [x] Isolated local worktree prepared without merging branches or including unrelated root changes.
- [x] Backend 1,282 tests, full Ruff/format and strict mypy pass.
- [x] Mobile 895 tests/83 suites, strict TypeScript and unused checks pass; Amsterdam subset 53 tests passes.
- [x] Privacy/API, account-isolation mocks, auth/network, injury/recovery and retry/precondition coverage included in full tests.
- [x] Registration disabled before network in the preparation overlay; legacy create payload retained and regression-tested.
- [x] Android Hermes export and native prebuild pass, with placeholder public key; no real-device claim.
- [ ] Resolve native compilation failure (Ninja dirty manifest in screens/worklets with long-path warnings) and validate a correctly signed AAB. No candidate AAB was produced.
- [ ] Triage/resolve or explicitly accept scoped dependency risk: npm production-tree audit reports 47 findings, including 1 critical and 10 high; no upgrade or audit fix was made.
- [ ] Verify live backend provides accepted A6 recovery and supports the complete selected mobile scope.
- [ ] Establish required A5 schema/function/grant compatibility; four V2 migrations stay deferred/off.
- [ ] Establish exact Railway SHA, service/project/environment IDs, connected Git branch, auto-deploy/watch triggers, overrides and rollback artifact.
- [ ] Resolve production URL reporting `local`; attach genuine review provenance and verify production validators, dependency readiness and exact revision. Do not invent or bypass them.
- [ ] Verify current Play Internal Testing release and each installed version from authoritative evidence; retain the existing two testers and opt-in link.
- [ ] Verify existing Play app identity/upload certificate and EAS remote credentials; do not rotate them.
- [ ] Verify final AAB configuration/content and compatibility against both approved backend revisions plus the currently distributed app.
- [ ] Commit the approved exact source, record SHA, rerun checks affected by any changes; do not build from an uncommitted overlay.
- [ ] Obtain explicit release approval after the GO/NO-GO is revisited.
- [ ] Complete and record the applicable real-device checklist; tests here are still unperformed.

## Existing Android/EAS configuration

`mobile/app.json`: display name Wombo, version `1.0.0`; `mobile/package.json` also `1.0.0`. Android package and iOS bundle ID are `com.adrivdbs.wombo`. EAS project ID is `57a06d4f-7405-432b-9b63-a3753c1ebf88`, owner `adrivdbs-team`, slug `start23`. Existing EAS build 22 confirms the Android identity. Play Console identity/certificate remains an explicit verification gate.

`mobile/eas.json`: `cli.appVersionSource=remote`, `build.wombo.environment=production`, `autoIncrement=true`; wombo has no development client, APK override or internal-distribution override. Its default Android store output is an **AAB**. The separate development/preview profiles are not the Play build command. `submit.wombo.android.track=internal` and `serviceAccountKeyPath=./credentials-google-play.json`. Keep that exact track. Do not use an unscoped submit command or automatic submission.

Read-only EAS production values: API `https://start23-production.up.railway.app`; Supabase `https://isfumhgqphieoayqahjv.supabase.co`; publishable key exists and was not printed in this audit. No public UI variable is configured, so the approved V1 default applies and the V2 switch remains available. These observations are not a guarantee about a future artifact. Candidate export used an obvious placeholder public key solely for build validation.

Remote counter observed **23**; latest completed Wombo store build is **22**, version `1.0.0`, source `ee229a9ac2b8de56a6b5bf69026921eab0ab5b56`. The next allocation is expected to be 24 only if the counter is unchanged. Re-read at approval time and require a versionCode strictly greater than all uploaded/installed versions. User-visible version is consistently `1.0.0`; retain or intentionally revise it consistently before final verification, not incidentally through a build counter.

The final dependency audit has 1 critical (`shell-quote`), 10 high (including direct `expo-router`), 31 moderate and 5 low findings. Some are tooling/transitive dependencies; Android runtime reachability was not established. The sanitized evidence lists advisory links and suggested fixes without applying them. Do not use forced fixes that change the approved SDK/dependency set merely to clear the count. Security triage/acceptance remains open.

The local offline arm64 release compilation was attempted after the final full mobile suite. It failed after 3m28s in `react-native-screens` and `react-native-worklets`, with Ninja's dirty-manifest error and long-path warnings. The existing shared dependency junction was used, so generated native caches may reside beneath that dependency install; no existing tracked dependency/application source was changed. A shorter isolated build path/fresh native dependency workspace or approved cloud build can validate this later. Hermes export/prebuild succeeded but do not close the native/signing gate.

Local historical AAB `mobile/dist/wombo-playstore-22.aab` SHA-256: `a70ce582030f2e0938d53d0c174b196259b2bf716219c917c07156d3aa6027b1`. Its signing certificate SHA-256: `7C:CF:6C:E5:73:1A:07:A4:51:A3:10:2F:50:AE:3D:6E:DA:DE:1F:60:D7:F6:61:27:5D:77:15:0D:34:F9:94:4A`. This is an artifact observation, not proof of a Play upload-certificate match. Generated local Gradle release configuration uses the default debug keystore; a local compile cannot substitute for the existing EAS upload signing credentials. No signing material was copied into the candidate or committed.

## Exact future commands — not executed

Run from the approved isolated worktree's `mobile` directory after all gates and explicit approval. The existing pinned CLI is used; no CLI upgrade is required by this audit. First verify source and read-only configuration:

```powershell
git status --short
git rev-parse HEAD
npx --yes eas-cli@23.2.0 build:version:get --platform android --profile wombo --json --non-interactive
npx --yes eas-cli@23.2.0 env:list production --format short
```

Keep credentials out of output capture. Confirm actual production URL/project/public key and no staging/local host. Do not invoke the local switch/start tasks: in production mode “Start backend” applies all pending migrations then deploys, and the mobile build helper mutates EAS variables. Both are outside this audit's authorized actions.

Create exactly one build, without auto-submit:

```powershell
npx --yes eas-cli@23.2.0 build --platform android --profile wombo --wait --json --non-interactive
```

Record the returned build ID as `$approvedBuildId` only after validating its exact Git SHA, package, versionName/code, production environment, finished status and AAB artifact. Do not substitute `--latest`. In the read-only review, inspect the existing Expo upload credentials in the dashboard without rotating them, compare the new AAB certificate with the established upload certificate, and inspect its manifest/JS configuration for production URLs and absence of server secrets/staging endpoints.

```powershell
$approvedBuildId = '<validated exact EAS build UUID>'
npx --yes eas-cli@23.2.0 build:view $approvedBuildId --json
```

The quoted UUID is deliberately an approval-time value, not a currently existing approved candidate. Ensure the existing ignored Google service-account JSON is available securely at the configured path; do not add it to Git, copy it into the JS bundle, or replace the existing Play app/credential identity.

Only after explicit submission approval, run this exact profile-scoped command:

```powershell
npx --yes eas-cli@23.2.0 submit --platform android --profile wombo --id $approvedBuildId --wait --non-interactive
```

`submit.wombo.android.track` must still equal **`internal`** immediately before execution. This command can change the live Internal Testing release; it is not a harmless validation command. Read back that exact internal release/version and unchanged tester membership afterwards, then test through the existing internal opt-in link. Never target another track.

Official command/config references checked: [Expo Android submission](https://docs.expo.dev/submit/android/) and [remote app versions](https://docs.expo.dev/build-reference/app-versions/). EAS profile behavior is also verified in the installed CLI/source configuration. Expo's generic example profile names are not instructions to replace WOMBO's existing `wombo` profile.

## Railway release and auto-deploy boundaries

Backend deployment is separately **NO-GO**. Google Play Internal Testing does not isolate the production API or database. The connected branch/auto-deploy settings are unknown because Railway CLI access is unauthorized. A push to a connected branch could trigger deployment, and watch paths/dashboard commands may override repository assumptions. No push to any branch is authorized. Local backend CI triggers on main; this is not evidence of Railway trigger settings.

Required deployed settings include `START23_ENVIRONMENT=production`, `START23_SUPABASE_URL`, publishable and server secret keys, and genuine `START23_PHYSIOLOGY_REVIEW_RECORD_ID`, `START23_PHYSIOLOGY_REVIEW_RULESET_VERSION=phase-13-joren-ruleset-1`, and `START23_PHYSIOLOGY_ACCOUNTABLE_OWNER`. Preserve both `START23_REALIZED_V2_STORAGE_READY=false` and `START23_REALIZED_V2_SELECTION_ENABLED=false`. Optional LLM/Polar credentials and approvals remain server-only. The example file's unprefixed `PHYSIOLOGY_REVIEW_RULESET_VERSION` is not the Settings environment key; do not infer deployment readiness from copying that example. Actual deployed variable values and review records remain unverified.

Repository Docker startup runs Uvicorn and has no migration hook. Hosted overrides must be inspected before eventual release. The production local task explicitly runs `supabase db push --linked --yes` then `railway up`; do not use it while deferred migrations exist. Do not deploy this branch to find out whether readiness passes. A future authorized release must pin the exact verified backend revision/configuration and verify dependency behavior separately from `/ready`.

## Separate rollback procedures

**A — Android Internal Testing.** Preserve the prior EAS artifact, source SHA, upload certificate and version identity. If the new UI is the issue, use the existing in-app V1 selector as a presentation fallback; it does not undo server state and lasts for the provider lifetime. For a code rollback, rebuild the previously verified compatible source with the **same package/signing identity and a higher versionCode**, submit only to the existing internal track after approval, then verify both testers update without data loss. A lower-versionCode AAB is not an update rollback. Do not uninstall/clear storage to conceal recovery problems. Current distributed revision is unknown, so record it before approving any release.

**B — Railway backend.** Before deployment, capture the current successful deployment ID, full Git SHA, configuration fingerprint and health/API smoke evidence. Following explicit rollback approval, restore that exact known-good artifact through Railway's existing rollback/redeploy mechanism and read back success for that deployment, health, environment, API contracts and tester flows. No executable rollback command can safely name a deployment here because its identity is unknown. Keep forward migrations and historical data; do not run down migrations, reset the database or recompute historical load. Verify the new Android app still works after backend rollback: the present A6 dependency means that claim currently fails against the observed older backend.

**C — feature/config activation.** Preserve both V2 server flags false and the fixed-off mobile registration gate. Future activation requires a separate reviewed source/config release; do not add a public env escape hatch. If selection later needs stopping, disable new selection without removing storage/readers needed for existing V2 records and corrections. Restore a previously captured configuration rather than guessed values; changing production to local is not a rollback. New catalog revisions must never replace historical identities. No destructive database change is necessary or authorized for an off-gated UI rollback, but exact runtime compatibility must first be established.

## Outstanding verification and final decision

Full local tests are green. Release is blocked by A6/live API incompatibility, A5/schema uncertainty, production environment misidentification, unknown hosted/distributed identities and remaining native/security/signing/device gates. A mobile-only update against the observed backend is **NO-GO**; a joint deployment is also **NO-GO**. No deployment, migration, submission or publication occurred.

**WOMBO INTERNAL TESTING NOT READY — BLOCKERS IDENTIFIED**
