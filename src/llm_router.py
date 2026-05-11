"""
llm_router.py — Unified multi-provider LLM interface.

Supports three providers for sector classification:
  • OpenAI  (GPT-4o-mini)
  • Google  (Gemini 2.0 Flash)
  • Anthropic (Claude 3.5 Haiku)

Each provider uses its native SDK directly — no heavy abstraction
libraries required.
"""

import logging
import time

logger = logging.getLogger(__name__)

# ── System prompt (identical for all providers) ─────────────────────
_SYSTEM_PROMPT = (
    "Eres un experto en clasificación de sectores económicos. "
    "Responde ÚNICAMENTE con el nombre del sector (máximo 2 palabras). "
    "Si es ambiguo, responde 'Otros'."
)

_USER_PROMPT_TPL = 'Clasifica el sector de esta empresa según su objeto social: "{text}"'


# ── Provider implementations ────────────────────────────────────────

def _call_openai(api_key: str, user_prompt: str) -> str:
    """Call OpenAI GPT-4o-mini."""
    import openai
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=20,
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def _call_gemini(api_key: str, user_prompt: str) -> str:
    """Call Google Gemini 2.0 Flash."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=_SYSTEM_PROMPT,
    )
    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=20,
            temperature=0,
        ),
    )
    return response.text.strip()


def _call_anthropic(api_key: str, user_prompt: str) -> str:
    """Call Anthropic Claude 3.5 Haiku."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=20,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )
    return message.content[0].text.strip()


_PROVIDERS = {
    "openai": _call_openai,
    "gemini": _call_gemini,
    "anthropic": _call_anthropic,
}

# ── Public API ──────────────────────────────────────────────────────

def classify_sector(objeto_social: str, provider: str, api_key: str) -> str:
    """
    Classify a company's *objeto social* into an economic sector using
    the specified LLM provider.

    Parameters
    ----------
    objeto_social : str
        The company activity description to classify.
    provider : str
        One of ``"openai"``, ``"gemini"``, ``"anthropic"``.
    api_key : str
        The API key for the chosen provider.

    Returns
    -------
    str
        The detected sector name, or ``"Otros"`` on failure.
    """
    if not api_key:
        logger.warning("No API key provided — skipping LLM classification.")
        return "Otros"

    call_fn = _PROVIDERS.get(provider)
    if call_fn is None:
        logger.error(f"Unknown LLM provider: {provider}")
        return "Otros"

    user_prompt = _USER_PROMPT_TPL.format(text=objeto_social)

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            raw = call_fn(api_key, user_prompt)
            # Normalise the response
            result = (
                raw.replace("*", "")
                .replace("#", "")
                .replace('"', "")
                .lower()
                .strip()
            )
            return result[:50] if result else "Otros"

        except Exception as e:
            err = str(e).lower()
            if "429" in err or "rate" in err or "quota" in err:
                logger.warning(
                    f"Rate limit ({provider}). Retrying in {retry_delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"LLM API error ({provider}): {e}")
                return "Otros"

    return "Otros"


def test_connection(provider: str, api_key: str) -> dict:
    """
    Send a lightweight test request to verify the API key works.

    Returns a dict with ``{"success": bool, "message": str}``.
    """
    if not api_key:
        return {"success": False, "message": "No se ha proporcionado una clave API."}

    try:
        result = classify_sector("Construcción de edificios residenciales", provider, api_key)
        if result and result != "Otros":
            return {"success": True, "message": f"Conexión exitosa. Sector detectado: '{result}'"}
        # "Otros" is also a valid answer — the point is the call succeeded
        return {"success": True, "message": f"Conexión exitosa. Respuesta: '{result}'"}
    except Exception as e:
        return {"success": False, "message": f"Error de conexión: {str(e)}"}
