"""
Rutas de la API REST
"""
import uuid
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..config import settings
from ..models import (
    ChatRequest,
    ChatResponse,
    SessionHistoryResponse,
    MessageHistoryItem,
    TenantStatsResponse,
    HealthResponse,
)
from ..auth import (
    create_access_token,
    Token,
    TenantRegister,
    TenantLogin,
    get_current_tenant,
)
from ..auth.schemas import AuthResponseSuccess, AuthResponseError
from ..db import (
    register_tenant,
    verify_tenant_credentials,
    tenant_exists,
    get_db,
    init_db,
)
from ..services import TenantService

# Instancia global del servicio
tenant_service = TenantService(storage_dir=settings.storage_dir)

router = APIRouter()


# ============================================================================
# AUTENTICACIÓN (Fase 2)
# ============================================================================

@router.post(
    "/auth/register",
    response_model=AuthResponseSuccess,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    responses={400: {"model": AuthResponseError}}
)
async def register_tenant_endpoint(request: TenantRegister):
    """
    Registra un nuevo tenant
    
    - **tenant_id**: ID único del tenant (3-255 chars)
    - **password**: Contraseña (mín 8 chars)
    - **name**: Nombre descriptivo (opcional)
    
    Retorna JWT token para usar en siguientes requests
    """
    # Validar que tenant no existe
    if tenant_exists(request.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant '{request.tenant_id}' ya existe"
        )
    
    # Registrar tenant
    success = register_tenant(
        tenant_id=request.tenant_id,
        password=request.password,
        name=request.name
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al registrar tenant"
        )
    
    # Crear token
    access_token = create_access_token(
        tenant_id=request.tenant_id,
        expires_delta=timedelta(hours=24)
    )
    
    return AuthResponseSuccess(
        message=f"Tenant '{request.tenant_id}' registrado exitosamente",
        data=Token(
            access_token=access_token,
            tenant_id=request.tenant_id,
            expires_in=86400  # 24 horas
        )
    )


@router.post(
    "/auth/login",
    response_model=AuthResponseSuccess,
    tags=["Authentication"],
    responses={401: {"model": AuthResponseError}}
)
async def login_tenant_endpoint(request: TenantLogin):
    """
    Login de tenant y obtención de JWT token
    
    - **tenant_id**: ID del tenant
    - **password**: Contraseña
    
    Retorna JWT token válido por 24 horas
    """
    # Verificar credenciales
    if not verify_tenant_credentials(request.tenant_id, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token
    access_token = create_access_token(
        tenant_id=request.tenant_id,
        expires_delta=timedelta(hours=24)
    )
    
    return AuthResponseSuccess(
        message=f"Login exitoso para '{request.tenant_id}'",
        data=Token(
            access_token=access_token,
            tenant_id=request.tenant_id,
            expires_in=86400  # 24 horas
        )
    )


# ============================================================================
# HEALTH & PROTECTED ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": settings.app_version,
        "service": "core-chat-service"
    }


@router.post("/api/v1/chat/{tenant_id}", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(tenant_id: str, request: ChatRequest):
    """
    Endpoint principal de chat (multi-tenant)
    
    - **tenant_id**: ID único del tenant (requerido en URL)
    - **message**: Mensaje del usuario
    - **session_id**: ID de sesión (opcional, se genera si no se proporciona)
    """
    if not tenant_id or not tenant_id.strip():
        raise HTTPException(status_code=400, detail="tenant_id required in URL")
    
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="message required")
    
    session_id = request.session_id or str(uuid.uuid4())[:8]
    
    try:
        # Procesa el mensaje
        result = tenant_service.process_message(tenant_id, request.message, session_id)
        
        return ChatResponse(
            tenant_id=tenant_id,
            session_id=session_id,
            message=request.message,
            response=result["response"],
            confidence=result["confidence"],
            source=result["source"],
            pattern_matched=result["pattern_matched"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/api/v1/history/{tenant_id}/{session_id}",
    response_model=SessionHistoryResponse,
    tags=["History"]
)
async def get_history(tenant_id: str, session_id: str):
    """
    Obtiene el historial de mensajes de una sesión
    
    - **tenant_id**: ID del tenant
    - **session_id**: ID de la sesión
    """
    if not tenant_id or not session_id:
        raise HTTPException(status_code=400, detail="tenant_id and session_id required")
    
    try:
        history = tenant_service.get_session_history(tenant_id, session_id)
        
        return SessionHistoryResponse(
            tenant_id=tenant_id,
            session_id=session_id,
            history=[
                MessageHistoryItem(
                    timestamp=item["timestamp"],
                    user=item["user"],
                    bot=item["bot"]
                )
                for item in history
            ],
            total_messages=len(history),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/api/v1/stats/{tenant_id}",
    response_model=TenantStatsResponse,
    tags=["Stats"]
)
async def get_stats(tenant_id: str):
    """
    Obtiene estadísticas de un tenant
    
    - **tenant_id**: ID del tenant
    """
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required")
    
    try:
        stats = tenant_service.get_tenant_stats(tenant_id)
        
        return TenantStatsResponse(
            tenant_id=tenant_id,
            app_name=settings.app_name,
            version=settings.app_version,
            total_sessions=stats["total_sessions"],
            total_messages=stats["total_messages"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
