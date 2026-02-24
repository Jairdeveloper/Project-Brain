"""
Modelos de request/response para FastAPI
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Solicitud de chat"""
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión (opcional)")
    
    class Config:
        example = {
            "message": "Hola, ¿cómo estás?",
            "session_id": "abc123"
        }


class ChatResponse(BaseModel):
    """Respuesta de chat"""
    tenant_id: str
    session_id: str
    message: str
    response: str
    confidence: float
    source: str
    pattern_matched: bool
    
    class Config:
        example = {
            "tenant_id": "tenant-1",
            "session_id": "abc123",
            "message": "Hola, ¿cómo estás?",
            "response": "¡Hola! Me va bien, ¿y a ti?",
            "confidence": 0.9,
            "source": "pattern",
            "pattern_matched": True
        }


class MessageHistoryItem(BaseModel):
    """Item del historial de mensajes"""
    timestamp: str
    user: str
    bot: str


class SessionHistoryResponse(BaseModel):
    """Respuesta con historial de sesión"""
    tenant_id: str
    session_id: str
    history: List[MessageHistoryItem]
    total_messages: int
    
    class Config:
        example = {
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


class TenantStatsResponse(BaseModel):
    """Estadísticas de un tenant"""
    tenant_id: str
    app_name: str
    version: str
    total_sessions: int
    total_messages: int
    
    class Config:
        example = {
            "tenant_id": "tenant-1",
            "app_name": "Core Chat Service",
            "version": "1.0",
            "total_sessions": 5,
            "total_messages": 42
        }


class HealthResponse(BaseModel):
    """Respuesta de health check"""
    status: str
    version: str
    service: str
    
    class Config:
        example = {
            "status": "ok",
            "version": "1.0",
            "service": "core-chat-service"
        }
