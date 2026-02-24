"""
Configuración centralizada del ChatBot
"""
import os


class Settings:
    """Configuración centralizada"""
    
    APP_NAME = "ChatBot Evolution"
    APP_VERSION = "2.1"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")
    SQLALCHEMY_ECHO = False
    
    # NLP
    PATTERN_TIMEOUT = 5.0
    MIN_CONFIDENCE = 0.5
    
    # Embeddings
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    ENABLE_EMBEDDINGS = True
    
    # LLM Fallback
    USE_LLM_FALLBACK = True
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "mistral"
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 150
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # API
    API_HOST = "127.0.0.1" if not os.getenv("DOCKER_CONTAINER") else "0.0.0.0"
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_WORKERS = 4
    
    # Multi-tenant
    MAX_TENANTS = int(os.getenv("MAX_TENANTS", "1000"))
    TENANT_ISOLATION = os.getenv("TENANT_ISOLATION", "True").lower() == "true"


settings = Settings()
