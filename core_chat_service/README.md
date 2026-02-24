# Core Chat Service

API REST multi-tenant para chat que utiliza la librería modular `chatbot_core`.

## Estructura

```
core_chat_service/
├── app/
│   ├── __init__.py
│   ├── config/              # Configuración
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── models/              # Modelos Pydantic (request/response)
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/            # Lógica de negocios
│   │   ├── __init__.py
│   │   └── tenant_service.py
│   └── api/                 # Rutas
│       ├── __init__.py
│       └── routes.py
├── main.py                  # Aplicación FastAPI
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## Características

- **Multi-tenant**: Cada tenant tiene su propia instancia de Actor y almacenamiento
- **REST API**: Endpoints claros y documentados con Swagger
- **Aislamiento**: Las conversaciones se almacenan separadamente por tenant
- **Health Check**: Endpoint `/health` para monitoreo
- **Historial**: Acceso al historial de conversaciones por sesión
- **Estadísticas**: Estadísticas de uso por tenant

## Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Asegurar que chatbot_core está disponible

Opción A: Agregar el path a `PYTHONPATH`:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/chatbot_monolitic"
python main.py
```

Opción B: Instalar chatbot_core localmente:
```bash
cd ../chatbot_monolitic
pip install -e .  # Requiere setup.py
```

## Uso

### Iniciar el servidor

```bash
python main.py
```

o con uvicorn directamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Swagger UI

La documentación interactiva estará disponible en:
- `http://localhost:8001/docs` (Swagger UI)
- `http://localhost:8001/redoc` (ReDoc)

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0",
  "service": "core-chat-service"
}
```

### Chat (Multi-tenant)

```bash
POST /api/v1/chat/{tenant_id}
Content-Type: application/json

{
  "message": "Hola, ¿cómo estás?",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "tenant_id": "tenant-1",
  "session_id": "abc123",
  "message": "Hola, ¿cómo estás?",
  "response": "¡Hola! Me va bien, ¿y a ti?",
  "confidence": 0.9,
  "source": "pattern",
  "pattern_matched": true
}
```

## Autenticación JWT (Fase 2)

La API ahora soporta autenticación JWT para mayor seguridad y aislamiento de tenants.

### Registro de Tenant

```bash
POST /auth/register
Content-Type: application/json

{
  "tenant_id": "acme-corp",
  "password": "SecurePassword123",
  "name": "ACME Corporation"
}
```

Response:
```json
{
  "status": "success",
  "message": "Tenant 'acme-corp' registrado exitosamente",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "tenant_id": "acme-corp",
    "expires_in": 86400
  }
}
```

### Login

```bash
POST /auth/login
Content-Type: application/json

{
  "tenant_id": "acme-corp",
  "password": "SecurePassword123"
}
```

Response: (igual que registro)

### Uso del Token

Agrega el token en el header `Authorization`:

```bash
curl -X GET http://localhost:8001/api/v1/chat/acme-corp \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### Tenant Demo

Para testing, existe un tenant demo pre-configurado:
- **tenant_id**: `demo`
- **password**: `demo1234`

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "demo",
    "password": "demo1234"
  }'
```

### Session History

```bash
GET /api/v1/history/{tenant_id}/{session_id}
```

Response:
```json
{
  "tenant_id": "tenant-1",
  "session_id": "abc123",
  "history": [
    {
      "timestamp": "2024-02-24T10:00:00",
      "user": "Hola",
      "bot": "¡Hola! ¿Cómo estás?"
    }
  ],
  "total_messages": 1
}
```

### Tenant Stats

```bash
GET /api/v1/stats/{tenant_id}
```

Response:
```json
{
  "tenant_id": "tenant-1",
  "app_name": "Core Chat Service",
  "version": "1.0",
  "total_sessions": 5,
  "total_messages": 42
}
```

## Variables de Entorno

```bash
# Configuración de la API
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=False
LOG_LEVEL=INFO

# Multi-tenant
MAX_TENANTS=1000
TENANT_ISOLATION=True

# Almacenamiento
STORAGE_DIR=./data
```

## Próximos Pasos

Este es el inicio de la evolución hacia una plataforma SaaS modular:

1. **Persistencia multi-tenant**: En lugar de JSON, usar una BD (PostgreSQL)
2. **Autenticación**: Agregar JWT/OAuth para tenants
3. **Rate limiting**: Proteger endpoints con límites de velocidad
4. **Webhooks**: Notificar eventos a sistemas externos
5. **Brain Management API**: Servicio dedicado para gestionar patrones

## Ver también

- [chatbot_core](../chatbot_monolitic/chatbot_core/) - Librería modular subyacente
- [chatbot_monolith.py](../chatbot_monolitic/chatbot_monolith.py) - Launcher CLI/API monolítico
