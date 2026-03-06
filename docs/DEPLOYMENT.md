# Deployment Notes

This document covers what you need to know before deploying the AI Infra Research Dashboard to a production environment.

## Prerequisites

- Docker Engine 24+ with Compose v2 (`docker compose`)
- A managed PostgreSQL instance (or self-hosted) — minimum Postgres 14
- A Redis instance (managed or self-hosted) — minimum Redis 6
- An SMTP relay for invite emails (optional — invite URLs are also returned in the API response)

## Environment Variables

Copy `.env.example` to `.env` and edit every value marked below.

| Variable | Required | Notes |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | yes | Used by the `postgres` Docker container only |
| `DATABASE_URL` | yes | Full asyncpg connection string — update host/port/user/pass |
| `REDIS_URL` | yes | Update host to your Redis endpoint |
| `JWT_SECRET` | **yes** | Generate with `openssl rand -hex 32`; never commit to git |
| `JWT_ACCESS_TTL_MIN` | yes | 15 minutes is fine for production |
| `JWT_REFRESH_TTL_DAYS` | yes | 7 days is a reasonable default |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | yes | Initial admin; change immediately after first login |
| `BCRYPT_ROUNDS` | recommended | Set to 12+ in production (default); 4 only for local dev speed |
| `CORS_ORIGINS` | yes | Comma-separated list of your frontend origins, e.g. `https://app.example.com` |
| `FRONTEND_BASE_URL` | yes | Used to construct invite URLs, e.g. `https://app.example.com` |
| `ENVIRONMENT` | yes | Set to `production` — controls log format and `/system/info` output |
| `LOG_LEVEL` | recommended | `INFO` for production; `DEBUG` for troubleshooting |
| `VITE_API_URL` | yes | Build-time variable — set to your API URL, e.g. `https://api.example.com` |

## Building for Production

```bash
# Build the API image
docker build -f apps/api/Dockerfile -t ai-infra-api:latest .

# Build the frontend (static files)
cd apps/web
VITE_API_URL=https://api.example.com npm run build
# Output: apps/web/dist/ — serve with nginx or any static host
```

## Docker Compose in Production

The provided `docker-compose.yml` is intended for local development. For production:

1. Remove the `postgres` and `redis` services — use managed infrastructure.
2. Remove volume mounts that expose source code (`./apps/api:/app`).
3. Set `restart: always` on `api`, `worker`, and `scheduler` services.
4. Add health checks.
5. Run behind a reverse proxy (nginx, Caddy, or a load balancer) with TLS termination.

Minimal production compose override:

```yaml
# docker-compose.prod.yml
services:
  api:
    image: ai-infra-api:latest
    restart: always
    environment:
      - ENVIRONMENT=production
    # no volume mounts

  worker:
    image: ai-infra-api:latest
    restart: always
    command: celery -A api.workers.celery_app worker --loglevel=info

  scheduler:
    image: ai-infra-api:latest
    restart: always
    command: celery -A api.workers.celery_app beat --loglevel=info
```

Run with: `docker compose -f infra/docker-compose.yml -f docker-compose.prod.yml up -d`

## Database Migrations

Always run migrations before starting the API in production:

```bash
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

In a CI/CD pipeline, run migrations as a separate step before deploying the new image.

## First Run

```bash
# 1. Run migrations
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

# 2. Create the admin user and seed sample data (idempotent)
docker compose -f infra/docker-compose.yml exec api python scripts/seed.py
```

## Security Checklist

- [ ] `JWT_SECRET` is at least 32 random bytes, not committed to git
- [ ] `ADMIN_PASSWORD` is changed from the default
- [ ] `CORS_ORIGINS` only lists your frontend origin(s)
- [ ] TLS is terminated at the load balancer / reverse proxy
- [ ] PostgreSQL is not exposed to the public internet
- [ ] Redis is not exposed to the public internet (use AUTH or a private network)
- [ ] `BCRYPT_ROUNDS` is 12 or higher
- [ ] `ENVIRONMENT=production` is set

## Health Check

```
GET /healthz
```

Returns `{"status": "ok"}` if the API process is running. Use this for load balancer health checks.

## System Info (Admin Only)

```
GET /api/v1/system/info
Authorization: Bearer <admin-token>
```

Returns version, environment, uptime, and live DB + Redis connectivity status. Useful for verifying a new deployment.

## Logging

Logs are written to stdout in JSON format when `ENVIRONMENT=production`. Ship them to your log aggregator (Datadog, CloudWatch, Loki, etc.).

Each request carries an `X-Request-Id` header (UUID). This ID appears in all log lines for that request, making cross-service tracing straightforward.

## Scaling

- **API**: Stateless — scale horizontally behind a load balancer.
- **Worker**: Scale Celery workers independently; they consume from the same Redis queue.
- **Scheduler**: Run exactly one instance to avoid duplicate periodic tasks.
- **Frontend**: Static files — serve from a CDN.
