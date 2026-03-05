# Unified Search (Slice 6)

## Overview

The unified search feature provides full-text search across two content types:

- **ResearchNotes** — authored markdown research documents
- **SourceDocuments** — ingested news articles and external content

Results are ranked by relevance using PostgreSQL's `ts_rank` and returned with highlighted snippets.

## Architecture

```
GET /api/v1/search?q=...
        │
        ▼
  SearchService
        ├── cache lookup (Redis, 60s TTL, keyed by q + filters + role)
        ├── search_notes()    ── to_tsvector @@ websearch_to_tsquery
        ├── search_sources()  ── to_tsvector @@ websearch_to_tsquery
        ├── merge + sort by ts_rank (for type=all)
        └── cache set
```

## API

### `GET /api/v1/search`

**Auth:** Required (any authenticated user)

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string (1–300 chars) | required | Search query (uses `websearch_to_tsquery`) |
| `type` | `all` \| `note` \| `source` | `all` | Result type filter |
| `limit` | int (1–100) | 20 | Page size |
| `offset` | int ≥ 0 | 0 | Pagination offset |
| `tags` | string[] | — | Filter notes by tag (repeat for multiple) |
| `status` | string | — | Filter notes by status (`draft`, `review`, `published`) |
| `entity_type` | string | — | Filter by linked entity type (`hardware_product`, `company`, `datacenter`) |
| `entity_id` | UUID | — | Filter by linked entity ID |
| `start` | ISO 8601 datetime | — | Filter by created_at ≥ start |
| `end` | ISO 8601 datetime | — | Filter by created_at ≤ end |
| `source_type` | string | — | Filter sources by type (`rss`, `json`, `file`) |

**Response:**

```json
{
  "items": [
    {
      "type": "note",
      "id": "uuid",
      "title": "H100 Training Cluster Analysis",
      "snippet": "Deep dive into <mark>H100</mark> GPU clusters.",
      "score": 0.0759,
      "status": "published",
      "tags": ["gpu"],
      "author_id": "uuid",
      "slug": "h100-analysis-a1b2c3d4",
      "published_at": "2024-01-15T10:00:00Z",
      "created_at": "2024-01-10T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    },
    {
      "type": "source",
      "id": "uuid",
      "title": "NVIDIA H100 Deployment Surge",
      "snippet": "<mark>H100</mark> GPUs deployed across Azure datacenters.",
      "score": 0.0607,
      "url": "https://example.com/h100",
      "source_name": "AI Hardware Weekly",
      "source_type": "file",
      "status": "ingested",
      "published_at": "2024-01-20T10:00:00Z",
      "created_at": "2024-01-20T10:00:00Z"
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0,
  "query": "H100"
}
```

## RBAC

| Role | Visible Notes | Visible Sources |
|---|---|---|
| viewer | Published only | All ingested |
| analyst | Own (any status) + published | All ingested |
| admin | All | All ingested |

## Indexing

Two GIN indexes are created by the migration `f5a6b7c8d9e0`:

```sql
CREATE INDEX ix_research_notes_fts ON research_notes USING GIN
  (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body_markdown,'')));

CREATE INDEX ix_source_documents_fts ON source_documents USING GIN
  (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(raw_text,'')));
```

These expression indexes are used automatically by PostgreSQL when the `@@` operator is applied against `websearch_to_tsquery`.

## Cache Invalidation

Search results (60s TTL) are invalidated when:
- A research note is created, updated, published, or deleted → `search:*` pattern deleted
- An ingestion run completes (new source documents added) → `search:*` pattern deleted

## Frontend

The search page (`/search`) provides:

- **Search input** — debounced 400ms, syncs with URL `?q=` param
- **Type tabs** — All / Notes / Sources with result count in active tab
- **Filter panel** — collapsible, shows status filter (Note Status) and source_type filter; viewers only see the `published` status option
- **Result cards** — note cards link to `/notes/:id`, source cards link to `/sources/:id`
- **Snippet rendering** — `dangerouslySetInnerHTML` renders `<mark>` tags from `ts_headline`
- **Pagination** — previous/next buttons when total > limit

## Query Syntax

The `q` parameter is passed to `websearch_to_tsquery('english', ...)` which supports:

| Syntax | Meaning |
|---|---|
| `H100 GPU` | Both words (default AND) |
| `"H100 GPU"` | Exact phrase |
| `H100 OR A100` | Either word |
| `-H100` | Exclude H100 |
| `H100 -training` | H100 without training |
