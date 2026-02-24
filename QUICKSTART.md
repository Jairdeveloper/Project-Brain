# 🚀 Quick Start Guide

## Visión General de la Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│  USUARIOS (Web, Mobile, Sistemas Externos)                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌──────────────────┐      ┌──────────────────┐
        │   CLI (dev)      │      │   API (prod)     │
        │  chatbot_monolith│      │ core_chat_service│
        │  --mode cli      │      │  (FastAPI)       │
        └────────┬─────────┘      └────────┬─────────┘
                 │                          │
                 └──────────┬───────────────┘
                            │
                            ▼
                 ┌──────────────────────────┐
                 │   chatbot_core (lib)     │
                 │                          │
                 │  ├─ NLP (Pattern Match)  │
                 │  ├─ Actor (Orchestrator) │
                 │  ├─ Storage              │
                 │  ├─ LLM Providers        │
                 │  └─ Brain Manager        │
                 └──────────────────────────┘
```

## 5 Minutos: Setup Inicial

### Paso 1: Prerequisitos
```bash
# Windows, macOS, ou Linux
python --version        # >= 3.8

# CD al directorio raiz del proyecto
cd /path/to/chatbot
```

### Paso 2: Instalar librería chatbot_core
```bash
cd chatbot_monolitic
pip install -e .

# Verifíca
python -c "from chatbot_core import Actor; print('✅ OK')"
```

### Paso 3: Instalar core_chat_service
```bash
cd ../core_chat_service
pip install -r requirements.txt
```

### Paso 4: Validar todo
```bash
cd ..
python validate_refactoring.py
# Resultado esperado: ✅ ¡REFACTORIZACIÓN EXITOSA!
```

## 10 Minutos: Primer Chat

### Opción A: CLI Interactivo

```bash
cd chatbot_monolitic
python chatbot_monolith.py --mode cli
```

Ejemplo:
```
> Hola, ¿cómo estás?
Bot: ¡Hola! Me va bien, ¿y a ti?
> Tengo un día genial
Bot: That's interesting, tell me more
> (quit)
Bye!
```

### Opción B: API REST

**Terminal 1:**
```bash
cd core_chat_service
python main.py
# Esperado: ✅ API running at http://0.0.0.0:8001
```

**Terminal 2:**
```bash
# Test health check
curl http://localhost:8001/health

# Resultado:
# {"status":"ok","version":"1.0","service":"core-chat-service"}
```

**Terminal 3 (Chat):**
```bash
# POST /api/v1/chat/{tenant_id}
curl -X POST http://localhost:8001/api/v1/chat/acme \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello world"}'

# Resultado:
# {
#   "tenant_id": "acme",
#   "session_id": "abc123",
#   "message": "Hello world",
#   "response": "Hi there! How can I help?",
#   "confidence": 0.9,
#   "source": "pattern",
#   "pattern_matched": true
# }
```

## Swagger UI - Documentación Interactiva

Con la API corriendo, visita:

**`http://localhost:8001/docs`**

Desde aquí puedes:
- 📖 Ver todos los endpoints
- 🧪 Testear endpoints directamente
- 📋 Ver schemas de request/response

## 3 Modos de Ejecución

### Modo 1: CLI (Desarrollo Local)
```bash
python chatbot_monolith.py --mode cli
```
✅ Interactivo
✅ Para desarrollo/debugging
❌ No multi-tenant
❌ No REST

### Modo 2: API REST (Recomendado para Producción)
```bash
# Opción A
cd core_chat_service && python main.py

# Opción B
cd core_chat_service && uvicorn main:app --host 0.0.0.0 --port 8001
```
✅ Multi-tenant
✅ REST API
✅ Documentación automática
✅ Production-ready

### Modo 3: Brain Manager API (Mantenimiento de Patrones)
```bash
python chatbot_monolith.py --mode brain
```
✅ CRUD de patrones
✅ Search/Export
❌ No es para chat directo

## Estructura de Directorios Explicada

### `chatbot_monolitic/chatbot_core/` - La Librería Modular

```
chatbot_core/                 # Librería reutilizable
├── settings/                 # Config centralizada
│   └── config.py            # Settings class
├── nlp/                      # Natural Language Processing
│   ├── pattern.py           # PatternEngine (regex-based matching)
│   ├── tokenizer.py         # Tokenizer (text splitting)
│   ├── pronoun_translator.py # PronounTranslator
│   └── embedding.py         # EmbeddingService (optional)
├── actor/                    # Orquestador
│   └── actor.py             # Actor class
├── storage/                  # Persistencia
│   └── conversation.py      # SimpleConversationStorage
├── llm/                      # LLM Integration
│   ├── providers.py         # OpenAIProvider, OllamaProvider
│   └── fallback.py          # LLMFallback
├── brain_manager/            # Pattern Management
│   └── manager.py           # BrainManager class
└── utils/                    # Utilities
    └── logging.py           # get_logger()
```

