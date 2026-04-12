from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "BPO Nexus API"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bpo_nexus"
    redis_url: str = "redis://localhost:6379/0"
    auth0_domain: str = ""
    auth0_audience: str = ""
    claude_api_key: str = ""

    # ── OAuth (Google + Microsoft social login) ──
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    microsoft_tenant: str = "common"  # "common" allows any Microsoft account

    # Where Google/Microsoft redirect users back to (must point at THIS API)
    oauth_redirect_base_url: str = "http://localhost:8000"
    # Where the API redirects users after OAuth completes (the web app)
    frontend_url: str = "http://localhost:3000"
    # Secret used to sign short-lived OAuth state tokens
    oauth_state_secret: str = "change-me-in-production-please"

    # Comma-separated list of allowed CORS origins (e.g. "http://localhost:3000,https://app.example.com")
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache
def get_settings() -> Settings:
    return Settings()
