# Arquitectura: De Monolito a SaaS Modular

## Estado Actual (Fase 1: Refactorización)

### Estructura del Repositorio

```
/chatbot
├── chatbot_monolitic/              # Monolito refactorizado
│   ├── chatbot_core/               # 📦 NUEVA LIBRERÍA MODULAR
│   │   ├── __init__.py
│   │   ├── settings/               # Configuración centralizada
│   │   ├── nlp/                    # NLP (Pattern, Tokenizer, Embeddings)
│   │   ├── actor/                  # Orquestador de respuestas
│   │   ├── storage/                # Persistencia (conversaciones)
│   │   ├── llm/                    # LLM Providers (OpenAI, Ollama)
│   │   ├── brain_manager/          # Gestor de patrones CRUD
│   │   └── utils/                  # Utilidades
│   ├── chatbot_monolith.py         # 🚀 LAUNCHER FINO (CLI/API/Brain)
│   ├── brain_data.json             # Patrones persistidos
│   ├── conversations.json          # Historial de conversaciones
│   └── setup.py                    # setuptools para instalación
│
├── core_chat_service/              # 🎯 NUEVA API REST DEDICADA
│   ├── app/
│   │   ├── config/                 # Configuración de la app
│   │   ├── models/                 # Schemas Pydantic
│   │   ├── services/               # Lógica de negocio (TenantService)
│   │   └── api/                    # Rutas FastAPI
│   ├── main.py                     # Aplicación FastAPI
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
└── venv/                           # Entorno virtual
```

## Componentes Principales

### 1. **chatbot_core/** - Librería Modular

Una librería Python reutilizable que encapsula toda la lógica del chatbot:

#### Módulos:

