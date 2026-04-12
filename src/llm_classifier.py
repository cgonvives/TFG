import openai
import os
import logging
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# OpenAI client (initialized once)
_client = None

def _get_client(api_key=None):
    """Gets or creates the OpenAI client."""
    global _client
    if _client is None:
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            return None
        _client = openai.OpenAI(api_key=key)
    return _client

def classify_sector_llm(objeto_social: str, api_key: str = None) -> str:
    """
    Uses OpenAI GPT-4o-mini to classify a company's 'objeto social' into a sector.
    
    Parameters
    ----------
    objeto_social : str
        The description of the company's activities.
    api_key : str, optional
        OpenAI API Key. If None, reads from OPENAI_API_KEY env variable.
        
    Returns
    -------
    str
        The detected sector or "Otros" if classification fails.
    """
    client = _get_client(api_key)
    if not client:
        logger.warning("OPENAI_API_KEY not found. Skipping LLM classification.")
        return "Otros"
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un experto en clasificación de sectores económicos. Responde ÚNICAMENTE con el nombre del sector (máximo 2 palabras). Si es ambiguo, responde 'Otros'."},
                    {"role": "user", "content": f"Clasifica el sector de esta empresa según su objeto social: \"{objeto_social}\""}
                ],
                max_tokens=20,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().replace("*", "").replace("#", "").replace("\"", "").lower()
            return result[:50] if result else "Otros"
            
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                logger.warning(f"Rate limit. Reintentando en {retry_delay}s... (Intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Error OpenAI API: {e}")
                return "Otros"
                
    return "Otros"
