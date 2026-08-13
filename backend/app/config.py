from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env.local"), extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./mailpilot.db"
    frontend_url: str = "http://localhost:3000"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/backend/api/v1/auth/google/callback"
    token_encryption_key: str = ""
    session_secret: str = "development-only-change-me"
    cron_secret: str = "development-cron-secret"
    default_send_interval_seconds: int = 45


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

