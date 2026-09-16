"""Application configuration loaded from environment using Pydantic Settings.

This module is the underlying implementation; `config/settings.py` re-exports it
and is the preferred/canonical public import path used across the codebase
(11 modules import via `config.settings`, 2 import this module directly).
"""

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


def reload_settings() -> Settings:
    """Re-read `.env` from disk and update the module-level `settings` singleton in place.

    `Settings()` only reads `.env` once at process start. Some flows (e.g. the
    Streamlit Settings page writing a new OPENROUTER_API_KEY/OPENROUTER_MODEL to
    `.env`) need those changes picked up immediately, without restarting the
    process. Rather than returning a brand-new `Settings` instance (which callers
    that already did `from configs.settings import settings` or
    `from config.settings import settings` would never see), this mutates the
    existing `settings` object's fields in place so every existing reference to
    it observes the fresh values.

    Note: this intentionally does NOT call `get_settings.cache_clear()`.
    `get_settings()` is only ever invoked once, at import time, to build the
    `settings` singleton above -- nothing else in the codebase calls it again.
    Since `lru_cache` memoizes that same singleton object, a future
    `get_settings()` call (with no clear) would keep returning this exact
    mutated instance, which matches the singleton guarantee this function
    exists to uphold. Clearing the cache would instead make that hypothetical
    future call construct and return a brand-new, unmutated `Settings()`
    object -- a different instance than `settings`, silently breaking the
    reload guarantee for that caller.
    """
    fresh = Settings()
    for field_name in Settings.model_fields:
        setattr(settings, field_name, getattr(fresh, field_name))
    return settings
