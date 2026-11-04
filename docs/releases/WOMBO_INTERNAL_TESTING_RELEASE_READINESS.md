> Historical audit snapshot. Current remediation and decisions: [remediation report](WOMBO_INTERNAL_TESTING_REMEDIATION_REPORT.md). The original audit worktree remains unchanged.

# WOMBO Internal Testing release-readiness audit

Audit date: 2026-11-04, Europe/Amsterdam. **Backend NO-GO. Mobile NO-GO against the currently observed backend.** Google Play Internal Testing is the confirmed channel, for the owner and Joren only. No track change or tester-list change is proposed.

## Release identity and scope

Exact proposed cumulative source SHA: `f5831d3cbde04f60053402eb3083a1f1e6ade7a8`, branch `feat/joren-three-sport-catalog-c2`. **Rejected for release as-is.** Isolated preparation branch: `release/wombo-internal-testing-audit-20261104`; worktree: `F:/Projecten Business/Start23/Code/.worktrees/wombo-internal-testing-rc`.

The preparation worktree includes a small, uncommitted mobile release-gate overlay, described below. It is a review candidate, not a finalized distributable commit. There is **no approved final release SHA**. Before any build, the exact approved source must be committed and its identity recorded; do not present the base SHA as identifying the overlay. `evidence/candidate-source-hashes.json` identifies every changed mobile file; its SHA-256 is `daf64a5c8310a354c32dfc31da29f6cb68632c36d4d5109e2adf944e879e4037`. No commit, push, merge, deploy, migration, remote build, submission, publication, feature activation or tester change was performed during this audit.

| Identity | Read-only evidence and result |
| --- | --- |
| Current Railway Git SHA | **UNKNOWN.** Existing Railway CLI 5.45.10 reports unauthorized. No new login or link was attempted. `/ready` exposes version `0.1.0`, not a Git revision. |
| Railway connected branch / auto-deploy / service overrides | **UNKNOWN.** Local `origin/main` is only a cached Git ref; it cannot establish hosted connection or trigger state. |
| Configured public backend | EAS production environment and existing local mode metadata both select `https://start23-production.up.railway.app`. Its public `/ready` returns `ready`, version `0.1.0`, **environment `local`**. |
| Distributed Internal Testing version and source | **UNKNOWN.** No authoritative Play Console release snapshot was obtained. EAS completion alone does not prove distribution. |
| Latest completed EAS Wombo store build | Build `0b1a3606-7476-4607-b4c7-a37e763249c0`, version `1.0.0`, versionCode **22**, Git SHA `ee229a9ac2b8de56a6b5bf69026921eab0ab5b56`, package `com.adrivdbs.wombo`, `FINISHED`, `STORE`, created 2026-10-01 09:26:34 UTC. |
| EAS remote Android counter | **23**, from `build:version:get --platform android --profile wombo`. This is a counter, not evidence of a distributed build 23. Re-read before building; with the observed counter, the next auto-increment should allocate 24. |
| Installed internal app | **UNKNOWN.** ADB enumerated no connected devices. |
| Latest cumulative accepted backend source | C2.1 tip `f5831d3cbde04f60053402eb3083a1f1e6ade7a8`; last backend implementation change `5b6c960cf817dfebc31cffbd6e7f6fc58f2309be`. Acceptance of local software is not operational activation approval. |
| Latest cumulative accepted mobile source | Realized V2 delivery `cef4d0adfb09f5f1937528a98c594a6442816f20`; mobile subtree is byte-identical at C2.1. Last mobile-file commit `4d807f9ac18f576fb2fda51eb0016d48510c177d` changes test whitespace; prior full-suite snapshot `a0096135814c474ed667adcb957b99a66b54b769`. |
| Latest integrated UI V2 | `aff74558d0a6511286a4a84a44ea25a03ca57549`, including accepted Batch 12 `569cfc60702f10252f059feaa169c2f07ca4c5cb` and release-build V1/V2 selection. **Included in C2.1.** |

Browser verification ended because Computer Use could not determine the active Chrome URL safely. No subsequent UI calls were made. The old local `.runtime/google-play-track-audit.mjs` was inspected but not run: it creates a Play edit and lists tracks, outside this strictly read-only internal-release identity check.

## Verified history and UI inclusion

