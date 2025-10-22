from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用级配置。"""

    api_title: str = Field(default="Floor Plan Comparison API", description="FastAPI 标题")
    api_version: str = Field(default="0.1.0", description="API 版本号")
    allow_origins: list[str] = Field(
        default=["*"],
        description="允许跨域的来源列表，后续可替换为具体域名",
    )
    storage_dir: str = Field(default="storage", description="文件存储根目录")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FLOORPLAN_", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """懒加载配置，避免重复解析环境变量。"""

    return Settings()
