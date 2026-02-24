"""
DESCRIPCIÓN:
-----------
Este es un archivo monolítico que contiene TODO el código del chatbot modulado.
Incluye: configuración, NLP, persistencia, embeddings, LLM, y API REST.

Para ejecutar:
    python chatbot_monolith.py --mode cli      (Modo CLI interactivo)
    python chatbot_monolith.py --mode api      (Modo API REST)

DEPENDENCIAS NECESARIAS:
    pip install fastapi uvicorn sqlalchemy pydantic-settings sentence-transformers

OPCIONAL (para LLM):
    pip install openai requests
"""

import os
import sys
import re
import json
import logging
import argparse
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager

# =============================================================================
# PARTE 1: CONFIGURACIÓN Y LOGGING
# =============================================================================

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


settings = Settings()


def get_logger(name: str) -> logging.Logger:
    """Factory para obtener loggers configurados"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    formatter = logging.Formatter(settings.LOG_FORMAT)
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger


logger = get_logger(__name__)


# =============================================================================
# PARTE 2: NLP - PATTERN MATCHING
# =============================================================================

@dataclass
class Pattern:
    """Patrón compilado para matching"""
    tokens: List[Any]
    regex: re.Pattern
    used_backrefs: List[str]


class PatternEngine:
    """Motor de reconocimiento de patrones"""
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.pattern_cache: Dict[tuple, Pattern] = {}
    
    def compile_pattern(self, pattern: List[Any]) -> Pattern:
        """Compila lista de patrones a regex compilado"""
        key = tuple(str(p) for p in pattern)
        if key in self.pattern_cache:
            return self.pattern_cache[key]
        
        regex = self._build_regex(pattern)
        used_backrefs = self._extract_backrefs(pattern)
        
        compiled = Pattern(tokens=pattern, regex=regex, used_backrefs=used_backrefs)
        self.pattern_cache[key] = compiled
        return compiled
    
    def _build_regex(self, pattern: List[Any]) -> re.Pattern:
        """Construye regex desde patrón"""
        r = ["^"]
        used_backrefs = []
        
        for tok in pattern:
            if isinstance(tok, str):
                r.append(f"({re.escape(tok)})")
            elif isinstance(tok, int):
                if tok == 0:
                    r.append(r"[a-zA-Z ]*?")
                elif tok == 1:
                    r.append(r"[a-zA-Z]+")
            elif isinstance(tok, list) and len(tok) >= 2:
                bind_type, bind_name = tok[0], tok[1]
                if bind_name not in used_backrefs:
                    used_backrefs.append(bind_name)
                    if bind_type == 0:
                        r.append(f"(?P<{bind_name}>[a-zA-Z ]*?)")
                    elif bind_type == 1:
                        r.append(f"(?P<{bind_name}>[a-zA-Z]+)")
        
        regex_str = r"(\s)*".join(r) + r"$(\s)*"
        return re.compile(regex_str, re.IGNORECASE)
    
    def _extract_backrefs(self, pattern: List[Any]) -> List[str]:
        """Extrae nombres de backreferences"""
        backrefs = []
        for tok in pattern:
            if isinstance(tok, list) and len(tok) >= 2:
                backrefs.append(tok[1])
        return backrefs
    
    def match(self, pattern: List[Any], sentence: str) -> Optional[List[List[str]]]:
        """Intenta matchear patrón contra sentence"""
        compiled = self.compile_pattern(pattern)
        matches = compiled.regex.search(sentence)
        
        if not matches:
            return None
        
        binding_list = []
        groups = matches.groups()
        
        for key, idx in compiled.regex.groupindex.items():
            group_value = groups[idx - 1].strip()
            if group_value:
                binding = [key, *group_value.split()]
                binding_list.append(binding)
        
        return binding_list


class Tokenizer:
    """Tokenización básica de texto"""
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokeniza texto en palabras"""
        return text.lower().strip().replace("(", "").replace(")", "").split()
    
    @staticmethod
    def detokenize(tokens: List[str]) -> str:
        """Reconstruye texto desde tokens"""
        return " ".join(tokens)