`git merge-base --is-ancestor <SHA> f5831d3...` returned success for every entry below. `git merge-base integration/wombo-ui-v2-main feat/joren-three-sport-catalog-c2` equals `aff74558...`; there are no UI integration commits outside C2.1 in that comparison. No merge was needed.

| Component | Exact ancestor |
| --- | --- |
| A10 verification gate | `11591b9924ebfd3872314deecb82c57fc278126b` |
| A3 restrictions | `b65ea78be1db886586d793f721bb2910ddbc6a41` |
| A4 check-in handoff | `4bb0cdea8f46242018ad8e5d22fa79a706cbf207` |
| A5 committed proposal recovery | `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf` |
| A6 account-scoped planning recovery | `24b27ebd34ccfe662ca57994a736f4f853af8d0b` |
| A7 activity synchronization | `75f172d4161f71a763247b04c027fd165901afbd` |
| A8 auth/network recovery | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` |
| A9 performance | `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` |
| Realized V2 | `cef4d0adfb09f5f1937528a98c594a6442816f20` |
| Catalog C1 | `e436285e9f169908a45ff8f34aeed0e003ba6bc2` |
| Catalog C2 | `ed052211ce413dd045b2e91af0d6a8e59ee534ff` |
| Catalog C2.1 implementation | `5b6c960cf817dfebc31cffbd6e7f6fc58f2309be` |

Inspected the Git worktree inventory, UI integration, final visual batch branches, and older `F:/wv2` sync branch. The latter's tip `23243e027b9674308c13d9c946dc03ce90a01c55` is also an ancestor. The later UI branches in the inventory are ancestors of integration rather than missing alternative cumulative implementations. The main checkout's uncommitted weekly-plan, tooling and documentation work was not incorporated. Existing worktrees and tracked/untracked source files were preserved.

The root/mobile AGENTS, current roadmap and its V2 authority amendment, UI main-switch/Batch 12 evidence, A10/A3–A9 reports, Realized V2 report/specification, C1/C2/C2.1 reports, catalog readiness, database workflow, security documentation, deployment scripts and CI configuration informed this audit. Historical claims of a development-only V2 switch are superseded by the accepted main-switch report. V1 remains the default when `EXPO_PUBLIC_UI_VERSION` is absent; V2 is available through the release-build controls. Both presentations retain shared controllers and write locks.

## Blocking findings

1. **Mobile/backend contract mismatch:** live public OpenAPI has 69 paths; the candidate has 71. The active backend does not advertise `GET /api/v1/weekly-plans/recovery`. `usePlanningController.ts` calls `discoverPlanning()` on startup/resume; a missing endpoint sets recovery failure instead of proving no plan exists. This affects both UI versions. Do not remove owner isolation, treat failure as empty state, or create replacement plans to conceal it.
2. **Backend/schema dependency:** A5 calls `get_checkin_plan_proposal` before generating check-in proposals. Linked hosted Data API metadata does not advertise that RPC, while legacy check-in and v15 planning RPCs are advertised. The migration ledger and actual grants/function behavior remain unverified. The four V2 RPC groups are also not advertised. V2 gates do not disable A5.
3. **Production configuration/readiness:** the configured production URL reports `environment: local`. Settings default to local and do not infer Railway production from Railway variables. Production review/key/Polar/V2 validators apply only when `START23_ENVIRONMENT` is correctly set. `/ready` performs no schema/RPC/revision probe. A healthy response cannot close these gates. Do not change the environment merely to bypass validation or invent review evidence.
4. **Operational identities:** deployed SHA, connected Railway branch and auto-deploy settings, current Play Internal Testing release, upload-certificate match, and both installed versions remain unverified.
5. **Native/signing and hosted/device gates:** Hermes export is not a signed, tested store AAB. Full native compilation, dependency risk, real-token isolation and device findings are recorded in the checklist/evidence. PostgreSQL/pgTAP remains **DEFERRED BY OWNER — PRE-BETA**, never passed.

The original C2.1 mobile tree also exposes new registration buttons and sends `performed_duration_confirmed`, which the observed older API forbids as an extra field. The preparation overlay fixes those two boundaries with a fixed-off code gate, UI hiding in both presentations, transport rejection before any registration fetch, and omission of the V2 request field. Existing manual duration entry stays explicit and blank by default. Three regressions verify these behaviors. Two older expected-payload fixtures now assert the approved legacy release shape; no physiological rule or backend test was weakened. The A6 mismatch remains a blocker, so this overlay is not represented as a complete release fix.

## Software verification

Backend runtime, tests, migrations and catalog source are unchanged from the exact cumulative base. Mobile tests ran against the prepared overlay identified by the source manifest.

| Check | Result |
| --- | --- |
| Full backend `python -B -m pytest -q -p no:cacheprovider` | **1,282 passed**, 155.27s; one existing Starlette/httpx deprecation warning. |
| Ruff lint, entire backend | **PASS**. Includes unused imports/variables covered by configured F rules. |
| Ruff format, entire backend | **PASS**, 175 files already formatted. |
| Strict mypy `app tests benchmarks` | **PASS**, 171 source files; strict=true. |
| Full final mobile `npm test -- --ci`, TZ=UTC | **83 suites / 895 tests PASS**, 123.572s. |
| Strict TypeScript and both unused-code options | **PASS**. |
| Amsterdam date/calendar/proposal subset | **4 suites / 53 tests PASS**, 17.682s. |
| Privacy, API/OpenAPI, token/account, injury/recovery and stale/retry regressions | Included in the full suites; automated/mocked evidence only. |
| Registration gate probe | Disabled backend GET/PUT refuse before database I/O; zero MockTransport calls. Settings reject hosted storage activation in staging and production. |
| Android production Hermes export | **PASS**, 5.8 MB HBC bundle, placeholder public auth key. This verifies bundling, not authentication or distributed environment content. |
| Android prebuild | **PASS**, no tracked package/config changes. Existing warning requests expo-system-ui for userInterfaceStyle; no dependency upgrade made. |
| Credential/environment/diff hygiene | No privileged credential-pattern matches in application source; no tracked .env/credential files; `git diff --check` passes. |
| Native Android `:app:bundleRelease --offline --no-daemon -PreactNativeArchitectures=arm64-v8a` | **FAILED**, 3m28s. screens/worklets native compilation reports Ninja `manifest 'build.ninja' still dirty after 100 tries`, with Windows path-length warnings. No candidate AAB produced. |
| `npm audit --omit=dev --json` | **FAIL / unresolved risk**: 47 findings (1 critical, 10 high, 31 moderate, 5 low). See `evidence/dependency-audit-summary.json`. Severity is the advisory service's assessment, not proof of runtime exploitability; no fix/upgrade applied. |
| PostgreSQL/pgTAP/RLS execution | **NOT RUN — deferred by owner**. Schema metadata GET is not PostgreSQL verification. |
| Physical device, Play update, two real user sessions, hosted mutations | **NOT RUN**. |

Earlier attempts are retained honestly: an initial junction pointed to the older root install missing SVG/icon dependencies (45 suites could not load); it was replaced with an existing A9 dependency install with an identical package-lock hash. The first valid full mobile run, concurrent with export, had 893 passes and two unchanged 5-second navigation timeouts. The unchanged final suite passed in isolation. No assertions/timeouts were relaxed. Dependencies were not upgraded.

## Release recommendations

**Backend: NO-GO.** Establish deployment identity and explicit production configuration; prove the legacy schema including A5; resolve required database verification through a separately approved integration decision. The four V2 migrations are not required for an off-gated release and must not be applied as a shortcut.

**Mobile: NO-GO against the observed backend.** The fixed-off registration gate and legacy payload remove two incompatibilities, but A6 still requires an unavailable API. A mobile-only release is therefore **not verified or approved**. A future mobile-only candidate could use an explicitly reviewed compatibility implementation or a separately validated earlier scope; preserve account isolation and fail-closed resume semantics and rerun full checks. No unrelated branch was merged or guessed fallback added.

Existing planning/calendar/activity functionality and accepted UI/reliability fixes are the intended scope. New catalog/physiology activation remains excluded. [Feature matrix](WOMBO_INTERNAL_TESTING_FEATURE_MATRIX.md), [database compatibility](WOMBO_INTERNAL_TESTING_DATABASE_COMPATIBILITY.md), [device smoke test](WOMBO_INTERNAL_TESTING_SMOKE_TEST.md) and [release commands/checklist](WOMBO_INTERNAL_TESTING_RELEASE_CHECKLIST.md) define the boundaries and remaining evidence. No build/submission command in those reports is authorization to execute it.

**WOMBO INTERNAL TESTING NOT READY — BLOCKERS IDENTIFIED**
