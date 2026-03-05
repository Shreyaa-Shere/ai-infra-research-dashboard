# Architecture

## Overview

This is a monorepo for the **AI Infrastructure Research Dashboard** — a web application for researching and visualising AI infrastructure data.

## Layering

```
Browser (apps/web)
    │  HTTP / REST
    ▼
FastAPI (apps/api)          ← stateless, async
    ├── Routes    (src/api/routes/)
    ├── Services  (src/api/services/)   ← orchestration + cache invalidation
    ├── Repos     (src/api/repositories/) ← DB queries only
    ├── Models    (src/api/models/)     ← SQLAlchemy 2.0 declarative
    └── DB / Redis adapters
         │
         ├── PostgreSQL      ← primary data store
         └── Redis           ← list-endpoint cache (60s TTL)
```

## Domain Entity Relationships (Slice 2 + 3 + 4 + 5)

```
User
  │ id, email, hashed_password, role, is_active
  │
  ├──< ResearchNote            (author_id FK → User, CASCADE)
  │      │ id, title, body_markdown, status, slug, tags[], published_at
  │      │
  │      └──< NoteEntityLink   (note_id FK → ResearchNote, CASCADE)
  │             id, entity_type, entity_id  ← polymorphic ref (app-level FK)
  │
  └──< IngestionRun            (triggered_by FK → User, SET NULL)
         id, source_type, source_name, status, dry_run,
         started_at, finished_at, stats (JSONB), error_message

AuditLog                       (actor_user_id FK → User, SET NULL)
  id, action, entity_type, entity_id, meta_json

Company
  │ id, name (unique), type, region, website
  │
  └──< DatacenterSite          (owner_company_id FK → Company, SET NULL)
         id, name, region, power_mw, status

HardwareProduct                (standalone, no FK)
  id, name, vendor, category, release_date, memory_gb, tdp_watts, process_node

MetricSeries                   (entity_id is app-level, no hard FK)
  │ id, name, entity_type, entity_id, unit, frequency, source
  │
  └──< MetricPoint             (metric_series_id FK → MetricSeries, CASCADE)
         id, timestamp, value

SourceDocument                 (standalone, deduplicated by content_hash)
  │ id, title, url, publisher, published_at, raw_text
  │ content_hash (UNIQUE), extracted_entities (JSONB)
  │ source_type, source_name, status, created_at
  │
  └──< SourceEntityLink        (source_document_id FK → SourceDocument, CASCADE)
         id, entity_type, entity_id, entity_name
         ← polymorphic ref; entity_type reuses existing entity_type Postgres enum
```

### Enums

| Enum | Values |
|---|---|
| `hardware_category` | GPU, CPU, Networking, Accelerator |
| `company_type` | fab, idm, cloud, vendor, research |
| `datacenter_status` | planned, active, retired |
| `note_status` | draft, review, published |
| `entity_type` | hardware_product, company, datacenter |
| `metric_frequency` | daily, weekly, monthly |
| `source_type` | rss, json, file |
| `ingestion_status` | ingested, skipped, error |
| `run_status` | running, success, partial, error |

### Backend Layer Responsibilities

| Layer | Responsibility |
|---|---|
| `routes/` | HTTP binding, request/response serialisation, RBAC dependency injection |
| `services/` | Business logic, conflict validation, cache read/write/invalidation |
| `repositories/` | DB queries, pagination, filtering — no business logic |
| `models/` | SQLAlchemy table definitions + relationships |
| `schemas/` | Pydantic v2 DTOs (Create / Update / Response) |

## Repo Structure

```
/
├── apps/
│   ├── api/            FastAPI backend (Python 3.11+, src layout)
│   │   ├── src/api/    Application package
│   │   ├── alembic/    Database migrations
│   │   ├── tests/      Pytest tests
│   │   └── scripts/    One-off scripts (seed, etc.)
│   └── web/            Vite + React + TypeScript frontend
│       └── src/
│           ├── components/   Shared UI components
│           ├── routes/       Page-level route components
│           ├── lib/          Clients, query client, schemas
│           └── test/         Test setup + unit tests
├── infra/              Docker Compose definitions
├── packages/
│   └── shared/         Cross-cutting shared code (placeholder)
└── docs/               Architecture and ADRs
```

## Key Conventions

| Layer | Convention |
|---|---|
| API routes | `/api/v1/<resource>` |
| DB migrations | Alembic autogenerate; one migration per PR |
| Settings | All config via environment variables (Pydantic Settings) |
| Logging | Structured JSON; include `request_id` on every line |
| Frontend data fetching | TanStack Query; no manual `fetch` outside `lib/` |
| Validation | Zod on frontend, Pydantic on backend |

