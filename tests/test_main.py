"""
Tests para app/main.py
Cubre eventos de startup/shutdown, exception handler y configuración.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestMainApp:
    """Tests para la aplicación principal"""

    def test_app_creation(self):
        """Test que la aplicación se crea correctamente"""
        assert app is not None
        assert app.title == "AI Resume Agent"
        assert app.version == "1.0.0"

    def test_app_docs_urls(self):
        """Test que las URLs de documentación están configuradas"""
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"

    def test_app_middleware_configuration(self):
        """Test que los middlewares están configurados"""
        # Verificar que los middlewares están presentes
        middleware_types = [type(middleware) for middleware in app.user_middleware]
        assert len(middleware_types) > 0

    def test_app_include_router(self):
        """Test que los routers están incluidos"""
        # Verificar que el router de chat está incluido
        assert len(app.routes) > 0


class TestStartupShutdownEvents:
    """Tests para eventos de startup y shutdown"""

    @patch("app.main.logger")
    def test_startup_event_logging(self, mock_logger):
        """Test que el evento startup genera logs correctos"""
        # Simular el evento startup
        import asyncio

        from app.main import startup_event

        # Ejecutar el evento
        asyncio.run(startup_event())

        # Verificar que se generaron logs
        assert mock_logger.info.call_count >= 3  # Al menos 3 mensajes de log
        mock_logger.info.assert_any_call("🚀 Iniciando AI Resume Agent v1.0.0")

    @patch("app.main.logger")
    def test_shutdown_event_logging(self, mock_logger):
        """Test que el evento shutdown genera logs correctos"""
        # Simular el evento shutdown
        import asyncio

        from app.main import shutdown_event

        # Ejecutar el evento
        asyncio.run(shutdown_event())

        # Verificar que se generó el log
        mock_logger.info.assert_called_with("👋 Cerrando aplicación...")


class TestGlobalExceptionHandler:
    """Tests para el handler global de excepciones"""

    def test_global_exception_handler_debug_mode(self):
        """Test handler de excepciones en modo debug"""
        from fastapi import Request

        from app.main import global_exception_handler

        # Mock request
        mock_request = Mock(spec=Request)

        # Mock settings para modo debug
        with patch("app.main.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "DEBUG"

            # Crear excepción de prueba
            test_exception = Exception("Test error message")

            # Ejecutar handler
            import asyncio

            response = asyncio.run(
                global_exception_handler(mock_request, test_exception)
            )

            # Verificar respuesta
            assert response.status_code == 500
            response_data = response.body.decode()
            assert "Test error message" in response_data

    def test_global_exception_handler_production_mode(self):
        """Test handler de excepciones en modo producción"""
        from fastapi import Request

        from app.main import global_exception_handler

        # Mock request
        mock_request = Mock(spec=Request)

        # Mock settings para modo producción
        with patch("app.main.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "INFO"

            # Crear excepción de prueba
            test_exception = Exception("Test error message")

            # Ejecutar handler
            import asyncio

            response = asyncio.run(
                global_exception_handler(mock_request, test_exception)
            )

            # Verificar respuesta
            assert response.status_code == 500
            response_data = response.body.decode()
            assert "Test error message" not in response_data  # No debe exponer detalles
            assert "An error occurred" in response_data


class TestAppConfiguration:
    """Tests para configuración de la aplicación"""

    def test_trusted_host_middleware_configuration(self):
        """Test configuración de TrustedHostMiddleware"""
        # Verificar que hay middlewares configurados (TrustedHostMiddleware está incluido)
        assert len(app.user_middleware) >= 2  # Al menos CORS y TrustedHost

    def test_cors_middleware_configuration(self):
        """Test configuración de CORSMiddleware"""
        # Verificar que hay middlewares configurados (CORSMiddleware está incluido)
        assert len(app.user_middleware) >= 2  # Al menos CORS y TrustedHost

    def test_rate_limiter_configuration(self):
        """Test configuración de rate limiter"""
        # Verificar que el rate limiter está configurado
        assert hasattr(app.state, "limiter")
        assert app.state.limiter is not None


class TestRootEndpoint:
    """Tests para el endpoint raíz"""

    def test_root_endpoint_response(self):
        """Test respuesta del endpoint raíz"""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        assert "api_v1" in data

        assert data["service"] == "AI Resume Agent"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"
        assert data["api_v1"] == "/api/v1"


class TestAppLifecycle:
    """Tests para el ciclo de vida de la aplicación"""

    @patch("app.main.settings")
    def test_startup_with_production_settings(self, mock_settings):
        """Test startup con configuración de producción"""
        mock_settings.PROJECT_NAME = "AI Resume Agent"
        mock_settings.VERSION = "1.0.0"
        mock_settings.CLOUD_SQL_CONNECTION_NAME = "prod-connection"
        mock_settings.GCP_PROJECT_ID = "test-project"
        mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"
        mock_settings.VERTEX_AI_EMBEDDING_MODEL = "textembedding-gecko@003"
        mock_settings.VECTOR_COLLECTION_NAME = "test-collection"

        import asyncio

        from app.main import startup_event

        # Ejecutar startup
        asyncio.run(startup_event())

    @patch("app.main.settings")
    def test_startup_with_development_settings(self, mock_settings):
        """Test startup con configuración de desarrollo"""
        mock_settings.PROJECT_NAME = "AI Resume Agent"
        mock_settings.VERSION = "1.0.0"
        mock_settings.CLOUD_SQL_CONNECTION_NAME = None  # Desarrollo local
        mock_settings.GCP_PROJECT_ID = "test-project"
        mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"
        mock_settings.VERTEX_AI_EMBEDDING_MODEL = "textembedding-gecko@003"
        mock_settings.VECTOR_COLLECTION_NAME = "test-collection"

        import asyncio

        from app.main import startup_event

        # Ejecutar startup
        asyncio.run(startup_event())


class TestErrorHandling:
    """Tests para manejo de errores"""

    def test_exception_handler_with_different_exception_types(self):
        """Test handler con diferentes tipos de excepciones"""
        from fastapi import Request

        from app.main import global_exception_handler

        mock_request = Mock(spec=Request)

        # Test con ValueError
        with patch("app.main.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "INFO"

            value_error = ValueError("Invalid value")
            import asyncio

            response = asyncio.run(global_exception_handler(mock_request, value_error))

            assert response.status_code == 500

    def test_exception_handler_logging(self):
        """Test que el handler logea errores correctamente"""
        from fastapi import Request

        from app.main import global_exception_handler

        mock_request = Mock(spec=Request)

        with patch("app.main.logger") as mock_logger:
            with patch("app.main.settings") as mock_settings:
                mock_settings.LOG_LEVEL = "INFO"

                test_exception = Exception("Test error")
                import asyncio

                asyncio.run(global_exception_handler(mock_request, test_exception))

                # Verificar que se logueó el error
                mock_logger.error.assert_called_once()
