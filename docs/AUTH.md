# Authentication & Token Strategy

## Overview

The API uses a **JWT access + rotating refresh token** scheme.

| Token | TTL | Storage | Transport |
|---|---|---|---|
| Access token | 15 min (configurable) | In-memory (frontend) | `Authorization: Bearer <token>` |
| Refresh token | 7 days (configurable) | localStorage (dev) / httpOnly cookie (prod) | Request body |

## Token Lifecycle

```
POST /api/v1/auth/login
  → issues: access_token (JWT) + refresh_token (opaque)

  access_token expires after JWT_ACCESS_TTL_MIN
     ↓
POST /api/v1/auth/refresh  { refresh_token }
  → revokes old refresh token
  → issues: new access_token + new refresh_token  (rotation)

POST /api/v1/auth/logout  { refresh_token }  (+ Bearer access_token)
  → revokes refresh token immediately
```

## Refresh Token Security

- The **raw token** is never stored in the database.
- On issuance: `sha256(raw_token)` is stored in `refresh_tokens.token_hash`.
- On validation: the provided token is hashed and compared.
- On rotate / logout: `revoked_at` is set (soft revoke — row kept for audit).

## RBAC

Roles: `admin` | `analyst` | `viewer`

Use the `require_role` dependency in route handlers:

```python
from api.auth.dependencies import require_role

@router.get("/admin-only")
async def admin_only(user: User = Depends(require_role(["admin"]))):
    ...
```

## Rate Limiting

`POST /api/v1/auth/login` is limited to **10 requests / minute per IP** via `slowapi`.
Exceeding the limit returns HTTP 429.

## Security Considerations

### Production checklist
- [ ] Set `JWT_SECRET` to a strong random value (`openssl rand -hex 32`)
- [ ] Move refresh token from `localStorage` to `httpOnly` cookie (requires backend `/refresh` endpoint to read cookie, and CORS + `credentials: include` on frontend)
- [ ] Enable HTTPS — JWTs in `Authorization` headers are safe only over TLS
- [ ] Set short `JWT_ACCESS_TTL_MIN` (15 min default is reasonable)
- [ ] Add refresh token absolute expiry + sliding window rotation
- [ ] Consider adding `jti` claim to access tokens for revocation support

## Endpoints

| Method | Path | Auth required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/login` | No | Exchange credentials for tokens |
| POST | `/api/v1/auth/refresh` | No (refresh token) | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Bearer access token | Revoke refresh token |
| GET | `/api/v1/me` | Bearer access token | Get current user info |
