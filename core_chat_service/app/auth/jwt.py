"""
Lógica de JWT y seguridad de contraseñas
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
import hmac

# Configuración
SECRET_KEY = "your-secret-key-change-in-production"  # ⚠️ CAMBIAR EN PRODUCCIÓN
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas


def get_password_hash(password: str) -> str:
    """
    Crea hash de contraseña simple (usando SHA256)
    En Fase 2.5: Migrar a bcrypt con DB
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra hash"""
    return get_password_hash(plain_password) == hashed_password


def create_access_token(
    tenant_id: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea JWT token para tenant
    
    Args:
        tenant_id: ID del tenant
        expires_delta: Tiempo de expiración (default: 24 horas)
    
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": tenant_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verifica JWT token y retorna tenant_id
    
    Args:
        token: JWT token string
    
    Returns:
        tenant_id si es válido, None si no
        
    Raises:
        JWTError si el token es inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id: str = payload.get("sub")
        
        if tenant_id is None:
            return None
        
        return tenant_id
    
    except JWTError:
        return None
