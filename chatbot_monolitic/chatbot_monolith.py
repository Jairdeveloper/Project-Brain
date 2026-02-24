"""
LAUNCHER - ChatBot Evolution
=============================

Este archivo es un LAUNCHER fino que usa la librería modular chatbot_core.
Soporta 3 modos: CLI, API REST, y Brain Manager API.

Para ejecutar:
    python chatbot_monolith.py --mode cli      (Modo CLI interactivo)
    python chatbot_monolith.py --mode api      (Modo API REST multi-tenant)
    python chatbot_monolith.py --mode brain    (Brain Manager API)

DEPENDENCIAS:
    pip install fastapi uvicorn sentence-transformers

OPCIONAL (para LLM):
    pip install openai requests
"""

import sys
import argparse
import uuid
from typing import Optional

# Importa desde chatbot_core
from chatbot_core import (
    settings,
    get_logger,
    Actor,
    SimpleConversationStorage,
    BrainManager,
    get_default_brain,
)

logger = get_logger(__name__, settings.LOG_LEVEL)



# =============================================================================
# LAUNCHERS - Modos de ejecución que usan chatbot_core
# =============================================================================


def run_cli():
    """Modo CLI interactivo"""
    logger.info("Starting ChatBot CLI (using chatbot_core)")
    
    # Inicializa componentes desde librería
    pattern_responses, default_responses = get_default_brain()
    actor = Actor(pattern_responses, default_responses)
    storage = SimpleConversationStorage()
    session_id = str(uuid.uuid4())[:8]
    
    print("\n" + "=" * 70)
    print("ChatBot Evolution - Core Mode (CLI)")
    print("=" * 70)
    print("Type 'quit' o '(quit)' to exit\n")
    
    try:
        while True:
            try:
                user_input = input("> ").strip()
            except EOFError:
                print("\n(EOF) Type '(quit)' to exit")
                continue
            
            if not user_input:
                continue
            
            if user_input.lower() in ("(quit)", "quit", "exit"):
                print("Bye!")
                break
            
            response = actor.process(user_input)
            print(f"Bot: {response.text}")
            
            # Guarda conversación
            storage.save(session_id, user_input, response.text)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted. Bye!")


