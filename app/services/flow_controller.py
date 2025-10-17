"""
Controlador de flujo para captura de datos y gestión de estados.
Maneja la lógica de cuándo solicitar datos, consentimientos y transiciones de estado.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.models.analytics import ChatSession
from app.services.analytics_service import analytics_service
from app.services.gdpr_service import gdpr_service

logger = logging.getLogger(__name__)


class FlowState(Enum):
    """Estados del flujo de captura de datos."""

    WELCOME = "welcome"
    CONVERSATION_ACTIVE = "conversation_active"
    DATA_CAPTURE_PENDING = "data_capture_pending"
    DATA_CAPTURED = "data_captured"
    GDPR_CONSENT_PENDING = "gdpr_consent_pending"
    GDPR_CONSENT_GIVEN = "gdpr_consent_given"
    CONVERSATION_COMPLETE = "conversation_complete"


class ActionType(Enum):
    """Tipos de acciones que puede tomar el sistema."""

    SHOW_WELCOME = "show_welcome"
    REQUEST_DATA_CAPTURE = "request_data_capture"
    REQUEST_GDPR_CONSENT = "request_gdpr_consent"
    NORMAL_RESPONSE = "normal_response"
    PROCESS_DATA_CAPTURE = "process_data_capture"
    PROCESS_GDPR_CONSENT = "process_gdpr_consent"


class FlowController:
    """
    Controlador de flujo para captura de datos y gestión de estados.

    Maneja:
    - Determinación de la siguiente acción según el estado de la sesión
    - Lógica de cuándo solicitar captura de datos
    - Lógica de cuándo solicitar consentimiento GDPR
    - Transiciones de estado
    - Procesamiento de datos capturados
    """

    def __init__(self):
        """Inicializar el controlador de flujo."""
        self.analytics_service = analytics_service
        self.gdpr_service = gdpr_service

        logger.info("✓ FlowController inicializado")
        logger.info(f"   - analytics_service: {self.analytics_service}")
        logger.info(f"   - gdpr_service: {self.gdpr_service}")

    async def determine_next_action(
        self, session: ChatSession, message: Optional[str] = None
    ) -> Tuple[ActionType, FlowState, Dict[str, Any]]:
        """
        Determinar la siguiente acción basada en el estado de la sesión.

        Args:
            session: Sesión de chat actual
            message: Mensaje del usuario (opcional)

        Returns:
            Tuple[ActionType, FlowState, Dict]: Acción, estado siguiente y datos adicionales
        """
        logger.info(
            f"🚀 FlowController.determine_next_action llamado para sesión: {session.session_id}"
        )
        try:
            # Debug logs
            logger.info(f"🔍 Determinando acción para sesión {session.session_id}:")
            logger.info(f"   - total_messages: {session.total_messages}")
            logger.info(f"   - data_captured: {session.data_captured}")
            logger.info(f"   - gdpr_consent_given: {session.gdpr_consent_given}")
            logger.info(
                f"   - DATA_CAPTURE_AFTER_MESSAGES: {settings.DATA_CAPTURE_AFTER_MESSAGES}"
            )

            # Lógica de determinación de acción
            if session.total_messages == 1:
                # Primer mensaje - mostrar bienvenida
                logger.info("   → Acción: SHOW_WELCOME (primer mensaje)")
                return (
                    ActionType.SHOW_WELCOME,
                    FlowState.CONVERSATION_ACTIVE,
                    {"welcome_shown": True},
                )

            elif (
                session.total_messages == settings.DATA_CAPTURE_AFTER_MESSAGES
                and not session.data_captured
            ):
                # Momento de capturar datos (exactamente después de 2 mensajes)
                logger.info("   → Acción: REQUEST_DATA_CAPTURE (momento de captura)")
                return (
                    ActionType.REQUEST_DATA_CAPTURE,
                    FlowState.DATA_CAPTURE_PENDING,
                    {
                        "capture_reason": "engagement_threshold",
                        "message_count": session.total_messages,
                        "engagement_score": session.engagement_score,
                    },
                )

            elif (
                session.total_messages > settings.DATA_CAPTURE_AFTER_MESSAGES
                and not session.data_captured
            ):
                # Continuar solicitando captura de datos hasta que se capturen
                logger.info("   → Acción: REQUEST_DATA_CAPTURE (solicitud persistente)")
                return (
                    ActionType.REQUEST_DATA_CAPTURE,
                    FlowState.DATA_CAPTURE_PENDING,
                    {
                        "capture_reason": "persistent_request",
                        "message_count": session.total_messages,
                        "engagement_score": session.engagement_score,
                    },
                )

            elif (
                session.total_messages > settings.DATA_CAPTURE_AFTER_MESSAGES
                and session.data_captured
                and not session.gdpr_consent_given
            ):
                # Solicitar consentimiento GDPR después de capturar datos
                logger.info(
                    "   → Acción: REQUEST_GDPR_CONSENT (datos capturados, sin consentimiento)"
                )
                return (
                    ActionType.REQUEST_GDPR_CONSENT,
                    FlowState.GDPR_CONSENT_PENDING,
                    {
                        "consent_reason": "data_captured",
                        "message_count": session.total_messages,
                    },
                )

            else:
                # Respuesta normal del chatbot
                logger.info("   → Acción: NORMAL_RESPONSE (conversación normal)")
                return (
                    ActionType.NORMAL_RESPONSE,
                    FlowState.CONVERSATION_ACTIVE,
                    {"normal_conversation": True},
                )

        except Exception as e:
            logger.error(
                f"❌ Error determinando siguiente acción para sesión {session.session_id}: {e}"
            )
            # Fallback a respuesta normal
            return (
                ActionType.NORMAL_RESPONSE,
                FlowState.CONVERSATION_ACTIVE,
                {"error_fallback": True},
            )

    async def should_request_data_capture(
        self, session: ChatSession
    ) -> Tuple[bool, str]:
        """
        Determinar si se debe solicitar captura de datos.

        Args:
            session: Sesión de chat

        Returns:
            Tuple[bool, str]: (debe_capturar, razón)
        """
        try:
            # Verificar si ya se capturaron datos
            if session.data_captured:
                return False, "already_captured"

            # Verificar umbral de mensajes
            if session.total_messages < settings.DATA_CAPTURE_AFTER_MESSAGES:
                return False, "insufficient_messages"

            # Verificar umbral de engagement
            if session.engagement_score < settings.ENGAGEMENT_THRESHOLD:
                return False, "low_engagement"

            # Verificar tiempo de sesión (mínimo 2 minutos)
            session_duration = (datetime.utcnow() - session.created_at).total_seconds()
            if session_duration < 120:  # 2 minutos
                return False, "insufficient_session_time"

            return True, "engagement_threshold_met"

        except Exception as e:
            logger.error(
                f"❌ Error evaluando captura de datos para sesión {session.session_id}: {e}"
            )
            return False, "error"

    async def process_data_capture(
        self,
        session_id: str,
        email: str,
        user_type: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Tuple[bool, FlowState, Dict[str, Any]]:
        """
        Procesar datos capturados del usuario.

        Args:
            session_id: ID de la sesión
            email: Email del usuario
            user_type: Tipo de usuario
            company: Empresa (opcional)
            role: Rol (opcional)

        Returns:
            Tuple[bool, FlowState, Dict]: (éxito, estado_siguiente, datos)
        """
        try:
            # Capturar datos usando analytics service
            success = await self.analytics_service.capture_user_data(
                session_id=session_id,
                email=email,
                user_type=user_type,
                company=company,
                role=role,
            )

            if success:
                logger.info(
                    f"✓ Datos capturados exitosamente para sesión: {session_id}"
                )
                return (
                    True,
                    FlowState.DATA_CAPTURED,
                    {
                        "data_captured": True,
                        "email": email,
                        "user_type": user_type,
                        "company": company,
                        "role": role,
                    },
                )
            else:
                logger.warning(f"⚠️ Error capturando datos para sesión: {session_id}")
                return (
                    False,
                    FlowState.CONVERSATION_ACTIVE,
                    {"error": "capture_failed"},
                )

        except Exception as e:
            logger.error(
                f"❌ Error procesando captura de datos para sesión {session_id}: {e}"
            )
            return (False, FlowState.CONVERSATION_ACTIVE, {"error": str(e)})

    async def process_gdpr_consent(
        self,
        session_id: str,
        consent_types: list,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, FlowState, Dict[str, Any]]:
        """
        Procesar consentimiento GDPR del usuario.

        Args:
            session_id: ID de la sesión
            consent_types: Tipos de consentimiento dados
            ip_address: IP del usuario (opcional)
            user_agent: User agent del navegador (opcional)

        Returns:
            Tuple[bool, FlowState, Dict]: (éxito, estado_siguiente, datos)
        """
        try:
            # Registrar consentimiento usando GDPR service
            success = await self.gdpr_service.record_consent(
                session_id=session_id,
                consent_types=consent_types,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if success:
                logger.info(
                    f"✓ Consentimiento GDPR registrado para sesión: {session_id}"
                )
                return (
                    True,
                    FlowState.GDPR_CONSENT_GIVEN,
                    {
                        "consent_given": True,
                        "consent_types": consent_types,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            else:
                logger.warning(
                    f"⚠️ Error registrando consentimiento para sesión: {session_id}"
                )
                return (
                    False,
                    FlowState.GDPR_CONSENT_PENDING,
                    {"error": "consent_registration_failed"},
                )

        except Exception as e:
            logger.error(
                f"❌ Error procesando consentimiento GDPR para sesión {session_id}: {e}"
            )
            return (False, FlowState.GDPR_CONSENT_PENDING, {"error": str(e)})

    async def get_flow_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener el estado actual del flujo para una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con estado del flujo o None si no existe
        """
        try:
            # Obtener analytics de la sesión
            session_analytics = await self.analytics_service.get_session_analytics(
                session_id
            )

            if not session_analytics:
                return None

            # Determinar estado actual
            if session_analytics["total_messages"] == 1:
                current_state = FlowState.WELCOME
            elif not session_analytics.get("data_captured", False):
                current_state = FlowState.CONVERSATION_ACTIVE
            elif not session_analytics.get("gdpr_consent_given", False):
                current_state = FlowState.DATA_CAPTURED
            else:
                current_state = FlowState.GDPR_CONSENT_GIVEN

            return {
                "session_id": session_id,
                "current_state": current_state.value,
                "total_messages": session_analytics["total_messages"],
                "engagement_score": session_analytics["engagement_score"],
                "data_captured": session_analytics.get("data_captured", False),
                "gdpr_consent_given": session_analytics.get(
                    "gdpr_consent_given", False
                ),
                "user_type": session_analytics.get("user_type"),
                "created_at": session_analytics["created_at"],
                "last_activity": session_analytics["last_activity"],
            }

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo estado del flujo para sesión {session_id}: {e}"
            )
            return None

    async def should_request_gdpr_consent(
        self, session: ChatSession
    ) -> Tuple[bool, str]:
        """
        Determinar si se debe solicitar consentimiento GDPR.

        Args:
            session: Sesión de chat

        Returns:
            Tuple[bool, str]: (debe_solicitar, razón)
        """
        try:
            # Verificar si ya se dio consentimiento
            if session.gdpr_consent_given:
                return False, "already_given"

            # Verificar si se capturaron datos
            if not session.data_captured:
                return False, "no_data_captured"

            # Verificar tiempo desde captura de datos (mínimo 1 mensaje después)
            if session.total_messages <= settings.DATA_CAPTURE_AFTER_MESSAGES + 1:
                return False, "insufficient_messages_after_capture"

            return True, "data_captured_and_ready"

        except Exception as e:
            logger.error(
                f"❌ Error evaluando consentimiento GDPR para sesión {session.session_id}: {e}"
            )
            return False, "error"

    async def handle_flow_transition(
        self,
        session_id: str,
        action_type: ActionType,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Manejar transición de estado en el flujo.

        Args:
            session_id: ID de la sesión
            action_type: Tipo de acción realizada
            additional_data: Datos adicionales (opcional)

        Returns:
            Dict con resultado de la transición
        """
        try:
            # Obtener estado actual
            current_state = await self.get_flow_state(session_id)

            if not current_state:
                return {"error": "session_not_found"}

            # Procesar transición según tipo de acción
            if action_type == ActionType.PROCESS_DATA_CAPTURE:
                if additional_data:
                    success, new_state, data = await self.process_data_capture(
                        session_id=session_id,
                        email=additional_data.get("email", ""),
                        user_type=additional_data.get("user_type", ""),
                        company=additional_data.get("company"),
                        role=additional_data.get("role"),
                    )
                    return {
                        "success": success,
                        "new_state": new_state.value,
                        "data": data,
                    }

            elif action_type == ActionType.PROCESS_GDPR_CONSENT:
                if additional_data:
                    success, new_state, data = await self.process_gdpr_consent(
                        session_id=session_id,
                        consent_types=additional_data.get("consent_types", []),
                        ip_address=additional_data.get("ip_address"),
                        user_agent=additional_data.get("user_agent"),
                    )
                    return {
                        "success": success,
                        "new_state": new_state.value,
                        "data": data,
                    }

            return {
                "success": True,
                "current_state": current_state["current_state"],
                "message": "transition_handled",
            }

        except Exception as e:
            logger.error(
                f"❌ Error manejando transición de flujo para sesión {session_id}: {e}"
            )
            return {"error": str(e)}

    def get_flow_configuration(self) -> Dict[str, Any]:
        """
        Obtener configuración del flujo.

        Returns:
            Dict con configuración del flujo
        """
        return {
            "data_capture_after_messages": settings.DATA_CAPTURE_AFTER_MESSAGES,
            "engagement_threshold": settings.ENGAGEMENT_THRESHOLD,
            "gdpr_consent_after_capture": True,
            "min_session_duration_seconds": 120,
            "flow_states": [state.value for state in FlowState],
            "action_types": [action.value for action in ActionType],
        }


# Instancia global del controlador
flow_controller = FlowController()
