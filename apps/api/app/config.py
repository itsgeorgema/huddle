from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Huddle API"
    environment: str = "local"
    database_url: str = "sqlite:///./huddle.db"
    redis_url: str = "redis://localhost:6379/0"
    llm_mode: str = "mock"
    openai_api_key: str | None = None
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    celery_always_eager: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
