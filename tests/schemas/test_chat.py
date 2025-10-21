"""
Tests unitarios simples para app/schemas/chat.py
Testea que los esquemas se pueden importar y crear correctamente.
"""

import pytest
from datetime import datetime

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SourceDocument,
)


class TestChatSchemas:
    """Tests simples para esquemas de chat."""

    def test_chat_request_valid(self):
        """Test ChatRequest con datos válidos."""
        request = ChatRequest(
            message="Hello, how are you?",
            session_id="test-session-123"
        )
        assert request.message == "Hello, how are you?"
        assert request.session_id == "test-session-123"

    def test_chat_request_minimal(self):
        """Test ChatRequest con datos mínimos."""
        request = ChatRequest(
            message="Hi",
            session_id="minimal-session"
        )
        assert request.message == "Hi"
        assert request.session_id == "minimal-session"

    def test_chat_request_empty_message(self):
        """Test ChatRequest con mensaje vacío."""
        with pytest.raises(Exception):
            ChatRequest(message="", session_id="test-session")

    def test_chat_request_long_message(self):
        """Test ChatRequest con mensaje muy largo."""
        long_message = "a" * 601
        with pytest.raises(Exception):
            ChatRequest(message=long_message, session_id="test-session")

    def test_chat_request_max_length_message(self):
        """Test ChatRequest con mensaje de longitud máxima."""
        max_message = "a" * 600
        request = ChatRequest(message=max_message, session_id="test-session")
        assert len(request.message) == 600

    def test_chat_request_empty_session_id(self):
        """Test ChatRequest con session_id vacío."""
        with pytest.raises(Exception):
            ChatRequest(message="Hello", session_id="")

    def test_chat_request_injection_patterns(self):
        """Test ChatRequest con patrones de inyección."""
        with pytest.raises(Exception):
            ChatRequest(message="<script>alert('xss')</script>", session_id="test-session")
        with pytest.raises(Exception):
            ChatRequest(message="javascript:alert(1)", session_id="test-session")

    def test_chat_response_valid(self):
        """Test ChatResponse con datos válidos."""
        response = ChatResponse(
            message="Hello, how are you?",
            session_id="test-session-123",
            sources=[
                SourceDocument(
                    type="document",
                    content_preview="Some content",
                    metadata={"page": 1}
                )
            ],
            timestamp=datetime.now(),
            action_type="normal_response",
            next_flow_state="conversation_active",
            requires_data_capture=False,
            requires_gdpr_consent=False
        )
        assert response.message == "Hello, how are you?"
        assert response.session_id == "test-session-123"
        assert len(response.sources) == 1
        assert response.sources[0].content_preview == "Some content"

    def test_chat_response_minimal(self):
        """Test ChatResponse con datos mínimos."""
        response = ChatResponse(
            message="Hi",
            session_id="minimal-session",
            timestamp=datetime.now()
        )
        assert response.message == "Hi"
        assert response.sources == []

    def test_chat_response_empty_sources(self):
        """Test ChatResponse con sources vacíos."""
        response = ChatResponse(
            message="Question",
            session_id="test-session",
            sources=[],
            timestamp=datetime.now()
        )
        assert response.sources == []

    def test_chat_response_multiple_sources(self):
        """Test ChatResponse con múltiples sources."""
        response = ChatResponse(
            message="Question",
            session_id="test-session",
            sources=[
                SourceDocument(type="document"),
                SourceDocument(type="document")
            ],
            timestamp=datetime.now()
        )
        assert len(response.sources) == 2

    def test_health_response_valid(self):
        """Test HealthResponse con datos válidos."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now()
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"

    def test_health_response_unhealthy(self):
        """Test HealthResponse con estado unhealthy."""
        response = HealthResponse(
            status="unhealthy",
            version="1.0.0",
            timestamp=datetime.now()
        )
        assert response.status == "unhealthy"

    def test_chat_request_field_types(self):
        """Test tipos de campos en ChatRequest."""
        request = ChatRequest(message="Test", session_id="123")
        assert isinstance(request.message, str)
        assert isinstance(request.session_id, str)

    def test_chat_response_field_types(self):
        """Test tipos de campos en ChatResponse."""
        response = ChatResponse(
            message="Q", session_id="123", timestamp=datetime.now()
        )
        assert isinstance(response.message, str)
        assert isinstance(response.session_id, str)
        assert isinstance(response.sources, list)
        assert isinstance(response.timestamp, datetime)

    def test_health_response_field_types(self):
        """Test tipos de campos en HealthResponse."""
        response = HealthResponse(status="healthy", version="1.0.0", timestamp=datetime.now())
        assert isinstance(response.status, str)
        assert isinstance(response.version, str)
        assert isinstance(response.timestamp, datetime)

    def test_chat_request_serialization(self):
        """Test serialización de ChatRequest."""
        request = ChatRequest(message="Test", session_id="123")
        assert request.model_dump_json() is not None

    def test_chat_response_serialization(self):
        """Test serialización de ChatResponse."""
        response = ChatResponse(
            message="Q", session_id="123", timestamp=datetime.now()
        )
        assert response.model_dump_json() is not None

    def test_health_response_serialization(self):
        """Test serialización de HealthResponse."""
        response = HealthResponse(status="healthy", version="1.0.0", timestamp=datetime.now())
        assert response.model_dump_json() is not None

    def test_source_document_valid(self):
        """Test SourceDocument con datos válidos."""
        source = SourceDocument(
            type="document",
            content_preview="This is a preview.",
            metadata={"author": "Me"}
        )
        assert source.type == "document"
        assert source.content_preview == "This is a preview."
        assert source.metadata["author"] == "Me"

    def test_source_document_minimal(self):
        """Test SourceDocument con datos mínimos."""
        source = SourceDocument(type="web_page")
        assert source.type == "web_page"
        assert source.content_preview is None
        assert source.metadata is None

    def test_chat_request_validation(self):
        """Test validación de ChatRequest."""
        # Mensaje muy corto
        with pytest.raises(Exception):
            ChatRequest(message="", session_id="test")

        # Session ID muy corto
        with pytest.raises(Exception):
            ChatRequest(message="Hello", session_id="")

        # Mensaje con caracteres especiales peligrosos
        with pytest.raises(Exception):
            ChatRequest(message="<script>alert('xss')</script>", session_id="test")

    def test_source_document_validation(self):
        """Test validación de SourceDocument."""
        # Tipo requerido
        with pytest.raises(Exception):
            SourceDocument()

    def test_health_response_validation(self):
        """Test validación de HealthResponse."""
        # Status válido
        response = HealthResponse(status="healthy", version="1.0.0", timestamp=datetime.now())
        assert response.status == "healthy"

    def test_optional_fields(self):
        """Test campos opcionales en esquemas."""
        # ChatRequest solo requiere message y session_id
        request = ChatRequest(message="Hello", session_id="test")
        assert request.message == "Hello"
        assert request.session_id == "test"

        # SourceDocument puede tener campos opcionales
        source = SourceDocument(type="document")
        assert source.content_preview is None
        assert source.metadata is None

    def test_default_values(self):
        """Test valores por defecto en esquemas."""
        # ChatResponse tiene sources por defecto
        response = ChatResponse(
            message="Hello",
            session_id="test",
            timestamp=datetime.now()
        )
        assert response.sources == []

    def test_nested_objects(self):
        """Test objetos anidados en esquemas."""
        # ChatResponse con SourceDocument
        response = ChatResponse(
            message="Question",
            session_id="test",
            sources=[
                SourceDocument(
                    type="document",
                    metadata={"key": "value"}
                )
            ],
            timestamp=datetime.now()
        )
        assert len(response.sources) == 1
        assert response.sources[0].metadata["key"] == "value"

    def test_datetime_fields(self):
        """Test campos de tipo datetime."""
        now = datetime.now()
        
        response = ChatResponse(
            message="Hello",
            session_id="test",
            timestamp=now
        )
        assert response.timestamp == now

        health = HealthResponse(status="healthy", version="1.0.0", timestamp=now)
        assert health.timestamp == now

    def test_list_fields(self):
        """Test campos de tipo lista."""
        response = ChatResponse(
            message="Question",
            session_id="test",
            sources=[
                SourceDocument(type="document"),
                SourceDocument(type="document")
            ],
            timestamp=datetime.now()
        )
        assert isinstance(response.sources, list)
        assert len(response.sources) == 2

    def test_dict_fields(self):
        """Test campos de tipo diccionario."""
        source = SourceDocument(
            type="document",
            metadata={"author": "John", "year": 2024}
        )
        assert isinstance(source.metadata, dict)
        assert source.metadata["author"] == "John"