# AI Infrastructure Research Dashboard

A full-stack internal tool for researching and tracking AI infrastructure — hardware products, companies, datacenters, research notes, metrics, and ingested source documents.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL, Redis |
| Frontend | Vite, React 18, TypeScript, TanStack Query v5, Tailwind CSS |
| Workers | Celery + Celery Beat (ingestion pipeline) |
| Infrastructure | Docker Compose |

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum change JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD
```

### 2. Start all services

```bash
docker compose -f infra/docker-compose.yml up --build
```

This starts: `postgres`, `redis`, `api` (FastAPI on :8000), `web` (Vite dev server on :5173), `worker` (Celery), `scheduler` (Celery Beat).

### 3. Run database migrations

```bash
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

### 4. Seed the database

```bash
docker compose -f infra/docker-compose.yml exec api python scripts/seed.py
```

This creates the admin user (from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`), sample entities, metric series, and metric data points.

### 5. Open the app

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

**Default admin login:** `admin@example.com` / `Adminpass1!` (or whatever you set in `.env`)

---

## Common Commands

| Task | Command |
|---|---|
| Start services | `docker compose -f infra/docker-compose.yml up --build` |
| Stop services | `docker compose -f infra/docker-compose.yml down` |
| View logs | `docker compose -f infra/docker-compose.yml logs -f` |
| Run migrations | `docker compose -f infra/docker-compose.yml exec api alembic upgrade head` |
| Create migration | `docker compose -f infra/docker-compose.yml exec api alembic revision --autogenerate -m "describe change"` |
| Seed database | `docker compose -f infra/docker-compose.yml exec api python scripts/seed.py` |
| Run ingestion | `docker compose -f infra/docker-compose.yml exec api python -c "import asyncio; from api.workers.tasks import _async_periodic_run; asyncio.run(_async_periodic_run())"` |
| Backend tests | `docker compose -f infra/docker-compose.yml exec api pytest` |
| Frontend tests | `docker compose -f infra/docker-compose.yml exec web npm run test` |
| Backend lint | `docker compose -f infra/docker-compose.yml exec api ruff check src tests` |
| Frontend lint | `docker compose -f infra/docker-compose.yml exec web npm run lint` |

---

## Project Structure

```
/
├── apps/
│   ├── api/                  FastAPI backend (Python 3.11+, src layout)
│   │   ├── src/api/          Application package
│   │   │   ├── routes/       HTTP route handlers (RBAC at this layer)
│   │   │   ├── services/     Business logic + cache invalidation
│   │   │   ├── repositories/ DB queries only
│   │   │   ├── models/       SQLAlchemy models
│   │   │   ├── schemas/      Pydantic v2 DTOs
│   │   │   └── workers/      Celery app + tasks
│   │   ├── alembic/          Database migrations
│   │   ├── tests/            Pytest tests
│   │   └── scripts/          One-off scripts (seed.py)
│   └── web/                  Vite + React + TypeScript frontend
│       └── src/
│           ├── components/   Shared UI components
│           ├── routes/       Page-level route components
│           ├── lib/          API client, query client, Zod schemas
│           ├── store/        Auth context
│           └── test/         Vitest unit tests
├── infra/                    Docker Compose definitions
├── data/
│   └── ingest/               Sample JSON files for ingestion pipeline
├── docs/                     Architecture docs and ADRs
└── .env.example              Environment variable template
```

---

## Roles

| Role | Capabilities |
|---|---|
| `admin` | Full access — user management, audit log, all CRUD, all notes |
| `analyst` | Create/edit own notes, create metric series and points, trigger ingestion |
| `viewer` | Read-only — published notes only, all entities, all metric data |

---

## Key Features

- **JWT auth** with rotating refresh tokens, rate-limited login
- **Forgot / reset password** flow (SMTP email or console log in dev)
- **Admin invite flow** — invite users by email with time-limited tokens
- **Hardware Products, Companies, Datacenters** — full CRUD with pagination
- **Research Notes** — markdown editor, draft/review/published workflow, entity linking, public slug URLs
- **Metric Series + Points** — time-series data per entity, bulk upsert, CSV export, dashboard charts
- **Ingestion Pipeline** — JSON file ingestion, entity extraction, idempotent by content hash, Celery background workers
- **Unified Search** — PostgreSQL full-text search across notes and source documents with relevance ranking and highlighted snippets
- **Audit Log** — admin-visible record of all mutations
- **Redis cache** — 60s TTL on list/detail endpoints, invalidated on write

---

## Documentation

| Doc | Description |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, layering, entity relationships |
| [`docs/AUTH.md`](docs/AUTH.md) | JWT strategy, RBAC, rate limiting, password reset |
| [`docs/NOTES.md`](docs/NOTES.md) | Research notes workflow, status machine, entity linking |
| [`docs/METRICS.md`](docs/METRICS.md) | Metric series and points API, dashboard |
| [`docs/INGESTION.md`](docs/INGESTION.md) | Ingestion pipeline, entity extraction, Celery workers |
| [`docs/SEARCH.md`](docs/SEARCH.md) | Full-text search architecture, RBAC, query syntax |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production deployment guide |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Architecture decision records (ADRs) |

---

## Environment Variables

See [`.env.example`](.env.example) for the full list with descriptions.

Critical variables to set before deploying:

- `JWT_SECRET` — generate with `openssl rand -hex 32`
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` — initial admin account
- `DATABASE_URL` / `REDIS_URL` — connection strings
- `CORS_ORIGINS` / `FRONTEND_BASE_URL` — your frontend URL
- `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` — email delivery (leave blank to log invite/reset URLs to console in dev)
