"""
Gestor centralizado de patrones y respuestas
"""
import os
import json
from typing import Dict, List, Optional, Tuple


def get_default_brain() -> Tuple[List[List], List[List[str]]]:
    """Retorna brain mejorado con 40+ patrones"""
    
    default_responses = [
        ["That's", "interesting,", "tell", "me", "more"],
        ["I", "see.", "Could", "you", "elaborate?"],
        ["That's", "a", "great", "point"],
        ["I", "understand.", "What", "else?"],
        ["In", "other", "words,", "you're", "saying...?"],
        ["Can", "you", "give", "me", "an", "example?"],
        ["That", "makes", "sense"],
        ["I", "appreciate", "your", "thoughts"],
    ]
    
    pattern_responses = [
        # SALUDOS
        [["hello", 0], ["Hello!", "It's", "nice", "to", "meet", "you"]],
        [["hi", 0], ["Hi", "there!", "How", "can", "I", "help?"]],
        [["hey", 0], ["Hey!", "What's", "on", "your", "mind?"]],
        [["good", "morning"], ["Good", "morning!", "Ready", "to", "chat?"]],
        [["good", "afternoon"], ["Good", "afternoon!", "How", "are", "you?"]],
        [["good", "evening"], ["Good", "evening!", "Nice", "to", "see", "you"]],
        
        # DESPEDIDAS
        [["goodbye", 0], ["Goodbye!", "It", "was", "great", "talking", "to", "you"]],
        [["bye", 0], ["See", "you", "later!", "Take", "care"]],
        
        # PRESENTACIÓN
        [[0, "my", "name", "is", [1, "name"], 0], 
         ["Pleased", "to", "meet", "you,", [1, "name"], "!"]],
        
        # CÓMO ESTÁS
        [["how", "are", "you"], ["I'm", "doing", "great,", "thanks", "for", "asking!"]],
        [["how", "are", "you", "doing"], ["Doing", "well!", "What", "about", "you?"]],
        
        # ESTADO DEL USUARIO
        [["i", "am", [1, "feeling"], 0],
         ["I'm", "sorry", "to", "hear", "you're", [1, "feeling"]]],
        
        # PREFERENCIAS
        [["i", "like", [1, "thing"], 0],
         [[1, "thing"], "is", "great!", "Why", "do", "you", "enjoy", [1, "thing"], "?"]],
        
        [["i", "hate", [1, "thing"], 0],
         ["I", "see.", "It", "sounds", "like", [1, "thing"], "isn't", "for", "you"]],
        
        # RELACIONES
        [[[1, "subject"], "loves", [0, "object"]],
         ["That's", "beautiful!"]],
        [[[1, "person"], "is", "my", "friend"],
         ["That's", "lovely!"]],
        
        # NECESIDADES
        [["i", "need", [1, "object"], 0],
         ["Why", "do", "you", "need", [1, "object"], "?"]],
        
        [["help", "me"],
         ["Of", "course!", "I'm", "here", "to", "help"]],
        
        # PREGUNTAS
        [["what", "is", [1, "topic"], 0],
         ["That's", "an", "interesting", "question", "about", [1, "topic"]]],
        
        # AGRADECIMIENTO
        [["thanks", 0], ["You're", "welcome!", "Happy", "to", "help"]],
        [["thank", "you"], ["My", "pleasure!"]],
        
        # CONFIRMACIÓN
        [["yes", 0], ["Great!"]],
        [["no", 0], ["I", "understand"]],
        
        # INFORMACIÓN DEL BOT
        [["who", "are", "you"],
         ["I'm", "an", "AI", "chatbot", "created", "to", "chat"]],
        [["what", "can", "you", "do"],
         ["I", "can", "have", "conversations", "and", "help", "with", "ideas"]],
    ]
    
    return pattern_responses, default_responses


