# 🗺️ Roadmap: Evolución hacia Agent Platform

## Estado Actual (Fase 1 ✅)

```
✅ Librería modular chatbot_core
✅ Launcher CLI fino
✅ API REST multi-tenant
✅ Documentación completa
```

## Fase 2: Persistencia Multi-tenant & Escalabilidad (Q2 2026)

### 2.1 Base de Datos PostgreSQL

**Objetivo:** Reemplazar JSON con BD relacional

```sql
-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    session_id VARCHAR(255),
    user_message TEXT,
    bot_response TEXT,
    confidence FLOAT,
    source VARCHAR(50),
    pattern_matched BOOLEAN,
    created_at TIMESTAMP
);

-- Patterns (Brain)
CREATE TABLE patterns (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    pattern JSONB,
    response JSONB,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Implementación:**
- SQLAlchemy ORM en `chatbot_core/storage/`
- Migrations con Alembic
- Connection pooling

### 2.2 Autenticación & Autorización

**JWT para API:**
```python
# app/auth/jwt.py
from fastapi import Depends, HTTPException
from jose import JWTError, jwt

async def get_current_tenant(token: str = Depends(oauth2_scheme)):
    """Verifica JWT y retorna tenant_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id: str = payload.get("sub")
        if tenant_id is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)
    return tenant_id
```

**Endpoints de Auth:**
- `POST /auth/register` - Registra nuevo tenant
- `POST /auth/login` - Login y JWT token
- `POST /auth/refresh` - Refresh token

### 2.3 Rate Limiting

```python
# middleware/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/chat/{tenant_id}")
@limiter.limit("100/minute")  # 100 requests/min por tenant
async def chat(tenant_id: str, request: ChatRequest):
    ...
```

## Fase 3: Brain Service Independiente (Q3 2026)

### Separar en Microservicio

```
Brain Service (Puerto 8002)
├── GET /patterns
├── POST /patterns
├── PUT /patterns/{id}
├── DELETE /patterns/{id}
├── POST /patterns/search
├── POST /patterns/export
└── POST /patterns/import
```

**Estructura:**
```
brain_service/
├── app/
│   ├── api/
│   │   └── patterns.py
│   ├── models/
│   ├── services/
│   └── db/
├── main.py
└── requirements.txt
```

**Integración con Chat Service:**
```python
# core_chat_service/app/services/brain_client.py
class BrainServiceClient:
    def __init__(self, brain_service_url: str):
        self.base_url = brain_service_url
    
    async def get_patterns(self, tenant_id: str):
        """Obtiene patrones desde Brain Service"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/patterns",
                headers={"X-Tenant-ID": tenant_id}
            )
        return resp.json()
```

## Fase 4: Agent Orchestrator (Q4 2026)

### Orquestación de Agentes

```
Agent Orchestrator Service (Puerto 8003)
├── GET /agents
├── POST /agents/{agent_id}/run
├── GET /agents/{agent_id}/status
├── POST /workflows
├── GET /workflows/{workflow_id}
└── POST /workflows/{workflow_id}/execute
```

**Conceptos clave:**

```python
# Models
class Agent:
    id: str
    name: str
    description: str
    brain_id: str          # Referencia a Brain
    tools: List[Tool]      # Herramientas
    llm_provider: str      # "openai", "ollama", etc.
    parameters: Dict       # Config

class Tool:
    id: str
    name: str
    description: str
    execute_url: str       # Endpoint para ejecutar
    schema: Dict           # JSON schema de inputs

class Workflow:
    id: str
    name: str
    steps: List[WorkflowStep]

class WorkflowStep:
    id: str
    agent_id: str
    inputs: Dict
    outputs: Dict
    next_step: Optional[str]
```

**Ejemplo de orquestación:**

```
User input
    ↓
├─→ Agent 1 (Intent Recognition)
    ├─→ "Schedule meeting"
        ↓
    ├─→ Agent 2 (Calendar Tool)
        ├─→ Execute: GET /calendar/availability
        ├─→ Execute: POST /calendar/create-event
        ↓
    └─→ Agent 3 (Response Generation)
        ├─→ LLM: "Meeting scheduled for..."
            ↓
        └─→ Response
```

### Event-Driven Architecture

```python
# events.py
class AgentStartedEvent:
    agent_id: str
    timestamp: datetime

class AgentCompletedEvent:
    agent_id: str
    result: Dict
    timestamp: datetime

class WorkflowStartedEvent:
    workflow_id: str
    timestamp: datetime
```

## Fase 5: Memory Service (Q1 2027)

### Contexto Persistente

```python
# memory_service/
class MemoryService:
    async def save_memory(self, tenant_id: str, session_id: str, 
                         key: str, value: Any):
        """Guarda información en memoria"""
        
    async def get_memory(self, tenant_id: str, session_id: str, 
                        key: str) -> Any:
        """Recupera información de memoria"""
    
    async def semantic_search(self, tenant_id: str, session_id: str,
                              query: str) -> List[Dict]:
        """Búsqueda semántica en contexto"""