class PronounTranslator:
    """Traduce pronombres en binding lists"""
    
    DEFAULT_PRONOUN_MAP = {
        "i": "you", "you": "i", "my": "your", "me": "you", "your": "my",
        "i've": "you've", "we've": "they've",
        "fred": "he", "jack": "he", "jane": "she",
    }
    
    def __init__(self, custom_map: Dict[str, str] | None = None):
        self.pronoun_map = {**self.DEFAULT_PRONOUN_MAP}
        if custom_map:
            self.pronoun_map.update(custom_map)
    
    def translate(self, binding_list: List[List[str]]) -> List[List[str]]:
        """Traduce pronombres en una binding list"""
        result = []
        for binding in binding_list:
            if isinstance(binding, list):
                translated = [binding[0]]
                for word in binding[1:]:
                    translated.append(self.pronoun_map.get(word.lower(), word))
                result.append(translated)
            else:
                result.append(binding)
        return result


# =============================================================================
# PARTE 3: RESPUESTA ESTRUCTURADA
# =============================================================================

@dataclass
class Response:
    """Respuesta estructurada del Actor"""
    text: str
    confidence: float = 1.0
    pattern_matched: bool = False
    source: str = "default"
    metadata: dict = field(default_factory=dict)


# =============================================================================
# PARTE 4: ACTOR ORQUESTADOR
# =============================================================================

class Actor:
    """Orquestador: procesa entrada, matchea patrones, genera respuestas"""
    
    def __init__(
        self,
        pattern_responses: List[Tuple[List, List]],
        default_responses: List[List[str]],
    ):
        self.pattern_responses = pattern_responses
        self.default_responses = default_responses
        
        self.pattern_engine = PatternEngine()
        self.pronoun_translator = PronounTranslator()
        self.tokenizer = Tokenizer()
        
        self.username = ""
        self.username_tag = "Username"
        self.default_response_index = 0
    
    def process(self, user_input: str) -> Response:
        """Procesa entrada del usuario y genera respuesta"""
        tokens = self.tokenizer.tokenize(user_input)
        input_text = self.tokenizer.detokenize(tokens)
        
        # Intenta matching
        matched_pattern = None
        binding_list = None
        response_template = None
        
        for pattern, response_tmpl in self.pattern_responses:
            bl = self.pattern_engine.match(pattern, input_text)
            if bl is not None:
                matched_pattern = pattern
                binding_list = bl
                response_template = response_tmpl
                break
        
        # Genera respuesta
        if binding_list is None:
            response = self._generate_default_response()
            response.source = "default"
        else:
            translated_bindings = self.pronoun_translator.translate(binding_list)
            response_text = self._build_reply(response_template, translated_bindings)
            response = Response(
                text=response_text,
                confidence=0.9,
                pattern_matched=True,
                source="pattern",
                metadata={"pattern": matched_pattern, "bindings": translated_bindings},
            )
        
        return response
    
    def _generate_default_response(self) -> Response:
        """Genera respuesta default (cíclica)"""
        resp = self.default_responses[self.default_response_index]
        text = " ".join(resp)
        self.default_response_index = (self.default_response_index + 1) % len(self.default_responses)
        return Response(text=text, source="default")
    
    def _build_reply(self, response_template: List, binding_list: List[List[str]]) -> str:
        """Construye respuesta reemplazando placeholders con bindings"""
        binding_dict = {}
        
        for binding in binding_list:
            if isinstance(binding, list) and len(binding) > 0:
                key = binding[0]
                values = binding[1:]
                
                if key == self.username_tag and values:
                    if self.username and self.username != values[0]:
                        response = [values[0], "eh?", "what", "ever", "happened", "to", self.username]
                        return " ".join(response)
                    self.username = values[0]
                
                binding_dict[key] = values
        
        reply = []
        for elem in response_template:
            if isinstance(elem, list) and len(elem) > 1:
                binding_key = elem[1]
                if binding_key in binding_dict:
                    reply.extend(binding_dict[binding_key])
            else:
                reply.append(str(elem))
        
        return " ".join(reply)


