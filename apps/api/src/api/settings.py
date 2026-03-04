from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_version: str = "0.1.0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/airesearch"
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"


settings = Settings()
