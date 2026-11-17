# Implemented blocker resolution evidence

Starting SHA: `0fa6509190d292d0c83e3076cda68c55624c202e`. Candidate branch: `release/joren-v6-migration-blocker-resolution`. This folder contains local test evidence and sanitized read-only infrastructure metadata. It contains no access tokens, service keys, actual athlete rows or mutation journals. Local fixtures use synthetic records. `evidence-sha256.json` hashes every other file in this folder; historical report bytes are additionally covered by `history-sha256.json`.

Start with [verification.json](verification.json), the [owner decisions](../JOREN_V6_REMAINING_RELEASE_GATES_NL.md) and [rollout plan](../JOREN_V6_INACTIVE_PRODUCTION_ROLLOUT_PLAN.md). All seven required implementation/decision reports are adjacent. `starting-evidence-review.json` records reading/parsing the earlier six readiness reports and their machine evidence; this candidate implements the actionable blockers rather than repeating that assessment.

## Scope and retained failures

PostgreSQL tests ran on a new isolated portable PostgreSQL 17.11 cluster, loopback port 55443, max_connections 40 and shared_buffers 64MB. No Docker or production athlete data was used. Accepted portable binaries were read only. Clean accepted 47 and reproduced actual hosted drift were separate databases. Hosted reproduction includes both differing bodies, all observed default ACL metadata and four service catalog ACL differences. It does not reproduce managed Supabase17.6/Linux or genuine GoTrue/PostgREST.

The original A5 fixture is unchanged: 8 pass, 1 fail, then abort before 20 remaining assertions. Only the explicit onboarding/fingerprint overlay passes 29/29. Each SQL record includes original and executed SQL hashes and its overlay status. The original failure is evidence, not a passing test. Final-schema tests unavailable at 47 are reported in the boundary evidence rather than relabeled as old-schema passes.

Both bundle guard runs use explicit local fixture fingerprints for original ledger statement representations and provider metadata. Exact accepted/new migration bodies are unchanged. They prove atomicity, permissions and unknown-commit refusal locally, not production eligibility. Owner-review bundles remain BLOCKED and are generated offline; only their manifest is committed here.

The known eight-second `current:build_4` diagnostic timeout remains; forty historical outcomes and twenty-six accepted non-timeout references match exactly. Fifteen exact multisession oracle contexts / 20,061,679 products match excluding elapsed timing. The 200,000-node ceiling remains. Initial dependency/import/cluster harness failures are documented in verification.json; final passing runs are separate.

## Reproduction recipes

From `backend` with the existing environment, run the two new test files first, then the full suite:

```text
python -m pytest -q tests/test_activity_projection_compatibility.py tests/test_v6_hosted_verification_adapter.py
python -m pytest -q
python -m mypy app tests benchmarks
python -m mypy --strict --explicit-package-bases scripts/prepare_v6_rollout_bundles.py scripts/rehearse_v6_migration_boundary.py scripts/v6_rollout_policy.py scripts/verify_v6_activity_boundaries.py scripts/verify_v6_blocker_sql.py scripts/verify_v6_rollout_bundle_guards.py scripts/inspect_v6_recovery_options.py scripts/run_v6_hosted_verification_adapter.py scripts/cleanup_v6_verification_subjects.py
```

Ruff check and format --check cover app/tests/benchmarks and the same nine scripts. From `mobile`, use the accepted lockfile/dependency tree: `npm test -- --runInBand` and `npx tsc --noEmit --noUnusedLocals --noUnusedParameters`. No dependency versions changed in this candidate.

For real PostgreSQL rehearsals, use a NEW disposable database name matching `wombo_v6_boundary_[a-z0-9_]+`, the exact local cluster directory, psql executable and port. The scripts require `--execute-disposable-local-only` and verify loopback/cluster custody:

```text
python -m scripts.rehearse_v6_migration_boundary --execute-disposable-local-only --psql <psql.exe> --cluster-directory <isolated-pgdata> --port 55443 --database <new-disposable-name> --hosted-preflight ../docs/catalog/implementation/migration-readiness-20261116/hosted-before.json --with-blocker-corrections --private-output <private-output>
python -m scripts.verify_v6_activity_boundaries --execute-disposable-local-only --psql <psql.exe> --cluster-directory <isolated-pgdata> --port 55443 --database <another-new-name> --private-output <private-output>
python -m scripts.verify_v6_rollout_bundle_guards --execute-disposable-local-only --psql <psql.exe> --cluster-directory <isolated-pgdata> --port 55443 --database <another-new-name> --private-output <private-output>
```

Repeat boundary and bundle rehearsals with `--reproduce-hosted-drift ../docs/catalog/implementation/migration-readiness-20261116/hosted-detail-final.json`. The helper recreates the observed app/provider ACL metadata locally; no hosted connection is made. Fresh-schema SQL suite uses `scripts.verify_v6_final_sql` with the same psql/cluster/port/private-output arguments and a new `wombo_v6_final_[a-z0-9_]+` database, retaining its explicit A5 overlay and local-only protections. Lifecycle/evidence/frequency runners remain existing scripts (`verify_v6_lifecycle_completion`, `verify_v6_evidence_rescheduling`, `verify_v6_frequency_policy`) against approved disposable databases, including their separate reload processes. Their private traces remain local; only checks/hashes are included here.

Normal startup is compared in independent processes against the accepted readiness source. Its unchanged OpenAPI hash, repository and disabled controls appear in startup-public-contract.json. This is source compatibility evidence, not deployed identity: Railway remains Unauthorized and published endpoints differ. Recovery metadata is GET-only; no checkpoint/restore/export or infrastructure creation occurred. The new adapter was tested with genuine local ES256 signatures and constrained transports, never run against hosted V6. Do not run its launcher or cleanup without the separate approvals in its report.