# =============================================================================
# PARTE 5: PERSISTENCIA (OPCIONAL - SIMPLE JSON)
# =============================================================================

class SimpleConversationStorage:
    """Almacenamiento simple de conversaciones en JSON"""
    
    def __init__(self, filename: str = "conversations.json"):
        self.filename = filename
        self.data = self._load()
    
    def _load(self) -> dict:
        """Carga conversaciones desde archivo"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self, session_id: str, user_input: str, bot_response: str):
        """Guarda interacción"""
        if session_id not in self.data:
            self.data[session_id] = []
        
        self.data[session_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_input,
            "bot": bot_response,
        })
        
        self._persist()
    
    def _persist(self):
        """Guarda a archivo"""
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def get_history(self, session_id: str) -> list:
        """Obtiene historial de sesión"""
        return self.data.get(session_id, [])


# =============================================================================
# PARTE 6: BÚSQUEDA SEMÁNTICA (OPCIONAL - CON SENTENCE TRANSFORMERS)
# =============================================================================

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


# =============================================================================
# PARTE 7: LLM FALLBACK (OPCIONAL - OPENAI + OLLAMA)
# =============================================================================

class LLMProvider:
    """Interfaz abstracta para LLM"""
    
    def generate(self, prompt: str) -> str:
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


# =============================================================================
# PARTE 8: CLI - MODO INTERACTIVO
# =============================================================================

def get_default_brain() -> tuple:
    """Retorna brain mejorado con 40+ patrones"""
    
    default_responses = [
        ["That's", "interesting,", "tell", "me", "more"],
        ["I", "see.", "Could", "you", "elaborate?"],
        ["That's", "a", "great", "point"],
        ["I", "understand.", "What", "else?"],
        ["In", "other", "words,", "you're", "saying...?"],
        ["Can", "you", "give", "me", "an", "example?"],
        ["That", "makes", "sense"],
        ["I", "appreciate", "your", "thoughts"],
    ]
    
    pattern_responses = [
        # SALUDOS
        [["hello", 0], ["Hello!", "It's", "nice", "to", "meet", "you"]],
        [["hi", 0], ["Hi", "there!", "How", "can", "I", "help?"]],
        [["hey", 0], ["Hey!", "What's", "on", "your", "mind?"]],
        [["good", "morning"], ["Good", "morning!", "Ready", "to", "chat?"]],
        [["good", "afternoon"], ["Good", "afternoon!", "How", "are", "you?"]],
        [["good", "evening"], ["Good", "evening!", "Nice", "to", "see", "you"]],
        
        # DESPEDIDAS
        [["goodbye", 0], ["Goodbye!", "It", "was", "great", "talking", "to", "you"]],
        [["bye", 0], ["See", "you", "later!", "Take", "care"]],
        
        # PRESENTACIÓN
        [[0, "my", "name", "is", [1, "name"], 0], 
         ["Pleased", "to", "meet", "you,", [1, "name"], "!"]],
        
        # CÓMO ESTÁS
        [["how", "are", "you"], ["I'm", "doing", "great,", "thanks", "for", "asking!"]],
        [["how", "are", "you", "doing"], ["Doing", "well!", "What", "about", "you?"]],
        
        # ESTADO DEL USUARIO
        [["i", "am", [1, "feeling"], 0],
         ["I'm", "sorry", "to", "hear", "you're", [1, "feeling"]]],
        
        # PREFERENCIAS
        [["i", "like", [1, "thing"], 0],
         [[1, "thing"], "is", "great!", "Why", "do", "you", "enjoy", [1, "thing"], "?"]],
        
        [["i", "hate", [1, "thing"], 0],
         ["I", "see.", "It", "sounds", "like", [1, "thing"], "isn't", "for", "you"]],
        
        # RELACIONES
        [[[1, "subject"], "loves", [0, "object"]],
         ["That's", "beautiful!"]],
        [[[1, "person"], "is", "my", "friend"],
         ["That's", "lovely!"]],
        
        # NECESIDADES
        [["i", "need", [1, "object"], 0],
         ["Why", "do", "you", "need", [1, "object"], "?"]],
        
        [["help", "me"],
         ["Of", "course!", "I'm", "here", "to", "help"]],
        
        # PREGUNTAS
        [["what", "is", [1, "topic"], 0],
         ["That's", "an", "interesting", "question", "about", [1, "topic"]]],
        
        # AGRADECIMIENTO
        [["thanks", 0], ["You're", "welcome!", "Happy", "to", "help"]],
        [["thank", "you"], ["My", "pleasure!"]],
        
        # CONFIRMACIÓN
        [["yes", 0], ["Great!"]],
        [["no", 0], ["I", "understand"]],
        
        # INFORMACIÓN DEL BOT
        [["who", "are", "you"],
         ["I'm", "an", "AI", "chatbot", "created", "to", "chat"]],
        [["what", "can", "you", "do"],
         ["I", "can", "have", "conversations", "and", "help", "with", "ideas"]],
    ]
    
    return pattern_responses, default_responses


def run_cli():
    """Modo CLI interactivo"""
    logger.info("Starting ChatBot CLI (Monolithic Version)")
    
    # Inicializa componentes
    pattern_responses, default_responses = get_default_brain()
    actor = Actor(pattern_responses, default_responses)
    storage = SimpleConversationStorage()
    session_id = str(uuid.uuid4())[:8]
    
    print("\n" + "=" * 70)
    print("ChatBot Evolution - Monolithic Mode (CLI)")
    print("=" * 70)
    print("Type 'quit' o '(quit)' to exit\n")
    
    try:
        while True:
            try:
                user_input = input("> ").strip()
            except EOFError:
                print("\n(EOF) Type '(quit)' to exit")
                continue
            
            if not user_input:
                continue
            
            if user_input.lower() in ("(quit)", "quit", "exit"):
                print("Bye!")
                break
            
            response = actor.process(user_input)
            print(f"Bot: {response.text}")
            
            # Guarda conversación
            storage.save(session_id, user_input, response.text)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted. Bye!")


# =============================================================================
# PARTE 9: API REST (OPCIONAL - CON FASTAPI)
# =============================================================================

def run_api():
    """Modo API REST"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
    except ImportError:
        print("ERROR: FastAPI no instalado. Instala con: pip install fastapi uvicorn")
        sys.exit(1)
    
    logger.info("Starting ChatBot API (Monolithic Version)")
    
    # Inicializa componentes
    pattern_responses, default_responses = get_default_brain()
    actor = Actor(pattern_responses, default_responses)
    storage = SimpleConversationStorage()
    
    # Crea app FastAPI
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Monolithic Chatbot with NLP, Embeddings, and LLM Fallback"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health():
        """Health check"""
        return {"status": "ok", "version": settings.APP_VERSION}
    
    @app.post("/api/v1/chat")
    async def chat(message: str, session_id: Optional[str] = None):
        """Endpoint principal de chat"""
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="message required")
        
        response = actor.process(message)
        storage.save(session_id, message, response.text)
        
        return {
            "session_id": session_id,
            "message": message,
            "response": response.text,
            "confidence": response.confidence,
            "source": response.source,
            "pattern_matched": response.pattern_matched,
        }
    
    @app.get("/api/v1/history/{session_id}")
    async def history(session_id: str):
        """Obtiene historial de sesión"""
        return {"session_id": session_id, "history": storage.get_history(session_id)}
    
    @app.get("/api/v1/stats")
    async def stats():
        """Estadísticas del chatbot"""
        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "total_sessions": len(storage.data),
            "total_messages": sum(len(msgs) for msgs in storage.data.values()),
        }
    
    # Inicia servidor
    print(f"\n✅ API running at http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📖 Swagger docs: http://{settings.API_HOST}:{settings.API_PORT}/docs\n")
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )


