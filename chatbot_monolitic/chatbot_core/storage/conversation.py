"""
Almacenamiento de conversaciones
"""
import os
import json
from datetime import datetime
from typing import Dict, List


class SimpleConversationStorage:
    """Almacenamiento simple de conversaciones en JSON"""
    
    def __init__(self, filename: str = "conversations.json"):
        self.filename = filename
        self.data = self._load()
    
    def _load(self) -> dict:
        """Carga conversaciones desde archivo"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self, session_id: str, user_input: str, bot_response: str):
        """Guarda interacción"""
        if session_id not in self.data:
            self.data[session_id] = []
        
        self.data[session_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_input,
            "bot": bot_response,
        })
        
        self._persist()
    
    def _persist(self):
        """Guarda a archivo"""
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def get_history(self, session_id: str) -> list:
        """Obtiene historial de sesión"""
        return self.data.get(session_id, [])
    
    def get_all_sessions(self) -> Dict[str, List]:
        """Obtiene todas las sesiones"""
        return self.data
    
    def clear_session(self, session_id: str) -> bool:
        """Limpia una sesión"""
        if session_id in self.data:
            del self.data[session_id]
            self._persist()
            return True
        return False
