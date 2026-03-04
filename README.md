# AI Infrastructure Research Dashboard

A monorepo for researching and visualising AI infrastructure data.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Compose v2)
- [Make](https://www.gnu.org/software/make/) (`choco install make` on Windows / `brew install make` on macOS)

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd ai-infra-research-dashboard

# 2. Copy env file and edit as needed
cp .env.example .env

# 3. Start everything
make dev
```

| URL | Service |
|---|---|
| http://localhost:5173 | Frontend (React) |
| http://localhost:8000/docs | Backend API (Swagger UI) |
| http://localhost:8000/healthz | Health check |

> `make lint`, `make test`, and `make migrate` require the stack to be running (`make dev` in another terminal).

## Commands

| Command | Description |
|---|---|
| `make dev` | Build and start all services |
| `make down` | Stop all services |
| `make logs` | Tail logs from all services |
| `make lint` | Run ruff (backend) + ESLint (frontend) |
| `make format` | Run ruff formatter + Prettier |
| `make test` | Run pytest (backend) + Vitest (frontend) |
| `make migrate` | Apply pending Alembic migrations |
| `make makemigrations MSG="description"` | Create a new Alembic revision |
| `make seed` | Run the database seed script |

## Running Migrations

```bash
# Apply all pending migrations
make migrate

# After adding a SQLAlchemy model, autogenerate a new migration
make makemigrations MSG="add user table"
```

## Where to Put Future Modules

| Concern | Location |
|---|---|
| New API domain (e.g. papers) | `apps/api/src/api/routes/papers.py` + model in `src/api/models/` |
| New frontend page | `apps/web/src/routes/` + register in `App.tsx` |
| Shared types | `packages/shared/` |
| Infrastructure changes | `infra/docker-compose.yml` |
| Architecture decisions | `docs/` |

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for layering, conventions, and future slices.
