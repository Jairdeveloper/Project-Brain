#!/usr/bin/env python3
"""
Brain Server - Visualizador Interactivo
========================================

Ejecuta este script para ver un resumen visual del Brain Server.
"""

import json
from datetime import datetime

def print_header(text, width=70):
    print(f"\n{'='*width}")
    print(f"  {text}")
    print(f"{'='*width}\n")

def print_box(lines, width=70):
    print("┌" + "─"*(width-2) + "┐")
    for line in lines:
        # Ajusta líneas largas
        if len(line) > width - 4:
            line = line[:width-7] + "..."
        padding = width - len(line) - 4
        print(f"│ {line}{' '*padding} │")
    print("└" + "─"*(width-2) + "┘\n")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                     🧠 BRAIN MANAGER SERVER                                ║
║                                                                              ║
║                  Visualizador e Información del Servidor                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Descripción General
    print_header("1️⃣  ¿QUÉ ES EL BRAIN SERVER?")
    print_box([
        "Transform function get_default_brain() → REST API Server",
        "",
        "ANTES: def get_default_brain() -> tuple:",
        "        return pattern_responses, default_responses",
        "",
        "AHORA: python chatbot_monolith.py --mode brain",
        "       🚀 Servidor REST funcional con CRUD"
    ])
    
    # 2. Arquitectura
    print_header("2️⃣  ARQUITECTURA")
    print("""
    ┌─────────────────────────────────────┐
    │  chatbot_monolith.py --mode brain   │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │      run_brain_server()             │
    │  ├─ FastAPI Application             │
    │  ├─ BrainManager (CRUD)             │
    │  └─ uvicorn Server                  │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │      HTTP Server (Port 8000)        │
    │  ├─ /api/v1/brain/patterns (CRUD)   │
    │  ├─ /api/v1/brain/defaults (CRUD)   │
    │  ├─ /api/v1/brain/export/* (GET)    │
    │  └─ Swagger UI                      │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │      brain_data.json                │
    │  Persistencia Automática            │
    └─────────────────────────────────────┘
    """)
    
    # 3. Endpoints
    print_header("3️⃣  ENDPOINTS REST (14 TOTAL)")
    
    endpoints = {
        "Health": [
            ("GET", "/health", "Verificar estado")
        ],
        "Metadata": [
            ("GET", "/api/v1/brain/metadata", "Obtener metadatos")
        ],
        "Patrones (CRUD)": [
            ("GET", "/api/v1/brain/patterns", "Listar todos"),
            ("POST", "/api/v1/brain/patterns", "Crear nuevo"),
            ("GET", "/api/v1/brain/patterns/{i}", "Obtener uno"),
            ("PUT", "/api/v1/brain/patterns/{i}", "Actualizar"),
            ("DELETE", "/api/v1/brain/patterns/{i}", "Eliminar"),
            ("GET", "/api/v1/brain/patterns/search", "Buscar (q=X)")
        ],
        "Defaults (CRUD)": [
            ("GET", "/api/v1/brain/defaults", "Listar todos"),
            ("POST", "/api/v1/brain/defaults", "Agregar uno"),
            ("DELETE", "/api/v1/brain/defaults/{i}", "Eliminar uno")
        ],
        "Export": [
            ("GET", "/api/v1/brain/export/python", "Exportar Python"),
            ("GET", "/api/v1/brain/export/json", "Exportar JSON")
        ]
    }
    
    for category, methods in endpoints.items():
        print(f"  {category}:")
        for method, path, desc in methods:
            color = "🟢" if method == "GET" else "🟡" if method == "POST" else "🔵" if method == "PUT" else "🔴"
            print(f"    {color} {method:6} {path:40} {desc}")
        print()
    
    # 4. Flujo de Una Solicitud
    print_header("4️⃣  FLUJO DE UNA SOLICITUD (EJEMPLO)")
    print("""
    PASO 1: Cliente envía solicitud
    ┌─────────────────────────────────────────────────────────┐
    │ POST /api/v1/brain/patterns                             │
    │ {                                                       │
    │   "pattern": ["i", "love", [1, "thing"]],               │
    │   "response": [[1, "thing"], "is", "great!"]            │
    │ }                                                       │
    └────────────────┬────────────────────────────────────────┘
                     │
                     ▼
    PASO 2: FastAPI valida entrada
    ┌─────────────────────────────────────────────────────────┐
    │ ✓ Parámetros requeridos presentes                       │
    │ ✓ Tipos correctos (list)                                │
    │ ✓ No están vacíos                                       │
    └────────────────┬────────────────────────────────────────┘
                     │
                     ▼
    PASO 3: BrainManager procesa
    ┌─────────────────────────────────────────────────────────┐
    │ brain_manager.add_pattern(pattern, response)            │
    │ ├─ Agrega a self.data["pattern_responses"]              │
    │ ├─ Actualiza metadata ("total_patterns" += 1)           │
    │ └─ Persiste a brain_data.json                           │
    └────────────────┬────────────────────────────────────────┘
                     │
                     ▼
    PASO 4: Respuesta al cliente
    ┌─────────────────────────────────────────────────────────┐
    │ HTTP 200                                                │
    │ {                                                       │
    │   "status": "created",                                  │
    │   "index": 30,                                          │
    │   "pattern": ["i", "love", [1, "thing"]],               │
    │   "response": [[1, "thing"], "is", "great!"]            │
    │ }                                                       │
    └─────────────────────────────────────────────────────────┘
    """)
    
    # 5. Clases y Métodos
    print_header("5️⃣  CLASE BRAINMANAGER - MÉTODOS")
    
    methods = {
        "Inicialización": [
            "__init__(filename='brain_data.json')",
            "_load() -> dict",
            "_persist()"
        ],
        "Lectura": [
            "get_all_patterns() -> list",
            "get_pattern_by_index(index: int) -> dict",
            "get_default_responses() -> list",
            "get_metadata() -> dict",
            "search_patterns(keyword: str) -> list"
        ],
        "Escritura": [
            "add_pattern(pattern, response) -> dict",
            "update_pattern(index, pattern, response) -> dict",
            "delete_pattern(index) -> bool",
            "add_default_response(response) -> dict",
            "delete_default_response(index) -> bool"
        ],
        "Exportación": [
            "export_as_python() -> str"
        ]
    }
    
    for category, method_list in methods.items():
        print(f"  {category}:")
        for method in method_list:
            print(f"    • {method}")
        print()
    
    # 6. Ejemplo: Crear Patón
    print_header("6️⃣  EJEMPLO: CREAR UN PATRÓN")
    print("  1️⃣  Terminal 1 - Inicia servidor:")
    print("     $ python chatbot_monolith.py --mode brain")
    print()
    print("  2️⃣  Terminal 2 - Crear patrón con curl:")
    print("""     $ curl -X POST "http://localhost:8000/api/v1/brain/patterns" \\
       -H "Content-Type: application/json" \\
       -d '{
         "pattern": ["i", "am", [1, "feeling"]],
         "response": ["You", "seem", [1, "feeling"]]
       }'
    """)
    print("  3️⃣  Respuesta del servidor:")
    print("""     {
       "status": "created",
       "index": 30,
       "pattern": ["i", "am", [1, "feeling"]],
       "response": ["You", "seem", [1, "feeling"]]
     }
    """)
    print("  4️⃣  Verificar persistencia:")
    print("     $ cat brain_data.json | grep -A2 'feeling'")
    print("     ✅ El patrón se guardó en brain_data.json\n")
    
    # 7. Comparación Antes/Después
    print_header("7️⃣  COMPARACIÓN: ANTES vs DESPUÉS")
    
    comparison = [
        ("Aspecto", "ANTES", "AHORA"),
        ("─"*15, "─"*20, "─"*25),
        ("Función", "def get_default_brain()", "python --mode brain"),
        ("Tipo", "Código estático", "Servidor REST"),
        ("Lectura", "✅ Sí", "✅ Sí"),
        ("Escritura", "❌ No", "✅ Sí (CRUD)"),
        ("Persistencia", "❌ No", "✅ JSON"),
        ("Búsqueda", "❌ No", "✅ Sí (Keyword)"),
        ("Exportación", "❌ No", "✅ Python/JSON"),
        ("UI", "❌ Ninguna", "✅ Swagger"),
        ("API", "❌ No", "✅ RESTful"),
        ("Integración", "Hardcoded", "HTTP Client"),
        ("Escalabilidad", "Local", "Red"),
    ]
    
    for row in comparison:
        print(f"  {row[0]:20} │ {row[1]:20} │ {row[2]}")
    print()
    
    # 8. Casos de Uso
    print_header("8️⃣  CASOS DE USO")
    
    usecases = [
        ("🌐 Panel Web", "Admin UI que se conecta al Brain Server"),
        ("🤖 Entrenamiento", "Agrega patrones basado en feedback"),
        ("🔄 Sincronización", "Múltiples instancias de chatbot"),
        ("📊 Analytics", "Analiza patrones usados"),
        ("💾 Versionamiento", "Exporta y versiona en Git"),
        ("🚀 Escalabilidad", "Centraliza cerebro del chatbot"),
    ]
    
    for title, desc in usecases:
        print(f"  {title:20} → {desc}")
    print()
    
    # 9. Configuración
    print_header("9️⃣  CONFIGURACIÓN (EN SETTINGS)")
    
    config = {
        "API_HOST": '127.0.0.1 (cambiar a "0.0.0.0" para acceso remoto)',
        "API_PORT": '8000',
        "LOG_LEVEL": 'INFO',
        "Persistencia": "brain_data.json"
    }
    
    for key, value in config.items():
        print(f"  {key:20} = {value}")
    print()
    
    # 10. Próximos Pasos
    print_header("🔟 PRÓXIMOS PASOS")
    
    steps = [
        "1. Inicia el servidor",
        "   $ python chatbot_monolith.py --mode brain",
        "",
        "2. Abre Swagger UI",
        "   http://localhost:8000/docs",
        "",
        "3. Prueba endpoints",
        "   Usa Swagger para crear/editar/buscar patrones",
        "",
        "4. Crea cliente web/mobile",
        "   Conecta tu app al Brain Server",
        "",
        "5. Integra logística",
        "   Automatiza la creación de patrones",
        "",
        "6. Monitorea",
        "   Observa qué patrones se usan más"
    ]
    
    for step in steps:
        print(f"  {step}")
    print()
    
    # 11. Archivos Importantes
    print_header("1️⃣1️⃣ ARCHIVOS IMPORTANTES")
    
    files = [
        ("chatbot_monolith.py", "Código principal (600+ líneas nuevas)"),
        ("brain_data.json", "Persistencia automática"),
        ("BRAIN_SERVER_GUIDE.md", "Documentación completa"),
        ("BRAIN_SERVER_SETUP_SUMMARY.md", "Resumen de cambios"),
        ("brain_client_examples.py", "Ejemplos ejecutables"),
        ("BRAIN_SERVER_TECHNICAL_SUMMARY.md", "Resumen técnico")
    ]
    
    for filename, desc in files:
        print(f"  📄 {filename:40} → {desc}")
    print()
    
    # Final
    print_header("✅ ¡LISTO!")
    print_box([
        "Tu función get_default_brain() ahora es un",
        "SERVIDOR REST PROFESIONAL con capacidades",
        "CRUD completas, persistencia automática y",
        "documentación interactiva (Swagger UI).",
        "",
        "¡Disfruta del Brain Server! 🚀"
    ])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Visualizador interrumpido")
