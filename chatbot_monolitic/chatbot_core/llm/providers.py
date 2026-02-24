"""
Proveedores de LLM
"""
from typing import Optional
from abc import ABC, abstractmethod
from ..settings import settings
from ..utils import get_logger

logger = get_logger(__name__, settings.LOG_LEVEL)


class LLMProvider(ABC):
    """Interfaz abstracta para LLM"""
    
    @abstractmethod
    def generate(self, prompt: str) -> Optional[str]:
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """Provider para OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.available = False
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.available = True
                logger.info("OpenAI provider initialized")
            except ImportError:
                logger.warning("openai package not installed")
    
    def generate(self, prompt: str) -> Optional[str]:
        """Genera respuesta con GPT"""
        if not self.available:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None


class OllamaProvider(LLMProvider):
    """Provider para Ollama local"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.available = False
        
        try:
            import requests
            self.requests = requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                self.available = True
                logger.info(f"Ollama provider initialized at {self.base_url}")
        except:
            logger.warning(f"Ollama not available at {self.base_url}")
    
    def generate(self, prompt: str) -> Optional[str]:
        """Genera respuesta con modelo local"""
        if not self.available:
            return None
        
        try:
            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama error: {e}")
        
        return None
