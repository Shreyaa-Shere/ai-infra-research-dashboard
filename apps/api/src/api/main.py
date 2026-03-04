from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.auth.rate_limit import limiter
from api.logging_config import setup_logging
from api.middleware import RequestIdMiddleware
from api.routes import health, version
from api.routes import auth as auth_router
from api.routes import users as users_router
from api.settings import settings

setup_logging()

# HTTPBearer registered here so OpenAPI picks up the security scheme globally.
_bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title="AI Infrastructure Research Dashboard API",
    version=settings.app_version,
    lifespan=lifespan,
)

# ── Rate limiter ───────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestIdMiddleware)


# ── Error handlers ────────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        content = detail
    else:
        content = {
            "error": {"code": "HTTP_ERROR", "message": str(detail), "details": {}}
        }
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(version.router, prefix="/api/v1")
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(users_router.router, prefix="/api/v1")
