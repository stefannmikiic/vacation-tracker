# Vacation Tracker

FastAPI + PostgreSQL monolith for employee vacation allowances and usage.

Admins import CSV/Excel data and query records. Employees view their yearly balance and create usage within rules. Authentication is HTTP Basic Auth with admin/employee roles.

Built as a layered, src-layout Python package with intentional scope control (KISS/YAGNI).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Make](https://www.gnu.org/software/make/) (optional but recommended)
- [uv](https://docs.astral.sh/uv/) and Python 3.12+ (for local development without containers)

## Setup (Docker Compose — primary)

1. Copy environment template and fill secrets:

```bash
cp .env.example .env
```

Set at least `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD`.  
The API service overrides `DATABASE_URL` to reach Postgres as host `db` inside the Compose network.

2. Build and start services:

```bash
make up
# equivalent: docker compose up --build -d
```

3. Apply migrations (manual — not run on container start):

```bash
make migrate
# equivalent: docker compose exec api uv run alembic upgrade head
```

4. Create the bootstrap admin (idempotent upsert):

```bash
docker compose exec api uv run python scripts/create_admin.py
```

5. Open the API:

- App: http://localhost:8000  
- OpenAPI docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

Stop:

```bash
make down
```

## Local development (secondary)

Use this when iterating without rebuilding images. You still need a reachable Postgres (`DATABASE_URL` in `.env`, typically `localhost`).

```bash
make sync          # uv sync --group dev
make run           # uvicorn with --reload on :8000
uv run alembic upgrade head
uv run python scripts/create_admin.py
```

## Makefile targets

| Target | Purpose |
|--------|---------|
| `sync` | Install project + dev tools with uv |
| `run` | Local API with reload |
| `up` / `down` | Docker Compose up/down |
| `migrate` | Alembic upgrade inside the `api` container |
| `test` | Pytest |
| `lint` | Ruff check |

## Architecture overview

Installable package under `src/vacation_tracker/`:

| Layer | Responsibility |
|-------|----------------|
| `api/` | HTTP adapters, auth dependencies, routers |
| `schemas/` | Pydantic request/response DTOs |
| `services/` | Use-cases (auth, import, vacation rules) |
| `repositories/` | Thin SQLAlchemy queries |
| `db/` | Engine/session, models, mixins |
| `imports/` | Parse/validate files (no DB writes) |
| `core/` | Settings, logging, security, constants, exceptions |

Data model: `Employee`, `VacationAllowance` (per year), `VacationUsage` (date range). Used/available days are computed, not stored.

## API overview

All business endpoints use **HTTP Basic Auth** (username = email).  
OpenAPI at `/docs` is the detailed contract; summary below.

### Ops

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/health` | Liveness; no auth |

### Admin imports (`Admin` role)

Multipart field name: `file` (`.csv` or `.xlsx`).

| Method | Path | Notes |
|--------|------|--------|
| `POST` | `/api/v1/admin/imports/employees` | Upsert profiles; hash passwords |
| `POST` | `/api/v1/admin/imports/allowances` | Upsert days per employee/year |
| `POST` | `/api/v1/admin/imports/usages` | Create usages; reject overlaps |

Imports support **partial success**: HTTP 200 with `created` / `updated` / `failed` and row-level `errors`. Invalid file structure → 400.

### Importing sample data

After Compose is up, migrations applied, and the bootstrap admin exists, load `sample_data/` in this order (employees → allowances → usages):

```bash
# Employees
curl -u "$ADMIN_EMAIL:$ADMIN_PASSWORD" \
  -F "file=@sample_data/employee_profiles.csv" \
  http://localhost:8000/api/v1/admin/imports/employees

# Allowances (repeat for 2019 / 2020 / 2021)
curl -u "$ADMIN_EMAIL:$ADMIN_PASSWORD" \
  -F "file=@sample_data/vacations_2019.csv" \
  http://localhost:8000/api/v1/admin/imports/allowances

# Usages
curl -u "$ADMIN_EMAIL:$ADMIN_PASSWORD" \
  -F "file=@sample_data/used_vacation_dates.csv" \
  http://localhost:8000/api/v1/admin/imports/usages
```

Sanity-checked against the real API: profiles and allowances import cleanly; usages succeed with **one expected row failure** — duplicate `user33@rbt.rs` range `2020-10-20`–`2020-10-20` (CSV lines 584–585). Overlap/duplicate rejection is intentional; do not change import rules to force that row through.

### Admin queries (`Admin` role)

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/api/v1/admin/employees` | Paginated list (`limit` / `offset`) |
| `GET` | `/api/v1/admin/employees/{id}/allowances` | 404 if employee missing |
| `GET` | `/api/v1/admin/vacation-usages` | Optional filters: `employee_id`, `year`, `from`, `to`; pagination: `limit` / `offset` |

### Employee self-service (any authenticated user; always own data)

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/api/v1/me/vacations/summary?year=` | Total / used / available |
| `GET` | `/api/v1/me/vacations/usages?from=&to=` | List usages in range |
| `POST` | `/api/v1/me/vacations/usages` | Create usage; 201 on success |

Create conflicts: overlap → 409; missing allowance / insufficient balance / bad dates → 400.

## Assumptions

Documented domain rules (locked for this project):

1. **Day counting** uses inclusive calendar days: `end - start + 1` (not business days).
2. **Cross-year ranges** split at year boundaries; each day counts toward the year it falls in.
3. **Employees** only access `/me` data for themselves; **admins** can query all imported data.
4. **Overlapping usages** for the same employee are rejected in application code (service create and usage import). Concurrent requests could theoretically race; there is no DB exclusion constraint for overlapping date ranges in this project scope.
5. **Create usage** is rejected if any affected year would go negative on available balance.
6. **Passwords** are bcrypt-hashed on import/admin create; plaintext is never stored.
7. **Admin bootstrap** is explicit via `scripts/create_admin.py` (not seeded in app lifespan).
8. Sample CSV **metadata rows** like `Vacation year,2019` are skipped by parsers; allowance year comes from that metadata when present.

## Architecture decisions

1. **`src/` installable layout** — Forces package installs and clean imports (`vacation_tracker.*`), matching common production Python practice.
2. **uv + `pyproject.toml` / `uv.lock` only** — Single dependency source; no parallel `requirements.txt`.
3. **Sync SQLAlchemy 2.0 + Alembic** — Simpler than asyncio for this assignment size; one session-per-request style.
4. **Layered monolith** — Routers → services → repositories → models. Enough separation without hexagonal/ports ceremony.
5. **HTTP Basic Auth + roles** — Matches the brief; no JWT/session store. Admin vs employee enforced in FastAPI dependencies.
6. **Import pipeline split** — Parsers/validators produce rows; `ImportService` persists. Keeps file IO out of repositories.
7. **Computed balances** — Used/available derived in `VacationService` so the schema stays small and rules stay in one place.
8. **Docker Compose at repo root** — Minimal packaging story; migrations remain an explicit operator step.

## Design tradeoffs

Deliberately **not** built (and why):

| Rejected | Reason |
|----------|--------|
| Microservices / import workers | Assignment is a single deployable API |
| JWT / OAuth | Brief specifies Basic Auth |
| Redis / Celery / message bus | No async jobs required at this scale |
| CQRS / event sourcing / outbox | Zero payoff for three entities |
| Full hexagonal / ports & adapters tree | Layers already provide boundaries |
| Splitting vacation into many services | One `VacationService` stays cohesive |
| Auto-migrate on container start | Keeps schema changes an explicit, reviewable step |
| DB exclusion constraint on overlapping usages | App-level check is enough for this assignment; concurrent race is an accepted tradeoff |

Partial-success imports trade strict all-or-nothing transactions for operator-friendly feedback on large CSVs. Usage imports do not enforce yearly balance (create-via-API does); that matches “load historical data, then enforce going forward.”

## Testing and CI

```bash
make test   # pytest (needs DATABASE_URL / local Postgres for DB-backed tests)
make lint   # ruff check
```

Test layout:

- `tests/unit/` — day math, parsers, services, authz smoke tests  
- `tests/integration/` — HTTP flow: import → summary → create usage  
- `tests/factories/` — small builders for Employee / Allowance / Usage  

CI (`.github/workflows/ci.yml` on `main` push/PR): Ruff → Alembic against Postgres 16 → Pytest → Docker image build.
