"""
Modelos SQLAlchemy para la base de datos
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Tenant(Base):
    """Modelo de Tenant en BD"""
    __tablename__ = "tenants"
    
    tenant_id = Column(String(255), primary_key=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")
    patterns = relationship("Pattern", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(tenant_id='{self.tenant_id}', name='{self.name}')>"


class Conversation(Base):
    """Modelo de Conversación"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    source = Column(String(50), default="pattern")
    pattern_matched = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relación
    tenant = relationship("Tenant", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(tenant_id='{self.tenant_id}', session_id='{self.session_id}')>"


class Pattern(Base):
    """Modelo de Patrón (Brain)"""
    __tablename__ = "patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    pattern = Column(JSON, nullable=False)  # Almacena el patrón como JSON
    response = Column(JSON, nullable=False)  # Almacena la respuesta como JSON
    metadata = Column(JSON)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación
    tenant = relationship("Tenant", back_populates="patterns")
    
    def __repr__(self):
        return f"<Pattern(tenant_id='{self.tenant_id}')>"
