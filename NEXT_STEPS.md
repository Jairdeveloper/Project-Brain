# 🚀 PRÓXIMOS PASOS - Guía Paso a Paso

## Fase 1: Validación Local (Ahora)

Verifica que todo funciona en tu máquina:

### Paso 1: Instalar chatbot_core como paquete
```powershell
cd c:\Users\1973b\zpa\Projects\manufacturing\chatbot
pip install -e chatbot_monolitic/
```

**Qué hace:** Instala chatbot_core en modo editable (cambios reflejados inmediatamente)

**Resultado esperado:**
```
Successfully installed chatbot-core
```

---

### Paso 2: Verificar validación nuevamente
```powershell
python validate_refactoring.py
```

**Qué hace:** Ejecuta todos los tests de estructura

**Resultado esperado:**
```
✅ Estructura: PASS
✅ Launcher: PASS
✅ Core Chat Service: PASS
✅ Imports: PASS

✅ ¡REFACTORIZACIÓN EXITOSA!
```

---

### Paso 3: Probar CLI (Modo interactivo)
```powershell
python chatbot_monolitic\chatbot_monolith.py --mode cli
```

**Qué hace:** Inicia el chatbot en modo consola interactivo

**Resultado esperado:**
```
Welcome to the Chatbot CLI!
...
> Enter your message:
```

**Prueba:** Escribe un mensaje, presiona Enter. Deberías recibir una respuesta.

---

### Paso 4: Instalar dependencias de core_chat_service
```powershell
cd core_chat_service
pip install -r requirements.txt
```

**Qué hace:** Instala FastAPI, uvicorn, pydantic, python-dotenv

**Resultado esperado:**
```
Successfully installed fastapi-0.104.1 uvicorn[standard]-0.24.0 pydantic-2.5.0 python-dotenv-1.0.0
```

---

### Paso 5: Copiar archivo .env
```powershell
copy .env.example .env
```

**Qué hace:** Crea archivo de configuración local

**Resultado esperado:** Archivo `.env` creado en `core_chat_service/`

---

### Paso 6: Probar API (FastAPI)
```powershell
# Desde core_chat_service/
python main.py
```

**Qué hace:** Inicia el servidor API en puerto 8000

**Resultado esperado:**
```
INFO:     Started server process [1234]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Luego:** Abre en navegador: http://localhost:8000/docs

---

### Paso 7: Probar Endpoint de Chat
En Swagger UI (http://localhost:8000/docs):

1. Haz click en `POST /api/v1/chat/{tenant_id}`
2. Click en "Try it out"
3. En `tenant_id`, escribe: `customer-123`
4. En `message`, escribe: `Hello!`
5. Click "Execute"

**Resultado esperado:**
```json
{
  "tenant_id": "customer-123",
  "session_id": "generated-uuid",
  "message": "Hello!",
  "response": "Hi there! 👋"
}
```

---

### Paso 8: Probar Endpoint de Historial
1. Click en `GET /api/v1/history/{tenant_id}/{session_id}`
2. Usa los mismos tenant_id y session_id del paso anterior
3. Click "Execute"

**Resultado esperado:**
```json
{
  "tenant_id": "customer-123",
  "session_id": "generated-uuid",
  "history": [
    {
      "timestamp": "2026-02-24T...",
      "user": "Hello!",
      "bot": "Hi there! 👋"
    }
  ],
  "total_messages": 1
}
```

---

## Fase 2: Primeros Cambios (Próxima Semana)

### 2.1: Crear Archivo README.md en Raíz
```powershell
# En c:\Users\1973b\zpa\Projects\manufacturing\chatbot\
```

Contenido:
```markdown
# Chatbot Modular SaaS Platform

## Quick Start

### 1. Install dependencies
pip install -e chatbot_monolitic/

### 2. Run CLI
python chatbot_monolitic/chatbot_monolith.py --mode cli

### 3. Run API
cd core_chat_service && python main.py

## Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [QUICKSTART.md](QUICKSTART.md) - 5-10 min setup
- [ROADMAP.md](ROADMAP.md) - Phase 2-6 evolution
```

---

### 2.2: Crear requirements.txt en Raíz
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

---

### 2.3: Agregar .gitignore
```
__pycache__/
*.pyc
.env
.env.local
venv/
.venv/
dist/
build/
*.egg-info/
.pytest_cache/
.mypy_cache/
.vscode/
.idea/
*.json
!.gitkeep
```

---

## Fase 3: Testing (Próximas 2 Semanas)

### 3.1: Crear tests para chatbot_core

```powershell
mkdir tests\test_chatbot_core
```

Crear `tests/test_chatbot_core/test_actor.py`:
```python
import pytest
from chatbot_core import Actor, get_default_brain

def test_actor_process_simple_message():
    actor = Actor(get_default_brain())
    response = actor.process("Hello")
    
    assert response.text is not None
    assert len(response.text) > 0
```

Crear `tests/test_chatbot_core/test_settings.py`:
```python
from chatbot_core import settings

def test_settings_loaded():
    assert settings.API_PORT == 8000
    assert settings.LOG_LEVEL == "INFO"
```

Ejecutar:
```powershell
pytest tests/test_chatbot_core/
```

---

### 3.2: Crear tests para core_chat_service

```powershell
mkdir tests\test_core_chat_service
```

Crear `tests/test_core_chat_service/test_routes.py`:
```python
from fastapi.testclient import TestClient
from core_chat_service.main import create_app