```

**Implementación con embeddings:**

```python
class SemanticMemory:
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        self.vector_store = PgVector()  # PostgreSQL + pgvector
    
    async def remember(self, session_id: str, text: str):
        """Guarda texto + embeddings"""
        embedding = self.embedding_service.embed(text)
        await self.vector_store.upsert({
            "session_id": session_id,
            "text": text,
            "embedding": embedding
        })
    
    async def recall(self, session_id: str, query: str) -> List[str]:
        """Recupera contexto similar"""
        query_embedding = self.embedding_service.embed(query)
        results = await self.vector_store.similarity_search(
            query_embedding, k=5
        )
        return results
```

## Fase 6: LLM Gateway (Q2 2027)

### Centralización de LLMs

```python
# llm_gateway/
class LLMGateway:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "ollama": OllamaProvider(),
            "anthropic": AnthropicProvider(),
        }
        self.fallback_chain = [
            "openai",
            "anthropic",
            "ollama",
        ]
    
    async def generate(self, prompt: str, 
                      fallback: bool = True) -> str:
        """Genera respuesta con fallback automático"""
        for provider_name in self.fallback_chain:
            provider = self.providers[provider_name]
            try:
                return await provider.generate(prompt)
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                if not fallback:
                    raise
        raise Exception("All LLM providers failed")
```

**Endpoints:**
```
GET /api/llms                    # Lista providers disponibles
POST /api/llms/{provider}/generate
GET /api/llms/stats              # Estadísticas de uso
```

## Infraestructura & DevOps

### Docker Compose (Phase 2)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
  
  redis:
    image: redis:7
  
  chatbot-core:
    build: ./chatbot_monolitic
    depends_on:
      - postgres
  
  chat-service:
    build: ./core_chat_service
    depends_on:
      - postgres
      - redis
    ports:
      - "8001:8001"
  
  brain-service:
    build: ./brain_service
    depends_on:
      - postgres
    ports:
      - "8002:8002"
```

### Kubernetes Deployment (Phase 3)

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: chatbot

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-service
  namespace: chatbot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-service
  template:
    metadata:
      labels:
        app: chat-service
    spec:
      containers:
      - name: chat-service
        image: chatbot/chat-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
```

## Testing & Quality Assurance

### Test Coverage Targets

| Fase | Unit | Integration | E2E |
|------|------|-------------|-----|
| 1 | 60% | 40% | 20% |
| 2 | 75% | 60% | 40% |
| 3 | 80% | 70% | 60% |
| 4+ | 85% | 80% | 80% |

### Performance Targets

| Métrica | Target | Actual |
|---------|--------|--------|
| Chat latency | < 200ms | TBD |
| Throughput | 1000 req/s | TBD |
| Uptime | 99.9% | TBD |
| DB query time | < 50ms | TBD |

## Timeline Estimado

```
2026
├─ Q2: Fase 2 (PostgreSQL, Auth, Rate Limit)
├─ Q3: Fase 3 (Brain Service)
├─ Q4: Fase 4 (Agent Orchestrator)
└─ Q1 2027: Fase 5 (Memory Service)

2027
├─ Q2: Fase 6 (LLM Gateway)
├─ Q3: Cloud deployment (AWS, GCP, Azure)
└─ Q4: Enterprise features (SAML, SSO, Audit)
```

## Budget & Resources Estimado

| Fase | Dev Hours | Infrastructure |
|------|-----------|-----------------|
| 2 | 200h | $500/mes |
| 3 | 150h | $800/mes |
| 4 | 300h | $1200/mes |
| 5 | 200h | $1000/mes |
| 6 | 150h | $800/mes |

## Riesgos & Mitigación

| Riesgo | Impacto | Mitigation |
|--------|---------|-----------|
| Escalabilidad BD | Alto | Partitioning, caching |
| Latencia LLM | Alto | Caching, pre-computation |
| Dependencias 3rd party | Medio | Abstracciones, fallbacks |
| Complejidad arquitectura | Medio | Documentación, testing |

## Conclusión

Roadmap propuesto transforma el proyecto en una **plataforma SaaS modular escalable**:

- **Fase 2:** Producción-ready
- **Fase 3:** Escalabilidad
- **Fase 4:** Inteligencia
- **Fase 5:** Memoria
- **Fase 6:** Multi-LLM

**Visión final:** Una Agent Platform que orquesta múltiples servicios especializados para entregar capacidades de IA avanzadas.

---

**Revisión recomendada:** Cada trimestre

**Última actualización:** 24 de febrero, 2026