def run_api():
    """Modo API REST multi-tenant"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
    except ImportError:
        print("ERROR: FastAPI no instalado. Instala con: pip install fastapi uvicorn")
        sys.exit(1)
    
    logger.info("Starting ChatBot Core Service (API)")
    
    # Inicializa componentes
    pattern_responses, default_responses = get_default_brain()
    
    # Diccionario de tenants (en production sería una BD)
    tenants: dict = {}
    
    def get_or_create_tenant(tenant_id: str):
        """Obtiene o crea una instancia del Actor para un tenant"""
        if tenant_id not in tenants:
            tenants[tenant_id] = {
                "actor": Actor(pattern_responses, default_responses),
                "storage": SimpleConversationStorage(f"conversations_{tenant_id}.json"),
            }
        return tenants[tenant_id]
    
    # Crea app FastAPI
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="ChatBot Core Service - Multi-Tenant Chat API (using chatbot_core)"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health():
        """Health check"""
        return {"status": "ok", "version": settings.APP_VERSION, "service": "core-chat-service"}
    
    @app.post("/api/v1/chat/{tenant_id}")
    async def chat(tenant_id: str, message: str, session_id: Optional[str] = None):
        """Endpoint principal de chat (multi-tenant)"""
        if not tenant_id or not tenant_id.strip():
            raise HTTPException(status_code=400, detail="tenant_id required in URL")
        
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="message required")
        
        # Obtiene tenant
        tenant = get_or_create_tenant(tenant_id)
        actor = tenant["actor"]
        storage = tenant["storage"]
        
        # Procesa
        response = actor.process(message)
        storage.save(session_id, message, response.text)
        
        return {
            "tenant_id": tenant_id,
            "session_id": session_id,
            "message": message,
            "response": response.text,
            "confidence": response.confidence,
            "source": response.source,
            "pattern_matched": response.pattern_matched,
        }
    
    @app.get("/api/v1/history/{tenant_id}/{session_id}")
    async def history(tenant_id: str, session_id: str):
        """Obtiene historial de sesión"""
        tenant = get_or_create_tenant(tenant_id)
        storage = tenant["storage"]
        return {
            "tenant_id": tenant_id,
            "session_id": session_id,
            "history": storage.get_history(session_id)
        }
    
    @app.get("/api/v1/stats/{tenant_id}")
    async def stats(tenant_id: str):
        """Estadísticas del tenant"""
        tenant = get_or_create_tenant(tenant_id)
        storage = tenant["storage"]
        return {
            "tenant_id": tenant_id,
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "total_sessions": len(storage.get_all_sessions()),
            "total_messages": sum(len(msgs) for msgs in storage.get_all_sessions().values()),
        }
    
    # Inicia servidor
    print(f"\n{'='*70}")
    print("🚀 CHATBOT CORE SERVICE (API)")
    print(f"{'='*70}")
    print(f"✅ API running at http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📖 Swagger docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"📊 Multi-tenant mode: /api/v1/chat/{{tenant_id}}\n")
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )


def run_brain_server():
    """Servidor dedicado a gestionar el brain (CRUD de patrones)"""
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
        description="Gestor de patrones y respuestas del chatbot (using chatbot_core)"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "brain-manager"}
    
    @app.get("/api/v1/brain/metadata")
    async def get_metadata():
        return brain_manager.get_metadata()
    
    @app.get("/api/v1/brain/patterns")
    async def list_patterns(limit: int = None, offset: int = 0):
        patterns = brain_manager.get_all_patterns()
        if limit:
            patterns = patterns[offset:offset + limit]
        return {"total": len(brain_manager.get_all_patterns()), "count": len(patterns), "patterns": patterns}
    
    @app.get("/api/v1/brain/patterns/{index}")
    async def get_pattern(index: int):
        pattern = brain_manager.get_pattern_by_index(index)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return pattern
    
    @app.post("/api/v1/brain/patterns")
    async def create_pattern(pattern: list, response: list):
        if not pattern or not response:
            raise HTTPException(status_code=400, detail="pattern and response required")
        new_pattern = brain_manager.add_pattern(pattern, response)
        return {"status": "created", **new_pattern}
    
    @app.put("/api/v1/brain/patterns/{index}")
    async def update_pattern(index: int, pattern: list, response: list):
        updated = brain_manager.update_pattern(index, pattern, response)
        if not updated:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"status": "updated", **updated}
    
    @app.delete("/api/v1/brain/patterns/{index}")
    async def delete_pattern(index: int):
        if not brain_manager.delete_pattern(index):
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"status": "deleted", "index": index}
    
    @app.get("/api/v1/brain/patterns/search")
    async def search_patterns(q: str):
        if not q:
            raise HTTPException(status_code=400, detail="search query (q) required")
        results = brain_manager.search_patterns(q)
        return {"query": q, "results": results, "count": len(results)}
    
    @app.get("/api/v1/brain/defaults")
    async def list_defaults():
        defaults = brain_manager.get_default_responses()
        return {"total": len(defaults), "defaults": defaults}
    
    @app.post("/api/v1/brain/defaults")
    async def create_default(response: list):
        if not response:
            raise HTTPException(status_code=400, detail="response required")
        new_default = brain_manager.add_default_response(response)
        return {"status": "created", **new_default}
    
    @app.delete("/api/v1/brain/defaults/{index}")
    async def delete_default(index: int):
        if not brain_manager.delete_default_response(index):
            raise HTTPException(status_code=404, detail="Default not found")
        return {"status": "deleted", "index": index}
    
    @app.get("/api/v1/brain/export/python")
    async def export_python():
        code = brain_manager.export_as_python()
        return {"format": "python", "code": code, "filename": "get_default_brain.py"}
    
    @app.get("/api/v1/brain/export/json")
    async def export_json():
        return {"format": "json", "data": brain_manager.data, "filename": "brain_data.json"}
    
    print(f"\n{'='*70}")
    print("🧠 BRAIN MANAGER SERVER")
    print(f"{'='*70}")
    print(f"✅ Server running at http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📖 Swagger docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"🎯 CRUD endpoints: /api/v1/brain/patterns/*\n")
    
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, log_level="info")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Entry point principal"""
    parser = argparse.ArgumentParser(
        description="ChatBot Evolution - Core Service (using modular chatbot_core library)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chatbot_monolith.py --mode cli        CLI mode (interactive)
  python chatbot_monolith.py --mode api        API REST mode (multi-tenant)
  python chatbot_monolith.py --mode brain      Brain Manager Server (pattern CRUD)
  python chatbot_monolith.py --help            Show help
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["cli", "api", "brain"],
        default="cli",
        help="Modo de ejecución (default: cli)",
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "cli":
            run_cli()
        elif args.mode == "api":
            run_api()
        elif args.mode == "brain":
            run_brain_server()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
