"""
Tests unitarios para app/core/secrets.py
Testea la gestión de secretos con Google Cloud Secret Manager y fallback a variables de entorno.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from google.api_core import exceptions as gcp_exceptions

from app.core.secrets import SecretManager, get_database_password, get_groq_api_key, get_gcp_project_id


class TestSecretManager:
    """Tests para la clase SecretManager."""

    def test_secret_manager_init_with_client(self):
        """Test inicialización exitosa con cliente Secret Manager."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            secret_manager = SecretManager()
            
            assert secret_manager.client is not None
            mock_client_class.assert_called_once()

    def test_secret_manager_init_without_client(self):
        """Test inicialización sin cliente Secret Manager (fallback)."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            secret_manager = SecretManager()
            
            assert secret_manager.client is None

    def test_get_secret_from_secret_manager_success(self):
        """Test obtención exitosa de secreto desde Secret Manager."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.payload.data.decode.return_value = "secret-value"
            mock_client.access_secret_version.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            with patch('app.core.secrets.settings') as mock_settings:
                mock_settings.GCP_PROJECT_ID = "test-project"
                
                secret_manager = SecretManager()
                result = secret_manager.get_secret("test-secret")
                
                assert result == "secret-value"
                mock_client.access_secret_version.assert_called_once()

    def test_get_secret_secret_not_found_fallback_env(self):
        """Test fallback a variable de entorno cuando secreto no se encuentra."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client = Mock()
            mock_client.access_secret_version.side_effect = gcp_exceptions.NotFound("Not found")
            mock_client_class.return_value = mock_client
            
            with patch('app.core.secrets.settings') as mock_settings:
                mock_settings.GCP_PROJECT_ID = "test-project"
                
                with patch.dict(os.environ, {'TEST_SECRET': 'env-value'}):
                    secret_manager = SecretManager()
                    result = secret_manager.get_secret("test-secret")
                    
                    assert result == "env-value"

    def test_get_secret_secret_manager_error_fallback_env(self):
        """Test fallback a variable de entorno cuando hay error en Secret Manager."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client = Mock()
            mock_client.access_secret_version.side_effect = Exception("GCP Error")
            mock_client_class.return_value = mock_client
            
            with patch('app.core.secrets.settings') as mock_settings:
                mock_settings.GCP_PROJECT_ID = "test-project"
                
                with patch.dict(os.environ, {'TEST_SECRET': 'env-value'}):
                    secret_manager = SecretManager()
                    result = secret_manager.get_secret("test-secret")
                    
                    assert result == "env-value"

    def test_get_secret_no_client_fallback_env(self):
        """Test fallback a variable de entorno cuando no hay cliente."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            with patch.dict(os.environ, {'TEST_SECRET': 'env-value'}):
                secret_manager = SecretManager()
                result = secret_manager.get_secret("test-secret")
                
                assert result == "env-value"

    def test_get_secret_with_default_value(self):
        """Test uso de valor por defecto cuando no se encuentra en ninguna fuente."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            secret_manager = SecretManager()
            result = secret_manager.get_secret("nonexistent-secret", default_value="default-value")
            
            assert result == "default-value"

    def test_get_secret_no_sources_raises_error(self):
        """Test que se lanza error cuando no hay fuentes disponibles."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            secret_manager = SecretManager()
            
            with pytest.raises(ValueError, match="No se pudo obtener el secreto"):
                secret_manager.get_secret("nonexistent-secret")

    def test_get_secret_env_var_name_conversion(self):
        """Test conversión correcta del nombre del secreto a variable de entorno."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            with patch.dict(os.environ, {'CLOUD_SQL_PASSWORD': 'env-password'}):
                secret_manager = SecretManager()
                result = secret_manager.get_secret("cloud-sql-password")
                
                assert result == "env-password"

    def test_get_secret_env_var_name_with_hyphens(self):
        """Test conversión de nombres con guiones a guiones bajos."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            with patch.dict(os.environ, {'GROQ_API_KEY': 'env-key'}):
                secret_manager = SecretManager()
                result = secret_manager.get_secret("groq-api-key")
                
                assert result == "env-key"


class TestSecretFunctions:
    """Tests para las funciones helper de secretos."""

    def test_get_database_password_from_secret_manager(self):
        """Test obtención de contraseña de base de datos."""
        with patch('app.core.secrets.secret_manager') as mock_secret_manager:
            mock_secret_manager.get_secret.return_value = "test-password"
            
            result = get_database_password()
            
            assert result == "test-password"
            mock_secret_manager.get_secret.assert_called_once_with("CLOUD_SQL_PASSWORD")

    def test_get_groq_api_key_from_secret_manager(self):
        """Test obtención de API key de Groq."""
        with patch('app.core.secrets.secret_manager') as mock_secret_manager:
            mock_secret_manager.get_secret.return_value = "test-api-key"
            
            result = get_groq_api_key()
            
            assert result == "test-api-key"
            mock_secret_manager.get_secret.assert_called_once_with("GROQ_API_KEY")

    def test_get_gcp_project_id_with_default(self):
        """Test obtención de Project ID con valor por defecto."""
        with patch('app.core.secrets.secret_manager') as mock_secret_manager:
            mock_secret_manager.get_secret.return_value = "test-project"
            
            result = get_gcp_project_id()
            
            assert result == "test-project"
            mock_secret_manager.get_secret.assert_called_once_with(
                "GCP_PROJECT_ID", 
                default_value="ai-resume-agent"
            )

    def test_get_gcp_project_id_custom_default(self):
        """Test obtención de Project ID con valor por defecto personalizado."""
        with patch('app.core.secrets.secret_manager') as mock_secret_manager:
            mock_secret_manager.get_secret.return_value = "custom-project"
            
            result = get_gcp_project_id()
            
            assert result == "custom-project"


class TestSecretManagerIntegration:
    """Tests de integración para SecretManager."""

    def test_secret_manager_with_real_env_vars(self):
        """Test con variables de entorno reales."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            with patch.dict(os.environ, {
                'CLOUD_SQL_PASSWORD': 'real-password',
                'GROQ_API_KEY': 'real-api-key',
                'GCP_PROJECT_ID': 'real-project'
            }):
                secret_manager = SecretManager()
                
                assert secret_manager.get_secret("cloud-sql-password") == "real-password"
                assert secret_manager.get_secret("groq-api-key") == "real-api-key"
                assert secret_manager.get_secret("gcp-project-id") == "real-project"

    def test_secret_manager_error_handling(self):
        """Test manejo de errores en SecretManager."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client = Mock()
            mock_client.access_secret_version.side_effect = Exception("Network error")
            mock_client_class.return_value = mock_client
            
            with patch('app.core.secrets.settings') as mock_settings:
                mock_settings.GCP_PROJECT_ID = "test-project"
                
                with patch.dict(os.environ, {'TEST_SECRET': 'fallback-value'}):
                    secret_manager = SecretManager()
                    result = secret_manager.get_secret("test-secret")
                    
                    assert result == "fallback-value"

    def test_secret_manager_logging(self):
        """Test que el logging funciona correctamente."""
        with patch('app.core.secrets.secretmanager.SecretManagerServiceClient') as mock_client_class:
            mock_client_class.side_effect = Exception("GCP not available")
            
            with patch('app.core.secrets.logger') as mock_logger:
                secret_manager = SecretManager()
                
                # Verificar que se registró el warning
                mock_logger.warning.assert_called()
