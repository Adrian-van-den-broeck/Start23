# A9.0 baseline — 28 October 2026

Accepted A8: `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` (clean,
877 mobile tests / 80 suites; backend unchanged since the 828-test baseline).
Isolated branch `fix/wombo-end-to-end-performance`, worktree
`.worktrees/wombo-end-to-end-performance`. No application behavior changed in A9.0.

Windows 10 Pro 19045; Intel i7-7820X 3.60 GHz, 8 cores / 16 logical CPUs,
32 GiB RAM; CPython 3.10.10. Same synthetic source-catalog projection as the
audit, 154 source options plus reviewed built-ins. No hosted data or database
measurements. CLI scripts under `backend/benchmarks`; safe fingerprint/timing
evidence under `evidence/a9`. Full input/output values are never logged.

| Rank | Bottleneck | Evidence | Planned narrow correction |
| --- | --- | --- | --- |
| 1 | Exact selection repeatedly reconstructs identical path comparison keys | Three timed runs: mixed triathlon median 14.800 s, maximum 14.842 s; zero-history triathlon fails closed, median 17.761 s, maximum 17.900 s. Profile: 32.8 million calls; 10.2 million UUID conversions (9.333 s self); path-key generator 12.854 s cumulative in the instrumented 23.209 s run. | Precompute immutable comparison/option metadata and retain each state's comparison key. Preserve iteration, states, pruning, tie-breaks and arithmetic. |
| 2 | Async planning handlers execute the domain search on the event loop | Actual authenticated proposal route and concurrent authenticated Calendar read, synthetic repositories, three runs each. Calendar wait measured from catalog readiness (including scheduler starvation): median 14.635 s with one planner, 31.277 s with two. All proposal responses 201, Calendar responses 200. | Isolate pure computation with bounded execution; keep verified ownership, persistence, optimistic concurrency and idempotency in the request lifecycle. Measure rather than assume GIL behavior. |
| 3 | Completed intake waits on unrelated auxiliary reads | Real OnboardingScreen, React development renderer, 5 runs, controlled onboarding 40 ms / auxiliary reads 240 ms: median navigation callback 257 ms; three requests. | Determine completion before requiring auxiliary form data; avoid callback identity causing repeated loads. |
| 4 | Multiple consumers independently load the same complete onboarding state | Each complete state invokes eleven already-parallel owner-scoped repository reads. No in-flight coalescing in the client. Profile mount/revisit both require one complete state; calibration and activity also consume it. | Coalesce overlapping identical reads only, scoped by exact token and write generation. Preserve freshness and A8 cancellation. Do not introduce a persistent authoritative cache. |
| 5 | V1 cold rendering and range initialization | Actual V1 route/controller harness, five runs, 40 ms controlled reads: Week cold 231 ms, Calendar cold 196 ms; warm Week 76 ms and Calendar 36 ms. Warm transitions already reuse owners/ranges and make no redundant reads. Profile cold 102 ms, remounted warm 98 ms. | Preserve the existing warm cache and owner rules. Investigate avoidable work with measurements; do not treat renderer times as device latency. |

Domain parity fingerprints cover initial/returning, single/multiple sports,
zero history, constrained/no availability, repeated occurrences, build/recovery/
taper, injury rest-only and partial-week fail-closed cases. Fingerprints include
full dataclass fields, Decimal strings, selected templates/occurrences, schedule,
warnings, provenance and intermediate target/eligibility/selection/schedule
results. Fixture inputs are hashed too, so changing the input cannot hide output
drift. Raw timings retained in evidence; no CI wall-clock threshold.

Mobile benchmark: `cd mobile; node node_modules/jest/bin/jest.js --config
jest.performance.config.js --runInBand`, with `A9_BENCH_OUTPUT` set to an output
file. The benchmark uses actual screens, Expo Router and shared controllers;
synthetic API responses, native animation adapters and React development
Profiler. Its cold label means a newly mounted screen/controller, not a cold
native module/bundle. It is not production or device performance. React transform
startup is excluded. API delays are controlled test inputs, not measured backend
or Supabase latency. Additional route inventory and native limitations belong in
the final report. An isolated release APK is being attempted under
`com.adrivdbs.wombo.a9benchmark`; existing installed app data is untouched.

PostgreSQL/pgTAP: DEFERRED BY OWNER — PRE-BETA

No production/staging changes. No push, merge or deployment.
