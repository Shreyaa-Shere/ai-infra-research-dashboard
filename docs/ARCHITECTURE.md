# Architecture

## Overview

This is a monorepo for the **AI Infrastructure Research Dashboard** — a web application for researching and visualising AI infrastructure data.

## Layering

```
Browser (apps/web)
    │  HTTP / REST
    ▼
FastAPI (apps/api)          ← stateless, async
    ├── Routes (src/api/routes/)
    ├── Services / use-cases  ← to be added in feature slices
    ├── SQLAlchemy models     ← to be added per domain
    └── DB / Redis adapters
         │
         ├── PostgreSQL      ← primary data store
         └── Redis           ← caching / pub-sub (future)
```

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

1. **Slice 1 — Auth**: JWT-based login, protected routes, user model
2. **Slice 2 — Research entities**: Papers, datasets, infrastructure records
3. **Slice 3 — Search & filter**: Full-text search via PostgreSQL / Typesense
4. **Slice 4 — Visualisations**: Chart components backed by aggregation endpoints
