"""
Endpoints de chat para el chatbot RAG.
Maneja las peticiones de chat y respuestas del usuario.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse
from app.services.rag_service import RAGService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar RAG service (singleton para reutilizar conexiones)
try:
    rag_service = RAGService()
    logger.info("✓ RAG Service inicializado en router")
except Exception as e:
    logger.error(f"❌ Error inicializando RAG Service: {e}")
    rag_service = None


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal de chat.
    Recibe un mensaje del usuario y devuelve una respuesta generada por RAG.
    
    Args:
        request: ChatRequest con el mensaje del usuario
        
    Returns:
        ChatResponse con la respuesta generada y fuentes
        
    Raises:
        HTTPException: Si hay un error en el procesamiento
    """
    if rag_service is None:
        logger.error("RAG Service no está inicializado")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de chat no está disponible. Intenta más tarde."
        )
    
    try:
        logger.info(f"Petición de chat recibida. Sesión: {request.session_id}")
        
        # Generar respuesta usando RAG
        result = await rag_service.generate_response(
            question=request.message,
            session_id=request.session_id
        )
        
        # Construir response
        response = ChatResponse(
            message=result["response"],
            sources=result.get("sources", []),
            session_id=result.get("session_id"),
            model=result.get("model", settings.GROQ_MODEL)
        )
        
        logger.info(f"✓ Respuesta generada exitosamente")
        return response
        
    except Exception as e:
        logger.error(f"Error en endpoint /chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando tu pregunta: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Verifica que el servicio está funcionando y puede conectarse a la DB.
    
    Returns:
        HealthResponse con el estado del servicio
    """
    try:
        # Verificar que RAG service está inicializado
        if rag_service is None:
            return HealthResponse(
                status="unhealthy",
                version=settings.VERSION
            )
        
        # Test de conexión
        connection_ok = await rag_service.test_connection()
        
        if connection_ok:
            return HealthResponse(
                status="healthy",
                version=settings.VERSION
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "version": settings.VERSION,
                    "detail": "No se puede conectar al vector store"
                }
            )
            
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "version": settings.VERSION,
                "detail": str(e)
            }
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint del API.
    Proporciona información básica sobre el servicio.
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "endpoints": {
            "chat": f"{settings.API_V1_STR}/chat",
            "health": f"{settings.API_V1_STR}/health"
        }
    }