## Ingestion Pipeline (Slice 5)

```
data/ingest/*.json
        │
        ▼
  Celery Worker / make ingest
        │
        ▼
  IngestionService.execute_run()
        ├── _load_from_files()       read *.json from INGEST_DIR
        ├── _compute_hash()          sha256 idempotency key
        ├── repo.get_by_hash()       skip duplicates
        ├── SourceDocument insert
        ├── EntityExtractor.extract() case-insensitive name match vs DB
        └── SourceEntityLink inserts
```

**Idempotency:** `sha256(title|url|published_at|raw_text[:500])` — re-running always skips already-ingested documents.

**Entity extraction:** Loads all HardwareProduct/Company/DatacenterSite names from the DB at extraction time and matches them case-insensitively against `title + raw_text`.

**Workers:**
- `worker` — Celery worker, handles `run_ingestion_task` jobs
- `scheduler` — Celery Beat, triggers periodic ingestion on `INGESTION_INTERVAL_MIN` schedule

## Search Architecture (Slice 6)

```
GET /api/v1/search?q=...
        │
        ▼
  SearchService (services/search.py)
        ├── cache lookup — "search:<md5(q+type+filters+role+pagination)>"
        ├── search_notes()    — to_tsvector('english', title||body) @@ websearch_to_tsquery
        ├── search_sources()  — to_tsvector('english', title||raw_text) @@ websearch_to_tsquery
        ├── ts_rank + ts_headline per result
        ├── merge + sort by score (type=all)
        └── cache set (60s)
```

**GIN Indexes** (migration f5a6b7c8d9e0):
- `ix_research_notes_fts` on `to_tsvector('english', title || body_markdown)`
- `ix_source_documents_fts` on `to_tsvector('english', title || raw_text)`

**Cache invalidation:** `search:*` is invalidated on note create/update/delete/publish and after every successful ingestion run.

## User Invite Flow (Slice 7)

```
Admin
  │
  ├── POST /api/v1/users/invite  (admin only)
  │     ├── validate email not already registered
  │     ├── generate secrets.token_urlsafe(32)
  │     ├── store sha256(token) → user_invites.token_hash
  │     └── return { invite_url: FRONTEND_BASE_URL/accept-invite?token=<raw> }
  │
  └── Invitee visits /accept-invite?token=<raw>
        ├── POST /api/v1/users/accept-invite
        │     ├── sha256(raw) → lookup user_invites by token_hash
        │     ├── validate not used, not expired
        │     ├── create User with invite.role
        │     └── mark invite.used_at = now()
        └── redirect → /login
```

**UserInvite model** (`user_invites` table, migration `g6b7c8d9e0f1`):
```
UserInvite
  id, email, role, token_hash (UNIQUE), expires_at, used_at, created_at
  created_by_user_id FK → users (SET NULL)
```

## Security Headers (Slice 7)

`SecurityHeadersMiddleware` (pure ASGI, `middleware.py`) injects on every response:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

CORS origins are configurable via `CORS_ORIGINS` env var (comma-separated).

## CI / Tooling (Slice 7)

- **Pre-commit:** `.pre-commit-config.yaml` — ruff lint+format, ESLint, Prettier, trailing-whitespace
- **GitHub Actions:** `.github/workflows/ci.yml` — backend (postgres service + ruff + pytest), frontend (ESLint + Vitest), e2e (Playwright against docker-compose stack)
- **Playwright:** `apps/web/e2e/happy-path.spec.ts` — login, dashboard, search, admin user management, RBAC, accept-invite

## Completed Slices

1. **Slice 1 — Auth**: JWT-based login, protected routes, user model ✓
2. **Slice 2 — Core domain entities**: HardwareProduct, Company, DatacenterSite, CRUD APIs, list/detail UI ✓
3. **Slice 3 — Research Notes + Markdown Editor + Entity Linking + Publish Workflow** ✓
4. **Slice 4 — MetricsSeries + MetricPoints + Dashboard Aggregates + Charts** ✓
5. **Slice 5 — Ingestion Pipeline**: SourceDocument + SourceEntityLink + IngestionRun + Celery workers + Sources UI ✓
6. **Slice 6 — Unified Search**: PostgreSQL FTS + GIN indexes + search endpoint + search UI ✓
7. **Slice 7 — Admin User Management + Security + CI**: Invite flow, RBAC, security headers, pre-commit, GitHub Actions, Playwright e2e ✓
