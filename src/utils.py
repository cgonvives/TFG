import json
import os
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = "data/sector_cache.json"

def load_sector_cache():
    """Loads the sector cache from a JSON file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sector cache: {e}")
    return {}

def save_sector_cache(cache):
    """Saves the sector cache to a JSON file."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving sector cache: {e}")
