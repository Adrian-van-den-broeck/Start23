# Audit evidence and reproducibility

Audit date: 26 October 2026. Frozen source: `aff74558d0a6511286a4a84a44ea25a03ca57549`. Branch: `audit/wombo-full-system-review`, workspace `.worktrees/audit-wombo-full-system-review`.

This directory contains only audit reports, public release/schema metadata, synthetic fixtures/probes and local command results. It contains no real athlete records, database credentials, privileged keys, provider tokens or Auth sessions. Public project/domain/build IDs are metadata, not credentials.

## Requested deliverables

- `../WOMBO_FULL_SYSTEM_AUDIT.md`
- `../WOMBO_SECURITY_PRIVACY_AUDIT.md`
- `../WOMBO_END_TO_END_TEST_MATRIX.md`
- `../WOMBO_TECHNICAL_DEBT_AND_RISKS.md`
- `../WOMBO_JOREN_REVIEW_QUESTIONS.md`
- `../WOMBO_PRIORITIZED_FIX_PLAN.md`

`artifact-manifest.json` lists every created file under docs/audits with size and SHA-256. `findings.json` is the structured source for the twenty confirmed records. U-001/U-002 remain explicitly unconfirmed and are documented separately in the main audit.

## Existing suite commands and authority

Commands were run in the isolated worktree. The existing Python venv and the integration mobile dependency installation were reused without installation or update; mobile/node_modules is a local junction. This is not a clean-room dependency-install verification. Exact package/environment versions are in `environment.json`.

From `backend` using the existing `backend/.venv/Scripts/python.exe` in the original repository:

```text
python -m pytest -p no:cacheprovider
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests
```

Results: 778 backend tests pass; Ruff, formatting and strict mypy pass. Test output contains one upstream Starlette/httpx deprecation warning. Output logs are normalized from Windows UTF-16 to portable UTF-8 without changing their text.

Strict mobile compilation was run with the installed TypeScript executable:

```text
node mobile/node_modules/typescript/bin/tsc --noEmit -p mobile/tsconfig.json
node mobile/node_modules/typescript/bin/tsc --noEmit --noUnusedLocals --noUnusedParameters -p mobile/tsconfig.json
```

Both exited 0 with empty output. Canonical tests were launched **from mobile**, with cache/output directed into the audit workspace:

```text
node node_modules/jest/bin/jest.js --runInBand --ci --cacheDirectory ../.audit-jest-cache-mobile --json --outputFile ../docs/audits/evidence/mobile-jest-canonical-results.json
```

Canonical result: 67 suites pass, 1 fails; 611 tests pass and 2 fail. `test-result-summary.json` extracts the authoritative Jest totals. `mobile-jest-canonical.log` contains the actual failure output. An initial run from repository root had alias-resolution failures; `mobile-jest.log` / `mobile-jest-results.json` are retained diagnostics and are **not** the canonical test result.

The failing `src/screens/PlanningProposalBoundary.test.tsx` was rerun alone (`proposal-repeat*`): 10 pass, 2 fail. A diagnostic rerun added existing `./jest.setup.ts` plus `../docs/audits/evidence/freeze-date.cjs` to setupFilesAfterEnv, setting Date to 2026-10-05: 12/12 pass (`proposal-frozen*`). Product source and existing test files were not changed. This diagnoses a clock-dependent test defect; it is not substituted for a green canonical suite.

PowerShell sometimes labels native stderr as NativeCommandError even when Jest writes PASS. Use actual exits and structured JSON, not that category label, to determine success.

## Added audit probes

From backend:

```text
python -m pytest -p no:cacheprovider ../docs/audits/evidence/test_audit_backend.py
```

Five probes pass: three adjacent-week spacing context omissions (run/bike/swim) through the actual layout service, one production review-version gap, one dependency-free readiness signal. The spacing probes construct minimal typed projections to isolate context omission; they do not certify Pydantic inputs, PostgreSQL or a persisted API flow.

From mobile, set `EXPO_PUBLIC_API_BASE_URL=https://synthetic.invalid` for the synthetic transport module and run:

```text
node node_modules/jest/bin/jest.js --config ../docs/audits/evidence/audit-jest.config.cjs --runInBand --ci --json --outputFile ../docs/audits/evidence/audit-mobile-results.json
```

Eleven probes pass across three suites. They characterize lost resume references, cross-account locator side effects, stale pending-feedback history, cached activities, restriction hydration, disconnected check-in approval, transient auth-token deletion, no fetch deadline and invalid-JSON recovery. AUD-006 is a **protected control** for the actual backend idempotent approval-retry contract. An earlier mock that incorrectly rejected the replay was corrected and excluded as defect evidence. Ten mobile probes are gap characterizations; a passing characterization means the defect was observed, not that behavior is acceptable.

`audit_engine_matrix.py` executes seven bounded subprocess cases using the tracked full-source catalog projection and current domain. It uses stable synthetic source IDs; hosted V2 successors use separately generated IDs. No network or persistence call occurs. Results are in `engine-matrix-results.json`; each child had a 20-second audit limit, and every recorded case completed. These timings are local domain timings, not Railway/API/device benchmarks.

## Read-only release and advisory observations

- `git ls-remote origin refs/heads/main` verified the baseline. No fetch/push/merge was performed.
- `read_release_metadata.py` requested Railway production status with a strict output allowlist. `railway-release-metadata.json` records invalid saved grant/Unauthorized. No login, variable read/reveal, deployment or service mutation occurred.
- Public `/ready` and `/openapi.json` GETs were requested at the two known URLs. Python's trust chain failed in this environment (`public-health.json`); Windows curl with verification enabled succeeded (`public-health-windows-curl.json`, transcribed from the actual command result). No TLS verification was disabled.
- Local and public OpenAPI snapshots contain schemas only. `openapi-comparison.json` records path/component differences; `openapi-normalized-comparison.json` verifies production components match after removing Decimal pattern metadata. A schema match is not a source SHA or functional test.
- `read_eas_metadata.py` ran `eas build:list --platform android --limit 3 --json --non-interactive`. Only allowlisted build/status/source/version metadata was retained. No artifact URL, credential, new build, submission or store-track mutation occurred.
- `read_npm_audit.py` ran read-only `npm audit --omit=dev --json` with stdout/stderr separated. `npm-audit-clean.json` is valid authoritative registry output; `npm-audit-initial-mixed.log` preserves the first malformed PowerShell mixed-stream capture. No fixes/install/update were run. Advisory occurrence does not prove application exploitability.
- `secret-pattern-scan.json` records current tracked application pattern locations only, never matched secret values. Dummy test keys were deliberately excluded. It is not a full-history or binary secret scan.

`source-references.json`, `environment.json`, `largest-source-files.json`, `git-source-manifest.json` and `audit-validation.json` support the review. Generators `build_findings.py`/`build_reports.py` are audit artifact tooling, not application behavior. Five other requested documents were authored directly as Markdown.

## Unexecuted gates

No local Docker/PostgreSQL/pgTAP runtime was available; all 27 tracked database suites remain a fresh verification gate. No hosted migration, staging test-account/row/file mutation, OAuth/provider operation, production athlete request, physical-device test, native build/install or rollback was executed. Existing historical reports were not counted as current successes.

Generated Jest cache directories were verified to reside inside the audit workspace, checked not to be reparse points and removed with native PowerShell. The dependency junction remains ignored local workspace setup; it was not recursively deleted or modified. Final git checks show only docs/audits is added in the audit worktree, the UI V2 integration worktree is clean, and the original unrelated dirty-file list remains unchanged.
