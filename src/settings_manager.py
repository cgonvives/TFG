"""
settings_manager.py — Persistent configuration management.

Stores user preferences (LLM provider, API key, data metadata) in a
JSON file located in APP_DATA/settings.json.
"""

import json
import os
import logging
from datetime import datetime

from src.config import SETTINGS_FILE

logger = logging.getLogger(__name__)

# ── Default settings ────────────────────────────────────────────────
_DEFAULTS = {
    "llm_provider": "gemini",           # "openai" | "gemini" | "anthropic"
    "api_key": "",                       # API key for the selected provider
    "original_filename": "",             # Name the user uploaded
    "last_upload_date": "",              # ISO datetime
    "last_training_date": "",            # ISO datetime
}


def _ensure_file():
    """Create the settings file with defaults if it doesn't exist."""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(_DEFAULTS, f, ensure_ascii=False, indent=2)


def load_settings() -> dict:
    """Load settings from disk, merging with defaults for any missing keys."""
    _ensure_file()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults so new keys are always present
        merged = {**_DEFAULTS, **data}
        return merged
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return dict(_DEFAULTS)


def save_settings(updates: dict) -> dict:
    """
    Merge *updates* into the existing settings and persist to disk.

    Returns the full settings dict after saving.
    """
    current = load_settings()
    current.update(updates)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
    return current


def get_api_key() -> str:
    """Shortcut to retrieve the current API key."""
    return load_settings().get("api_key", "")


def get_llm_provider() -> str:
    """Shortcut to retrieve the current LLM provider name."""
    return load_settings().get("llm_provider", "gemini")


def record_upload(original_filename: str):
    """Record metadata about a data upload."""
    save_settings({
        "original_filename": original_filename,
        "last_upload_date": datetime.now().isoformat(),
    })


def record_training():
    """Record the timestamp of the last successful training."""
    save_settings({
        "last_training_date": datetime.now().isoformat(),
    })
