# Start23 development instructions

## Architecture

- Mobile client: React Native with Expo and TypeScript.
- Backend: Python with FastAPI.
- Database, authentication and storage: hosted Supabase.
- Deployment target for backend: Railway.
- Start as a modular monolith.
- Do not introduce microservices, Celery, Redis, TimescaleDB or Kubernetes
  unless explicitly requested.

## Business logic

- Physiological decisions must be implemented as deterministic Python code.
- The LLM may extract structured context and explain recommendations.
- The LLM must not independently mutate training plans or user zones.
- Changes to critical objects must first be stored as pending.
- User confirmation is required before applying those changes.
- Planned and realized TSS must never be returned to the mobile UI.

## Security

- Never expose service role keys, database passwords or LLM API keys
  in the mobile application.
- Derive the user identity from a verified access token.
- Enable Row Level Security on user-owned tables.
- Do not commit .env files.

## Engineering style

- Use strict TypeScript.
- Use Pydantic models for API input and output.
- Keep route handlers thin.
- Put business logic in services or domain modules.
- Add tests for all physiological calculations.
- Prefer small, reviewable changes.
- Do not modify unrelated files.