- **settings/** - Configuración centralizada
  - Manejo de environment variables
  - Valores por defecto

- **nlp/** - Natural Language Processing
  - `PatternEngine`: Matching de patrones basado en regex
  - `Tokenizer`: Tokenización de texto
  - `PronounTranslator`: Traducción de pronombres
  - `EmbeddingService`: Embeddings semánticos (opcional)

- **actor/** - Orquestador
  - `Actor`: Procesa input, matchea patrones, genera respuestas
  - `Response`: Estructura de respuesta

- **storage/** - Persistencia
  - `SimpleConversationStorage`: JSON-based (actual)
  - Extensible a BD (future)

- **llm/** - LLM Fallback
  - `LLMProvider`: Interfaz abstracta
  - `OpenAIProvider`: Integración con GPT
  - `OllamaProvider`: Integración con modelos locales
  - `LLMFallback`: Orquestador de providers

- **brain_manager/** - Gestor de Patrones
  - CRUD de patrones
  - Export/Import
  - Search

### 2. **chatbot_monolith.py** - Launcher Fino

Archivo de entrada que utiliza `chatbot_core`:

```bash
python chatbot_monolith.py --mode cli      # CLI interactivo
python chatbot_monolith.py --mode api      # API multi-tenant simple
python chatbot_monolith.py --mode brain    # Brain Manager API
```

**Ventajas:**
- Thin wrapper alrededor de chatbot_core
- Mantiene la retrocompatibilidad
- Facilita testing

### 3. **core_chat_service/** - API REST Dedicada

Servicio FastAPI especializado para exposición de API multi-tenant:

- **TenantService**: Gestiona instancias de Actor por tenant
- **Endpoints**: Health, Chat, History, Stats
- **Schemas**: Validación con Pydantic
- **Storage aislado**: Conversations por tenant

## Flujo de Integración

```
┌─────────────────────────────────────────────────────────────┐
│  Cliente (Browser, Mobile, otro servicio)                   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  core_chat_service/main.py (FastAPI)                        │
│  - Routes: /health, /api/v1/chat/{tenant_id}, ...          │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  TenantService (app/services/tenant_service.py)             │
│  - Gestiona instancias por tenant                            │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  chatbot_core (Librería modular)                             │
│  ├─ Actor.process() - Procesa mensaje                        │
│  ├─ SimpleConversationStorage - Guarda historial            │
│  ├─ NLP Engine - Matching de patrones                       │
│  └─ BrainManager - Gestión de patrones                      │
└──────────────────────────────────────────────────────────────┘
```

## Transición: Monolito → Modular

### Antes (Monolito)

```python
# TODO en chatbot_monolith.py
class Settings: ...
class PatternEngine: ...
class Tokenizer: ...
class Actor: ...
class SimpleConversationStorage: ...
# ... 1000+ líneas en un solo archivo
```

### Después (Modular)

```python
# chatbot_monolith.py (launcher fino)
from chatbot_core import (
    Actor, SimpleConversationStorage, get_default_brain, settings
)

def run_cli():
    pattern_responses, default_responses = get_default_brain()
    actor = Actor(pattern_responses, default_responses)
    storage = SimpleConversationStorage()
    # ... 50 líneas
```

## Fase 2: Evolution a Agent Platform

### Visión Futura

```
┌─────────────────────────────────────────────────────────────┐
│  Agent Gateway (Punto de entrada)                           │
│  - Autenticación & Rate Limiting                            │
│  - Request routing                                          │
└────────┬────────────────────────────────────────────────────┘
         │
         ├──────────────────────────────────────────────────────┐
         │                                                        │
         ▼                                                        ▼
    ┌─────────────────┐                              ┌──────────────────┐
    │ Chat Service    │                              │ Agent Orchestrator
    │ (core_chat)     │                              │ (nuevo)
    └─────────────────┘                              └────┬─────────────┘
                                                          │
                                                          ├──► Brain Manager
                                                          ├──► Tool Executor
                                                          ├──► LLM Gateway
                                                          └──► Memory Service
```

### Componentes Nuevos (Fase 2)

1. **Agent Orchestrator**
   - Orquesta rules, brains, LLMs, herramientas externas
   - Ejecuta workflows (secuencias de pasos)

2. **Tool Executor**
   - Ejecuta herramientas externas (APIs, DB queries, etc.)
   - Plugins system

3. **LLM Gateway**
   - Centraliza acceso a LLMs
   - Load balancing entre providers
   - Fallback inteligente

4. **Memory Service**
   - Contexto de conversación persistente
   - Embedding-based retrieval

5. **Rules Engine**
   - Define lógica condicional
   - Integração con Brain

## Decisiones de Arquitectura

### 1. Modularidad
✅ Cada componente responsable de una función
✅ Bajo acoplamiento
✅ Fácil testing

### 2. Multi-tenancy
✅ TenantService aísla instancias
✅ Storage separado por tenant
✅ Preparado para BD multi-tenant

### 3. Extensibilidad
✅ LLMProvider como interfaz abstracta
✅ brain_manager permite CRUD + export

### 4. API-First
✅ core_chat_service expone SOLO API
✅ Schemas validados con Pydantic
✅ FastAPI → documentación automática

## Instalación y Setup

### Opción 1: Desarrollo Local

```bash
# Instalar chatbot_core en modo editable
cd chatbot_monolitic
pip install -e .

# Instalar core_chat_service
cd ../core_chat_service
pip install -r requirements.txt

# Exportar path para que se encuentren los módulos
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../chatbot_monolitic"
```

### Opción 2: Con setup.py (Recomendado)

```bash
cd chatbot_monolitic
pip install -e .  # Instala chatbot_core

cd ../core_chat_service
pip install -r requirements.txt
python main.py
```

## Ejecución

### CLI (legacy, pero funcional)
```bash
cd chatbot_monolitic
python chatbot_monolith.py --mode cli
```

### API FastAPI (nuevo)
```bash
cd core_chat_service
python main.py
# O: uvicorn main:app --reload --port 8001
```

### Brain Manager API
```bash
cd chatbot_monolitic
python chatbot_monolith.py --mode brain
```

## Testing

```bash
# Test de chatbot_core
cd chatbot_monolitic
pytest tests/

# Test de core_chat_service
cd ../core_chat_service
pytest tests/
```

## Próximos Pasos

1. ✅ Refactorización a librería modular (HECHO)
2. ✅ API REST multi-tenant (HECHO)
3. ⏳ BD PostgreSQL para persistencia
4. ⏳ Autenticación JWT para tenants
5. ⏳ Agent Orchestrator
6. ⏳ Tool Executor con plugins
7. ⏳ Memory Service con embeddings

## Beneficios de esta Arquitectura

| Aspecto | Anterior | Ahora |
|---------|----------|-------|
| Reutilización | Copiar-pegar | Librería modular |
| Testing | Complejo | Por módulo |
| Escalabilidad | Limitada | Multi-tenant |
| Extensión | Monolito crece | Plugins/services |
| Deployment | Un solo binario | Servicios independientes |
| Mantenibilidad | Difícil | Separation of concerns |

## Conclusión

La refactorización a `chatbot_core` + `core_chat_service` prepara el terreno para una evolución ordenada hacia una plataforma SaaS modular, sin perder retrocompatibilidad con el launcher monolítico.

**Arquitectura escalable, mantenible, y lista para crecer.** 🚀
