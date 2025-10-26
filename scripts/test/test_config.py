#!/usr/bin/env python3
"""
🧪 TEST SIMPLE - Verificar configuración local
"""

import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno desde archivo .env
from dotenv import load_dotenv
load_dotenv()

def test_configuration():
    """Verificar que la configuración esté correcta"""
    print("🔧 Verificando configuración local...")
    
    # Verificar archivo .env
    if not Path(".env").exists():
        print("❌ No se encontró el archivo .env")
        print("💡 Copia env_template.txt como .env y edita los valores:")
        print("   cp env_template.txt .env")
        print("   nano .env")
        return False
    
    print("✅ Archivo .env encontrado")
    
    # Verificar variables requeridas
    required_vars = ["GEMINI_API_KEY", "CLOUD_SQL_PASSWORD", "CLOUD_SQL_HOST"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {value[:10]}...")
    
    if missing_vars:
        print(f"❌ Variables faltantes: {', '.join(missing_vars)}")
        print("💡 Asegúrate de tener estas variables en tu archivo .env")
        return False
    
    # Verificar configuración adicional
    print(f"✅ VECTOR_SEARCH_K: {os.getenv('VECTOR_SEARCH_K', '20')}")
    print(f"✅ GEMINI_TEMPERATURE: {os.getenv('GEMINI_TEMPERATURE', '0.7')}")
    
    return True

def test_imports():
    """Verificar que los imports funcionen"""
    print("\n📦 Verificando imports...")
    
    try:
        from app.services.rag_service import RAGService
        print("✅ RAGService importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando RAGService: {e}")
        return False
    
    try:
        from app.core.config import settings
        print("✅ Settings importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando Settings: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("🧪 TEST SIMPLE - AI Resume Agent v5.1")
    print("=" * 50)
    
    # Verificar configuración
    if not test_configuration():
        print("\n❌ Configuración incorrecta. Revisa los pasos anteriores.")
        return
    
    # Verificar imports
    if not test_imports():
        print("\n❌ Error en imports. Verifica la instalación.")
        return
    
    print("\n🎉 ¡Todo listo para el testing!")
    print("💡 Ahora puedes ejecutar:")
    print("   python test_local_v51.py")

if __name__ == "__main__":
    main()
