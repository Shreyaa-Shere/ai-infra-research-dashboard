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
