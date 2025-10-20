"""
Endpoints de chat para el chatbot RAG.
Maneja las peticiones de chat y respuestas del usuario con analytics integrados.
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse
from app.services.analytics_service import analytics_service
from app.services.flow_controller import ActionType, FlowState, flow_controller
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Inicializar RAG service (singleton para reutilizar conexiones)
try:
    rag_service = RAGService()
    logger.info("✓ RAG Service inicializado en router")
except Exception as e:
    logger.error(f"❌ Error inicializando RAG Service: {e}")
    rag_service = None


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal de chat con analytics integrados.
    Recibe un mensaje del usuario y devuelve una respuesta generada por RAG.
    Maneja el flujo de captura de datos y consentimiento GDPR.

    Args:
        request: Starlette Request (para rate limiting)
        chat_request: ChatRequest con el mensaje del usuario

    Returns:
        ChatResponse con la respuesta generada, fuentes y estado del flujo

    Raises:
        HTTPException: Si hay un error en el procesamiento
    """
    if rag_service is None:
        logger.error("RAG Service no está inicializado")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de chat no está disponible. Intenta más tarde.",
        )

    # Validación adicional de seguridad
    message = chat_request.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje no puede estar vacío",
        )

    start_time = time.time()
    session_id = (
        chat_request.session_id or f"session-{int(time.time())}-{hash(message) % 10000}"
    )

    try:
        logger.info(f"Petición de chat recibida. Sesión: {session_id}")

        # 1. Crear o actualizar sesión de analytics (solo si analytics está habilitado)
        if settings.ENABLE_ANALYTICS and not settings.TESTING:
            session = await analytics_service.get_or_create_session(
                session_id=session_id,
                email=chat_request.email,
                user_type=chat_request.user_type,
            )

            # Incrementar contador de mensajes
            await analytics_service.increment_message_count(session_id)

            # Obtener sesión actualizada después del incremento
            session = await analytics_service.get_or_create_session(session_id)

            # 2. Determinar siguiente acción según el estado del flujo (después de incrementar)
            (
                action_type,
                next_flow_state,
                flow_data,
            ) = await flow_controller.determine_next_action(
                session=session, message=message
            )
        else:
            # Modo testing o analytics deshabilitado - respuesta normal
            action_type = ActionType.NORMAL_RESPONSE
            next_flow_state = FlowState.CONVERSATION_ACTIVE
            flow_data = {"testing_mode": True}

        logger.info(
            f"🔍 Flow controller devolvió: action_type={action_type.value}, next_state={next_flow_state.value}"
        )

        # 3. Manejar diferentes tipos de acciones
        if action_type == ActionType.SHOW_WELCOME:
            # Mostrar mensaje de bienvenida
            response = ChatResponse(
                message="¡Hola! Soy el asistente virtual de Álvaro Maldonado. Puedo ayudarte con información sobre mi experiencia profesional, habilidades técnicas y proyectos. ¿En qué puedo ayudarte?",
                sources=[],
                session_id=session_id,
                model=settings.GROQ_MODEL,
                action_type="show_welcome",
                next_flow_state=next_flow_state.value,
                requires_data_capture=False,
                requires_gdpr_consent=False,
            )

        elif action_type == ActionType.REQUEST_DATA_CAPTURE:
            # 4. Procesar mensaje con RAG PRIMERO, luego solicitar captura
            result = await rag_service.generate_response(
                question=message, session_id=session_id
            )

            # 5. Trackear métricas del mensaje (solo si analytics está habilitado)
            if settings.ENABLE_ANALYTICS and not settings.TESTING:
                response_time_ms = int((time.time() - start_time) * 1000)
                await analytics_service.track_message_metrics(
                    session_id=session_id,
                    message=message,
                    response_time_ms=response_time_ms,
                )

            # 6. Construir respuesta con RAG + solicitud de captura
            response = ChatResponse(
                message=result["response"],
                sources=result.get("sources", []),
                session_id=session_id,
                model=settings.GROQ_MODEL,
                action_type="request_data_capture",
                next_flow_state=next_flow_state.value,
                requires_data_capture=True,
                requires_gdpr_consent=False,
            )

        elif action_type == ActionType.REQUEST_GDPR_CONSENT:
            # 4. Procesar mensaje con RAG PRIMERO, luego solicitar GDPR
            result = await rag_service.generate_response(
                question=message, session_id=session_id
            )

            # 5. Trackear métricas del mensaje (solo si analytics está habilitado)
            if settings.ENABLE_ANALYTICS and not settings.TESTING:
                response_time_ms = int((time.time() - start_time) * 1000)
                await analytics_service.track_message_metrics(
                    session_id=session_id,
                    message=message,
                    response_time_ms=response_time_ms,
                )

            # 6. Construir respuesta con RAG + solicitud de GDPR
            response = ChatResponse(
                message=result["response"],
                sources=result.get("sources", []),
                session_id=session_id,
                model=settings.GROQ_MODEL,
                action_type="request_gdpr_consent",
                next_flow_state=next_flow_state.value,
                requires_data_capture=False,
                requires_gdpr_consent=True,
            )

        else:
            # 4. Procesar mensaje normal con RAG
            result = await rag_service.generate_response(
                question=message, session_id=session_id
            )

            # 5. Trackear métricas del mensaje (solo si analytics está habilitado)
            if settings.ENABLE_ANALYTICS and not settings.TESTING:
                response_time_ms = int((time.time() - start_time) * 1000)
                await analytics_service.track_message_metrics(
                    session_id=session_id,
                    message=message,
                    response_time_ms=response_time_ms,
                )

            # 6. Construir respuesta normal
            response = ChatResponse(
                message=result["response"],
                sources=result.get("sources", []),
                session_id=session_id,
                model=result.get("model", settings.GROQ_MODEL),
                action_type="normal_response",
                next_flow_state=next_flow_state.value,
                requires_data_capture=False,
                requires_gdpr_consent=False,
            )

        logger.info(f"✓ Respuesta generada exitosamente. Acción: {action_type.value}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        # Log error details internally but don't expose to client
        logger.error(f"Error en endpoint /chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor. Por favor, intenta de nuevo más tarde.",
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
            return HealthResponse(status="unhealthy", version=settings.VERSION)

        # Test de conexión
        connection_ok = await rag_service.test_connection()

        if connection_ok:
            return HealthResponse(status="healthy", version=settings.VERSION)
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "version": settings.VERSION,
                    "detail": "No se puede conectar al vector store",
                },
            )

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "version": settings.VERSION,
                "detail": str(e),
            },
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
            "health": f"{settings.API_V1_STR}/health",
        },
    }
