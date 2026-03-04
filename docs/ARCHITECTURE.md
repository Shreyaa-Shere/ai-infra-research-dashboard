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

## Domain Entity Relationships (Slice 2 + 3)

```
User
  │ id, email, hashed_password, role, is_active
  │
  └──< ResearchNote            (author_id FK → User, CASCADE)
         │ id, title, body_markdown, status, slug, tags[], published_at
         │
         └──< NoteEntityLink   (note_id FK → ResearchNote, CASCADE)
                id, entity_type, entity_id  ← polymorphic ref (app-level FK)

AuditLog                       (actor_user_id FK → User, SET NULL)
  id, action, entity_type, entity_id, meta_json

Company
  │ id, name (unique), type, region, website
  │
  └──< DatacenterSite          (owner_company_id FK → Company, SET NULL)
         id, name, region, power_mw, status

HardwareProduct                (standalone, no FK)
  id, name, vendor, category, release_date, memory_gb, tdp_watts, process_node
```

### Enums

| Enum | Values |
|---|---|
| `hardware_category` | GPU, CPU, Networking, Accelerator |
| `company_type` | fab, idm, cloud, vendor, research |
| `datacenter_status` | planned, active, retired |
| `note_status` | draft, review, published |
| `entity_type` | hardware_product, company, datacenter |

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

## Future Slices

1. **Slice 1 — Auth**: JWT-based login, protected routes, user model ✓
2. **Slice 2 — Core domain entities**: HardwareProduct, Company, DatacenterSite, CRUD APIs, list/detail UI ✓
3. **Slice 3 — Research Notes + Markdown Editor + Entity Linking + Publish Workflow** ✓
4. **Slice 4 — MetricsSeries + MetricPoints + Dashboard Aggregates + Charts**
5. **Slice 5 — Full-text Search + Advanced Filters**
