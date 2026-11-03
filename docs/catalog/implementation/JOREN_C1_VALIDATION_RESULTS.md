# C1 validation results

Date: 2026-11-04, Europe/Amsterdam. Local offline verification only.
Start SHA: `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Final software SHA: see the local delivery addendum in
[the implementation report](JOREN_C1_IMPLEMENTATION_REPORT.md).

## Results

| Check | Actual result |
| --- | --- |
| Original source custody | All four supplied hashes and byte counts match; original files unchanged |
| Preserved review reports | 16/16 copies byte-identical to review worktree originals |
| Source coverage | 61/61; RUN 20, BIKE 21, SWIM 20; all source IDs retained |
| Original cells | 966 retained cells including header/notes; all 915 workout cells preserved |
| Complete execution | 444 ordered events: 168 timed zones, 154 swim distance blocks, 122 stationary wall rests |
| Row structure | All five zone subtotals and total time/distance agree on every row; no inferred segments or time |
| Identities | 61 unique keys and 61 unique IDs; no cross-collision or overlap with 336 offline historical UUID literals |
| Source revisions | Any changed workbook or PDF bytes rejected before XML processing |
| Operational state | All 61 inactive, method/release unset, approved operational TSS unavailable, A–F pending |
| Determinism | Two CLI runs and the golden artifact produce identical JSON and UUIDs; caller Decimal precision does not affect regeneration |
| New focused C1 tests | **156 passed**, final focused rerun 1.83 seconds |
| Full backend suite | **1,169 passed**, 132.84 seconds, one existing Starlette/httpx deprecation warning |
| Ruff | `python -m ruff check app tests`: pass using existing backend virtualenv, Ruff 0.16.0 |
| Formatting | `python -m ruff format --check app tests`: pass, 158 files |
| Strict mypy | `python -m mypy app tests`: pass, 158 source files; repository `strict=true` |
| Diff hygiene | `git diff --check`: pass |

The complete backend run includes the existing catalog/planning/repository,
source/migration static contracts, public OpenAPI and recursive private-load leak
checks, Realized TSS V2, exact A9 planning parity and weekly completeness tests.
No earlier Realized V2 or A3–A9 test was modified or weakened. A final focused C1
rerun also covers the explicit provenance/rounding-policy metadata added while
the complete regression was running; those fields do not change active behavior.

## Reproduction

From `backend`, using the existing project virtual environment:

```text
python -m app.jobs.joren_catalog_dry_run --dry-run
python -m app.jobs.joren_catalog_dry_run --dry-run --private-output ../docs/catalog/implementation/joren_c1_manifest_v1.json
python -m pytest tests/test_joren_c1_draft.py -q
python -m pytest -q
python -m ruff check app tests
python -m ruff format --check app tests
python -m mypy app tests
```

Canonical manifest SHA-256:
`3c149c9096dd568156eab0246f7f6c679fc6ac98416b073a798c7bde3b68bc85`.
The command emits a load-free JSON summary with no row errors and all six
approval gaps. Default execution writes no file. Use a new local path for each
optional `--timings` report; timings are deliberately not reproducible metadata.
Git attributes preserve original report/source bytes and canonical manifest LF
bytes even under this workstation's `core.autocrlf=true` setting.

Focused tests use independent original OOXML cells and the review's independently
materialized numerical table as oracles. They cover every row's raw values,
numeric precision, ordered/repeated blocks and exact token spans; sprint seconds;
swim meters and unknown duration; explicit unzoned/rest/RPE absence; five zone
totals; source/proposal provenance; identity collisions/changed revisions;
idempotent regeneration; malformed/empty/unsupported tokens, missing/reordered/
formula cells and nonfinite numbers; unavailable operational method; frozen
activation fields; no network access; no private evidence in normal output,
errors or repr; source bytes; and unchanged historical catalog snapshots.

## Parser timings, separate from planner performance

Two independent local dry runs on this Windows/Python 3.10 workstation:

| Stage | Run 1 | Run 2 |
| --- | --- | --- |
| Offline historical UUID registry | 35.09 ms | 35.70 ms |
| Verify / parse / normalize all sources and proposal | 51.40 ms | 54.27 ms |
| Serialize private JSON | 75.46 ms | 99.90 ms |

No real planner was executed by the C1 command. These are local measurements,
not a latency guarantee or a planner benchmark. The eight automatic-search
timeouts from the review remain separate C7/follow-up work. No selection
algorithm, coefficient or search behavior changed.

## Open verification and approval gates

- **PostgreSQL/pgTAP: DEFERRED BY OWNER — PRE-BETA.** No database integration,
  durable uniqueness, fresh/upgrade replay, grants/RLS or real-token execution
  is claimed. No database tools were installed and no database was contacted.
- A–F are still open. Scientific method/precision/compatibility, catalog release,
  athlete/selection scope, per-block guidance, swim planning/rest scope and
  activation remain approval-dependent. No operational P participates in a plan.
- Public/mobile behavior is unchanged. TypeScript/device checks are not applicable
  to this Python-only offline adapter; C3/C8 must validate any later contract/UI
  changes. No claim is made about device or hosted readiness.

C1's offline source/software scope is verified. These later integration and
release gates are preserved, not silently treated as passed.
