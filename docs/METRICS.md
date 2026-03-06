# Metrics System (Slice 4)

## Overview

The Metrics system lets analysts track time-series data for any linked entity (hardware products, companies, datacenter sites). The dashboard aggregates all metric series into KPI cards and interactive charts.

---

## Data Model

### `MetricSeries`

Defines a named time-series for a specific entity.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `name` | String(256) | e.g. "H100 Shipment Volume" |
| `entity_type` | Enum | `hardware_product \| company \| datacenter` |
| `entity_id` | UUID | FK (app-level, no hard constraint) |
| `unit` | String(64) | e.g. "units", "MW", "USD billions" |
| `frequency` | Enum | `daily \| weekly \| monthly` |
| `source` | String(256)? | Optional data source description |
| `created_at` / `updated_at` | DateTime TZ | |

**Unique constraint:** `(name, entity_type, entity_id, unit, frequency)`

### `MetricPoint`

A single measurement for a `MetricSeries`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `metric_series_id` | UUID FK → `metric_series(id)` CASCADE | |
| `timestamp` | DateTime TZ | Measurement instant |
| `value` | Float | |

**Unique constraint:** `(metric_series_id, timestamp)` — enables idempotent upsert

---

## API Endpoints

### Metric Series

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/metric-series` | any | List all series (paginated) |
| `POST` | `/api/v1/metric-series` | analyst+ | Create a new series |
| `GET` | `/api/v1/metric-series/{id}` | any | Get series by ID |
| `PATCH` | `/api/v1/metric-series/{id}` | analyst+ | Update series metadata |
| `DELETE` | `/api/v1/metric-series/{id}` | admin | Delete series + all points |

### Metric Points

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/metric-series/{id}/points` | analyst+ | Bulk upsert points (idempotent) |
| `GET` | `/api/v1/metric-series/{id}/points` | any | List points (date range + limit) |
| `GET` | `/api/v1/metric-series/{id}/export.csv` | any | Download points as CSV |

### Overview / Dashboard

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/metrics/overview` | any | KPI cards + chart data |

---

## Bulk Upsert

`POST /metric-series/{id}/points` accepts up to 5000 points per request and uses PostgreSQL `INSERT ... ON CONFLICT (metric_series_id, timestamp) DO UPDATE SET value = excluded.value`. This makes re-sending the same data fully idempotent — re-running a seed script or backfill will not create duplicates.

---

## Caching Strategy

All endpoints use Redis with the following TTLs:

| Cache key | TTL |
|-----------|-----|
| `metric:series:list:*` | 60 s |
| `metric:series:detail:{id}` | 60 s |
| `metric:points:{id}:*` | 60 s |
| `metric:overview` | 60 s |

Cache is invalidated pattern-wide after any write (create / update / delete / upsert).

---

## Dashboard

The `/dashboard` route shows:

1. **KPI Cards** — entity counts (hardware, companies, datacenters, published notes, metric series) plus the latest value of the first available series.
2. **Metric Trend Charts** — one chart per metric series, showing the last 18 data points. DC/power series render as BarCharts; all others render as LineCharts.

Charts are built with [Recharts](https://recharts.org).

---

## Seed Data

Running `docker compose -f infra/docker-compose.yml exec api python scripts/seed.py` creates 4 metric series with 18 monthly points each (2024-01 → 2025-06):

| Series | Entity | Unit |
|--------|--------|------|
| H100 Shipment Volume | H100 GPU | units (thousands) |
| NVIDIA Revenue | NVIDIA | USD billions |
| US West DC Power Usage | US West GPU Cluster | MW |
| EU AI DC Power Usage | EU AI Datacenter | MW |
