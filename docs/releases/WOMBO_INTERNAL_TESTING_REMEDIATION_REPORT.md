# WOMBO Internal Testing blocker remediation report

2026-11-04, Europe/Amsterdam. **Partial remediation; mobile-only and joint release remain NO-GO.** Confirmed channel is the existing Google Play Internal Testing track, exclusively the owner and Joren. No channel or tester change was investigated or proposed.

## Exact baseline and overlay preservation

Start SHA: `f5831d3cbde04f60053402eb3083a1f1e6ade7a8`. Original audit branch/worktree: `release/wombo-internal-testing-audit-20261104`, `.worktrees/wombo-internal-testing-rc`. All five audit reports were read before changes. Root/mobile AGENTS and current roadmap/V2 authority were followed; no nearer instructions apply.

The audit manifest SHA-256 `daf64a5c8310a354c32dfc31da29f6cb68632c36d4d5109e2adf944e879e4037` matched **all eight files**. They were copied byte-for-byte into new branch `fix/wombo-internal-testing-remediation-20261104`, worktree `F:/Projecten Business/Start23/Code/.worktrees/wombo-internal-testing-remediation`, together with the original five reports/evidence. No reset, clean, checkout-overwrite or branch merge was used. The original audit overlay and unrelated root work remain unchanged.

Preserved overlay files: `mobile/src/api/client.ts`, its tests, `features/activities/ActivityFlowProvider.test.tsx`, `activityCreateInput.ts`, `lib/releaseGates.ts`, `screens/ActivityScreen.tsx`, `ui/ActivityBoundary.tsx` and its tests. Registration stays fixed off before network in both UIs, and the activity request keeps the old-server shape with manual actual duration intact.

Final verified software/source commit: `8f75140169e074111e868d48bcf67e82aed8f899`. Source commit `132d503` and contract-fixture commit `8f75140` form this verified source. The required observed-schema test fixture is committed, so tests do not depend on untracked data. A subsequent report-only delivery commit records that immutable SHA; its exact HEAD is reported in the handoff. No eventual source behavior relies on the old uncommitted worktree. Remediation source hashes and changed-file evidence identify the verified runtime tree.

## Changes made

- A6 failure classification and capability-specific diagnosis retain all existing successful new-backend behavior. No unsafe legacy discovery fallback was invented. Known plans/locators remain retained; failed/unknown recovery blocks replacement generation and locator clearing. Auth, authorization, transient, unknown, unavailable and authoritative-empty outcomes remain distinct. Localized shared messages apply to V1/V2.
- Added old/new API and exact observed activity-schema tests, including retry, pending identity, account switch and no network mutation while recovery is unavailable.
- Retained and accepted the audit's eight-file release overlay into this reproducible candidate. New catalog, Realized V2 storage/selection and C3–C8 remain inactive; historical calculations and physiological rules are unchanged.
- Added seven scoped dependency overrides, changing ten existing package nodes only. Removed the critical advisory and four high package-node classifications; six high remain unaccepted. Added deterministic compatibility/security probes.
- Added isolated short-path Android release verification script; no shared old native cache was cleaned, no global software changed, and no signing key rotated.
- Corrected only the backend example's review-variable prefix and made its V2-off defaults explicit. Production validation and actual hosted variables remain unchanged.

No backend runtime, API route, SQL migration, coefficient, progression rule or historical record was changed. The accepted cumulative A10/A3–A9 and V2 software history is retained by ancestry.

## Verification on the candidate

| Check | Exact final-source result |
| --- | --- |
| Full backend pytest | **1,282 passed**, 175.37s; one existing Starlette/httpx warning. |
| Ruff / format | **PASS**; 175 files already formatted. |
| Strict mypy (app/tests/benchmarks) | **PASS**, 171 source files. |
| Full mobile Jest, UTC | **84 suites / 923 tests PASS**, 144.146s. Existing overlapping-act warnings remain visible; no assertions or timeouts relaxed. |
| Strict TypeScript / unused locals and parameters | **PASS**. |
| A6 old/new, release gates, activity/RPE, Calendar, injury, auth/retry, account and V1/V2 regressions | Included in full suites; new exact observed older input-schema test passes. |
| Dependency compatibility/security probe | **PASS**; no quoted input executed. |
| Native Android | **PASS** in fresh short path; exact final source rebuild passes. Arm64/local default signing/placeholder key only; not distributable. |
| npm production-tree advisory check | **42 unresolved findings**, 0 critical / 6 high / 31 moderate / 5 low; high risk not accepted. |
| Application credential scan / tracked-env / whitespace | **PASS**; no privileged application-source matches or tracked secret/env files; diff check passes. |
| PostgreSQL/pgTAP and hosted two-user writes/concurrency | **NOT RUN**, deferred by owner. |
| Physical-device/Internal Testing install/update | **NOT RUN**. |

