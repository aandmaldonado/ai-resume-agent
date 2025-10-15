"""
Tests para el servicio RAG
"""
from unittest.mock import Mock, patch

import pytest

# Mock de las dependencias antes de importar
with patch("app.services.rag_service.ChatGroq"), patch(
    "app.services.rag_service.HuggingFaceEmbeddings"
), patch("app.services.rag_service.PGVector"):
    from app.services.rag_service import RAGService


@pytest.fixture
def mock_rag_service():
    """Fixture que crea un RAGService mockeado"""
    with patch("app.services.rag_service.ChatGroq"), patch(
        "app.services.rag_service.HuggingFaceEmbeddings"
    ), patch("app.services.rag_service.PGVector"):
        service = RAGService()
        return service


def test_rag_service_initialization(mock_rag_service):
    """Test que el servicio se inicializa correctamente"""
    assert mock_rag_service is not None
    assert mock_rag_service.llm is not None
    assert mock_rag_service.embeddings is not None
    assert mock_rag_service.vector_store is not None


@pytest.mark.asyncio
async def test_generate_response_success(mock_rag_service):
    """Test que genera respuesta exitosamente"""
    # Mock del chain de LangChain
    mock_result = {
        "answer": "Tengo más de 15 años de experiencia...",
        "source_documents": [
            Mock(
                page_content="Experiencia laboral...",
                metadata={"type": "experience", "company": "InAdvance"},
            )
        ],
    }

    with patch.object(mock_rag_service, "vector_store") as mock_vector_store:
        mock_retriever = Mock()
        mock_vector_store.as_retriever.return_value = mock_retriever

        with patch("app.services.rag_service.ConversationalRetrievalChain") as mock_qa:
            mock_chain = Mock()
            mock_chain.return_value = mock_result
            mock_qa.from_llm.return_value = mock_chain

            result = await mock_rag_service.generate_response(
                "¿Cuál es tu experiencia?"
            )

            assert "response" in result
            assert "sources" in result
            assert len(result["sources"]) > 0


@pytest.mark.asyncio
async def test_generate_response_with_session(mock_rag_service):
    """Test que mantiene session_id"""
    session_id = "test-session-123"

    mock_result = {"answer": "Respuesta de prueba", "source_documents": []}

    with patch.object(mock_rag_service, "vector_store"):
        with patch("app.services.rag_service.ConversationalRetrievalChain") as mock_qa:
            mock_chain = Mock()
            mock_chain.return_value = mock_result
            mock_qa.from_llm.return_value = mock_chain

            result = await mock_rag_service.generate_response(
                "Test question", session_id=session_id
            )

            assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_format_sources(mock_rag_service):
    """Test que formatea las fuentes correctamente"""
    from langchain.docstore.document import Document

    documents = [
        Document(
            page_content="Test content for experience at company X",
            metadata={"type": "experience", "company": "Test Corp"},
        ),
        Document(
            page_content="Test content for skills in Python and Java",
            metadata={"type": "skills", "category": "Programming"},
        ),
    ]

    sources = mock_rag_service._format_sources(documents)

    assert len(sources) == 2
    assert sources[0]["type"] == "experience"
    assert sources[1]["type"] == "skills"
    assert "content_preview" in sources[0]


@pytest.mark.asyncio
async def test_test_connection_success(mock_rag_service):
    """Test de conexión exitosa"""
    from langchain.docstore.document import Document

    mock_doc = Document(page_content="Test", metadata={"type": "test"})

    with patch.object(
        mock_rag_service.vector_store, "similarity_search", return_value=[mock_doc]
    ):
        result = await mock_rag_service.test_connection()
        assert result is True


@pytest.mark.asyncio
async def test_test_connection_failure(mock_rag_service):
    """Test de conexión fallida"""
    with patch.object(
        mock_rag_service.vector_store,
        "similarity_search",
        side_effect=Exception("Connection error"),
    ):
        result = await mock_rag_service.test_connection()
        assert result is False


def test_system_prompt_creation(mock_rag_service):
    """Test que el system prompt se crea correctamente"""
    prompt = mock_rag_service.system_prompt

    assert prompt is not None
    assert "Álvaro" in prompt.template
    assert "primera persona" in prompt.template.lower()
    assert "context" in prompt.input_variables
    assert "question" in prompt.input_variables


# Tests de integración (requieren conexión real)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_rag_pipeline():
    """
    Test de integración real (solo ejecutar si tienes las credenciales configuradas)
    Requiere: GCP credentials, Groq API key, Cloud SQL running
    """
    pytest.skip("Requiere credenciales reales - ejecutar manualmente")

    from app.services.rag_service import RAGService

    service = RAGService()
    result = await service.generate_response("¿Cuál es tu experiencia con Python?")

    assert "response" in result
    assert len(result["response"]) > 0
    assert "Python" in result["response"]
