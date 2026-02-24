"""
Servicio de embeddings semánticos
"""
from typing import Optional, List
from ..settings import settings
from ..utils import get_logger

logger = get_logger(__name__, settings.LOG_LEVEL)


class EmbeddingService:
    """Servicio de embeddings semánticos (opcional)"""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled and settings.ENABLE_EMBEDDINGS
        self.model = None
        
        if self.enabled:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info(f"Embedding model loaded: {settings.EMBEDDING_MODEL}")
            except ImportError:
                logger.warning("sentence-transformers not installed. Embeddings disabled.")
                self.enabled = False
    
    def embed(self, text: str) -> Optional[List[float]]:
        """Genera embedding para texto"""
        if not self.enabled or not self.model:
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None