Additional date/proposal/calendar subsets **PASS: 4 suites / 53 tests** in both Europe/Amsterdam (11.594s) and America/Los_Angeles (11.138s), using the final source. Backend runtime and migration source are unchanged; complete migration hashes are retained. The final mobile/source hash inventory matches the source copied into the successful final native build.

Automated/mocked tests do not replace hosted two-token/RLS/concurrency or device verification. PostgreSQL/pgTAP is **DEFERRED BY OWNER — PRE-BETA**, not passed. No new DB tools were installed. No physical-device installation/update, live athlete mutation or real-session login was performed.

All 19 changed source/config/test files, with exact SHA-256 values, are listed in [changed-source-files.json](evidence/remediation/changed-source-files.json). This inventory includes every preserved overlay file and all added recovery, localization, dependency and build-verification work.

## Refreshed release identities

| Surface | Evidence / status |
| --- | --- |
| Public API | `https://start23-production.up.railway.app`; `/ready`: ready, version 0.1.0, **local**; 69 OpenAPI paths, A6 GET absent. |
| Railway production project/service/environment, SHA, branch, auto-deploy and rollback artifact | **UNKNOWN**; existing CLI unauthorized. No new login/link or hosted mutation. Stored local link says r6-staging, not verified production. |
| Latest completed EAS store build | `0b1a3606-7476-4607-b4c7-a37e763249c0`, 1.0.0/code 22, metadata Git SHA `ee229a9ac2b8de56a6b5bf69026921eab0ab5b56`, `wombo`, FINISHED/STORE. |
| EAS remote version counter | **23**, freshly read. Does not establish a published build 23. |
| Android/EAS identity | Existing `com.adrivdbs.wombo`; project `57a06d4f-7405-432b-9b63-a3753c1ebf88`; wombo production build/remote auto-increment, existing remote signing; submit profile targets **internal**. No rotation or cloud build. |
| Current Play internal release/version and authorized tester configuration | **UNKNOWN from authoritative read-only evidence**. EAS completion is not distribution. Existing channel/two testers are the owner's confirmed scope, not a newly verified Console snapshot. |
| Installed build versions | **UNKNOWN**; no device checks performed. |
| Play upload certificate match | **UNVERIFIED**; historical local AAB certificate is recorded in the original audit, not treated as Play Console proof. |

The existing Play API helper creates an edit and lists tracks, so it was not used for this read-only, fixed-track task. No additional login or browser credential flow was attempted.

## Remaining requirements and decisions

**Mobile-only NO-GO:** old backend cannot provide complete A6 discovery/proof of absence; returning an empty result would violate owner isolation and duplicate-prevention requirements. Runtime decoder-chain high risk remains unaccepted. Production environment/deployment/distribution identities, upload signing and real-device checks remain open. A local verification build does not close those gates.

**Backend + mobile NO-GO:** all mobile gates plus genuine production configuration/review, exact Railway identity and separately executed A5/historical-schema validation remain required. Keeping V2 off removes its four migration dependencies, not the A5 gate. No production validation or A5 protection was removed.

Owner steps and evidence are in [final GO/NO-GO](WOMBO_INTERNAL_TESTING_FINAL_GO_NO_GO.md), [A6](WOMBO_INTERNAL_TESTING_A6_COMPATIBILITY.md), [A5/configuration](WOMBO_INTERNAL_TESTING_A5_DATABASE_GATE.md), [Android](WOMBO_INTERNAL_TESTING_ANDROID_BUILD_FIX.md) and [dependency triage](WOMBO_INTERNAL_TESTING_DEPENDENCY_TRIAGE.md).

No push, merge, deployment, migration, hosted configuration change, cloud build, tester change, submission or publication occurred. Local source/report commits are the only Git mutations beyond creating the isolated worktree.
