# Start23 backend

FastAPI foundation, Supabase access-token authentication, and the deterministic
Phase 3 physiology core for the Start23 modular monolith.

The backend contains configuration, structured logging, health endpoints,
local verification of Supabase user access tokens, and pure Python physiology
rules for debt, intensity, progression, anti-stack timing, recovery, taper,
zone structure, and confirmed-injury redistribution. It does not contain
database models, Supabase data access, LLM integrations, background workers,
or application-layer plan mutation. Draft rules fail closed, and BR-009
clinical validation is excluded from `phase-3-ruleset-1` until its limits are
approved.

All API errors use a stable `{"error": ...}` envelope and include a generated
request ID in both the response body and `X-Request-ID` header. Request-provided
correlation IDs are not trusted.

## Requirements

- Python 3.10 or newer
- IANA timezone data is installed through the `tzdata` project dependency,
  including on Windows

## Local setup

Run these commands from the `backend` directory.

### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

### macOS or Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

The endpoints are then available at:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/ready`
- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/api/v1/ready`
- `http://127.0.0.1:8000/api/v1/me`

## Configuration

Configuration is loaded from environment variables with the `START23_` prefix.
A local `.env` file is optional and ignored by Git and Docker.

| Variable | Default | Purpose |
|---|---|---|
| `START23_ENVIRONMENT` | `local` | Runtime environment: `local`, `test`, `staging`, or `production` |
| `START23_LOG_LEVEL` | `INFO` | Application log level |
| `START23_API_V1_PREFIX` | `/api/v1` | Versioned API prefix |
| `START23_SUPABASE_URL` | Start23 Supabase URL | Project used to determine issuer and JWKS URL |
| `START23_SUPABASE_JWT_AUDIENCE` | `authenticated` | Required user-token audience |
| `START23_SUPABASE_JWKS_CACHE_SECONDS` | `300` | Bounded JWKS cache lifetime; maximum 600 |
| `START23_SUPABASE_JWKS_TIMEOUT_SECONDS` | `5` | JWKS network timeout; maximum 30 |

## Authentication

The client signs in through Supabase Auth and sends its user access token:

```http
Authorization: Bearer <supabase-user-access-token>
```

`GET /api/v1/me` verifies the ES256 signature against the project's public JWKS
and validates issuer, audience, expiry, issued-at time, subject, and the
`authenticated` role. A successful response is:

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "role": "authenticated"
}
```

The identity comes exclusively from the verified token subject. User IDs in
request paths, query strings, headers, or bodies are not trusted.

The `EXPO_PUBLIC_SUPABASE_KEY` publishable key is a public client credential,
not a user JWT. It is not used for backend ES256 verification and must not be
sent as the bearer token. No service-role or Supabase secret key is required by
this authentication phase.

## Tests and quality checks

```bash
pytest
ruff check .
ruff format --check .
mypy app tests
```

The repository CI workflow runs these checks on backend pull requests and
pushes to `main`, rejects committed `.env` files, and checks application files
for privileged Supabase/database credential patterns.

## Docker

Build from the `backend` directory:

```bash
docker build -t start23-backend .
docker run --rm -p 8000:8000 -e PORT=8000 start23-backend
```

The image runs as a non-root user and reads Railway's `PORT` environment
variable when provided. `railway.toml` selects the Dockerfile build and uses
`/ready` as the deployment health check. Configure Railway's service root as
`/backend` and its config path as `/backend/railway.toml`.
