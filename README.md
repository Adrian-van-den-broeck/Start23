# Start23 (Wombo)

Start23 is a triathlon training app, published to athletes as **Wombo**. It
builds a weekly plan from deterministic, reviewed training rules, calibrates
heart-rate zones from field tests, and asks the athlete to approve every plan
or zone change before it becomes active.

## Repository layout

| Path | What it holds |
|---|---|
| `backend/` | FastAPI modular monolith: physiology rules, onboarding, planning, activities, calibration, Polar integration. Deployed to Railway. |
| `mobile/` | React Native app (Expo SDK 57, TypeScript strict, expo-router). |
| `supabase/` | Forward-only database migrations, seed data and pgTAP tests for the hosted Supabase project. |
| `docs/` | Requirements, decisions, architecture, implementation notes and UI specifications. |
| `scripts/` | PowerShell helpers to switch between local and production mode and to build the Play Store bundle. |

## Before you change anything

- Read [`AGENTS.md`](AGENTS.md) and, for app work, [`mobile/AGENTS.md`](mobile/AGENTS.md).
- The current plan is [`docs/implementation/mvp-roadmap.md`](docs/implementation/mvp-roadmap.md).
  Approved owner decisions live in [`docs/decisions/`](docs/decisions/).
- The approved interface is V3, described in [`docs/ui/WOMBO_UI_V3.md`](docs/ui/WOMBO_UI_V3.md).
- Planned and realized TSS (private load) never leaves the server: not in
  athlete-facing APIs, the app, logs or errors.

## Backend

Full setup, endpoints and configuration are in [`backend/README.md`](backend/README.md).
In short, from `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API then runs on `http://127.0.0.1:8000`; `/ready` is the health check.

## Mobile app

From `mobile/`:

```powershell
npm install
Copy-Item .env.example .env
npm start
```

`.env` needs the Supabase URL, the Supabase **publishable** key and the API base
URL. Never put a secret or service-role key in the app.

`EXPO_PUBLIC_UI_VERSION` selects the presentation baked into the bundle. Unset
or `v3` gives V3 (the default); `v2` is kept as a fallback.

`npm start` expects a development build (`expo-dev-client`). In VS Code, the
**Wombo: Run Android app** task starts the backend, the emulator bridges and
the app together.

## Checks

Run every check that applies to your change before committing.

Backend, from `backend/`:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests
```

Mobile, from `mobile/`:

```powershell
npm run typecheck
npm run check:unused
npm test
```

Run the mobile tests a second time with `EXPO_PUBLIC_UI_VERSION=v2` to cover
the V2 fallback.

Database, from the repository root with the Supabase CLI and a local stack:

```powershell
supabase test db
```

## Database changes

Migrations in `supabase/migrations/` are forward-only. Never edit a migration
that has already been applied; add a new one. Keep row-level security enabled
on athlete-owned data.

## Deployment

- **Backend:** Railway builds `backend/Dockerfile` from `main` and checks
  `/ready` before switching traffic (see `backend/railway.toml`).
- **Mobile:** EAS builds with the `wombo` profile in `mobile/eas.json`.
  `scripts/set-start23-mode.ps1 -Mode production` points the app at Railway,
  then `scripts/build-start23-playstore.ps1` creates the Play Store bundle.
  Both are also available as VS Code tasks.

## Test accounts

Test account credentials are stored locally in the Git-ignored
`.env.test-accounts.local` file. Ask the project owner for test access.
