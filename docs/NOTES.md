# Research Notes — Slice 3

## Status Workflow

```
draft → review → published
```

| Status      | Who can set it                       | Description                            |
|-------------|--------------------------------------|----------------------------------------|
| `draft`     | author (analyst/admin) on create     | Work in progress, not visible to others|
| `review`    | author (via PATCH `status=review`)   | Ready for peer review                  |
| `published` | author or admin (POST `/publish`)    | Publicly readable, immutable           |

Rules:
- Status can only move forward (`draft → review`, `review/draft → published`).
- Published notes cannot be moved back to draft or review.
- Publishing sets `published_at` and generates a `slug` (if not already set).

## Slug Generation

Slug is generated on publish from `title` + first 8 chars of the note UUID:

```python
slug = f"{slugified_title}-{uid[:8]}"
# e.g. "h100-supply-chain-analysis-a1b2c3d4"
```

Slugs are unique. If a conflict occurs (very rare), the UUID prefix ensures uniqueness.

## Linking Model

`NoteEntityLink` is a junction table connecting a note to entities across three domain tables:

| `entity_type`      | References table        |
|--------------------|-------------------------|
| `hardware_product` | `hardware_products`     |
| `company`          | `companies`             |
| `datacenter`       | `datacenter_sites`      |

Entity validation is performed at the application layer (service checks the entity exists before saving a link). A unique constraint `(note_id, entity_type, entity_id)` prevents duplicate links.

Links can be replaced atomically via `PUT /api/v1/notes/{id}/links`.

## Caching Strategy

| Endpoint                      | Cache key                                     | TTL   |
|-------------------------------|-----------------------------------------------|-------|
| `GET /api/v1/notes`           | `note:list:{role}:{limit}:{offset}:{filters}` | 60s   |
| `GET /api/v1/notes/{id}`      | `note:detail:{id}`                            | 60s   |
| `GET /api/v1/published/{slug}`| `note:pub:{slug}`                             | 300s  |

Cache is invalidated on create, update, delete, and publish using `cache_delete_pattern`.

The list cache key includes the user's **role** because different roles see different subsets of notes (viewer → published only; analyst → own + published; admin → all).

## RBAC Summary

| Action              | Viewer | Analyst (own notes) | Analyst (others) | Admin |
|---------------------|--------|---------------------|------------------|-------|
| List notes          | ✅ (published only) | ✅ | ✅ (published) | ✅ |
| Get note detail     | ✅ (published only) | ✅ | ✅ (published) | ✅ |
| Create note         | ❌     | ✅                  | —                | ✅    |
| Update note         | ❌     | ✅                  | ❌               | ✅    |
| Delete note         | ❌     | ✅                  | ❌               | ✅    |
| Publish note        | ❌     | ✅                  | ❌               | ✅    |
| Read published page | ✅ (no auth) | ✅           | ✅               | ✅    |

## Audit Logging

All note mutations are recorded in the `audit_logs` table:

| Action           | Triggered by         |
|------------------|----------------------|
| `note.created`   | POST /notes          |
| `note.updated`   | PATCH /notes/{id}    |
| `note.published` | POST /notes/{id}/publish |
| `note.deleted`   | DELETE /notes/{id}   |

Audit logs are accessible to admins via `GET /api/v1/audit`.
