from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration values."""

    api_title: str = Field(default="Floor Plan Comparison API", description="FastAPI title")
    api_version: str = Field(default="0.1.0", description="API version string")
    allow_origins: list[str] = Field(
        default=["*"],
        description="List of allowed CORS origins; replace with concrete domains in production",
    )
    storage_dir: str = Field(default="storage", description="Root directory for file storage")
    celery_broker_url: str = Field(
        default="memory://",
        description="Celery broker connection string; override with Redis for production",
    )
    celery_result_backend: str = Field(
        default="cache+memory://",
        description="Celery result backend connection string",
    )
    celery_task_always_eager: bool = Field(
        default=True,
        description="Whether Celery tasks should run eagerly (synchronously)",
    )
    celery_task_eager_propagates: bool = Field(
        default=True,
        description="Whether eager tasks should propagate exceptions",
    )

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FLOORPLAN_", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """Load and cache application settings."""

    return Settings()
