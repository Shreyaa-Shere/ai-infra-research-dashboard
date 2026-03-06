# Ingestion Pipeline

## Overview

The ingestion pipeline reads structured JSON files from `./data/ingest/`, extracts entities using rules-based name matching against the database, and stores deduplication-safe `SourceDocument` records with linked entity references.

Background processing is handled by **Celery** (worker) and **Celery Beat** (scheduler) using Redis as the message broker.

---

## Architecture

```
POST /api/v1/ingestion/run
        │
        ▼
  IngestionService.trigger_run()
        │  creates IngestionRun (status=running)
        │  enqueues run_ingestion_task.delay(run_id)
        │
        ▼
  Celery Worker: run_ingestion_task
        │  calls IngestionService.execute_run(run_id)
        │
        ▼
  _load_from_files()          ← reads *.json from INGEST_DIR
        │
        ▼
  _process_item() per doc
    ├── _compute_hash()       ← sha256(title|url|published_at|text[:500])
    ├── repo.get_by_hash()    ← skip if already ingested (idempotent)
    ├── create SourceDocument
    ├── EntityExtractor.extract()  ← case-insensitive name match vs DB
    └── create SourceEntityLink rows
        │
        ▼
  repo.finish_run()           ← update status, store stats JSON
```

**Periodic ingestion:** Celery Beat triggers `periodic_ingestion_task` every `INGESTION_INTERVAL_MIN` minutes (default: 60). It creates a new `IngestionRun` and calls `execute_run` directly.

---

## Models

### `SourceDocument`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `content_hash` | VARCHAR(64) UNIQUE | sha256 idempotency key |
| `title` | TEXT | |
| `url` | TEXT nullable | |
| `source_name` | TEXT | e.g. `local-ingest`, `techcrunch-rss` |
| `source_type` | ENUM | `file \| rss \| json` |
| `published_at` | TIMESTAMP nullable | |
| `raw_text` | TEXT nullable | |
| `extracted_entities` | JSONB nullable | `{hardware_products: [...], companies: [...], datacenters: [...]}` |
| `status` | ENUM | `ingested \| skipped \| error` |
| `created_at` | TIMESTAMP | |

### `SourceEntityLink`

Polymorphic entity reference reusing the existing `entity_type` enum.

| Column | Type |
|---|---|
| `id` | UUID PK |
| `source_document_id` | UUID FK → source_documents |
| `entity_type` | ENUM (`hardware_product \| company \| datacenter`) |
| `entity_id` | UUID |
| `entity_name` | TEXT |

### `IngestionRun`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `source_type` | ENUM | |
| `source_name` | TEXT | |
| `status` | ENUM | `running \| success \| partial \| error` |
| `dry_run` | BOOLEAN | No DB writes if true |
| `started_at` | TIMESTAMP | |
| `finished_at` | TIMESTAMP nullable | |
| `stats_json` | JSONB nullable | `{ingested, skipped, errors, total}` |
| `triggered_by` | UUID FK → users SET NULL | |

---

## Idempotency

Every document is hashed:

```python
sha256(
    normalize(title)
    + "|" + normalize(url or "")
    + "|" + (published_at.isoformat() if published_at else "")
    + "|" + raw_text[:500]
)
```

If a document with the same `content_hash` already exists, it is counted as `skipped` and not re-inserted. This makes all ingestion runs safe to re-run.

---

## Entity Extraction

`EntityExtractor.extract(session, title, raw_text)` performs case-insensitive substring matching against all entity names loaded from the database at extraction time:

- `HardwareProduct.name` → `hardware_products`
- `Company.name` → `companies`
- `DatacenterSite.name` → `datacenters`

Results are stored in `SourceDocument.extracted_entities` (JSONB) and as individual `SourceEntityLink` rows for relational querying.

---

## REST API

### Trigger a run

```
POST /api/v1/ingestion/run
Authorization: Bearer <analyst_or_admin_token>
Content-Type: application/json

{
  "source_type": "file",
  "source_name": "local-ingest",
  "dry_run": false
}
```

Response `202`:
```json
{
  "run_id": "uuid",
  "status": "running",
  "message": "Ingestion run queued"
}
```

### List runs

```
GET /api/v1/ingestion/runs?limit=20&offset=0
Authorization: Bearer <analyst_or_admin_token>
```

### Get run

```
GET /api/v1/ingestion/runs/{id}
```

### List sources

```
GET /api/v1/sources?source_type=file&q=h100&limit=20&offset=0
Authorization: Bearer <any_authenticated_token>
```

### Get source detail

```
GET /api/v1/sources/{id}
```

---

## Sample Data

Three sample files are included in `data/ingest/`:

| File | Articles |
|---|---|
| `sample1.json` | NVIDIA H100, Google TPU v5, AMD MI300X |
| `sample2.json` | Meta Louisiana DC, Intel Gaudi 3, AWS Trainium 2 |
| `sample3.json` | NVIDIA Blackwell B200, EU datacenter expansion, Qualcomm Cloud AI 100 Ultra |

---

## Running Ingestion

### Via command line (one-shot, no Celery needed)

```bash
docker compose -f infra/docker-compose.yml exec api python -c \
  "import asyncio; from api.workers.tasks import _async_periodic_run; asyncio.run(_async_periodic_run())"
```

### Via API (queues async Celery task)

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"source_type": "file", "source_name": "local-ingest"}'
```

### Adding new ingest files

1. Create a JSON file in `data/ingest/` with the schema:
   ```json
   [
     {
       "title": "Article Title",
       "url": "https://example.com/article",
       "source_name": "my-source",
       "published_at": "2024-01-15T10:00:00Z",
       "raw_text": "Full article text..."
     }
   ]
   ```
2. Run the ingestion command above or trigger via the API.
   Already-ingested documents (by content hash) are automatically skipped.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `INGESTION_SOURCE_TYPE` | `file` | Source type for periodic ingestion |
| `INGESTION_SOURCE_NAME` | `local-ingest` | Source name label |
| `INGESTION_INTERVAL_MIN` | `60` | Beat schedule interval in minutes |
| `INGEST_DIR` | `/app/data/ingest` | Directory path inside the container |
