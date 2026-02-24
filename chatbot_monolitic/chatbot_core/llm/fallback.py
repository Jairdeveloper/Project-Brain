"""
Gestor de fallback a LLM
"""
from typing import Optional
from .providers import LLMProvider, OpenAIProvider, OllamaProvider
from ..settings import settings


class LLMFallback:
    """Gestor de fallback a LLM"""
    
    def __init__(self):
        self.provider: Optional[LLMProvider] = None
        
        if not settings.USE_LLM_FALLBACK:
            return
        
        # Intenta OpenAI primero
        if settings.OPENAI_API_KEY:
            self.provider = OpenAIProvider()
            if self.provider.available:
                return
        
        # Fallback a Ollama
        self.provider = OllamaProvider()
    
    def generate(self, prompt: str) -> Optional[str]:
        """Genera respuesta si provider disponible"""
        if not self.provider:
            return None
        
        return self.provider.generate(prompt)