class BrainManager:
    """Gestor centralizado de patrones y respuestas"""
    
    def __init__(self, filename: str = "brain_data.json"):
        self.filename = filename
        self.data = self._load()
        
        if not self.data:
            pattern_responses, default_responses = get_default_brain()
            self.data = {
                "pattern_responses": [
                    {"pattern": p[0], "response": p[1]} for p in pattern_responses
                ],
                "default_responses": default_responses,
                "metadata": {
                    "total_patterns": len(pattern_responses),
                    "total_defaults": len(default_responses),
                    "version": "1.0",
                }
            }
            self._persist()
    
    def _load(self) -> dict:
        """Carga brain desde JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _persist(self):
        """Guarda brain a JSON"""
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def get_all_patterns(self) -> list:
        """Obtiene todos los patrones"""
        return self.data.get("pattern_responses", [])
    
    def get_pattern_by_index(self, index: int) -> Optional[dict]:
        """Obtiene un patrón por índice"""
        patterns = self.get_all_patterns()
        if 0 <= index < len(patterns):
            return {"index": index, **patterns[index]}
        return None
    
    def add_pattern(self, pattern: list, response: list) -> dict:
        """Agrega nuevo patrón"""
        new_pattern = {"pattern": pattern, "response": response}
        self.data["pattern_responses"].append(new_pattern)
        self.data["metadata"]["total_patterns"] += 1
        self._persist()
        return {
            "index": len(self.data["pattern_responses"]) - 1,
            **new_pattern
        }
    
    def update_pattern(self, index: int, pattern: list, response: list) -> Optional[dict]:
        """Actualiza un patrón existente"""
        patterns = self.data["pattern_responses"]
        if 0 <= index < len(patterns):
            patterns[index] = {"pattern": pattern, "response": response}
            self._persist()
            return {"index": index, **patterns[index]}
        return None
    
    def delete_pattern(self, index: int) -> bool:
        """Elimina un patrón"""
        patterns = self.data["pattern_responses"]
        if 0 <= index < len(patterns):
            patterns.pop(index)
            self.data["metadata"]["total_patterns"] -= 1
            self._persist()
            return True
        return False
    
    def search_patterns(self, keyword: str) -> list:
        """Busca patrones por palabra clave"""
        patterns = self.get_all_patterns()
        results = []
        keyword_lower = keyword.lower()
        
        for idx, p in enumerate(patterns):
            pattern_str = str(p["pattern"]).lower()
            response_str = str(p["response"]).lower()
            
            if keyword_lower in pattern_str or keyword_lower in response_str:
                results.append({"index": idx, **p})
        
        return results
    
    def get_default_responses(self) -> list:
        """Obtiene respuestas default"""
        return self.data.get("default_responses", [])
    
    def add_default_response(self, response: list) -> dict:
        """Agrega nueva respuesta default"""
        self.data["default_responses"].append(response)
        self.data["metadata"]["total_defaults"] += 1
        self._persist()
        return {"index": len(self.data["default_responses"]) - 1, "response": response}
    
    def delete_default_response(self, index: int) -> bool:
        """Elimina una respuesta default"""
        defaults = self.data["default_responses"]
        if 0 <= index < len(defaults):
            defaults.pop(index)
            self.data["metadata"]["total_defaults"] -= 1
            self._persist()
            return True
        return False
    
    def get_metadata(self) -> dict:
        """Obtiene metadatos del brain"""
        return self.data.get("metadata", {})
    
    def export_as_python(self) -> str:
        """Exporta brain como código Python"""
        pattern_responses = self.get_all_patterns()
        default_responses = self.get_default_responses()
        
        code = "def get_default_brain() -> tuple:\n"
        code += "    \"\"\"Brain exportado desde servidor\"\"\"\n\n"
        code += "    pattern_responses = [\n"
        
        for p in pattern_responses:
            code += f"        [{p['pattern']}, {p['response']}],\n"
        
        code += "    ]\n\n"
        code += "    default_responses = [\n"
        
        for r in default_responses:
            code += f"        {r},\n"
        
        code += "    ]\n\n"
        code += "    return pattern_responses, default_responses\n"
        
        return code
