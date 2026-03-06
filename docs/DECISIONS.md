# Architecture Decision Records

## ADR-001 — Invite token hashing

**Date:** 2026-03-05
**Status:** Accepted

### Context

Admin users need to invite colleagues via a one-time link. The link contains a secret token. If the `user_invites` table were ever compromised, raw tokens must not be recoverable.

### Decision

Store only the **SHA-256 hex digest** of the token in the database (`token_hash VARCHAR(64)`). The raw token is generated with `secrets.token_urlsafe(32)` (256 bits of entropy), returned once in the API response, and immediately embedded in the invite URL returned to the admin. It is never persisted.

Lookup at accept-time: `sha256(raw_token)` → query by `token_hash`.

### Consequences

- Token cannot be recovered from the DB if the `user_invites` table leaks.
- If an admin loses the invite URL, they must create a new invite (old one can be left to expire naturally after `INVITE_TOKEN_TTL_DAYS`).
- Same pattern already used for `refresh_tokens`, so no new infrastructure needed.

---

## ADR-002 — Email delivery via stdlib SMTP with console fallback

**Date:** 2026-03-05
**Status:** Accepted

### Context

The invite and password-reset flows need to deliver URLs to users. Integrating a transactional email provider (SendGrid, SES, Resend) adds external dependencies and secrets management complexity.

### Decision

Use Python's stdlib `smtplib` (no new dependencies) wrapped in `asyncio.run_in_executor` so it does not block the async event loop. An `EmailService` singleton (`services/email.py`) handles both invite and password-reset emails.

**Console/log fallback:** When `SMTP_HOST` is empty (default in `.env.example`), the email body and URL are printed to the API container logs instead of sent. This makes local development zero-config.

**Configuration:** Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TLS` in `.env` to enable real delivery.

### Consequences

- No external dependencies added — stdlib only.
- Works in dev with zero config (console mode).
- Invite URL is also returned in the `POST /api/v1/users/invite` API response as a fallback, so admins can still copy and share it manually if SMTP is not configured.
- For high-volume production use, replace `EmailService._send_sync` with an API-based provider (Resend, SES) — the `send_invite` / `send_password_reset` interface stays the same.

---

## ADR-003 — Refresh token storage (httpOnly cookie plan)

**Date:** 2026-03-05
**Status:** Partially implemented

### Context

Refresh tokens stored in `localStorage` are accessible to JavaScript and therefore vulnerable to XSS attacks. The current implementation stores the refresh token in `localStorage` (key `rft`) for simplicity during local development.

### Decision

The production-safe approach is to store the refresh token in an **httpOnly, Secure, SameSite=Strict cookie** set by the API server. The frontend would then call `/api/v1/auth/refresh` with no body — the browser sends the cookie automatically.

### Current state

`localStorage` is used in `apps/web/src/store/AuthContext.tsx`. A comment (`// Production note: move refresh_token to an httpOnly cookie`) marks the upgrade point.

### Upgrade path

1. `POST /api/v1/auth/login` — set `Set-Cookie: rft=<token>; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh`
2. `POST /api/v1/auth/refresh` — read cookie server-side instead of request body
3. `POST /api/v1/auth/logout` — clear the cookie
4. Remove `localStorage` usage from `AuthContext`

No schema or token-hashing changes required.

---

## ADR-004 — PostgreSQL FTS over external search engine

**Date:** 2026-03-05
**Status:** Accepted

### Context

Slice 6 required full-text search across ResearchNotes and SourceDocuments.

### Decision

Use **PostgreSQL native FTS** (`to_tsvector` + `websearch_to_tsquery` + GIN expression indexes) rather than an external engine (Elasticsearch, Typesense, Meilisearch).

### Rationale

- No additional service to operate or provision.
- `websearch_to_tsquery` supports natural-language queries (AND, OR, phrase, negation) out of the box.
- GIN expression indexes provide sub-millisecond lookups for the expected data volumes (<100k documents).
- `ts_headline` gives highlighted snippets without extra processing.

### Consequences

- Search quality is good but not semantic — no vector similarity or typo tolerance.
- At >1M documents, a dedicated engine would be warranted; migration path is straightforward (replace `SearchRepository` only).

---

## ADR-005 — Security headers via pure ASGI middleware

**Date:** 2026-03-05
**Status:** Accepted

### Context

`X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` headers should be added to every HTTP response.

### Decision

Implemented as a **pure ASGI middleware** (`SecurityHeadersMiddleware` in `middleware.py`), following the same pattern as `RequestIdMiddleware`. This avoids the known task-cancellation bugs in Starlette's `BaseHTTPMiddleware`.

### Headers set

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

---

## ADR-006 — Invite role restriction (no admin invites)

**Date:** 2026-03-05
**Status:** Accepted

### Context

Admins can invite new users with `analyst` or `viewer` roles. The question was whether admins should be able to invite other admins via the invite flow.

### Decision

**Admin role is excluded** from the invite flow. `UserInviteCreate` has a Pydantic validator that raises a 422 if `role == "admin"`. Admin accounts must be created directly via `docker compose -f infra/docker-compose.yml exec api python scripts/seed.py` or a direct DB insert.

### Rationale

- Limits the blast radius if an admin account is compromised — it cannot self-propagate admin access.
- Keeps admin account creation as a deliberate, out-of-band operation.
