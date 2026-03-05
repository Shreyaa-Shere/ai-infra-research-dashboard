from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────────
    app_version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/airesearch"
    )

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 7

    # ── Bcrypt ────────────────────────────────────────────────────────────────
    # Lower this to 4 in .env for faster local dev; keep 12+ in production.
    bcrypt_rounds: int = 12

    # ── Seed / Admin ──────────────────────────────────────────────────────────
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme123!"

    # ── Ingestion ─────────────────────────────────────────────────────────────
    ingestion_source_type: str = "file"
    ingestion_source_name: str = "local-ingest"
    ingestion_interval_min: int = 60
    ingest_dir: str = "/app/data/ingest"

    # ── CORS / Security ────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173"
    frontend_base_url: str = "http://localhost:5173"

    # ── Invites ────────────────────────────────────────────────────────────────
    invite_token_ttl_days: int = 7


settings = Settings()
