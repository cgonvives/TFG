import json
import os
import logging

logger = logging.getLogger(__name__)

import unicodedata
from src.config import SECTOR_CACHE_FILE

def clean_text(text):
    """
    NLP cleaning for company descriptions and need contexts.
    Centralized here to ensure consistency between training and inference.
    """
    if not isinstance(text, str): return ""
    text = text.lower()
    # Remove common legal prefixes
    prefixes = ["la sociedad tiene por objeto", "objeto social:", "actividad principal", "la participacion.", "la explotacion", "cnae"]
    for p in prefixes:
        text = text.replace(p, "")
    # Remove symbols and extra spaces
    text = "".join([c if c.isalnum() or c.isspace() else " " for c in text])
    return " ".join(text.split())

def load_sector_cache():
    """Loads the sector cache from a JSON file."""
    if os.path.exists(SECTOR_CACHE_FILE):
        try:
            with open(SECTOR_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sector cache: {e}")
    return {}

def save_sector_cache(cache):
    """Saves the sector cache to a JSON file."""
    os.makedirs(os.path.dirname(SECTOR_CACHE_FILE), exist_ok=True)
    try:
        with open(SECTOR_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving sector cache: {e}")

def remove_accents(text):
    """
    Removes accents from a string.
    """
    if not isinstance(text, str):
        return ""
    # Normalize to NFD (Normal Form Decomposition) and filter non-spacing marks
    normalized = unicodedata.normalize('NFD', text)
    return "".join(c for c in normalized if unicodedata.category(c) != 'Mn')
