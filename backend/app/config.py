from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    app_name: str = "Multi-Agent Research Assistant"
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM provider. Leave empty to use the built-in deterministic fallback engine.
    llm_provider: str = "openai"  # openai | anthropic | none
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-0"
    base_url: str = "https://api.openai.com/v1"


    # Web search. Leave empty to use the built-in metadata fallback searcher.
    tavily_api_key: str = ""
    brave_api_key: str = ""
    duckduckgo_enabled: bool = True

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    upload_dir: Path = BASE_DIR / "uploads"
    data_dir: Path = Path(os.getenv("MAR_DATA_DIR", str(BASE_DIR.parent.parent / "data"))) / "tasks"

    max_document_bytes: int = 15 * 1024 * 1024
    max_runs_bytes: int = 15 * 1024 * 1024
    max_sources_per_agent: int = 4

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key or self.openai_api_key or self.anthropic_api_key)

    @property
    def search_configured(self) -> bool:
        return bool(self.tavily_api_key or self.brave_api_key or self.duckduckgo_enabled)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()