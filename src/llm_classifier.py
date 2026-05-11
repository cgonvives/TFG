"""
llm_classifier.py — Sector classification via LLM.

This module is the public entry-point called by ``optimizer.py``.
It delegates the actual API call to ``llm_router.py`` which supports
OpenAI, Gemini and Anthropic.  The provider and API key are read from
the persistent settings managed by ``settings_manager.py``.
"""

import logging

logger = logging.getLogger(__name__)


def classify_sector_llm(objeto_social: str, api_key: str = None) -> str:
    """
    Uses the configured LLM provider to classify a company's
    'objeto social' into an economic sector.

    Parameters
    ----------
    objeto_social : str
        The description of the company's activities.
    api_key : str, optional
        Override API key.  When ``None`` the key stored in
        ``settings.json`` is used.

    Returns
    -------
    str
        The detected sector or ``"Otros"`` if classification fails.
    """
    try:
        from src.settings_manager import get_api_key, get_llm_provider
        from src.llm_router import classify_sector
    except ImportError:
        from settings_manager import get_api_key, get_llm_provider
        from llm_router import classify_sector

    provider = get_llm_provider()
    key = api_key or get_api_key()

    if not key:
        logger.warning("No API key configured — skipping LLM classification.")
        return "Otros"

    return classify_sector(objeto_social, provider, key)