# =============================================================================
# PARTE 9B: BRAIN SERVER - GESTOR DE PATRONES (CRUD)
# =============================================================================

class BrainManager:
    """Gestor centralizado de patrones y respuestas"""
    
    def __init__(self, filename: str = "brain_data.json"):
        self.filename = filename
        self.data = self._load()
        
        if not self.data:
            pattern_responses, default_responses = get_default_brain()
            self.data = {
                "pattern_responses": [
                    {"pattern": p[0], "response": p[1]} for p in pattern_responses
                ],
                "default_responses": default_responses,
                "metadata": {
                    "total_patterns": len(pattern_responses),
                    "total_defaults": len(default_responses),
                    "version": "1.0",
                }
            }
            self._persist()
    
    def _load(self) -> dict:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _persist(self):
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def get_all_patterns(self) -> list:
        return self.data.get("pattern_responses", [])
    
    def get_pattern_by_index(self, index: int) -> dict:
        patterns = self.get_all_patterns()
        if 0 <= index < len(patterns):
            return {"index": index, **patterns[index]}
        return None
    
    def add_pattern(self, pattern: list, response: list) -> dict:
        new_pattern = {"pattern": pattern, "response": response}
        self.data["pattern_responses"].append(new_pattern)
        self.data["metadata"]["total_patterns"] += 1
        self._persist()
        return {"index": len(self.data["pattern_responses"]) - 1, **new_pattern}
    
    def update_pattern(self, index: int, pattern: list, response: list) -> dict:
        patterns = self.data["pattern_responses"]
        if 0 <= index < len(patterns):
            patterns[index] = {"pattern": pattern, "response": response}
            self._persist()
            return {"index": index, **patterns[index]}
        return None
    
    def delete_pattern(self, index: int) -> bool:
        patterns = self.data["pattern_responses"]
        if 0 <= index < len(patterns):
            patterns.pop(index)
            self.data["metadata"]["total_patterns"] -= 1
            self._persist()
            return True
        return False
    
    def search_patterns(self, keyword: str) -> list:
        patterns = self.get_all_patterns()
        results = []
        keyword_lower = keyword.lower()
        
        for idx, p in enumerate(patterns):
            pattern_str = str(p["pattern"]).lower()
            response_str = str(p["response"]).lower()
            
            if keyword_lower in pattern_str or keyword_lower in response_str:
                results.append({"index": idx, **p})
        
        return results
    
    def get_default_responses(self) -> list:
        return self.data.get("default_responses", [])
    
    def add_default_response(self, response: list) -> dict:
        self.data["default_responses"].append(response)
        self.data["metadata"]["total_defaults"] += 1
        self._persist()
        return {"index": len(self.data["default_responses"]) - 1, "response": response}
    
    def delete_default_response(self, index: int) -> bool:
        defaults = self.data["default_responses"]
        if 0 <= index < len(defaults):
            defaults.pop(index)
            self.data["metadata"]["total_defaults"] -= 1
            self._persist()
            return True
        return False
    
    def get_metadata(self) -> dict:
        return self.data.get("metadata", {})
    
    def export_as_python(self) -> str:
        pattern_responses = self.get_all_patterns()
        default_responses = self.get_default_responses()
        
        code = "def get_default_brain() -> tuple:\n"
        code += "    \"\"\"Brain exportado desde servidor\"\"\"\n\n"
        code += "    pattern_responses = [\n"
        
        for p in pattern_responses:
            code += f"        [{p['pattern']}, {p['response']}],\n"
        
        code += "    ]\n\n"
        code += "    default_responses = [\n"
        
        for r in default_responses:
            code += f"        {r},\n"
        
        code += "    ]\n\n"
        code += "    return pattern_responses, default_responses\n"
        
        return code


