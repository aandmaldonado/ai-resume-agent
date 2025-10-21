"""
Tests unitarios para app/core/config.py
Testea la configuración de la aplicación usando Pydantic Settings.
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    """Tests para la clase Settings."""

    def test_default_settings(self):
        """Test que los valores por defecto se cargan correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key'
        }):
            settings = Settings()
            
            # Valores por defecto
            assert settings.PROJECT_NAME == "AI Resume Agent"
            assert settings.VERSION == "1.0.0"
            assert settings.API_V1_STR == "/api/v1"
            assert settings.GCP_REGION == "europe-west1"
            assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
            assert settings.GROQ_TEMPERATURE == 0.7
            assert settings.GROQ_MAX_TOKENS == 1024
            assert settings.GROQ_TIMEOUT == 30
            assert settings.VERTEX_AI_EMBEDDING_MODEL == "textembedding-gecko@003"
            assert settings.VERTEX_AI_EMBEDDING_LOCATION == "us-central1"
            assert settings.VECTOR_COLLECTION_NAME == "portfolio_knowledge"
            assert settings.VECTOR_SEARCH_K == 3
            assert settings.MAX_CONVERSATION_HISTORY == 5
            assert settings.SESSION_TIMEOUT_MINUTES == 60
            assert settings.RATE_LIMIT_PER_MINUTE == 10
            assert settings.TESTING is False
            assert settings.ENABLE_ANALYTICS is True
            assert settings.DATA_CAPTURE_AFTER_MESSAGES == 2
            assert settings.ENGAGEMENT_THRESHOLD == 0.6
            assert settings.MAX_DATA_CAPTURE_ATTEMPTS == 3
            assert settings.MAX_GDPR_CONSENT_ATTEMPTS == 3
            assert settings.DATA_RETENTION_DAYS == 365
            assert settings.ANONYMIZE_AFTER_DAYS == 90
            assert settings.LOG_LEVEL == "INFO"

    def test_environment_variables(self):
        """Test que las variables de entorno se cargan correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'my-project',
            'GROQ_API_KEY': 'my-groq-key',
            'CLOUD_SQL_HOST': 'my-host',
            'CLOUD_SQL_PORT': '5433',
            'CLOUD_SQL_DB': 'my-db',
            'CLOUD_SQL_USER': 'my-user',
            'CLOUD_SQL_PASSWORD': 'my-password',
            'PORTFOLIO_BUCKET': 'my-bucket',
            'PORTFOLIO_FILE': 'my-file.yaml'
        }):
            settings = Settings()
            
            assert settings.GCP_PROJECT_ID == "my-project"
            assert settings.GROQ_API_KEY == "my-groq-key"
            assert settings.CLOUD_SQL_HOST == "my-host"
            assert settings.CLOUD_SQL_PORT == "5433"
            assert settings.CLOUD_SQL_DB == "my-db"
            assert settings.CLOUD_SQL_USER == "my-user"
            assert settings.CLOUD_SQL_PASSWORD == "my-password"
            assert settings.PORTFOLIO_BUCKET == "my-bucket"
            assert settings.PORTFOLIO_FILE == "my-file.yaml"

    def test_database_url_property(self):
        """Test que la propiedad database_url se construye correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'CLOUD_SQL_HOST': 'localhost',
            'CLOUD_SQL_PORT': '5432',
            'CLOUD_SQL_DB': 'testdb',
            'CLOUD_SQL_USER': 'testuser',
            'CLOUD_SQL_PASSWORD': 'testpass'
        }):
            settings = Settings()
            expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
            assert settings.database_url == expected_url

    def test_database_url_with_connection_name(self):
        """Test que la URL de base de datos incluye connection_name cuando está disponible."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'CLOUD_SQL_CONNECTION_NAME': 'test-project:europe-west1:test-instance',
            'CLOUD_SQL_HOST': 'localhost',
            'CLOUD_SQL_PORT': '5432',
            'CLOUD_SQL_DB': 'testdb',
            'CLOUD_SQL_USER': 'testuser',
            'CLOUD_SQL_PASSWORD': 'testpass'
        }):
            settings = Settings()
            expected_url = "postgresql://testuser:testpass@/testdb?host=/cloudsql/test-project:europe-west1:test-instance"
            assert settings.database_url == expected_url

    def test_async_database_url_property(self):
        """Test que la propiedad ASYNC_DATABASE_URL se construye correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'CLOUD_SQL_HOST': 'localhost',
            'CLOUD_SQL_PORT': '5432',
            'CLOUD_SQL_DB': 'testdb',
            'CLOUD_SQL_USER': 'testuser',
            'CLOUD_SQL_PASSWORD': 'testpass'
        }):
            settings = Settings()
            expected_url = "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
            assert settings.ASYNC_DATABASE_URL == expected_url

    def test_async_database_url_with_connection_name(self):
        """Test que la URL async de base de datos incluye connection_name cuando está disponible."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'CLOUD_SQL_CONNECTION_NAME': 'test-project:europe-west1:test-instance',
            'CLOUD_SQL_HOST': 'localhost',
            'CLOUD_SQL_PORT': '5432',
            'CLOUD_SQL_DB': 'testdb',
            'CLOUD_SQL_USER': 'testuser',
            'CLOUD_SQL_PASSWORD': 'testpass'
        }):
            settings = Settings()
            expected_url = "postgresql+asyncpg://testuser:testpass@/testdb?host=/cloudsql/test-project:europe-west1:test-instance"
            assert settings.ASYNC_DATABASE_URL == expected_url

    def test_boolean_parsing(self):
        """Test que los valores booleanos se parsean correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'TESTING': 'true',
            'ENABLE_ANALYTICS': 'false'
        }):
            settings = Settings()
            assert settings.TESTING is True
            assert settings.ENABLE_ANALYTICS is False

    def test_integer_parsing(self):
        """Test que los valores enteros se parsean correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'GROQ_MAX_TOKENS': '2048',
            'GROQ_TIMEOUT': '60',
            'RATE_LIMIT_PER_MINUTE': '20'
        }):
            settings = Settings()
            assert settings.GROQ_MAX_TOKENS == 2048
            assert settings.GROQ_TIMEOUT == 60
            assert settings.RATE_LIMIT_PER_MINUTE == 20

    def test_float_parsing(self):
        """Test que los valores float se parsean correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'GROQ_TEMPERATURE': '0.5',
            'ENGAGEMENT_THRESHOLD': '0.8'
        }):
            settings = Settings()
            assert settings.GROQ_TEMPERATURE == 0.5
            assert settings.ENGAGEMENT_THRESHOLD == 0.8


    def test_cors_origins_default(self):
        """Test que CORS_ORIGINS tiene valores por defecto correctos."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key'
        }):
            settings = Settings()
            expected_origins = [
                'http://localhost:3000',
                'http://localhost:3001', 
                'http://localhost:5173',
                'http://127.0.0.1:5500',
                'https://almapi.dev',
                'https://*.almapi.dev'
            ]
            assert settings.CORS_ORIGINS == expected_origins

    def test_cors_origins_custom(self):
        """Test que CORS_ORIGINS puede ser sobrescrito por variables de entorno."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key',
            'CORS_ORIGINS': '["https://example.com", "https://test.com"]'
        }):
            settings = Settings()
            assert settings.CORS_ORIGINS == ["https://example.com", "https://test.com"]


    def test_settings_repr(self):
        """Test que el string representation funciona correctamente."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'test-project',
            'GROQ_API_KEY': 'test-key'
        }):
            settings = Settings()
            repr_str = repr(settings)
            assert "Settings" in repr_str
            assert "PROJECT_NAME='AI Resume Agent'" in repr_str
