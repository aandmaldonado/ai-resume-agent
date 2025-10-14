#!/usr/bin/env python3
"""
Script de prueba para verificar que la memoria conversacional funciona.
"""
import requests
import json
from uuid import uuid4

# Configuración
API_URL = "http://localhost:8080/api/v1/chat"
SESSION_ID = f"test-{uuid4()}"

def send_message(message: str, session_id: str) -> dict:
    """Envía un mensaje al chatbot y retorna la respuesta"""
    payload = {
        "message": message,
        "session_id": session_id
    }
    
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()

def main():
    print("🧪 PRUEBA DE MEMORIA CONVERSACIONAL")
    print("=" * 60)
    print(f"Session ID: {SESSION_ID}")
    print("=" * 60)
    print()
    
    # Test 1: Primera pregunta
    print("👤 Usuario: ¿Cuál es tu experiencia con Python?")
    response1 = send_message("¿Cuál es tu experiencia con Python?", SESSION_ID)
    print(f"🤖 Bot: {response1['message'][:200]}...")
    print()
    
    # Test 2: Segunda pregunta
    print("👤 Usuario: ¿Y con Java?")
    response2 = send_message("¿Y con Java?", SESSION_ID)
    print(f"🤖 Bot: {response2['message'][:200]}...")
    print()
    
    # Test 3: Pregunta que requiere contexto (LA CLAVE)
    print("👤 Usuario: ¿Cuál de los dos prefieres?")
    response3 = send_message("¿Cuál de los dos prefieres?", SESSION_ID)
    print(f"🤖 Bot: {response3['message']}")
    print()
    
    # Verificación
    print("=" * 60)
    print("✅ VERIFICACIÓN:")
    if "python" in response3['message'].lower() or "java" in response3['message'].lower():
        print("✅ ¡MEMORIA FUNCIONA! El bot recordó Python y Java")
    else:
        print("❌ MEMORIA NO FUNCIONA - El bot no recordó el contexto")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar al servidor en http://localhost:8080")
        print("   Asegúrate de que el servidor esté corriendo con:")
        print("   ./scripts/setup/start-local.sh")
    except Exception as e:
        print(f"❌ ERROR: {e}")

