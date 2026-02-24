"""
Esquemas Pydantic para autenticación
"""
from pydantic import BaseModel, Field
from typing import Optional


class TenantRegister(BaseModel):
    """Modelo para registro de tenant"""
    tenant_id: str = Field(..., min_length=3, max_length=255, description="ID único del tenant")
    password: str = Field(..., min_length=8, max_length=255, description="Contraseña (mín 8 chars)")
    name: Optional[str] = Field(None, max_length=255, description="Nombre del tenant")
    
    class Config:
        example = {
            "tenant_id": "acme-corp",
            "password": "SecurePass123!",
            "name": "ACME Corporation"
        }


class TenantLogin(BaseModel):
    """Modelo para login de tenant"""
    tenant_id: str = Field(..., description="ID del tenant")
    password: str = Field(..., description="Contraseña")
    
    class Config:
        example = {
            "tenant_id": "acme-corp",
            "password": "SecurePass123!"
        }


class Token(BaseModel):
    """Modelo de respuesta JWT"""
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    expires_in: int = Field(default=86400, description="Segundos hasta expiración")
    
    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "tenant_id": "acme-corp",
            "expires_in": 86400
        }


class TokenData(BaseModel):
    """Datos extraídos del JWT"""
    tenant_id: Optional[str] = None


class AuthResponseSuccess(BaseModel):
    """Respuesta exitosa de autenticación"""
    status: str = "success"
    message: str
    data: Token
    
    class Config:
        example = {
            "status": "success",
            "message": "Tenant registrado exitosamente",
            "data": {
                "access_token": "...",
                "token_type": "bearer",
                "tenant_id": "acme-corp",
                "expires_in": 86400
            }
        }


class AuthResponseError(BaseModel):
    """Respuesta de error de autenticación"""
    status: str = "error"
    detail: str
    
    class Config:
        example = {
            "status": "error",
            "detail": "Credenciales inválidas"
        }
