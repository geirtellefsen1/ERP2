from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "BPO Nexus API"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bpo_nexus"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    auth0_domain: str = ""
    auth0_audience: str = ""
    claude_api_key: str = ""

    # ── JWT signing — dedicated key, NEVER reuse another provider's key.
    # In dev/test, leave blank and the auth module will derive a stable
    # per-process key from a hardcoded placeholder (with a loud warning).
    # In production, set to at least 32 random bytes:
    #     openssl rand -hex 32
    jwt_signing_key: str = ""

    # ── Integration secrets master key (Fernet-compatible). Used by
    # services/secrets.py to encrypt per-agency credentials at rest.
    integration_secrets_key: str = ""

    # ── Rate limiting
    rate_limit_per_minute: int = 30
    rate_limit_login_per_minute: int = 10

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
