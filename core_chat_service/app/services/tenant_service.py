"""
Servicio de gestión de tenants
"""
import os
from typing import Dict, Optional
from chatbot_core import (
    Actor,
    SimpleConversationStorage,
    get_default_brain,
)


class TenantService:
    """Servicio para gestionar instancias por tenant"""
    
    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = storage_dir
        self.tenants: Dict[str, dict] = {}
        
        # Crea directorio de almacenamiento
        os.makedirs(storage_dir, exist_ok=True)
    
    def get_or_create_tenant(self, tenant_id: str) -> dict:
        """Obtiene o crea una instancia del Actor para un tenant"""
        if tenant_id not in self.tenants:
            # Crea instancia para este tenant
            pattern_responses, default_responses = get_default_brain()
            actor = Actor(pattern_responses, default_responses)
            
            # Crea almacenamiento aislado por tenant
            storage_path = os.path.join(self.storage_dir, f"conversations_{tenant_id}.json")
            storage = SimpleConversationStorage(storage_path)
            
            self.tenants[tenant_id] = {
                "actor": actor,
                "storage": storage,
                "created_at": "",
            }
        
        return self.tenants[tenant_id]
    
    def process_message(
        self,
        tenant_id: str,
        message: str,
        session_id: Optional[str] = None
    ) -> dict:
        """Procesa un mensaje para un tenant específico"""
        tenant = self.get_or_create_tenant(tenant_id)
        actor = tenant["actor"]
        storage = tenant["storage"]
        
        # Procesa con el Actor
        response = actor.process(message)
        
        # Guarda en storage
        storage.save(session_id or "", message, response.text)
        
        return {
            "response": response.text,
            "confidence": response.confidence,
            "source": response.source,
            "pattern_matched": response.pattern_matched,
        }
    
    def get_session_history(self, tenant_id: str, session_id: str) -> list:
        """Obtiene el historial de una sesión"""
        tenant = self.get_or_create_tenant(tenant_id)
        storage = tenant["storage"]
        return storage.get_history(session_id)
    
    def get_tenant_stats(self, tenant_id: str) -> dict:
        """Obtiene estadísticas de un tenant"""
        tenant = self.get_or_create_tenant(tenant_id)
        storage = tenant["storage"]
        all_sessions = storage.get_all_sessions()
        
        return {
            "total_sessions": len(all_sessions),
            "total_messages": sum(len(msgs) for msgs in all_sessions.values()),
        }
