"""
Dependencias FastAPI para autenticación
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from .jwt import verify_token

security = HTTPBearer()


async def get_current_tenant(credentials = Depends(security)) -> str:
    """
    Extrae y valida tenant_id del JWT token en Authorization header
    
    Uso en rutas:
    @app.post("/api/v1/protected")
    async def protected_route(tenant_id: str = Depends(get_current_tenant)):
        return {"tenant_id": tenant_id}
    
    Args:
        credentials: HTTP Bearer token del header Authorization
    
    Returns:
        tenant_id si el token es válido
        
    Raises:
        HTTPException 401 si el token es inválido o expirado
    """
    token = credentials.credentials
    tenant_id = verify_token(token)
    
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return tenant_id
