"""
ChatBot Core - Librería modular para chatbot con NLP, Storage, LLM
"""

# Settings
from .settings import Settings, settings

# NLP
from .nlp import (
    PatternEngine,
    Pattern,
    Tokenizer,
    PronounTranslator,
    EmbeddingService,
)

# Actor
from .actor import Actor, Response

# Storage
from .storage import SimpleConversationStorage

# LLM
from .llm import (
    LLMProvider,
    OpenAIProvider,
    OllamaProvider,
    LLMFallback,
)

# Brain Manager
from .brain_manager import BrainManager, get_default_brain

# Utils
from .utils import get_logger

__version__ = "2.1"

__all__ = [
    # Settings
    "Settings",
    "settings",
    # NLP
    "PatternEngine",
    "Pattern",
    "Tokenizer",
    "PronounTranslator",
    "EmbeddingService",
    # Actor
    "Actor",
    "Response",
    # Storage
    "SimpleConversationStorage",
    # LLM
    "LLMProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "LLMFallback",
    # Brain Manager
    "BrainManager",
    "get_default_brain",
    # Utils
    "get_logger",
]