### `core_chat_service/` - API REST Moderno

```
core_chat_service/            # Servicio FastAPI
├── app/
│   ├── config/              # Configuration
│   │   └── settings.py      # APISettings
│   ├── models/              # Pydantic schemas
│   │   └── schemas.py       # Request/Response models
│   ├── services/            # Business logic
│   │   └── tenant_service.py # TenantService (multi-tenant)
│   └── api/                 # Routes
│       └── routes.py        # FastAPI routers
├── main.py                  # FastAPI app
├── requirements.txt         # Dependencies
└── .env.example             # Environment variables
```

## API Endpoints Principales

### Health Check
```
GET /health
```
Respuesta: `{"status": "ok", "version": "1.0", "service": "core-chat-service"}`

### Chat (Multi-tenant)
```
POST /api/v1/chat/{tenant_id}
Body: {"message": "...", "session_id": "..."}
```
Crea o recupera una sesión y procesa el mensaje

### Historial
```
GET /api/v1/history/{tenant_id}/{session_id}
```
Retorna todos los mensajes de una sesión

### Estadísticas
```
GET /api/v1/stats/{tenant_id}
```
Retorna # de sesiones y mensajes totales

## Variables de Entorno

### core_chat_service
```bash
API_HOST=0.0.0.0           # Host de escucha
API_PORT=8001              # Puerto
DEBUG=False                # Modo debug
LOG_LEVEL=INFO             # Nivel de logging
STORAGE_DIR=./data         # Directorio de datos
MAX_TENANTS=1000           # Máximo de tenants
TENANT_ISOLATION=True      # Aislar tenants
```

### chatbot_monolitic
```bash
DEBUG=False                # Modo debug
LOG_LEVEL=INFO             # Nivel de logging
API_PORT=8000              # Puerto (para launcher)
ENABLE_EMBEDDINGS=True     # Embeddings (opcional)
USE_LLM_FALLBACK=False     # LLM Fallback
OPENAI_API_KEY=sk-...      # API key OpenAI (opcional)
```

## Testing

### Verificar estructura
```bash
python validate_refactoring.py
```

### Test della librería
```bash
cd chatbot_monolitic
pytest tests/
```

### Test del servicio
```bash
cd core_chat_service
pytest tests/
```

## Troubleshooting

### "No module named 'chatbot_core'"
```bash
# Solución 1: Instalar con setup.py
cd chatbot_monolitic && pip install -e .

# Solución 2: Agregar al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/chatbot_monolitic"
```

### API no responde en localhost:8001
```bash
# Verifíca que el puerto esté disponible
# Windows
netstat -ano | findstr :8001

# macOS/Linux
lsof -i :8001

# Cambia el puerto en .env
API_PORT=8002
```

### Import error: "cannot import name 'Actor'"
```bash
# Verifíca que chatbot_core está en el path
python -c "from chatbot_core import Actor; print('OK')"

# Si no funciona, lista los imports
python -c "import sys; print(sys.path)"
```

## Próximos Pasos Recomendados

1. **Explorar la librería**
   - Abre `chatbot_monolitic/chatbot_core/__init__.py`
   - Entiende los módulos principales

2. **Probar la API**
   - Abre `http://localhost:8001/docs`
   - Prueba los endpoints con ejemplos

3. **Crear tests**
   - Agrega tests en `chatbot_monolitic/tests/`
   - Agrega tests en `core_chat_service/tests/`

4. **Extender funcionalidad**
   - Crear nuevos Providers en `llm/`
   - Agregar herramientas en `brain_manager/`

## Documentación Completa

- **ARCHITECTURE.md** - Descripción completa de la arquitectura
- **REFACTORING_SUMMARY.md** - Resumen del trabajo realizado
- **core_chat_service/README.md** - Guía específica de la API

## Status del Proyecto

| Componente | Status | Notas |
|-----------|--------|-------|
| chatbot_core librería | ✅ Completado | Modular, reutilizable |
| CLI launcher | ✅ Completado | Python CLI, backwards-compatible |
| API REST | ✅ Completado | FastAPI, multi-tenant |
| Documentación | ✅ Completado | Swagger, ARCHITECTURE.md |
| Tests | 🟡 Parcial | Necesita cobertura |
| BD Postgres | ⏳ Planeado | Fase 2 |
| Autenticación | ⏳ Planeado | Fase 2 |
| Agent Orchestrator | ⏳ Planeado | Fase 3 |

---

**¿Listo para empezar?** Ejecuta:
```bash
cd core_chat_service && python main.py
```

**Luego accede a:** `http://localhost:8001/docs`

¡Buena suerte! 🎉