def test_health():
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_chat_endpoint():
    app = create_app()
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/chat/tenant-123",
        json={"message": "Hello"}
    )
    
    assert response.status_code == 200
    assert "response" in response.json()
```

Ejecutar:
```powershell
pytest tests/test_core_chat_service/
```

---

### 3.3: Configurar pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

---

## Fase 4: CI/CD (Semana 3)

### 4.1: Crear `.github/workflows/test.yml`
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -e chatbot_monolitic/
        cd core_chat_service && pip install -r requirements.txt
    
    - name: Run tests
      run: pytest tests/
    
    - name: Validate structure
      run: python validate_refactoring.py
```

---

## Fase 5: Producción (Semana 4-6)

### 5.1: PostgreSQL Setup
```sql
CREATE DATABASE chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
```

### 5.2: Migrar storage a SQLAlchemy
Reemplaza en `chatbot_core/storage/conversation.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class ConversationDB(Base):
    __tablename__ = "conversations"
    
    id: int = Column(Integer, primary_key=True)
    tenant_id: str = Column(String)
    session_id: str = Column(String)
    messages: str = Column(JSON)  # Serializad JSON
```

### 5.3: Agregar Autenticación JWT
```python
# En core_chat_service/app/services/auth.py
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-here"

def create_access_token(tenant_id: str):
    payload = {
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY)
        return payload["tenant_id"]
    except JWTError:
        raise HTTPException(status_code=401)
```

---

## Fase 6: Deployment (Semana 7-8)

### 6.1: Docker
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY chatbot_monolitic/ ./chatbot_monolitic/
COPY core_chat_service/ ./core_chat_service/
COPY requirements.txt .

RUN pip install -e ./chatbot_monolitic/
RUN cd core_chat_service && pip install -r requirements.txt

CMD ["python", "core_chat_service/main.py"]
```

### 6.2: Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: chatbot_db
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://chatbot_user:secure_password@db/chatbot_db
    depends_on:
      - db

volumes:
  postgres_data:
```

Ejecutar:
```powershell
docker-compose up
```

---

## ✅ Checklist de Siguientes Pasos

### Inmediato (Hoy)
- [ ] Paso 1: pip install -e chatbot_monolitic/
- [ ] Paso 2: python validate_refactoring.py
- [ ] Paso 3: Probar CLI mode
- [ ] Paso 4: pip install requirements.txt (core_chat_service)
- [ ] Paso 5: copy .env.example .env
- [ ] Paso 6-8: Probar API + endpoints

### Esta Semana
- [ ] Crear README.md raíz
- [ ] Crear requirements.txt raíz
- [ ] Crear .gitignore
- [ ] Empujar a git

### Próxima Semana (Phase 2 Testing)
- [ ] Crear tests for chatbot_core
- [ ] Crear tests for core_chat_service
- [ ] Configurar pytest
- [ ] Target: 60% coverage

### Semana 3 (CI/CD)
- [ ] Crear `.github/workflows/test.yml`
- [ ] Verificar que pasa en GitHub

### Semana 4-6 (Phase 2 Features)
- [ ] PostgreSQL + SQLAlchemy
- [ ] JWT Authentication
- [ ] Rate Limiting
- [ ] Documentar API changes

### Semana 7-8 (Deployment)
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] Deploy a staging
- [ ] Deploy a producción

---

## 📞 Preguntas Comunes

### P: ¿Dónde empiezo?
**R:** Comienza con **Paso 1-8** en "Fase 1: Validación Local"

### P: ¿Qué si falla la validación?
**R:** 
1. Verifica que estás en el directorio correcto
2. Verifica que tengas Python 3.8+
3. Lee el error específico
4. Revisa [QUICKSTART.md](QUICKSTART.md)

### P: ¿Cómo agrego un nuevo patrón?
**R:** 
1. Manual: Edita `chatbot_core/brain_manager/manager.py`
2. API: Usa POST `/api/v1/brain/patterns` (requiere Phase 2)

### P: ¿Cómo conecto a un LLM?
**R:** 
1. Edita `core_chat_service/.env`:
   ```
   USE_LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   ```
2. El Actor automáticamente usará LLM fallback

### P: ¿Cuándo viene PostgreSQL?
**R:** Phase 2, planeado para Q2 2026

---

## 📚 Referencias Rápidas

| Recurso | Ubicación | Propósito |
|---------|-----------|-----------|
| **Docs Arquitectura** | [ARCHITECTURE.md](ARCHITECTURE.md) | Diseño completo |
| **Setup Rápido** | [QUICKSTART.md](QUICKSTART.md) | 5-10 min |
| **Roadmap** | [ROADMAP.md](ROADMAP.md) | Fases 2-6 |
| **Checklist** | [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) | Todo lo completado |
| **Índice Archivos** | [FILE_INDEX.md](FILE_INDEX.md) | Dónde está cada cosa |

---

## 🎯 Meta de Esta Semana

```
□ Validación local (Fase 1 Paso 1-8)
□ Inicializar git + push
□ README.md + .gitignore en raíz

Tiempo estimado: 2-3 horas
```

---

**Éxito! Comienza con el Paso 1 arriba ⬆️**
