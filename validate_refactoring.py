#!/usr/bin/env python3
"""
Script de validación para verificar la refactorización
"""
import sys
import os

def check_structure():
    """Verifica que la estructura de directorios sea correcta"""
    print("🔍 Verificando estructura de directorios...")
    
    checks = {
        "chatbot_monolitic/chatbot_core/__init__.py": "chatbot_core librería",
        "chatbot_monolitic/chatbot_core/settings/__init__.py": "settings módulo",
        "chatbot_monolitic/chatbot_core/nlp/__init__.py": "nlp módulo",
        "chatbot_monolitic/chatbot_core/actor/__init__.py": "actor módulo",
        "chatbot_monolitic/chatbot_core/storage/__init__.py": "storage módulo",
        "chatbot_monolitic/chatbot_core/llm/__init__.py": "llm módulo",
        "chatbot_monolitic/chatbot_core/brain_manager/__init__.py": "brain_manager módulo",
        "chatbot_monolitic/chatbot_core/utils/__init__.py": "utils módulo",
        "chatbot_monolitic/chatbot_monolith.py": "launcher chatbot_monolith.py",
        "core_chat_service/main.py": "core_chat_service main.py",
        "core_chat_service/app/__init__.py": "core_chat_service app",
        "core_chat_service/app/config/__init__.py": "core_chat_service config",
        "core_chat_service/app/models/__init__.py": "core_chat_service models",
        "core_chat_service/app/api/__init__.py": "core_chat_service api",
        "core_chat_service/app/services/__init__.py": "core_chat_service services",
        "ARCHITECTURE.md": "documentación de arquitectura",
    }
    
    all_ok = True
    for filepath, description in checks.items():
        # Usa ruta relativa al directorio actual
        full_path = os.path.join(os.getcwd(), filepath)
        if os.path.exists(full_path):
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} (NOT FOUND: {filepath})")
            all_ok = False
    
    return all_ok


def check_imports():
    """Verifica que los imports funcionan correctamente"""
    print("\n🔍 Verificando imports...")
    
    # Agregar path para que encuentre chatbot_core
    sys.path.insert(0, os.path.join(os.getcwd(), "chatbot_monolitic"))
    
    try:
        print("  📦 Importing chatbot_core...")
        from chatbot_core import (
            settings, get_logger, Actor, Response,
            SimpleConversationStorage, BrainManager,
            PatternEngine, Tokenizer, PronounTranslator,
            EmbeddingService, LLMFallback
        )
        print("  ✅ chatbot_core imports OK")
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False


def check_launcher():
    """Verifica que el launcher tenga la estructura correcta"""
    print("\n🔍 Verificando launcher (chatbot_monolith.py)...")
    
    launcher_path = "chatbot_monolitic/chatbot_monolith.py"
    
    try:
        with open(launcher_path, 'r') as f:
            content = f.read()
        
        checks = {
            "from chatbot_core import": "Importa desde chatbot_core",
            "def run_cli()": "Tiene función run_cli",
            "def run_api()": "Tiene función run_api",
            "def run_brain_server()": "Tiene función run_brain_server",
            "def main()": "Tiene función main",
        }
        
        all_ok = True
        for check, description in checks.items():
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  ❌ Error reading launcher: {e}")
        return False


def check_core_chat_service():
    """Verifica que core_chat_service esté bien estructurado"""
    print("\n🔍 Verificando core_chat_service...")
    
    checks = {
        "core_chat_service/main.py": "main.py exists",
        "core_chat_service/app/config/settings.py": "settings.py",
        "core_chat_service/app/models/schemas.py": "schemas.py",
        "core_chat_service/app/services/tenant_service.py": "tenant_service.py",
        "core_chat_service/app/api/routes.py": "routes.py",
    }
    
    all_ok = True
    for filepath, description in checks.items():
        if os.path.exists(filepath):
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} NOT FOUND")
            all_ok = False
    
    return all_ok


def main():
    """Ejecuta todas las validaciones"""
    print("\n" + "=" * 70)
    print("🚀 VALIDACIÓN DE REFACTORIZACIÓN")
    print("=" * 70)
    
    results = []
    
    results.append(("Estructura", check_structure()))
    results.append(("Launcher", check_launcher()))
    results.append(("Core Chat Service", check_core_chat_service()))
    results.append(("Imports", check_imports()))
    
    print("\n" + "=" * 70)
    print("📊 RESULTADOS")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✅ ¡REFACTORIZACIÓN EXITOSA!")
        print("\nPróximos pasos:")
        print("  1. Instalar dependencies: pip install -e chatbot_monolitic/")
        print("  2. Instalar core_chat_service: cd core_chat_service && pip install -r requirements.txt")
        print("  3. Ejecutar launcher: python chatbot_monolitic/chatbot_monolith.py --mode cli")
        print("  4. Ejecutar API: cd core_chat_service && python main.py")
        return 0
    else:
        print("\n❌ Hay problemas que resolver.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
