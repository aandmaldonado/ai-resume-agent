"""
Tests para el módulo de gestión de secretos.
Cubre Secret Manager y fallback a variables de entorno.
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.api_core import exceptions as gcp_exceptions

from app.core.secrets import (
    SecretManager,
    get_database_password,
    get_gcp_project_id,
    get_groq_api_key,
)


class TestSecretManager:
    """Tests para la clase SecretManager"""

    def test_secret_manager_init_with_client(self):
        """Test inicialización exitosa con cliente"""
        with patch(
            "app.core.secrets.secretmanager.SecretManagerServiceClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            sm = SecretManager()

            assert sm.client is not None
            assert sm.client == mock_client

    def test_secret_manager_init_without_client(self):
        """Test inicialización sin cliente (fallback)"""
        with patch(
            "app.core.secrets.secretmanager.SecretManagerServiceClient",
            side_effect=Exception("No credentials"),
        ):
            sm = SecretManager()

            assert sm.client is None

    def test_get_secret_from_secret_manager_success(self):
        """Test obtención exitosa de secreto desde Secret Manager"""
        with patch(
            "app.core.secrets.secretmanager.SecretManagerServiceClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.payload.data = b"secret_value"
            mock_client.access_secret_version.return_value = mock_response
            mock_client_class.return_value = mock_client

            sm = SecretManager()
            result = sm.get_secret("test-secret")

            assert result == "secret_value"
            mock_client.access_secret_version.assert_called_once()

    def test_get_secret_secret_not_found_fallback_env(self):
        """Test fallback a variable de entorno cuando secreto no encontrado"""
        with patch(
            "app.core.secrets.secretmanager.SecretManagerServiceClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.access_secret_version.side_effect = gcp_exceptions.NotFound(
                "Secret not found"
            )
            mock_client_class.return_value = mock_client

            with patch.dict(os.environ, {"TEST_SECRET": "env_value"}, clear=False):
                sm = SecretManager()
                result = sm.get_secret("test-secret")

                assert result == "env_value"

    def test_get_secret_secret_manager_error_fallback_env(self):
        """Test fallback a variable de entorno cuando hay error en Secret Manager"""
        with patch(
            "app.core.secrets.secretmanager.SecretManagerServiceClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.access_secret_version.side_effect = Exception(
                "Connection error"
            )
            mock_client_class.return_value = mock_client

            with patch.dict(os.environ, {"TEST_SECRET": "env_value"}, clear=False):
                sm = SecretManager()
                result = sm.get_secret("test-secret")

                assert result == "env_value"

    def test_get_secret_no_client_fallback_env(self):
        """Test fallback a variable de entorno cuando no hay cliente"""
        with patch.dict(os.environ, {"TEST_SECRET": "env_value"}, clear=False):
            sm = SecretManager()
            sm.client = None  # Simular sin cliente

            result = sm.get_secret("test-secret")

            assert result == "env_value"

    def test_get_secret_with_default_value(self):
        """Test usando valor por defecto cuando no se encuentra en ninguna fuente"""
        sm = SecretManager()
        sm.client = None

        # Limpiar variable de entorno
        with patch.dict(os.environ, {}, clear=True):
            result = sm.get_secret("nonexistent-secret", default_value="default_value")

            assert result == "default_value"

    def test_get_secret_no_sources_raises_error(self):
        """Test que lanza error cuando no hay fuentes disponibles"""
        sm = SecretManager()
        sm.client = None

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No se pudo obtener el secreto"):
                sm.get_secret("nonexistent-secret")


class TestSecretFunctions:
    """Tests para las funciones helper de secretos"""

    def test_get_database_password_from_secret_manager(self):
        """Test obtención de contraseña de BD desde Secret Manager"""
        with patch("app.core.secrets.secret_manager") as mock_sm:
            mock_sm.get_secret.return_value = "db_password_123"

            result = get_database_password()

            assert result == "db_password_123"
            mock_sm.get_secret.assert_called_once_with("CLOUD_SQL_PASSWORD")

    def test_get_groq_api_key_from_secret_manager(self):
        """Test obtención de API key de Groq desde Secret Manager"""
        with patch("app.core.secrets.secret_manager") as mock_sm:
            mock_sm.get_secret.return_value = "groq_api_key_456"

            result = get_groq_api_key()

            assert result == "groq_api_key_456"
            mock_sm.get_secret.assert_called_once_with("GROQ_API_KEY")

    def test_get_gcp_project_id_with_default(self):
        """Test obtención de Project ID con valor por defecto"""
        with patch("app.core.secrets.secret_manager") as mock_sm:
            mock_sm.get_secret.return_value = "ai-resume-agent"

            result = get_gcp_project_id()

            assert result == "ai-resume-agent"
            mock_sm.get_secret.assert_called_once_with(
                "GCP_PROJECT_ID", default_value="ai-resume-agent"
            )

    def test_get_gcp_project_id_custom_default(self):
        """Test obtención de Project ID con valor por defecto personalizado"""
        with patch("app.core.secrets.secret_manager") as mock_sm:
            mock_sm.get_secret.return_value = "custom-project"

            result = get_gcp_project_id()

            assert result == "custom-project"
            mock_sm.get_secret.assert_called_once_with(
                "GCP_PROJECT_ID", default_value="ai-resume-agent"
            )


class TestSecretManagerIntegration:
    """Tests de integración para Secret Manager"""

    def test_secret_manager_with_real_env_vars(self):
        """Test con variables de entorno reales"""
        with patch.dict(
            os.environ,
            {"TEST_SECRET_1": "env_value_1", "TEST_SECRET_2": "env_value_2"},
            clear=False,
        ):
            sm = SecretManager()
            sm.client = None  # Forzar uso de variables de entorno

            result1 = sm.get_secret("test-secret-1")
            result2 = sm.get_secret("test-secret-2")

            assert result1 == "env_value_1"
            assert result2 == "env_value_2"

    def test_secret_manager_error_handling(self):
        """Test manejo de errores en diferentes escenarios"""
        sm = SecretManager()
        sm.client = None

        # Test con variable de entorno vacía
        with patch.dict(os.environ, {"EMPTY_SECRET": ""}):
            result = sm.get_secret("empty-secret", default_value="default")
            assert result == "default"

        # Test con variable de entorno None
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                sm.get_secret("nonexistent-secret")

    def test_secret_manager_logging(self):
        """Test que verifica que se generan logs apropiados"""
        with patch("app.core.secrets.logger") as mock_logger:
            # Test log de inicialización exitosa
            with patch("app.core.secrets.secretmanager.SecretManagerServiceClient"):
                sm = SecretManager()
                mock_logger.info.assert_called_with(
                    "✓ Secret Manager client inicializado"
                )

            # Test log de inicialización fallida
            with patch(
                "app.core.secrets.secretmanager.SecretManagerServiceClient",
                side_effect=Exception("No credentials"),
            ):
                sm = SecretManager()
                mock_logger.warning.assert_called_with(
                    "⚠️ Secret Manager no disponible: No credentials. Usando variables de entorno."
                )
