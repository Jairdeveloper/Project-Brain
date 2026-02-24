# =============================================================================
# PARTE 9B: BRAIN SERVER - GESTOR DE PATRONES (CRUD)
# =============================================================================

class BrainManager:
    """Gestor centralizado de patrones y respuestas"""
    
    def __init__(self, filename: str = "brain_data.json"):
        self.filename = filename
        self.data = self._load()
        
        # Si no existe, crear con datos default
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
    
    def get_pattern_by_index(self, index: int) -> dict:
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
    
    def update_pattern(self, index: int, pattern: list, response: list) -> dict:
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
        """Obtiene respuestas por defecto"""
        return self.data.get("default_responses", [])
    
    def add_default_response(self, response: list) -> dict:
        """Agrega respuesta por defecto"""
        self.data["default_responses"].append(response)
        self.data["metadata"]["total_defaults"] += 1
        self._persist()
        return {
            "index": len(self.data["default_responses"]) - 1,
            "response": response
        }
    
    def delete_default_response(self, index: int) -> bool:
        """Elimina respuesta por defecto"""
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


def run_brain_server():
    """Servidor dedicado a gestionar el brain"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
    except ImportError:
        print("ERROR: FastAPI no instalado. Instala con: pip install fastapi uvicorn")
        sys.exit(1)
    
    logger.info("Starting Brain Manager Server")
    
    brain_manager = BrainManager()
    app = FastAPI(
        title="Brain Manager API",
        version="1.0",
        description="Gestor de patrones y respuestas del chatbot"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ========== HEALTH ==========
    @app.get("/health")
    async def health():
        """Health check"""
        return {"status": "ok", "service": "brain-manager"}
    
    # ========== METADATA ==========
    @app.get("/api/v1/brain/metadata")
    async def get_metadata():
        """Obtiene metadatos del brain"""
        return brain_manager.get_metadata()
    
    # ========== PATRONES ==========
    @app.get("/api/v1/brain/patterns")
    async def list_patterns(limit: int = None, offset: int = 0):
        """Lista todos los patrones"""
        patterns = brain_manager.get_all_patterns()
        
        if limit:
            patterns = patterns[offset:offset + limit]
        
        return {
            "total": len(brain_manager.get_all_patterns()),
            "count": len(patterns),
            "patterns": patterns
        }
    
    @app.get("/api/v1/brain/patterns/{index}")
    async def get_pattern(index: int):
        """Obtiene un patrón específico"""
        pattern = brain_manager.get_pattern_by_index(index)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return pattern
    
    @app.post("/api/v1/brain/patterns")
    async def create_pattern(pattern: list, response: list):
        """Crea un nuevo patrón"""
        if not pattern or not response:
            raise HTTPException(status_code=400, detail="pattern and response required")
        
        new_pattern = brain_manager.add_pattern(pattern, response)
        return {"status": "created", **new_pattern}
    
    @app.put("/api/v1/brain/patterns/{index}")
    async def update_pattern(index: int, pattern: list, response: list):
        """Actualiza un patrón"""
        updated = brain_manager.update_pattern(index, pattern, response)
        if not updated:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"status": "updated", **updated}
    
    @app.delete("/api/v1/brain/patterns/{index}")
    async def delete_pattern(index: int):
        """Elimina un patrón"""
        if not brain_manager.delete_pattern(index):
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"status": "deleted", "index": index}
    
    @app.get("/api/v1/brain/patterns/search")
    async def search_patterns(q: str):
        """Busca patrones"""
        if not q:
            raise HTTPException(status_code=400, detail="search query (q) required")
        
        results = brain_manager.search_patterns(q)
        return {"query": q, "results": results, "count": len(results)}
    
    # ========== RESPUESTAS DEFAULT ==========
    @app.get("/api/v1/brain/defaults")
    async def list_defaults():
        """Lista respuestas por defecto"""
        defaults = brain_manager.get_default_responses()
        return {"total": len(defaults), "defaults": defaults}
    
    @app.post("/api/v1/brain/defaults")
    async def create_default(response: list):
        """Agrega respuesta por defecto"""
        if not response:
            raise HTTPException(status_code=400, detail="response required")
        
        new_default = brain_manager.add_default_response(response)
        return {"status": "created", **new_default}
    
    @app.delete("/api/v1/brain/defaults/{index}")
    async def delete_default(index: int):
        """Elimina respuesta por defecto"""
        if not brain_manager.delete_default_response(index):
            raise HTTPException(status_code=404, detail="Default not found")
        return {"status": "deleted", "index": index}
    
    # ========== EXPORT ==========
    @app.get("/api/v1/brain/export/python")
    async def export_python():
        """Exporta brain como código Python"""
        code = brain_manager.export_as_python()
        return {
            "format": "python",
            "code": code,
            "filename": "get_default_brain.py"
        }
    
    @app.get("/api/v1/brain/export/json")
    async def export_json():
        """Exporta brain como JSON"""
        return {
            "format": "json",
            "data": brain_manager.data,
            "filename": "brain_data.json"
        }
    
    # Inicia servidor
    print(f"\n{'='*70}")
    print("🧠 BRAIN MANAGER SERVER")
    print(f"{'='*70}")
    print(f"✅ Server running at http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📖 Swagger docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"📋 ReDoc: http://{settings.API_HOST}:{settings.API_PORT}/redoc")
    print(f"\n📌 Endpoints principales:")
    print(f"   GET    /api/v1/brain/patterns       - Listar patrones")
    print(f"   POST   /api/v1/brain/patterns       - Crear patrón")
    print(f"   GET    /api/v1/brain/patterns/{{i}} - Obtener patrón")
    print(f"   PUT    /api/v1/brain/patterns/{{i}} - Actualizar patrón")
    print(f"   DELETE /api/v1/brain/patterns/{{i}} - Eliminar patrón")
    print(f"   GET    /api/v1/brain/defaults       - Listar respuestas default")
    print(f"   POST   /api/v1/brain/defaults       - Agregar respuesta default")
    print(f"   GET    /api/v1/brain/export/python  - Exportar como Python")
    print(f"   GET    /api/v1/brain/export/json    - Exportar como JSON")
    print(f"\n{'='*70}\n")
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )

