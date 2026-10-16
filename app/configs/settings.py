from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://kvitto:kvitto@localhost:5432/kvitto"
    webhook_secret: SecretStr


@lru_cache
def get_settings() -> Settings:
    return Settings()
