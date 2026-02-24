# 🔐 Fase 2: Autenticación JWT & Seguridad

## Estado: ✅ Completado (Componente 1 de 3)

### Componentes de Fase 2

```
Componente 1: ✅ Autenticación JWT (COMPLETADO)
Componente 2: ⏳ PostgreSQL + SQLAlchemy (Próximo)
Componente 3: ⏳ Rate Limiting (Próximo)
```

---

## 1. Autenticación JWT Implementada

### Cambios en la Arquitectura

```
Antes (Fase 1):
  Cualquiera puede acceder a los endpoints
  tenant_id se pasa por URL, sin validación
  
Después (Fase 2):
  tenant_id extraído del JWT token
  Validación de credenciales requerida
  Tokens expiran en 24 horas
  Hash de contraseña (SHA256 en Fase 2.1, bcrypt después)
```

### Archivos Creados

```
core_chat_service/app/
├── auth/                           ← Nuevo módulo
│   ├── __init__.py                 Exporta todo
│   ├── jwt.py                      Lógica JWT + password hash
│   ├── schemas.py                  Modelos Pydantic (TenantRegister, Token, etc)
│   └── dependencies.py             Dependency injection para FastAPI
├── db/                             ← Nuevo módulo (temporal, para Fase 2/3)
│   ├── __init__.py
│   └── tenants.py                  In-memory storage de tenants
└── api/routes.py                   ← Actualizado con endpoints /auth
```

### Nuevas Dependencias

```txt
python-jose[cryptography]>=3.3.0   # JWT handling
passlib[bcrypt]>=1.7.4             # Password hashing (futuro)
pyjwt>=2.8.0                       # JWT parsing
python-multipart>=0.0.5            # Form data parsing
```

---

## 2. Endpoints de Autenticación

### POST /auth/register

**Propósito:** Registra un nuevo tenant

**Request:**
```json
{
  "tenant_id": "acme-corp",
  "password": "MySecurePassword123",
  "name": "ACME Corporation (opcional)"
}
```

**Response (201 Created):**
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

**Errores:**
```json
{
  "status": "error",
  "detail": "Tenant 'acme-corp' ya existe"
}
```

---

### POST /auth/login

**Propósito:** Login y obtener JWT token

**Request:**
```json
{
  "tenant_id": "acme-corp",
  "password": "MySecurePassword123"
}
```

**Response (200 OK):** (igual que /register)

**Errores:**
```json
{
  "status": "error",
  "detail": "Credenciales inválidas"
}
```

---

## 3. Uso del Token

### Header Authorization

Todos los endpoints de chat ahora requieren JWT token:

```bash
# Opción A: Bearer token
curl -X POST http://localhost:8001/api/v1/chat/acme-corp \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Opción B: Swagger UI
# 1. Abre http://localhost:8001/docs
# 2. Click en "Authorize"
# 3. Pega el token en "value"
# 4. Prueba los endpoints
```

### Validación Automática

FastAPI valida automáticamente el token en cada request:

```python
# En routes.py
@router.post("/api/v1/chat/{tenant_id}")
async def chat_endpoint(
    tenant_id: str,
    request: ChatRequest,
    current_tenant: str = Depends(get_current_tenant)  # ← Validación JWT
):
    # El tenant_id del token debe coincidir con la URL
    if current_tenant != tenant_id:
        raise HTTPException(401, "Forbidd: Token doesn't match URL tenant")
```

---

## 4. Flujo de Autenticación (Flow Diagram)

```
Usuario
   ↓
[1] POST /auth/register
   ├─ Valida tenant_id único
   ├─ Hash password
   ├─ Guarda en memory (en Fase 2.1: PostgreSQL)
   └─ Retorna JWT token
   ↓
[2] Usuario guarda token (ej: localStorage en frontend)
   ↓
[3] POST /api/v1/chat/{tenant_id}
   ├─ Header: Authorization: Bearer {token}
   ├─ FastAPI valida JWT
   ├─ Extrae tenant_id del token
   └─ Procesa chat si todo es válido
   ↓
[4] Response con resultado del chat
```

---

