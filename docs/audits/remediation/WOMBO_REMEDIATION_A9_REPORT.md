# WOMBO Remediation A9 — backend and mobile performance

28 October 2026. **Verified locally at the boundaries described below.**

Full-catalog selection is substantially faster with exact A8 output parity.
Planning computation no longer monopolizes the API event loop. Completed intake
navigation no longer waits for unrelated form resources, overlapping onboarding
reads share one transport, and V1 warm tabs retain their entrance wrapper.
Both performance tracks were investigated independently. No scientific rule,
TSS calculation, training catalog, API DTO, database architecture, dependency
version or visual styling was changed.

**WOMBO-007 root cause:** repeated path formatting made exact catalog search
CPU-expensive, and async services executed that search on the event loop.

## Provenance and execution dependency

| Item | Exact value |
| --- | --- |
| Accepted A8 starting SHA | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` |
| Final tested application SHA | `8aca2655c2c36534a5c3973a466a5ffc3e396d00` |
| Final verified software / benchmark commit | `a5730729c3b2bd7ede8af286f9bcc0a5bfc1bbfc` |
| Branch | `fix/wombo-end-to-end-performance` |
| Worktree | `F:/Projecten Business/Start23/Code/.worktrees/wombo-end-to-end-performance` |

This report is finalized in a subsequent documentation-only commit; its exact
branch-head SHA is supplied in the completion message. The hashes above identify
the tested application and complete benchmark tooling without a self-referential
report hash.

A8's completed report, committed head and clean worktree were verified before
A9 implementation. Its 877 tests / 80 mobile suites and green software checks
were checked. A7/A8 had no backend implementation change; the inherited complete
backend baseline was 828 tests. A9 re-established full backend verification.
The first A9 commit branches directly from accepted A8, preserving the entire
earlier remediation chain. The A8 worktree remained clean after read-only
baseline execution. Other V1/V2 worktrees were not overwritten.

Applicable root/mobile AGENTS instructions, current MVP roadmap, full-system
audit, technical-debt/risk audit, end-to-end matrix, prioritized plan and completed
A10/A3/A4/A5/A6/A7/A8 reports informed this work. The full audit source documents
were read from the existing `audit-wombo-full-system-review` worktree; the
accepted remediation reports remain in this branch.

## Environment and measurement method

The host was Windows 10 Pro 19045, Intel i7-7820X 3.60 GHz, 8 cores / 16 logical
CPUs, 32 GiB nominal RAM. Python 3.10.10; FastAPI 0.139.2; Pydantic 2.13.4;
httpx 0.28.1; pytest 8.4.2; mypy 1.20.2; Ruff 0.16.0. Mobile used Node 24.18.0,
Expo 57.0.24, React 19.2.3, RN 0.86.3, Expo Router 57.0.22, TypeScript 6.0.3 and
Jest 29.7.0. Installed versions, AVD configuration and APK fingerprints are in
[environment evidence](evidence/a9/environment.json).

Backend measurements use the audit's deterministic full source-catalog
projection and reviewed built-ins, with synthetic histories and fixed dates.
No hosted catalog or athlete records were read. A9.0 recorded three samples per
scenario and a cProfile trace. A final paired benchmark alternates accepted A8
and optimized raw domain execution in the same environment, three runs each,
checking every result against the A8 golden outside the timer. The fifteen-case
timed parity harness additionally hashes intermediate calculations; its times
include that instrumentation and are distinguished from raw paired timings.

Real FastAPI authenticated proposal, swipe-create and Calendar handlers were
exercised through ASGI with an injected token verifier and owner-scoped in-memory
repositories. The lightweight request timer begins at catalog readiness,
including event-loop scheduling delay. One and two concurrent planning requests
were measured three times. The actual UI's swipe-create endpoint was also
measured against accepted A8 using the same harness. These are application
boundary timings, not deployed HTTP, provider-authentication or database latency.

Mobile development measurements use actual V1 screens, Expo Router and shared
controllers, React Profiler and controlled 40 ms reads / 240 ms auxiliary intake
reads. Five runs capture request counts, loading/navigation callback duration,
render duration and commit counts. Native animation adapters are mocked in this
harness. Its cold label means a fresh screen/controller mount, not cold native
module loading. Development numbers are not production performance; see the
[React Native performance guidance](https://reactnative.dev/docs/performance).

Native before/after measurements used a separate
`com.adrivdbs.wombo.a9benchmark` standalone Hermes **release variant**, without
Metro or a debugger, on the existing Pixel 4 AVD: Android 15 / API 35, x86_64,
4 virtual CPUs, 5,466 MB configured RAM, 1080×2280, density 440, GMT. The app used
only synthetic localhost services. The ordinary Wombo package was not opened or
cleared. Five runs per version covered authenticated process restart, cold/warm
Week/Calendar transitions and Profile visits through the actual V1 menu/Back
path. Temporary generated benchmark configuration was removed; the read-only
emulator, fixture server and temporary short-path alias were stopped/removed.

Windows builds used existing JDK 17.0.14.7 / Gradle 9.3.1 tooling,
`-PreactNativeArchitectures=x86_64` and the existing workspace
`scripts/android-short-paths.gradle` init script. `W:` temporarily mapped only
this worktree, with `start23.nativeRoot=W:/.runtime/cmake` and
`start23.projectRoot` set to the physical worktree path. The existing helper was
read and used without modifying it or another UI worktree.

Native timings are **sampled upper bounds for a stable public heading/form
label after required data**, including approximately 0.4 seconds of screenshot
capture/decode overhead. They are not exact first-frame or touch-latency timings.
The same marker rule, display, delays and sampling method were used before and
after. Five samples do not establish a reliable p95 or statistical significance.
External deep-link reloads and an earlier slower capture method were excluded
from the reported comparison. No physical-device timing is claimed.

## Measured bottlenecks and changes

| Rank | Root cause / evidence | Implemented response |
| --- | --- | --- |
| 1 | Exact search repeatedly converts the same UUIDs and reconstructs comparison paths. Baseline profile: 32,801,561 calls, including 10,195,454 UUID string conversions taking 9.333 s self time. | Precompute immutable option metadata and retain each state's canonical comparison tuple. Construct a new workout path only when it wins a state collision. Search order, state keys, bounds, feasibility tests, arithmetic and tie-breaks remain unchanged. |
| 2 | Async service handlers run synchronous CPU search on the event loop. Calendar waits 14.635 s behind one planner and 31.277 s behind two. | One bounded stdlib spawned calculation process per ASGI application. Authentication, repository access, preconditions and persistence stay in the API process. |
| 3 | Completed intake waits for goal-options and physiology resources. Callback identity changes can restart the load. | Parallel form reads remain available for incomplete intake; confirmed completion can navigate after onboarding alone. Latest navigation callback is retained without making it a data-loading dependency. Late/unmounted/account-old reads cannot navigate. |
| 4 | V1 view-keyed entrance wrapper remounts and replays its 420 ms fade on cached tab switches, despite zero requests. | Retain the wrapper across internal tabs. Initial entrance, layout animation, components and style tokens remain intact. A real-router regression verifies wrapper/owner lifetime and warm call counts. |
| 5 | Concurrent consumers independently request the same complete onboarding state. | Share only the in-flight promise by exact access token. Evict after success/error; fence reads at write start and settlement; old cleanup cannot erase a newer flight. No persistent/TTL response cache or new data owner. |
| 6 | Complete onboarding state performs eleven Data API operations; Profile and supporting tasks can consume it. | A barrier-based MockTransport test confirms those operations are already parallel and owner-scoped. Coalescing removes a duplicate state request. No speculative endpoint batching or database rewrite. |
| 7 | Calendar/Profile native waits remain measurable; accepted motion, loading and capture overhead contribute. | Record the limits without claiming a gain or changing visual design. Shared calendar caches, A7 freshness reads and existing FlashList virtualization were retained. |

After optimization the equivalent profile makes 3,047,017 calls and only **379**
UUID string conversions; its instrumented duration is 4.178 s rather than
23.209 s. Raw timings below provide the primary speed comparison.
[Profile evidence](evidence/a9/profile-summary.json).

## Before / after comparison

Values are medians. Backend rows have three samples; mobile rows have five.
Observed maxima and individual samples are retained in linked JSON evidence.
Percentages are calculated from the paired raw domain medians only.

| SCREEN / OPERATION | BASELINE TIME | OPTIMIZED TIME | IMPROVEMENT | ROOT CAUSE | VERIFICATION METHOD |
| --- | --- | --- | --- | --- | --- |
| Single-sport run, raw domain | 469.030 ms | 87.892 ms | 81.3% shorter | Repeated comparison work | Interleaved A8/current, identical output hash |
| Duathlon, raw domain | 345.697 ms | 99.224 ms | 71.3% shorter | Repeated comparison work | Interleaved A8/current, identical output hash |
| Full-catalog mixed triathlon | 14.945 s | 3.309 s | 77.9% shorter | UUID/path reconstruction | Interleaved raw domain and exact golden |
| All-zero-history triathlon, fail closed | 18.112 s | 3.934 s | 78.3% shorter; same rejection | Same search overhead | Exact error/output parity |
| Actual full-catalog swipe-create request | 16.301 s | 5.663 s | 10.638 s shorter | Search + execution boundary | Real authenticated ASGI route; cold child process included |
| Authenticated Calendar while one planner runs | 14.635 s | 23.670 ms | Search no longer holds the event loop | Synchronous CPU in async handler | Catalog-ready → authenticated response, including scheduling delay |
| Authenticated Calendar while two planners run | 31.277 s | 51.121 ms | Search no longer holds the event loop | Same; bounded concurrent work | Three concurrent-request trials |
| Completed intake → training callback, development | 257 ms | 59 ms | 198 ms shorter in controlled fixture | Unrelated auxiliary dependency | Actual OnboardingScreen; 40/240 ms reads |
| Authenticated native startup, stable data marker | 2,915 ms | 2,789 ms | Below sampling resolution; no firm gain claimed | Bootstrap/data/entrance path | Isolated release emulator, sampled upper bound |
| Native Week → Calendar, cold | 899 ms | 851 ms | No convincing native gain | Rendering/loading/motion | Same release/emulator/marker |
| Native Calendar → Week, warm | 876 ms | 530 ms | Observed 346 ms reduction; coarse sampling | Replayed entrance wrapper | Five runs plus deterministic remount regression |
| Native Week → Calendar, warm | 844 ms | 883 ms | No supported gain | Remaining layout/render/sampling delay | Five runs; zero API requests in both |
| Native Profile, cold | 1,262 ms | 1,252 ms | No supported gain | Fresh profile/reminder reads and task transition | Actual V1 menu / Back |
| Native Profile, warm revisit | 1,261 ms | 1,243 ms | No supported gain | Same freshness/transition | Same release fixture |

[Paired domain samples](evidence/a9/backend-paired.json),
[swipe A8](evidence/a9/swipe-a8.json), [swipe optimized](evidence/a9/swipe-final.json),
[API baseline](evidence/a9/responsiveness-baseline.json),
[API final](evidence/a9/responsiveness-final.json),
[development baseline](evidence/a9/mobile-baseline.json),
[development optimized](evidence/a9/mobile-optimized.json),
[native baseline](evidence/a9/native-baseline.json),
[native optimized](evidence/a9/native-optimized.json).

Raw mixed-case maxima were 15.159 → 3.531 s; zero-history maxima 18.867 →
4.278 s. Swipe-create maxima were 16.388 → 5.717 s. With two concurrent planners,
the final lightweight read's maximum was 123 ms; the slowest planning response
was 8.769 s. The fixture recreates the application per trial, so these request
times include lazy child-process startup. A warm complete HTTP lifecycle was
not assigned an invented latency from raw domain timing.

Profiler commit counts remained two for intake and three for Profile. Median
development render duration was 4 → 5 ms for intake and 49 → 47 ms for Profile.
The intake improvement comes from its dependency path, not a claimed general
render-count reduction. Development warm Week/Calendar medians were 69/32 ms
afterwards; native timing conclusions use the separate native evidence.

### Request counts and freshness

| Controlled operation | Before | After |
| --- | --- | --- |
| Two overlapping onboarding consumers | 2 physical state requests | 1 |
| Eleven-read `fetch_state` fan-out | Already parallel | Still parallel and owner-scoped |
| Native authenticated startup fixture | 9 requests | 9 |
| Native cold Calendar range | 1 | 1 |
| Native warm Week/Calendar | 0 | 0 |
| Native Profile visit, including shell reminder | 2 | 2 |

The eleven-read saving from removing one state request is a derived fan-out
count, not measured hosted traffic. The actual ProfileScreen/CalibrationScreen
integration reproduces overlapping reads through the real A8 transport.
Nonoverlapping Profile and Activity reads remain fresh.
[Read-count baseline](evidence/a9/overlapping-reads-baseline.json),
[optimized](evidence/a9/overlapping-reads-optimized.json).

## Execution isolation, cancellation and API semantics

A bounded thread prototype was measured first: its two-planner lightweight-read
median remained 627 ms. The final process boundary avoids sharing the search's
GIL with the API loop. One calculation runs and one may wait; further admission
uses the existing planning-unavailable 503 envelope. No Uvicorn, Railway or
production worker configuration was changed. Each ASGI worker would own one
lazy child; deployment CPU/memory implications require later capacity testing.
The implementation uses the standard
[Python 3.10 ProcessPoolExecutor](https://docs.python.org/3.10/library/concurrent.futures.html#processpoolexecutor).

Only detached pure calculation inputs and static pure helpers cross the process
boundary. No repository/HTTP client or access credential is serialized in jobs.
Immutable mapping proxies, Decimal values, enums and UUIDs retain their types;
the caller's Decimal context is copied for every calculation. Constraint errors
retain the exact code/message across process serialization.

Queued cancellation removes admission. Submitted work retains capacity until
it finishes; cancelling that owner's continuation prevents subsequent persistence.
HTTP disconnects/client deadlines do not prove handler cancellation or rollback.
A write can already have committed when response conversion fails or its owner
disconnects. A8's unknown-outcome classification, original identity, expected
revision and operation-specific reconciliation remain mandatory. No generic
POST/PUT/PATCH retry was added. A broken child fails closed to 503 until the
application restarts. [Execution details](WOMBO_A9_EXECUTION.md).

No endpoint, public DTO, database function/migration, TSS calculation, training
coefficient, rounding policy, catalog rule, warning or approval contract changed.
API/backend changes are limited to the local execution boundary and its service
injection. Existing optimistic concurrency and idempotent persistence remain
in the parent API process.

## Deterministic fidelity and benchmark matrix

The A8 golden covers fifteen cases: single-sport initial/returning run and swim;
duathlon; full mixed triathlon; all-zero history; unavailable sport baseline;
no/constrained availability; repeated occurrences; build, recovery and taper;
injury rest-only; and partial-week taper rejection. Each has three timing
samples, exact input hashes, full output/error hashes and intermediate
target/eligibility/injury-adjustment/selection/schedule fingerprints.

The same fifteen cases also pass through the spawned process. Ten adjacent
weeks carry successful historical outputs forward and match accepted A8:
seven successes and three identical fail-closed outcomes. Canonicalization
includes every dataclass field, exact Decimal strings, versions/provenance,
ordered templates/occurrences, counts, durations, placements, allocations,
warnings and errors. Explicit repeated occurrence IDs remain distinct within
their lifecycle. Nothing is made feasible by weakening a constraint.
[Single-week golden](evidence/a9/backend-baseline.json),
[instrumented optimized matrix](evidence/a9/backend-engine-optimized.json),
[adjacent-week golden](evidence/a9/multiweek-baseline.json).

Mobile coverage includes cold/warm navigation, valid cached revisits, approval
invalidation/authoritative handoff, Activity refresh, account switch, offline /
retry and background/foreground recovery. Call-count/state/parity tests have
no fragile performance thresholds. Controlled child gates verify unrelated
authenticated reads complete while planning is pending, bounded admission,
queued cancellation, no persistence after cancellation, error serialization and
Decimal-context restoration. Real expensive CPU measurements are separate from
those deterministic gates.

The [complete journey review](WOMBO_A9_JOURNEY_REVIEW.md) records every implemented
route and internal task inspected, fetch dependencies, ownership, native timing
coverage and unmeasured paths. Supporting screens, onboarding stages, detail,
creation/placement/proposal, check-in, activities/RPE, movement and integrations
were reviewed without inventing unimplemented routes. Existing history lists
already use FlashList. No broad provider/cache/list/navigation rewrite was made.

## A3–A8 preservation and UI compatibility

| Earlier remediation / boundary | Result |
| --- | --- |
| A3 injuries, restrictions, professional advice | Existing check-in/domain/adapter tests retained and passing; no extraction or safety-rule changes |
| A4 authoritative Week/Calendar handoff | Exact revision/receipt and return-navigation tests pass; warm reuse and changed-plan invalidation preserved |
| A5 proposal replay | Original check-in/proposal identity, immutable context and idempotent replay preserved |
| A6 discovery and locators | Account-scoped discovery, saved locator preservation and late-owner rejection remain passing |
| A7 Activity / remote pending RPE | Genuine focus refreshes, invalidation, remote resolution and unresolved local create/RPE state preserved |
| A8 auth and transport | Auth classification/retry/rotation/logout, bounded requests, ambiguous-write reconciliation and malformed-response tests remain passing |
| V1 | Existing visuals/components and functionality retained; first entrance/layout motion retained; warm wrapper no longer recreated |
| V2 | Shared owner/data behavior and all V2 tests pass; accepted styling untouched |
| Privacy / localization | No new athlete-facing copy, telemetry or raw diagnostic payloads; existing NL/EN behavior and privacy tests pass |

The in-flight map is scoped by exact token, removed on settlement/error and
fenced at write boundaries. It cannot publish another account's data or turn a
pending plan into an approved plan. A9 adds no authentication owner or persistent
data cache. RPE selection still saves immediately; no confirmation action was
added. User forms and unresolved mutation identities retain their existing owners.

## Final software verification

| Gate | Actual result |
| --- | --- |
| Complete backend suite | **850 passed**, 133.56 s; one existing Starlette/httpx deprecation warning |
| Complete mobile suite | **887 passed / 83 suites**, 124.767 s |
| New A9 regressions within totals | 22 backend cases; 10 mobile cases; no existing test deleted |
| Focused backend parity / onboarding fan-out run | 24 passed |
| Focused actual navigation including V1 lifetime regression | 49 passed |
| Actual screen/client read integration + read tests | 6 passed |
| API / A8 network recovery / shared-read run | 40 passed |
| Same A8 privacy/source/public-view group | **58 passed / 8 suites**, 2.227 s |
| Backend privacy/public-contract subset | **38 passed**, 812 deselected; included in full suite |
| Explicit OpenAPI/public-contract file | 6 passed; included above |
| Development performance harness | 2 passed / 2 suites; five samples each |
| Preserved native benchmark-tool smoke | One six-operation journey passed |
| Strict TypeScript and unused code | Both passed, exit 0 |
| Ruff / format | Passed for backend app/tests/benchmarks and native benchmark tooling |
| Strict mypy | Passed for app/tests/benchmarks, **148 source files** |
| Native compatibility | Baseline and optimized isolated release APKs built successfully with existing dependencies |
| PostgreSQL/pgTAP | **DEFERRED BY OWNER — PRE-BETA** |

Focused counts are subsets of the full totals and are not added to them.
The existing backend test spy was moved to module scope for process
serialization, retaining its original assertions. The existing check-in fixture
received the new execution dependency. No assertion was weakened to obtain green.
[Verification manifest](evidence/a9/verification.json).

Project checks were run from their owning directories: `pytest -q`,
`ruff check app tests benchmarks`, `ruff format ... --check`,
`mypy app tests benchmarks`, Jest `--runInBand`, `tsc --noEmit` and the explicit
unused flags. Benchmark reproduction commands are documented in
[backend benchmarks](../../../backend/benchmarks/README.md) and
[native tooling](../../../mobile/performance/native/README.md).
Development performance tests use `mobile/jest.performance.config.js`, with
`A9_BENCH_OUTPUT` and `A9_READ_BENCH_OUTPUT` output paths configured.

## Files, commits and remaining limits

Application changes are confined to planning search/execution/service injection,
the API's in-flight onboarding read helper, intake loading and V1 entrance-wrapper
lifetime. Tests, safe benchmark tooling and audit evidence accompany them.
The exact file inventory is [files changed](evidence/a9/files-changed.txt).
The implementation/evidence commits are listed in
[commit inventory](evidence/a9/commits.txt); phases A9.0–A9.5 are separable.

Remaining limitations:

- The exact search still takes several seconds on full catalog cases; cold
  complete swipe creation measures 5.663 s. Authoritative context preparation
  still repeats across draft actions. No approximate solver or cross-request
  private-state memoization was introduced.
- Production container CPU/memory, multi-worker deployment and hosted network /
  repository latency were not measured. The process boundary adds one lazy
  child per ASGI worker. No automatic production configuration change was made.
- Native physical-device performance, exact first-frame/interaction timing,
  Hermes JS stalls and per-screen native commit/frame distributions remain
  unverified. The native table is an emulator release-variant upper-bound
  comparison. Supporting paths without native timings are identified in the
  journey review; no fabricated latency is assigned to them.
- Calendar entry and Profile show no convincing native improvement. Their
  remaining motion/render/loading costs need finer target-device measurement.
  The existing unpaginated activity-history RPC is a potential volume-dependent
  follow-up; no PostgreSQL/history-volume performance was measured and no
  history was silently truncated or response contract changed.
- No strict production latency SLA was invented. Keep A8's 45 s ordinary and
  120 s planning transport deadlines. The local medians/maxima are pre-beta
  profiling references; owner latency budgets should follow controlled
  physical-device and hosted integration measurements.

`PostgreSQL/pgTAP: DEFERRED BY OWNER — PRE-BETA`

This remains an open integration/release verification gate, not a failed A9
software remediation. No database behavior or PostgreSQL performance is claimed
as verified. Docker, Podman, PostgreSQL and psql were not installed.

**Production/staging unchanged. No push, merge or deployment.**
