"""Application configuration loaded from environment using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    OPENROUTER_MODEL: str = Field(
        default="anthropic/claude-sonnet-4",
        description="Default LLM model slug on OpenRouter",
    )
    DB_PATH: str = Field(
        default=str(_BASE_DIR / "goalos.db"),
        description="Path to SQLite database",
    )
    CHROMA_PATH: str = Field(
        default=str(_BASE_DIR / "chroma_db"),
        description="Path to ChromaDB persistent vector memory",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Application logging level")
    LOG_FILE: str = Field(
        default=str(_BASE_DIR / "goalos.log"),
        description="Application log filepath",
    )
    GOALOS_API_TOKEN: str = Field(default="", description="Bearer token for API security")
    ENVIRONMENT: str = Field(default="development", description="Deployment environment")

    # Lowercase property aliases for standard Python compatibility
    @property
    def openrouter_api_key(self) -> str:
        return self.OPENROUTER_API_KEY

    @property
    def openrouter_model(self) -> str:
        return self.OPENROUTER_MODEL

    @property
    def db_path(self) -> str:
        return self.DB_PATH

    @property
    def chroma_path(self) -> str:
        return self.CHROMA_PATH


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
