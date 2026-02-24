"""
Rutas de la API REST
"""
import uuid
from fastapi import APIRouter, HTTPException
from ..config import settings
from ..models import (
    ChatRequest,
    ChatResponse,
    SessionHistoryResponse,
    MessageHistoryItem,
    TenantStatsResponse,
    HealthResponse,
)
from ..services import TenantService

# Instancia global del servicio
tenant_service = TenantService(storage_dir=settings.storage_dir)

router = APIRouter()


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
