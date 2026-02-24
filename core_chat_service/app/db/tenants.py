"""
Gestión de Tenants con SQLAlchemy + PostgreSQL
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session
from ..models.database import Tenant
from ..auth.jwt import get_password_hash, verify_password


def register_tenant(
    db: Session,
    tenant_id: str,
    password: str,
    name: Optional[str] = None
) -> bool:
    """
    Registra nuevo tenant en PostgreSQL
    
    Args:
        db: SQLAlchemy session
        tenant_id: ID único del tenant
        password: Contraseña (será hasheada)
        name: Nombre del tenant
    
    Returns:
        True si se registró, False si ya existe
    """
    # Verificar que no existe
    existing = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if existing:
        return False
    
    # Crear nuevo tenant
    tenant = Tenant(
        tenant_id=tenant_id,
        password_hash=get_password_hash(password),
        name=name or tenant_id,
        active=True
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return True


def get_tenant(db: Session, tenant_id: str) -> Optional[Dict]:
    """
    Obtiene datos de tenant desde PostgreSQL
    
    Args:
        db: SQLAlchemy session
        tenant_id: ID del tenant
    
    Returns:
        Dict con datos de tenant o None
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        return None
    
    return {
        "tenant_id": tenant.tenant_id,
        "password_hash": tenant.password_hash,
        "name": tenant.name,
        "active": tenant.active,
    }


def verify_tenant_credentials(
    db: Session,
    tenant_id: str,
    password: str
) -> bool:
    """
    Verifica credenciales de tenant contra BD
    
    Args:
        db: SQLAlchemy session
        tenant_id: ID del tenant
        password: Contraseña a verificar
    
    Returns:
        True si credenciales son válidas
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant or not tenant.active:
        return False
    
    return verify_password(password, tenant.password_hash)


def tenant_exists(db: Session, tenant_id: str) -> bool:
    """Verifica si tenant existe"""
    return db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first() is not None


def get_all_tenants(db: Session):
    """Obtiene todos los tenants (admin only)"""
    return db.query(Tenant).filter(Tenant.active == True).all()


def deactivate_tenant(db: Session, tenant_id: str) -> bool:
    """Desactiva un tenant (soft delete)"""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        return False
    
    tenant.active = False
    db.commit()
    
    return True

