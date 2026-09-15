"""Backward-compatible re-export of central settings from configs.settings."""

from configs.settings import _BASE_DIR, Settings, get_settings, settings

__all__ = ["_BASE_DIR", "Settings", "get_settings", "settings"]