## 5. Estructura de JWT Token

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "acme-corp",           // tenant_id
  "exp": 1708889040,            // Expiration (24 horas después del issue)
  "iat": 1708802640             // Issued at
}
```

**Signature:** HMAC-SHA256(SECRET_KEY)

---

## 6. Almacenamiento de Tenants (Temporal)

### En Memoria (Fase 2)

```python
# app/db/tenants.py
_tenants_db = {
    "demo": {
        "tenant_id": "demo",
        "password_hash": "sha256...",
        "name": "Demo Tenant",
        "active": True
    }
}
```

**Limitaciones:**
- ❌ Persiste solo mientras corra la app
- ❌ No sirve en multi-proceso
- ❌ Pierde datos al reiniciar

**Transición a Fase 2.1 (PostgreSQL):**
```python
# Reemplazar _tenants_db con tabla SQL
from sqlalchemy import Column, String, Boolean, DateTime

class Tenant(Base):
    __tablename__ = "tenants"
    
    tenant_id = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## 7. Seguridad (Estado Actual vs Futuro)

### Actual (Fase 2)

| Aspecto | Acción |Status |
|---------|--------|--------|
| **Password Hashing** | SHA256 | ⚠️ Básico, OK para demo |
| **Token Storage** | Memory | ⚠️ Reset al reiniciar |
| **Secret Key** | Hardcoded | ⚠️ CAMBIAR EN PRODUCCIÓN |
| **HTTPS** | No | ❌ Usar en prod |
| **Rate Limiting** | No | ❌ Será Componente 3 |
| **Refresh Tokens** | No | ❌ Planeado Fase 2.5 |

### Mejoras Planeadas

**Fase 2.1 (PostgreSQL):**
- ✅ Bcrypt para hashing de password
- ✅ Persistencia en BD

**Fase 2.2 (Seguridad):**
- ✅ Read SECRET_KEY from env vars
- ✅ HTTPS requirement
- ✅ Refresh token mechanism

**Fase 2.3 (Rate Limiting):**
- ✅ slowapi library
- ✅ Límites por tenant
- ✅ Throttling automático

---

## 8. Testing Manual

### Script de Test (PowerShell)

```powershell
# 1. Registrar nuevo tenant
$register_body = @{
    tenant_id = "test-company"
    password = "TestPass123!"
    name = "Test Company Inc"
} | ConvertTo-Json

$register = Invoke-WebRequest -Uri "http://localhost:8001/auth/register" `
  -Method POST `
  -Body $register_body `
  -ContentType "application/json" `
  -UseBasicParsing

$token = (ConvertFrom-Json -InputObject $register.Content).data.access_token
Write-Host "Token: $token"

# 2. Usar token para chat
$chat_body = @{
    message = "Hello"
} | ConvertTo-Json

$chat = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/chat/test-company" `
  -Method POST `
  -Headers @{"Authorization" = "Bearer $token"} `
  -Body $chat_body `
  -ContentType "application/json" `
  -UseBasicParsing

$chat.Content | ConvertFrom-Json | Format-List
```

---

## 9. Próximos Pasos

### Fase 2.2: PostgreSQL (próxima semana)

```
1. Crear DB schema con Alembic
2. Migrar tenants a PostgreSQL
3. Agregar sesiones y conversaciones
4. Implementar soft-deletes
```

### Fase 2.3: Rate Limiting (siguiente)

```
1. Instalar slowapi
2. Limiter por tenant_id
3. Limiter por IP (fallback)
4. Configurar límites por endpoint
```

---

## 10. Características Completadas

✅ JWT generation con HS256
✅ JWT validation y extracción de tenant_id
✅ Password hashing (SHA256)
✅ Endpoints /auth/register y /auth/login
✅ Dependency injection para validar tokens
✅ In-memory tenant storage
✅ Error handling (401 Unauthorized)
✅ Documentación Swagger actualizada
✅ Tenant demo preconfigur

ado

---

## Métricas de Implementación

| Métrica | Valor |
|---------|-------|
| Archivos creados | 4 (+auth, +db) |
| Líneas de código | ~300 |
| Endpoints nuevos | 2 (/auth/register, /auth/login) |
| Tiempo de dev | ~2 horas |
| Tests unitarios | ⏳ Próximo |

---

**Status:** ✅ COMPLETADO
**Version:** 1.0  
**Fecha:** 24 de febrero, 2026

Siguiente: PostgreSQL + Rate Limiting (Fase 2.2 & 2.3)
