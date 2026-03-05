# AI Infrastructure Research Dashboard

A monorepo for researching and visualising AI infrastructure data.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Compose v2)
- [Make](https://www.gnu.org/software/make/)

## Quick Start

```bash
cp .env.example .env        # edit JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD
make dev                    # builds + starts postgres, redis, api, web
# in another terminal:
make migrate                # runs alembic upgrade head
make seed                   # creates the default admin user
```

| URL | Service |
|---|---|
| http://localhost:5173 | Frontend |
| http://localhost:8000/docs | API Swagger UI |
| http://localhost:8000/healthz | Health check |

## Commands

| Command | Description |
|---|---|
| `make dev` | Build and start all services |
| `make down` | Stop all services |
| `make logs` | Tail logs |
| `make lint` | ruff (backend) + ESLint (frontend) |
| `make format` | ruff formatter + Prettier |
| `make test` | pytest (backend) + Vitest (frontend) |
| `make migrate` | Apply pending Alembic migrations |
| `make makemigrations MSG="..."` | Create new Alembic revision |
| `make seed` | Create default admin user (idempotent) |
| `make ingest` | Run a one-shot ingestion from `data/ingest/` |

> `make lint`, `make test`, `make migrate`, `make seed` require `make dev` to be running first.

## Creating the Admin User

```bash
make migrate   # ensure tables exist
make seed      # creates ADMIN_EMAIL / ADMIN_PASSWORD from .env
```

To change the admin credentials, update `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env` and re-run `make seed`.

## Logging In (local)

```bash
# via curl
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"changeme123!"}' | jq .

# or open http://localhost:5173/login in the browser
```

## Environment Variables

Copy `.env.example` → `.env` and set at minimum:

| Variable | Description |
|---|---|
| `JWT_SECRET` | Long random string — `openssl rand -hex 32` |
| `ADMIN_EMAIL` | Initial admin account email |
| `ADMIN_PASSWORD` | Initial admin account password |

See `.env.example` for the full list.

## Entity Management (Slice 2)

Slice 2 adds three core domain entities browsable via the sidebar.

### Pages

| URL | Description |
|---|---|
| `/hardware-products` | List all GPUs / CPUs / accelerators |
| `/hardware-products/:id` | Detail view with specs |
| `/companies` | List semiconductor vendors, fabs, cloud providers |
| `/companies/:id` | Detail view |
| `/datacenters` | List datacenter sites with capacity |
| `/datacenters/:id` | Detail view with owner company link |

### REST API

| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/hardware-products` | viewer+ |
| POST | `/api/v1/hardware-products` | analyst / admin |
| GET | `/api/v1/hardware-products/{id}` | viewer+ |
| PATCH | `/api/v1/hardware-products/{id}` | analyst / admin |
| DELETE | `/api/v1/hardware-products/{id}` | admin only |
| GET | `/api/v1/companies` | viewer+ |
| POST | `/api/v1/companies` | analyst / admin |
| GET | `/api/v1/companies/{id}` | viewer+ |
| PATCH | `/api/v1/companies/{id}` | analyst / admin |
| DELETE | `/api/v1/companies/{id}` | admin only |
| GET | `/api/v1/datacenters` | viewer+ |
| POST | `/api/v1/datacenters` | analyst / admin |
| GET | `/api/v1/datacenters/{id}` | viewer+ |
| PATCH | `/api/v1/datacenters/{id}` | analyst / admin |
| DELETE | `/api/v1/datacenters/{id}` | admin only |

List endpoints support `?limit=20&offset=0` pagination and are Redis-cached (60s TTL).

### Seed Data

`make seed` now also creates:
- **Companies**: NVIDIA, AMD, TSMC, Amazon, Google
- **Hardware Products**: H100, A100, MI300X
- **Datacenter Sites**: US West GPU Cluster, EU AI Datacenter

## Research Notes Workflow (Slice 3)

Slice 3 adds a full research notes system with markdown editing, entity linking, and a publish workflow.

### Pages

| URL | Description |
|---|---|
| `/notes` | List notes (filtered by status / tag / search query) |
| `/notes/new` | Create a new draft note |
| `/notes/:id` | Edit note — Write/Preview tabs, tag chips, entity linker |
| `/published/:slug` | Public read-only rendered page (no auth required) |

### REST API

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/notes` | viewer+ | List notes (RBAC-filtered) |
| POST | `/api/v1/notes` | analyst / admin | Create note |
| GET | `/api/v1/notes/{id}` | viewer+ | Get note detail |
| PATCH | `/api/v1/notes/{id}` | author / admin | Update title, body, tags, status |
| DELETE | `/api/v1/notes/{id}` | author / admin | Delete note |
| POST | `/api/v1/notes/{id}/publish` | analyst / admin | Publish note → generates slug |
| GET | `/api/v1/notes/{id}/links` | viewer+ | Get entity links |
| PUT | `/api/v1/notes/{id}/links` | author / admin | Atomically replace entity links |
| GET | `/api/v1/published/{slug}` | public | Fetch published note by slug |
| GET | `/api/v1/audit` | admin only | Audit log (recent activity) |

### Testing the Publish Flow

```bash
# 1. Login as analyst
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"analyst@example.com","password":"Analystpass1!"}' | jq -r .access_token)

# 2. Create a draft note
NOTE_ID=$(curl -s -X POST http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"My GPU Analysis","body_markdown":"# H100\n\nGreat chip.","tags":["gpu"]}' | jq -r .id)

# 3. Publish it
SLUG=$(curl -s -X POST "http://localhost:8000/api/v1/notes/$NOTE_ID/publish" \
  -H "Authorization: Bearer $TOKEN" | jq -r .slug)

# 4. Read without auth
curl -s "http://localhost:8000/api/v1/published/$SLUG" | jq .title
# or open: http://localhost:5173/published/$SLUG
```

### Seed Data

`make seed` also creates:
- **3 research notes** (1 published, 1 review, 1 draft)
- Notes linked to H100, NVIDIA, and US West GPU Cluster
- Tags: `gpu`, `supply-chain`, `datacenter`

The published note is immediately accessible at `/published/<slug>`.

## Metrics + Dashboard (Slice 4)

Slice 4 adds a `MetricSeries` + `MetricPoint` time-series model for tracking numeric KPIs against any entity, and replaces the placeholder Dashboard with live KPI cards and Recharts trend charts.

### Pages

| URL | Description |
|---|---|
| `/dashboard` | KPI cards + metric trend charts |

### REST API

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/metrics/overview` | any | KPI counts + chart data |
| `GET` | `/api/v1/metric-series` | any | List series (paginated) |
| `POST` | `/api/v1/metric-series` | analyst+ | Create series |
| `GET` | `/api/v1/metric-series/{id}` | any | Get series |
| `PATCH` | `/api/v1/metric-series/{id}` | analyst+ | Update series metadata |
| `DELETE` | `/api/v1/metric-series/{id}` | admin | Delete series |
| `POST` | `/api/v1/metric-series/{id}/points` | analyst+ | Bulk upsert points (idempotent) |
| `GET` | `/api/v1/metric-series/{id}/points` | any | List points (with date range filter) |
| `GET` | `/api/v1/metric-series/{id}/export.csv` | any | Download points as CSV |

### Seed Data

`make seed` now also creates 4 metric series with 18 monthly data points each:

- **H100 Shipment Volume** (hardware_product → H100, unit: units/thousands)
- **NVIDIA Revenue** (company → NVIDIA, unit: USD billions)
- **US West DC Power Usage** (datacenter → US West GPU Cluster, unit: MW)
- **EU AI DC Power Usage** (datacenter → EU AI Datacenter, unit: MW)

See [docs/METRICS.md](docs/METRICS.md) for full documentation.

## Ingestion Pipeline (Slice 5)

Slice 5 adds a full ingestion pipeline: file-based JSON ingest, idempotent deduplication (sha256 content hash), rules-based entity extraction, and Celery background workers.

### Services

| Service | Description |
|---|---|
| `worker` | Celery worker — processes ingestion tasks |
| `scheduler` | Celery Beat — triggers periodic ingestion every `INGESTION_INTERVAL_MIN` minutes |

### Pages

| URL | Description |
|---|---|
| `/sources` | List ingested documents with type/search filters; "Run Ingestion" button for analyst+ |
| `/sources/:id` | Document detail — extracted entity chips, raw text, entity breakdown |

### REST API

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/ingestion/run` | analyst+ | Trigger ingestion run (async, 202) |
| `GET` | `/api/v1/ingestion/runs` | analyst+ | List all runs (paginated) |
| `GET` | `/api/v1/ingestion/runs/{id}` | analyst+ | Get run status + stats |
| `GET` | `/api/v1/sources` | viewer+ | List source documents |
| `GET` | `/api/v1/sources/{id}` | viewer+ | Get document detail with entity links |

### Running ingestion

```bash
# One-shot (no Celery needed — runs directly in the api container)
make ingest

# Or trigger via API
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"analyst@example.com","password":"Analystpass1!"}' | jq -r .access_token)

curl -X POST http://localhost:8000/api/v1/ingestion/run \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"file","source_name":"local-ingest"}'
```

### Adding ingest data

Place JSON files in `data/ingest/`. Each file must be an array of objects:

```json
[
  {
    "title": "Article Title",
    "url": "https://example.com/article",
    "source_name": "my-feed",
    "published_at": "2024-01-15T10:00:00Z",
    "raw_text": "Full text content..."
  }
]
```

Three sample files with 9 AI hardware articles are included at `data/ingest/sample{1,2,3}.json`.

See [docs/INGESTION.md](docs/INGESTION.md) for full documentation.

## Unified Search (Slice 6)

Slice 6 adds a full-text search experience across ResearchNotes and SourceDocuments using PostgreSQL native FTS (tsvector + GIN indexes).

### Pages

| URL | Description |
|---|------|
| `/search` | Unified search with All/Notes/Sources tabs, filter panel, paginated results |

### REST API

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/search` | any | Full-text search across notes + sources |

**Key parameters:** `q` (required), `type=all|note|source`, `tags`, `status`, `entity_type`, `entity_id`, `source_type`, `start`, `end`, `limit`, `offset`

See [docs/SEARCH.md](docs/SEARCH.md) for full documentation.

## Where to Put Future Modules

| Concern | Location |
|---|---|
| New API domain (e.g. papers) | `apps/api/src/api/routes/papers.py` + model in `models/` |
| New frontend page | `apps/web/src/routes/` + register in `App.tsx` |
| Shared types | `packages/shared/` |
| Infrastructure changes | `infra/docker-compose.yml` |
| Architecture decisions | `docs/` |

## Architecture

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system overview
- [docs/AUTH.md](docs/AUTH.md) — token strategy & RBAC
