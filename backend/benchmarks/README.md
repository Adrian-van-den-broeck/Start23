# A9 reproducible local performance evidence

Run with the existing backend environment, from `backend`. These tools use only
synthetic fixtures, the checked-in audit source-catalog projection and local
Git history. They print aggregate times, safe operation labels and fingerprints;
never serialize complete planning inputs/outputs to logs. They do not access a
hosted repository or measure PostgreSQL.

```text
python -m benchmarks.planning --runs 3 --output ../.runtime/domain.json --profile ../.runtime/domain.prof
python -m benchmarks.paired --runs 3 --output ../.runtime/paired.json
python -m benchmarks.responsiveness --runs 3 --output ../.runtime/responsiveness.json
python -m benchmarks.responsiveness --operation swipe --counts 1 --runs 3 --output ../.runtime/swipe.json
```

`planning` covers fifteen deterministic scenarios. Its timings include the
intermediate fingerprint instrumentation. `paired` extracts the exact accepted
A8 domain source (`d0e726dfd291ffde12a459ec430b11fdc5cddc7a`) into an in-memory
module, alternates old/new execution order across three samples, and times raw
domain work. Output validation is outside its timer. Every output must match
the recorded A8 golden; these comparisons include all dataclass fields,
Decimal strings, ordered selections/placements, warnings and provenance.

`responsiveness` exercises real authenticated FastAPI proposal/swipe handlers
and Calendar handlers through ASGI, with owner-scoped in-memory repositories
and an injected token verifier. It measures the lightweight request from catalog
readiness, **including scheduler delay**. Timing only the request after the
blocked event loop resumes would conceal starvation. The default runs one and
two concurrent planning requests; swipe timing uses the actual UI's create
endpoint. Application lifespan owns and closes the calculation process.

For the A8 HTTP baseline, run the current benchmark module with the working
directory set to the accepted A8 `backend` and `PYTHONPATH` pointing to this
checkout's `backend`, writing results to this checkout's absolute runtime path.
Python resolves the A8 `app` from the working directory while using this same
benchmark/fixture code. Do not edit the accepted worktree. The A9.0 baseline
also records the original handler before the executor was introduced.

The parity tests have no wall-clock thresholds. They compare fifteen exact
single-week cases, the same cases through the spawned process, and ten adjacent
weeks carrying successful historical outputs (seven successes and three exact
fail-closed outcomes). The adjacent-week golden was generated with the accepted
A8 source. API workflow/concurrency tests separately cover identity, revisions,
approval, idempotency, bounded admission and cancellation before persistence.

Record environment, medians, observed maxima and run count. Three runs are not
enough for a reliable p95 or production SLA. Do not run CPU benchmarks alongside
other builds/tests. See the final report for the achieved local boundary and
remaining production/device/database gates.
