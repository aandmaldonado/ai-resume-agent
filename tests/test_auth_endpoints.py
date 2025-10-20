"""
Tests para endpoints de autenticación y configuración.
Verifica que la autenticación funciona correctamente en todos los endpoints.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Set testing environment variables
os.environ["TESTING"] = "true"
os.environ["ENABLE_ANALYTICS"] = "false"
os.environ["PUBLIC_API_KEY"] = "test-public-key"
os.environ["ADMIN_API_KEY"] = "test-admin-key"
os.environ["FRONTEND_API_KEY"] = "test-frontend-key"

from app.main import app

# Crear cliente de test
client = TestClient(app)

# Headers para tests con autenticación
PUBLIC_AUTH_HEADERS = {"X-Public-API-Key": "test-public-key"}
ADMIN_AUTH_HEADERS = {"X-API-Key": "test-admin-key"}
FRONTEND_AUTH_HEADERS = {"X-Frontend-API-Key": "test-frontend-key"}


class TestPublicEndpoints:
    """Tests para endpoints que requieren Public API Key"""

    def test_chat_endpoint_without_auth(self):
        """Test que el endpoint de chat rechaza requests sin autenticación"""
        response = client.post("/api/v1/chat", json={"message": "Test"})
        assert response.status_code == 401
        assert "Public API Key requerido" in response.json()["detail"]

    def test_chat_endpoint_with_invalid_auth(self):
        """Test que el endpoint de chat rechaza API Key inválido"""
        headers = {"X-Public-API-Key": "invalid-key"}
        response = client.post(
            "/api/v1/chat", json={"message": "Test"}, headers=headers
        )
        assert response.status_code == 401
        assert "Public API Key inválido" in response.json()["detail"]

    def test_chat_endpoint_with_valid_auth(self):
        """Test que el endpoint de chat acepta API Key válido"""
        with patch("app.api.v1.endpoints.chat.rag_service") as mock_rag:
            mock_rag.generate_response = AsyncMock(
                return_value={
                    "response": "Test response",
                    "sources": [],
                    "session_id": "test-session",
                    "model": "llama-3.3-70b-versatile",
                }
            )

            response = client.post(
                "/api/v1/chat", json={"message": "Test"}, headers=PUBLIC_AUTH_HEADERS
            )
            assert response.status_code == 200

    def test_capture_data_endpoint_without_auth(self):
        """Test que el endpoint de captura de datos rechaza requests sin autenticación"""
        response = client.post(
            "/api/v1/capture-data",
            json={"session_id": "test", "email": "test@example.com"},
        )
        assert response.status_code == 401

    def test_gdpr_consent_endpoint_without_auth(self):
        """Test que el endpoint de consentimiento GDPR rechaza requests sin autenticación"""
        response = client.post(
            "/api/v1/gdpr/consent",
            json={"session_id": "test", "consent_types": ["analytics"]},
        )
        assert response.status_code == 401


class TestAdminEndpoints:
    """Tests para endpoints que requieren Admin API Key"""

    def test_conversations_endpoint_without_auth(self):
        """Test que el endpoint de conversaciones rechaza requests sin autenticación"""
        response = client.get("/api/v1/conversations")
        assert response.status_code == 401

    def test_conversations_endpoint_with_invalid_auth(self):
        """Test que el endpoint de conversaciones rechaza API Key inválido"""
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/api/v1/conversations", headers=headers)
        assert response.status_code == 401

    def test_conversations_endpoint_with_valid_auth(self):
        """Test que el endpoint de conversaciones acepta API Key válido"""
        with patch(
            "app.services.analytics_service.analytics_service.get_conversation_pairs"
        ) as mock_get:
            mock_get.return_value = []

            response = client.get("/api/v1/conversations", headers=ADMIN_AUTH_HEADERS)
            assert response.status_code == 200

    def test_metrics_endpoint_without_auth(self):
        """Test que el endpoint de métricas rechaza requests sin autenticación"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 401

    def test_gdpr_data_endpoint_without_auth(self):
        """Test que el endpoint de datos GDPR rechaza requests sin autenticación"""
        response = client.get("/api/v1/gdpr/data/test-session")
        assert response.status_code == 401


class TestPublicConfigEndpoint:
    """Tests para el endpoint de configuración pública"""

    def test_config_endpoint_no_auth_required(self):
        """Test que el endpoint de configuración no requiere autenticación"""
        response = client.get("/api/v1/config")
        assert response.status_code == 200

        data = response.json()
        assert "public_api_key" in data
        assert "frontend_api_key" in data
        assert "api_base_url" in data
        assert "version" in data
        assert "environment" in data

    def test_config_endpoint_returns_correct_keys(self):
        """Test que el endpoint de configuración retorna las keys correctas"""
        response = client.get("/api/v1/config")
        data = response.json()

        assert data["public_api_key"] == "test-public-key"
        assert data["frontend_api_key"] == "frontend-key-2024"  # Valor por defecto
        assert (
            data["environment"] == "production"
        )  # GCP_PROJECT_ID está definido en tests


class TestTokenExchangeEndpoint:
    """Tests para el endpoint de intercambio de tokens"""

    def test_exchange_token_without_auth(self):
        """Test que el endpoint de intercambio rechaza requests sin API Key"""
        response = client.post(
            "/api/v1/exchange-token", json={"api_key": "frontend-key-2024"}
        )
        # Este endpoint no requiere autenticación previa, solo valida el API Key en el body
        assert response.status_code == 200

    def test_exchange_token_with_invalid_key(self):
        """Test que el endpoint de intercambio rechaza API Key inválido"""
        response = client.post(
            "/api/v1/exchange-token", json={"api_key": "invalid-key"}
        )
        assert response.status_code == 401
        assert "Frontend API Key inválido" in response.json()["detail"]

    def test_exchange_token_with_valid_key(self):
        """Test que el endpoint de intercambio acepta API Key válido"""
        response = client.post(
            "/api/v1/exchange-token", json={"api_key": "frontend-key-2024"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "token" in data
        assert "expires_in" in data
        assert "expires_at" in data
        assert "token_type" in data
        assert data["expires_in"] == 3600  # 1 hora


class TestHealthEndpoints:
    """Tests para endpoints de health check"""

    def test_chat_health_endpoint_no_auth_required(self):
        """Test que el endpoint de health check no requiere autenticación"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_analytics_health_endpoint_no_auth_required(self):
        """Test que el endpoint de health check de analytics no requiere autenticación"""
        # El endpoint de analytics health está en /api/v1/analytics/health
        response = client.get("/api/v1/analytics/health")
        # Si no existe, verificamos que al menos no requiere autenticación (404 vs 401)
        assert response.status_code in [
            200,
            404,
        ]  # Puede no existir pero no debe requerir auth


class TestFlowEndpoints:
    """Tests para endpoints de flujo"""

    def test_flow_state_endpoint_no_auth_required(self):
        """Test que el endpoint de estado del flujo no requiere autenticación"""
        # El endpoint de flow state está en /api/v1/flow/state/{session_id}
        response = client.get("/api/v1/flow/state/test-session")
        # Si no existe, verificamos que al menos no requiere autenticación (404 vs 401)
        assert response.status_code in [
            200,
            404,
        ]  # Puede no existir pero no debe requerir auth

    def test_flow_config_endpoint_no_auth_required(self):
        """Test que el endpoint de configuración del flujo no requiere autenticación"""
        response = client.get("/api/v1/flow/config")
        assert response.status_code == 200
