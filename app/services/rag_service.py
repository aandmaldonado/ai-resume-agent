"""
Servicio RAG (Retrieval Augmented Generation) principal.
Combina Groq (LLM), Vertex AI (Embeddings) y pgvector (Vector DB).
"""
import logging
from typing import Dict, List, Optional
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import PGVector
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Servicio principal de RAG para el chatbot.
    Inicializa LLM, embeddings y vector store, y maneja la generación de respuestas.
    """
    
    def __init__(self):
        """Inicializa los componentes del RAG"""
        logger.info("Inicializando RAGService...")
        
        # 1. LLM: Groq (Llama 3.1 - gratis y ultra rápido)
        logger.info(f"Configurando LLM: {settings.GROQ_MODEL}")
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            groq_api_key=settings.GROQ_API_KEY
        )
        
        # 2. Embeddings: HuggingFace (local, 100% gratis, sin APIs)
        logger.info("Configurando HuggingFace Embeddings (local)")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 3. Vector Store: pgvector en Cloud SQL
        logger.info(f"Conectando a vector store: {settings.VECTOR_COLLECTION_NAME}")
        self.vector_store = PGVector(
            connection_string=settings.database_url,
            embedding_function=self.embeddings,
            collection_name=settings.VECTOR_COLLECTION_NAME
        )
        
        # 4. System Prompt optimizado
        self.system_prompt = self._create_system_prompt()
        
        logger.info("✓ RAGService inicializado correctamente")
    
    def _create_system_prompt(self) -> PromptTemplate:
        """
        Crea el prompt template para el chatbot.
        Define la personalidad y comportamiento del asistente.
        """
        template = """Eres Álvaro Andrés Maldonado Pinto, un Senior Software Engineer con más de 15 años de experiencia.

TU IDENTIDAD:
- Eres un profesional especializado en Product Engineering y Artificial Intelligence
- Has trabajado como CTO, Technical Lead y Senior Engineer en empresas como Falabella, NTT DATA, Imagemaker
- Actualmente trabajas en InAdvance Consulting Group para BCI Bank en Chile
- Vives en Gandía, Valencia, España y buscas oportunidades 100% remotas
- Tu email es readme.md@almapi.dev y tu sitio web es https://almapi.dev

INSTRUCCIONES CRÍTICAS:
1. SIEMPRE responde en PRIMERA PERSONA como si fueras Álvaro
2. USA SOLO la información del contexto proporcionado abajo
3. Si no tienes información específica, admítelo y sugiere contactar directamente
4. Sé profesional pero cercano, técnico pero accesible
5. NO inventes información que no esté en el contexto
6. Responde en el mismo idioma que te pregunten (español o inglés)

CONTEXTO RELEVANTE DE MI PORTFOLIO:
{context}

PREGUNTA DEL VISITANTE:
{question}

MI RESPUESTA (en primera persona, natural y conversacional):"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    async def generate_response(
        self, 
        question: str, 
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Genera una respuesta usando RAG.
        
        Args:
            question: Pregunta del usuario
            session_id: ID de sesión (para futuro: mantener historial)
            
        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            logger.info(f"Generando respuesta para: '{question[:50]}...'")
            
            # Crear chain RAG
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",  # Concatena todos los docs recuperados
                retriever=self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": settings.VECTOR_SEARCH_K}
                ),
                chain_type_kwargs={"prompt": self.system_prompt},
                return_source_documents=True
            )
            
            # Generar respuesta
            result = qa_chain({"query": question})
            
            # Formatear sources
            sources = self._format_sources(result.get("source_documents", []))
            
            logger.info(f"✓ Respuesta generada. Fuentes usadas: {len(sources)}")
            
            return {
                "response": result["result"],
                "sources": sources,
                "session_id": session_id,
                "model": settings.GROQ_MODEL
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}", exc_info=True)
            raise
    
    def _format_sources(self, documents: List[Document]) -> List[Dict]:
        """
        Formatea los documentos fuente para la respuesta.
        
        Args:
            documents: Documentos recuperados del vector store
            
        Returns:
            Lista de sources formateados
        """
        sources = []
        
        for doc in documents:
            source = {
                "type": doc.metadata.get("type", "unknown"),
                "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                "metadata": {
                    k: v for k, v in doc.metadata.items() 
                    if k not in ["page_content"]
                }
            }
            sources.append(source)
        
        return sources
    
    async def test_connection(self) -> bool:
        """
        Prueba que todos los componentes están conectados correctamente.
        
        Returns:
            True si todo está OK, False otherwise
        """
        try:
            logger.info("Probando conexión al vector store...")
            
            # Hacer una búsqueda de prueba
            test_results = self.vector_store.similarity_search(
                "test", 
                k=1
            )
            
            logger.info(f"✓ Conexión OK. Documentos en DB: {len(test_results) > 0}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en test de conexión: {e}")
            return False

