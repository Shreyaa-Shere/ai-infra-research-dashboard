from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.logging_config import setup_logging
from api.middleware import RequestIdMiddleware
from api.routes import health, version
from api.settings import settings

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title="AI Infrastructure Research Dashboard API",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)

app.include_router(health.router)
app.include_router(version.router, prefix="/api/v1")
