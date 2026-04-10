from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "BPO Nexus API"
    debug: bool = False
    database_url: str = "postgresql://postgres:postgres@localhost:5432/bpo_nexus"
    redis_url: str = "redis://localhost:6379/0"
    auth0_domain: str = ""
    auth0_audience: str = ""
    claude_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "allow"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
