"""
Core Chat Service - Aplicación FastAPI
Servicio multi-tenant para chat que usa la librería chatbot_core
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import router


def create_app() -> FastAPI:
    """Crea la aplicación FastAPI"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-tenant Chat API Service powered by chatbot_core",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    
    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Registra las rutas
    app.include_router(router, prefix="", tags=["core-chat-service"])
    
    return app


# Instancia global de la app
app = create_app()


@app.on_event("startup")
async def startup_event():
    """Evento al iniciar la aplicación"""
    print("\n" + "=" * 70)
    print("🚀 CORE CHAT SERVICE")
    print("=" * 70)
    print(f"Application: {settings.app_name}")
    print(f"Version: {settings.app_version}")
    print(f"Debug: {settings.debug}")
    print(f"Multi-tenant mode enabled")
    print(f"Max tenants: {settings.max_tenants}")
    print("=" * 70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento al cerrar la aplicación"""
    print("\n👋 Core Chat Service stopped\n")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
