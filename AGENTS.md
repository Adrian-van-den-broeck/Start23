# Start23 development instructions

## Sources of truth

- Read this file and the current MVP roadmap before making significant changes.
- For work inside a subdirectory, also follow the nearest applicable AGENTS.md.
- The current roadmap and latest explicitly approved decision/specification
  override older implementation behavior, comments and tests when they conflict.
- Older implemented behavior may be historical. Do not preserve it solely because
  it already exists.
- Do not invent missing product, physiological or safety requirements. Fail closed
  and report the missing decision.

## Architecture

- Mobile: React Native with Expo and TypeScript.
- Backend: Python with FastAPI.
- Database/auth/storage: hosted Supabase.
- Backend deployment: Railway.
- Maintain a modular monolith.
- Do not introduce microservices, Celery, Redis, TimescaleDB or Kubernetes unless
  explicitly approved.

## Domain and physiology

- Physiological and training-rule decisions must be deterministic Python behavior.
- Keep the physiology domain independent of FastAPI, database, Supabase and LLM clients.
- The LLM may extract structured context and explain recommendations; it must not
  independently calculate zones, change physiological rules, or mutate plans/zones.
- Never invent physiological formulas, thresholds, calibration rules, progression
  values, taper factors or safety limits.
- Material physiological rule changes require explicit versioned ruleset provenance.
- Historical decisions/calculations must retain the ruleset/model version that produced them.
- Do not silently reinterpret historical data under a newer ruleset.

## State changes

- System-generated changes to critical training state must first be pending.
- Athlete confirmation is required before applying plan or zone changes where defined.
- Preserve stale-safe/version-precondition semantics.
- Preserve idempotency for retryable operations.
- Never replace optimistic concurrency with unconditional last-write-wins behavior.

## Privacy and security

- Planned and realized TSS/private load are server-private and must not appear in
  athlete-facing APIs, mobile UI, errors, logs, analytics or accessibility labels.
- Never expose service/secret keys, database passwords or LLM API keys to mobile.
- Derive athlete identity from a verified access token.
- Never accept a client user_id as authoritative.
- Enable and preserve RLS on user-owned data.
- Do not weaken grants/RLS to work around application issues.
- Do not commit .env files or secrets.

## Database

- Use forward-only migrations for already-migrated behavior.
- Do not rewrite an applied migration to change current behavior.
- Preserve historical records and provenance unless an explicit migration decision
  authorizes transformation/deletion.
- Do not recalculate historical physiological/private-load values without an
  explicitly defined migration rule.

## Engineering

- Use strict TypeScript.
- Use typed Pydantic API contracts.
- Keep FastAPI route handlers thin.
- Put business logic in services/domain modules.
- Prefer existing architectural patterns over introducing parallel abstractions.
- Prefer small, reviewable changes.
- Do not modify unrelated files.
- Do not weaken tests simply to make a change pass.
- When a test represents explicitly superseded behavior, replace it with coverage
  for the new approved requirement and document why.

## Verification

Run all checks relevant to the change, including where applicable:
- backend tests
- Ruff/formatting
- strict mypy
- OpenAPI/public-contract tests
- recursive TSS/private-load leak tests
- strict TypeScript/mobile tests
- database/pgTAP/RLS tests

If an environment prevents a required check from running, report it as an open
verification gate. Do not claim a phase or task is complete merely because local
unit tests pass.