def run_brain_server():
    """Servidor dedicado a gestionar el brain"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
    except ImportError:
        print("ERROR: FastAPI no instalado. Instala con: pip install fastapi uvicorn")
        sys.exit(1)
    
    logger.info("Starting Brain Manager Server")
    
    brain_manager = BrainManager()
    app = FastAPI(
        title="Brain Manager API",
        version="1.0",
        description="Gestor de patrones y respuestas del chatbot"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "brain-manager"}
    
    @app.get("/api/v1/brain/metadata")
    async def get_metadata():
        return brain_manager.get_metadata()
    
    @app.get("/api/v1/brain/patterns")
    async def list_patterns(limit: int = None, offset: int = 0):
        patterns = brain_manager.get_all_patterns()
        if limit:
            patterns = patterns[offset:offset + limit]
        return {"total": len(brain_manager.get_all_patterns()), "count": len(patterns), "patterns": patterns}
    
    @app.get("/api/v1/brain/patterns/{index}")
    async def get_pattern(index: int):
        pattern = brain_manager.get_pattern_by_index(index)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return pattern
    
    @app.post("/api/v1/brain/patterns")
    async def create_pattern(pattern: list, response: list):
        if not pattern or not response:
            raise HTTPException(status_code=400, detail="pattern and response required")
        new_pattern = brain_manager.add_pattern(pattern, response)
        return {"status": "created", **new_pattern}
    
    @app.put("/api/v1/brain/patterns/{index}")
    async def update_pattern(index: int, pattern: list, response: list):
        updated = brain_manager.update_pattern(index, pattern, response)
        if not updated:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"status": "updated", **updated}
    
    @app.delete("/api/v1/brain/patterns/{index}")
    async def delete_pattern(index: int):
        if not brain_manager.delete_pattern(index):
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"status": "deleted", "index": index}
    
    @app.get("/api/v1/brain/patterns/search")
    async def search_patterns(q: str):
        if not q:
            raise HTTPException(status_code=400, detail="search query (q) required")
        results = brain_manager.search_patterns(q)
        return {"query": q, "results": results, "count": len(results)}
    
    @app.get("/api/v1/brain/defaults")
    async def list_defaults():
        defaults = brain_manager.get_default_responses()
        return {"total": len(defaults), "defaults": defaults}
    
    @app.post("/api/v1/brain/defaults")
    async def create_default(response: list):
        if not response:
            raise HTTPException(status_code=400, detail="response required")
        new_default = brain_manager.add_default_response(response)
        return {"status": "created", **new_default}
    
    @app.delete("/api/v1/brain/defaults/{index}")
    async def delete_default(index: int):
        if not brain_manager.delete_default_response(index):
            raise HTTPException(status_code=404, detail="Default not found")
        return {"status": "deleted", "index": index}
    
    @app.get("/api/v1/brain/export/python")
    async def export_python():
        code = brain_manager.export_as_python()
        return {"format": "python", "code": code, "filename": "get_default_brain.py"}
    
    @app.get("/api/v1/brain/export/json")
    async def export_json():
        return {"format": "json", "data": brain_manager.data, "filename": "brain_data.json"}
    
    print(f"\n{'='*70}")
    print("🧠 BRAIN MANAGER SERVER")
    print(f"{'='*70}")
    print(f"✅ Server running at http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📖 Swagger docs: http://{settings.API_HOST}:{settings.API_PORT}/docs\n")
    
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, log_level="info")


# =============================================================================
# PARTE 10: MAIN ENTRY POINT
# =============================================================================

def main():
    """Entry point principal"""
    parser = argparse.ArgumentParser(
        description="ChatBot Evolution - Monolithic Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chatbot_monolith.py --mode cli        CLI mode (interactive)
  python chatbot_monolith.py --mode api        API REST mode (chat endpoint)
  python chatbot_monolith.py --mode brain      Brain Manager Server (pattern CRUD)
  python chatbot_monolith.py --help            Show help
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["cli", "api", "brain"],
        default="cli",
        help="Modo de ejecución (default: cli)",
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "cli":
            run_cli()
        elif args.mode == "api":
            run_api()
        elif args.mode == "brain":
            run_brain_server()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
