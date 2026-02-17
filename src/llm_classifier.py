import google.generativeai as genai
import os
import logging
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Cache for target model name
_target_model_name = None

def classify_sector_llm(objeto_social: str, api_key: str = None) -> str:
    """
    Uses Gemini LLM to classify a company's 'objeto social' into a sector.
    
    Parameters
    ----------
    objeto_social : str
        The description of the company's activities.
    api_key : str, optional
        Gemini API Key. If None, it tries to read from environment variable GEMINI_API_KEY.
        
    Returns
    -------
    str
        The detected sector or "Otros" if classification fails.
    """
    global _target_model_name
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        logger.warning("GEMINI_API_KEY not found. Skipping LLM classification.")
        return "Otros"
    
    max_retries = 5
    retry_delay = 15  # More aggressive initial wait for Free Tier
    
    for attempt in range(max_retries):
        try:
            genai.configure(api_key=key)
            
            if not _target_model_name:
                # Get all models once to decide
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # Try preferred list
                candidates = ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro', 'gemini-pro']
                for cand in candidates:
                    if cand in models or any(m.endswith(cand) for m in models):
                        _target_model_name = cand
                        break
                
                if not _target_model_name and models:
                    _target_model_name = models[0]
            
            if not _target_model_name:
                return "Otros"
                
            model = genai.GenerativeModel(_target_model_name)
            
            prompt = f"""
            Analiza el siguiente 'objeto social' y determina a qué sector pertenece la empresa.
            Objeto Social: "{objeto_social}"
            
            REGLAS:
            1. Responde ÚNICAMENTE con el nombre del sector (ej. "Tecnología", "Energía", "Salud").
            2. Máximo 2 palabras.
            3. Si es ambiguo, responde "Otros".
            """
            
            response = model.generate_content(prompt)
            result = response.text.strip().replace("*", "").replace("#", "")
            return result[:50] if result else "Otros"
            
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Quota 429. Reintentando en {retry_delay}s... (Intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff (10, 20, 40, 80...)
            else:
                logger.error(f"Error Gemini API: {e}")
                return "Otros"
                
    return "Otros"
