#!/usr/bin/env python3
"""
Script de prueba para verificar que los endpoints de analytics funcionan correctamente.
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from uuid import uuid4

import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
BASE_URL = "http://localhost:8080/api/v1"
session_id = f"test-endpoint-{uuid4().hex[:8]}"


def test_chat_endpoint():
    """Probar endpoint de chat con analytics integrados."""
    logger.info("🧪 Probando endpoint /chat con analytics...")

    # Test 1: Primer mensaje (debería mostrar bienvenida)
    logger.info("   📝 Test 1: Primer mensaje")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "Hola, ¿cómo estás?", "session_id": session_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "show_welcome"
    assert data["requires_data_capture"] == False
    assert data["requires_gdpr_consent"] == False
    logger.info("   ✅ Primer mensaje funcionando correctamente")

    # Esperar un poco para evitar rate limiting
    time.sleep(1)

    # Test 2: Segundo mensaje (debería solicitar captura de datos)
    logger.info("   📝 Test 2: Segundo mensaje")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "¿Cuál es tu experiencia con Python?",
            "session_id": session_id,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "request_data_capture"
    assert data["requires_data_capture"] == True
    logger.info("   ✅ Segundo mensaje funcionando correctamente")

    # Esperar un poco para evitar rate limiting
    time.sleep(1)

    # Test 3: Tercer mensaje (debería seguir solicitando captura hasta que se capturen datos)
    logger.info("   📝 Test 3: Tercer mensaje")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "¿Qué tecnologías conoces?", "session_id": session_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert (
        data["action_type"] == "request_data_capture"
    )  # Debería seguir solicitando captura
    assert data["requires_data_capture"] == True
    logger.info("   ✅ Tercer mensaje funcionando correctamente (solicita captura)")

    logger.info("🎉 Endpoint /chat funcionando correctamente!")


def test_complete_flow():
    """Probar el flujo completo: chat -> captura -> GDPR -> chat normal."""
    logger.info("🧪 Probando flujo completo...")

    session_id = f"complete-flow-{uuid4().hex[:8]}"

    # 1. Primer mensaje (bienvenida)
    logger.info("   📝 Paso 1: Primer mensaje")
    response = requests.post(
        f"{BASE_URL}/chat", json={"message": "Hola", "session_id": session_id}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "show_welcome"
    logger.info("   ✅ Primer mensaje OK")

    # Esperar para evitar rate limiting
    time.sleep(2)

    # 2. Segundo mensaje (solicita captura)
    logger.info("   📝 Paso 2: Segundo mensaje")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "¿Cuál es tu experiencia?", "session_id": session_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "request_data_capture"
    logger.info("   ✅ Segundo mensaje OK")

    # 3. Capturar datos
    logger.info("   📝 Paso 3: Capturar datos")
    response = requests.post(
        f"{BASE_URL}/capture-data",
        json={
            "session_id": session_id,
            "email": "test@example.com",
            "user_type": "recruiter",
            "company": "Test Company",
            "role": "Senior Developer",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data_captured"] == True
    logger.info("   ✅ Captura de datos OK")

    # Esperar para evitar rate limiting
    time.sleep(2)

    # 4. Tercer mensaje (debería solicitar GDPR)
    logger.info("   📝 Paso 4: Tercer mensaje")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "¿Qué tecnologías conoces?", "session_id": session_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "request_gdpr_consent"
    assert data["requires_gdpr_consent"] == True
    logger.info("   ✅ Tercer mensaje OK")

    # Esperar para evitar rate limiting
    time.sleep(2)

    # 5. Dar consentimiento GDPR
    logger.info("   📝 Paso 5: Consentimiento GDPR")
    response = requests.post(
        f"{BASE_URL}/gdpr/consent",
        json={
            "session_id": session_id,
            "consent_types": ["analytics", "data_processing"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["consent_given"] == True
    logger.info("   ✅ Consentimiento GDPR OK")

    # Esperar para evitar rate limiting
    time.sleep(2)

    # 6. Cuarto mensaje (debería ser normal)
    logger.info("   📝 Paso 6: Cuarto mensaje")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "¿Cuál es tu experiencia con Python?",
            "session_id": session_id,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "normal_response"
    assert data["requires_data_capture"] == False
    assert data["requires_gdpr_consent"] == False
    logger.info("   ✅ Cuarto mensaje OK")

    logger.info("🎉 Flujo completo funcionando correctamente!")

    # Esperar para evitar rate limiting
    time.sleep(2)

    # Limpiar datos
    requests.delete(f"{BASE_URL}/gdpr/data/{session_id}")


def test_capture_data_endpoint():
    """Probar endpoint de captura de datos."""
    logger.info("🧪 Probando endpoint /capture-data...")

    response = requests.post(
        f"{BASE_URL}/capture-data",
        json={
            "session_id": session_id,
            "email": "test@example.com",
            "user_type": "recruiter",
            "company": "Test Company",
            "role": "Senior Developer",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data_captured"] == True
    assert data["session_id"] == session_id
    logger.info("   ✅ Captura de datos funcionando correctamente")

    logger.info("🎉 Endpoint /capture-data funcionando correctamente!")


def test_gdpr_endpoints():
    """Probar endpoints GDPR."""
    logger.info("🧪 Probando endpoints GDPR...")

    # Test 1: Registrar consentimiento
    logger.info("   📝 Test 1: Registrar consentimiento")
    response = requests.post(
        f"{BASE_URL}/gdpr/consent",
        json={
            "session_id": session_id,
            "consent_types": ["analytics", "data_processing"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["consent_given"] == True
    logger.info("   ✅ Registro de consentimiento funcionando correctamente")

    # Test 2: Obtener datos del usuario
    logger.info("   📝 Test 2: Obtener datos del usuario")
    response = requests.get(f"{BASE_URL}/gdpr/data/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["user_data"] is not None
    assert data["user_data"]["session_id"] == session_id
    logger.info("   ✅ Obtención de datos funcionando correctamente")

    # Test 3: Exportar datos
    logger.info("   📝 Test 3: Exportar datos")
    response = requests.get(f"{BASE_URL}/gdpr/export/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["export_data"] is not None

    # Verificar que el JSON exportado es válido
    export_json = json.loads(data["export_data"])
    assert "export_metadata" in export_json
    assert "user_data" in export_json
    logger.info("   ✅ Exportación de datos funcionando correctamente")

    logger.info("🎉 Endpoints GDPR funcionando correctamente!")


def test_flow_endpoints():
    """Probar endpoints de flujo."""
    logger.info("🧪 Probando endpoints de flujo...")

    # Test 1: Obtener estado del flujo
    logger.info("   📝 Test 1: Obtener estado del flujo")
    response = requests.get(f"{BASE_URL}/flow/state/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["data_captured"] == True
    assert data["gdpr_consent_given"] == True
    logger.info("   ✅ Estado del flujo funcionando correctamente")

    # Test 2: Obtener configuración del flujo
    logger.info("   📝 Test 2: Obtener configuración del flujo")
    response = requests.get(f"{BASE_URL}/flow/config")

    assert response.status_code == 200
    data = response.json()
    assert "data_capture_after_messages" in data
    assert "engagement_threshold" in data
    assert "flow_states" in data
    logger.info("   ✅ Configuración del flujo funcionando correctamente")

    logger.info("🎉 Endpoints de flujo funcionando correctamente!")


def test_metrics_endpoints():
    """Probar endpoints de métricas."""
    logger.info("🧪 Probando endpoints de métricas...")

    # Test 1: Obtener métricas generales
    logger.info("   📝 Test 1: Obtener métricas generales")
    response = requests.get(f"{BASE_URL}/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert "total_messages" in data
    assert "leads_captured" in data
    logger.info("   ✅ Métricas generales funcionando correctamente")

    # Test 2: Obtener métricas diarias
    logger.info("   📝 Test 2: Obtener métricas diarias")
    response = requests.get(f"{BASE_URL}/metrics/daily?days=7")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    logger.info("   ✅ Métricas diarias funcionando correctamente")

    # Test 3: Agregar métricas diarias
    logger.info("   📝 Test 3: Agregar métricas diarias")
    response = requests.post(f"{BASE_URL}/metrics/aggregate")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    logger.info("   ✅ Agregación de métricas funcionando correctamente")

    logger.info("🎉 Endpoints de métricas funcionando correctamente!")


def cleanup_test_data():
    """Limpiar datos de prueba."""
    logger.info(f"🧹 Limpiando datos de prueba: {session_id}")

    try:
        # Eliminar datos del usuario
        response = requests.delete(f"{BASE_URL}/gdpr/data/{session_id}")

        if response.status_code == 200:
            logger.info("   ✅ Datos de prueba eliminados correctamente")
        else:
            logger.warning("   ⚠️ No se pudieron eliminar los datos de prueba")

    except Exception as e:
        logger.error(f"❌ Error limpiando datos de prueba: {e}")


def main():
    """Función principal de prueba."""
    logger.info("🚀 Iniciando pruebas de endpoints de analytics...")

    try:
        # Probar endpoints en orden
        test_chat_endpoint()
        test_complete_flow()
        test_capture_data_endpoint()
        test_gdpr_endpoints()
        test_flow_endpoints()
        test_metrics_endpoints()

        logger.info("🎉 ¡Todas las pruebas de endpoints pasaron exitosamente!")

    except Exception as e:
        logger.error(f"❌ Error en las pruebas: {e}")
        raise

    finally:
        # Limpiar datos de prueba
        cleanup_test_data()


if __name__ == "__main__":
    main()
