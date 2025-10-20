"""
Servicio de Analytics para captura de leads y métricas.
Maneja el tracking de sesiones, cálculo de engagement y análisis de contenido.
"""

import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.analytics import (
    Base,
    ChatMessage,
    ChatSession,
    ConversationPair,
    DailyAnalytics,
    GDPRConsent,
    SessionAnalytics,
)
from app.schemas.analytics import (
    AnalyticsMetrics,
    SessionAnalyticsCreate,
    SessionCreate,
    SessionUpdate,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Servicio principal para analytics y captura de leads.

    Maneja:
    - Tracking de sesiones de chat
    - Captura de datos de usuarios
    - Cálculo de métricas de engagement
    - Análisis de contenido (tecnologías, intenciones)
    - Agregación de métricas diarias
    """

    def __init__(self):
        """Inicializar el servicio de analytics."""
        # No inicializar en modo testing
        if settings.TESTING:
            logger.info(
                "✓ AnalyticsService en modo testing - inicialización deshabilitada"
            )
            return

        self.engine = create_async_engine(
            settings.ASYNC_DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self.AsyncSessionLocal = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

        # Patrones para detección de tecnologías
        self.technology_patterns = {
            "python": [r"\bpython\b", r"\bdjango\b", r"\bflask\b", r"\bfastapi\b"],
            "javascript": [
                r"\bjavascript\b",
                r"\bnode\.?js\b",
                r"\breact\b",
                r"\bvue\b",
                r"\bangular\b",
            ],
            "java": [r"\bjava\b", r"\bspring\b", r"\bmaven\b", r"\bgradle\b"],
            "cloud": [
                r"\bgcp\b",
                r"\baws\b",
                r"\bazure\b",
                r"\bcloud\b",
                r"\bkubernetes\b",
            ],
            "ai": [
                r"\bai\b",
                r"\bmachine learning\b",
                r"\bdeep learning\b",
                r"\bllm\b",
                r"\brag\b",
            ],
            "database": [r"\bpostgresql\b", r"\bmysql\b", r"\bmongodb\b", r"\bredis\b"],
            "devops": [r"\bdocker\b", r"\bci/cd\b", r"\bjenkins\b", r"\bterraform\b"],
        }

        # Patrones para detección de intenciones
        self.intent_patterns = {
            "experience": [
                r"\bexperiencia\b",
                r"\baños\b",
                r"\btrabajo\b",
                r"\bempresa\b",
                r"\bproyecto\b",
            ],
            "skills": [
                r"\bhabilidades\b",
                r"\bconocimientos\b",
                r"\btecnologías\b",
                r"\bprogramar\b",
            ],
            "education": [
                r"\bestudios\b",
                r"\buniversidad\b",
                r"\bformación\b",
                r"\bcertificación\b",
            ],
            "availability": [
                r"\bdisponibilidad\b",
                r"\bcontratar\b",
                r"\boportunidad\b",
                r"\btrabajo\b",
            ],
        }

        logger.info("✓ AnalyticsService inicializado")

    async def track_session(
        self,
        session_id: str,
        email: Optional[str] = None,
        user_type: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
    ) -> ChatSession:
        """
        Trackear una sesión de chat (crear o actualizar).

        Args:
            session_id: ID único de la sesión
            email: Email del usuario (opcional)
            user_type: Tipo de usuario (recruiter, client, curious)
            company: Empresa del usuario (opcional)
            role: Rol del usuario (opcional)

        Returns:
            ChatSession: Sesión creada o actualizada
        """
        # Obtener o crear sesión
        session = await self.get_or_create_session(
            session_id=session_id,
            email=email,
            user_type=user_type,
            company=company,
            role=role,
        )

        # Incrementar contador de mensajes
        await self.increment_message_count(session_id)

        # Obtener sesión actualizada
        async with await self.get_session() as db:
            result = await db.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            updated_session = result.scalar_one_or_none()

            if updated_session:
                await db.refresh(updated_session)
                return updated_session
            else:
                return session

    async def get_session(self) -> AsyncSession:
        """Obtener sesión de base de datos."""
        if settings.TESTING:
            raise RuntimeError("AnalyticsService no disponible en modo testing")
        return self.AsyncSessionLocal()

    async def get_or_create_session(
        self,
        session_id: str,
        email: Optional[str] = None,
        user_type: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
    ) -> ChatSession:
        """
        Obtener o crear una sesión sin incrementar el contador de mensajes.

        Args:
            session_id: ID único de la sesión
            email: Email del usuario (opcional)
            user_type: Tipo de usuario (recruiter, client, curious)
            company: Empresa del usuario (opcional)
            role: Rol del usuario (opcional)

        Returns:
            ChatSession: Sesión existente o nueva
        """
        from app.models.analytics import ChatSession

        # En modo testing, retornar una sesión mock
        if settings.TESTING:
            return ChatSession(
                session_id=session_id,
                email=email,
                user_type=user_type,
                company=company,
                role=role,
                total_messages=0,
                engagement_score=0.0,
                data_captured=False,
                gdpr_consent_given=False,
            )

        async with await self.get_session() as db:
            try:
                # Buscar sesión existente
                result = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                existing_session = result.scalar_one_or_none()

                if existing_session:
                    # Actualizar datos si se proporcionan
                    if email:
                        existing_session.email = email
                    if user_type:
                        existing_session.user_type = user_type
                    if company:
                        existing_session.company = company
                    if role:
                        existing_session.role = role

                    existing_session.last_activity = datetime.utcnow()
                    await db.commit()
                    await db.refresh(existing_session)

                    logger.info(f"✓ Sesión obtenida: {session_id}")
                    return existing_session

                else:
                    # Crear nueva sesión
                    new_session = ChatSession(
                        session_id=session_id,
                        email=email,
                        user_type=user_type,
                        company=company,
                        role=role,
                        total_messages=0,  # Sin mensajes aún
                        engagement_score=0.0,
                    )

                    db.add(new_session)
                    await db.commit()
                    await db.refresh(new_session)

                    logger.info(f"✓ Nueva sesión creada: {session_id}")
                    return new_session

            except SQLAlchemyError as e:
                logger.error(f"❌ Error obteniendo/creando sesión {session_id}: {e}")
                db.rollback()
                raise

    async def increment_message_count(self, session_id: str) -> bool:
        """
        Incrementar el contador de mensajes de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            bool: True si se incrementó exitosamente
        """
        # En modo testing, retornar True sin hacer nada
        if settings.TESTING:
            return True

        async with await self.get_session() as db:
            try:
                # Buscar sesión
                session = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                session = session.scalar_one_or_none()

                if not session:
                    logger.warning(
                        f"⚠️ Sesión no encontrada para incrementar mensajes: {session_id}"
                    )
                    return False

                # Incrementar contador
                session.total_messages += 1
                session.last_activity = datetime.utcnow()

                # Recalcular engagement score
                session.engagement_score = self._calculate_engagement_score(
                    session.total_messages, session.created_at, session.last_activity
                )

                await db.commit()

                logger.debug(
                    f"✓ Contador de mensajes incrementado para sesión: {session_id}"
                )
                return True

            except SQLAlchemyError as e:
                logger.error(f"❌ Error incrementando contador para {session_id}: {e}")
                await db.rollback()
                return False

    async def capture_user_data(
        self,
        session_id: str,
        email: str,
        user_type: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
    ) -> bool:
        """
        Capturar datos del usuario en una sesión existente.

        Args:
            session_id: ID de la sesión
            email: Email del usuario
            user_type: Tipo de usuario
            company: Empresa (opcional)
            role: Rol (opcional)

        Returns:
            bool: True si la captura fue exitosa
        """
        async with await self.get_session() as db:
            try:
                # Buscar sesión
                session = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                session = session.scalar_one_or_none()

                if not session:
                    logger.warning(
                        f"⚠️ Sesión no encontrada para captura: {session_id}"
                    )
                    return False

                # Actualizar datos
                session.email = email
                session.user_type = user_type
                session.company = company
                session.role = role
                session.data_captured = True
                session.last_activity = datetime.utcnow()

                await db.commit()

                logger.info(f"✓ Datos capturados para sesión: {session_id}")
                return True

            except SQLAlchemyError as e:
                logger.error(f"❌ Error capturando datos para {session_id}: {e}")
                await db.rollback()
                return False

    async def track_message_metrics(
        self, session_id: str, message: str, response_time_ms: Optional[int] = None
    ) -> bool:
        """
        Trackear métricas de un mensaje sin guardar el contenido.

        Args:
            session_id: ID de la sesión
            message: Contenido del mensaje
            response_time_ms: Tiempo de respuesta en ms (opcional)

        Returns:
            bool: True si el tracking fue exitoso
        """
        # En modo testing, retornar True sin hacer nada
        if settings.TESTING:
            return True

        async with await self.get_session() as db:
            try:
                # Detectar tecnologías e intenciones
                technologies = self._detect_technologies(message)
                intents = self._detect_intent_categories(message)

                # Crear registro de analytics
                analytics = SessionAnalytics(
                    session_id=session_id,
                    message_count=1,
                    avg_response_time_ms=response_time_ms,
                    technologies_mentioned=technologies,
                    intent_categories=intents,
                )

                db.add(analytics)
                await db.commit()

                logger.debug(f"✓ Métricas trackeadas para sesión: {session_id}")
                return True

            except SQLAlchemyError as e:
                logger.error(f"❌ Error trackeando métricas para {session_id}: {e}")
                await db.rollback()
                return False

    def _calculate_engagement_score(
        self, message_count: int, created_at: datetime, last_activity: datetime
    ) -> float:
        """
        Calcular score de engagement basado en actividad.

        Args:
            message_count: Número de mensajes
            created_at: Fecha de creación
            last_activity: Última actividad

        Returns:
            float: Score de engagement (0.0 - 1.0)
        """
        # Factor de mensajes (0.0 - 0.6)
        message_factor = min(message_count / 10.0, 0.6)

        # Factor de tiempo de sesión (0.0 - 0.4)
        session_duration = (last_activity - created_at).total_seconds() / 3600  # horas
        time_factor = min(session_duration / 2.0, 0.4)  # Máximo 2 horas

        return min(message_factor + time_factor, 1.0)

    def _detect_technologies(self, message: str) -> List[str]:
        """
        Detectar tecnologías mencionadas en el mensaje.

        Args:
            message: Contenido del mensaje

        Returns:
            List[str]: Lista de tecnologías detectadas
        """
        message_lower = message.lower()
        detected_technologies = []

        for tech_category, patterns in self.technology_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    detected_technologies.append(tech_category)
                    break  # Solo agregar una vez por categoría

        return detected_technologies

    def _detect_intent_categories(self, message: str) -> List[str]:
        """
        Detectar categorías de intención en el mensaje.

        Args:
            message: Contenido del mensaje

        Returns:
            List[str]: Lista de intenciones detectadas
        """
        message_lower = message.lower()
        detected_intents = []

        for intent_category, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    detected_intents.append(intent_category)
                    break  # Solo agregar una vez por categoría

        return detected_intents

    async def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener analytics de una sesión específica.

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con métricas de la sesión o None si no existe
        """
        async with await self.get_session() as db:
            try:
                # Obtener sesión
                result = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return None

                # Obtener analytics agregados
                analytics_result = await db.execute(
                    select(SessionAnalytics).where(
                        SessionAnalytics.session_id == session_id
                    )
                )
                analytics_query = analytics_result.scalars().all()

                # Agregar métricas
                all_technologies = []
                all_intents = []
                total_response_time = 0
                response_count = 0

                for analytics in analytics_query:
                    if analytics.technologies_mentioned:
                        all_technologies.extend(analytics.technologies_mentioned)
                    if analytics.intent_categories:
                        all_intents.extend(analytics.intent_categories)
                    if analytics.avg_response_time_ms:
                        total_response_time += analytics.avg_response_time_ms
                        response_count += 1

                return {
                    "session_id": session.session_id,
                    "user_type": session.user_type,
                    "total_messages": session.total_messages,
                    "engagement_score": session.engagement_score,
                    "technologies_mentioned": list(set(all_technologies)),
                    "intent_categories": list(set(all_intents)),
                    "avg_response_time_ms": (
                        total_response_time / response_count
                        if response_count > 0
                        else None
                    ),
                    "created_at": session.created_at,
                    "last_activity": session.last_activity,
                    "data_captured": session.data_captured,
                    "gdpr_consent_given": session.gdpr_consent_given,
                }

            except SQLAlchemyError as e:
                logger.error(f"❌ Error obteniendo analytics para {session_id}: {e}")
                return None

    async def aggregate_daily_metrics(self, target_date: Optional[date] = None) -> bool:
        """
        Agregar métricas diarias para una fecha específica.

        Args:
            target_date: Fecha objetivo (por defecto: hoy)

        Returns:
            bool: True si la agregación fue exitosa
        """
        if target_date is None:
            target_date = date.today()

        async with await self.get_session() as db:
            try:
                # Verificar si ya existe agregación para esta fecha
                existing_result = await db.execute(
                    select(DailyAnalytics).where(DailyAnalytics.date == target_date)
                )
                existing = existing_result.scalar_one_or_none()

                if existing:
                    logger.info(f"✓ Métricas diarias ya existen para {target_date}")
                    return True

                # Calcular métricas del día
                start_datetime = datetime.combine(target_date, datetime.min.time())
                end_datetime = datetime.combine(target_date, datetime.max.time())

                # Obtener sesiones del día
                sessions_result = await db.execute(
                    select(ChatSession).where(
                        and_(
                            ChatSession.created_at >= start_datetime,
                            ChatSession.created_at <= end_datetime,
                        )
                    )
                )
                sessions = sessions_result.scalars().all()

                # Calcular métricas
                total_sessions = len(sessions)
                total_messages = sum(s.total_messages for s in sessions)
                leads_captured = sum(1 for s in sessions if s.data_captured)

                recruiter_count = sum(1 for s in sessions if s.user_type == "recruiter")
                client_count = sum(1 for s in sessions if s.user_type == "client")
                curious_count = sum(1 for s in sessions if s.user_type == "curious")

                avg_engagement_score = (
                    sum(s.engagement_score for s in sessions) / total_sessions
                    if total_sessions > 0
                    else 0.0
                )

                # Obtener tecnologías e intenciones más frecuentes
                technologies_count = {}
                intents_count = {}

                for session in sessions:
                    analytics_result = await db.execute(
                        select(SessionAnalytics).where(
                            SessionAnalytics.session_id == session.session_id
                        )
                    )
                    analytics_query = analytics_result.scalars().all()

                    for analytics in analytics_query:
                        if analytics.technologies_mentioned:
                            for tech in analytics.technologies_mentioned:
                                technologies_count[tech] = (
                                    technologies_count.get(tech, 0) + 1
                                )

                        if analytics.intent_categories:
                            for intent in analytics.intent_categories:
                                intents_count[intent] = intents_count.get(intent, 0) + 1

                # Crear registro de métricas diarias
                daily_analytics = DailyAnalytics(
                    date=target_date,
                    total_sessions=total_sessions,
                    total_messages=total_messages,
                    leads_captured=leads_captured,
                    recruiter_count=recruiter_count,
                    client_count=client_count,
                    curious_count=curious_count,
                    avg_engagement_score=avg_engagement_score,
                    top_technologies=dict(
                        sorted(
                            technologies_count.items(), key=lambda x: x[1], reverse=True
                        )[:10]
                    ),
                    top_intents=dict(
                        sorted(intents_count.items(), key=lambda x: x[1], reverse=True)[
                            :10
                        ]
                    ),
                )

                db.add(daily_analytics)
                db.commit()

                logger.info(f"✓ Métricas diarias agregadas para {target_date}")
                return True

            except SQLAlchemyError as e:
                logger.error(
                    f"❌ Error agregando métricas diarias para {target_date}: {e}"
                )
                db.rollback()
                return False

    async def get_daily_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtener métricas diarias de los últimos N días.

        Args:
            days: Número de días a obtener

        Returns:
            List[Dict]: Lista de métricas diarias
        """
        async with await self.get_session() as db:
            try:
                # Calcular fecha de inicio
                end_date = date.today()
                start_date = date.fromordinal(end_date.toordinal() - days + 1)

                # Obtener métricas
                metrics_result = await db.execute(
                    select(DailyAnalytics)
                    .where(
                        and_(
                            DailyAnalytics.date >= start_date,
                            DailyAnalytics.date <= end_date,
                        )
                    )
                    .order_by(DailyAnalytics.date.desc())
                )
                metrics = metrics_result.scalars().all()

                return [
                    {
                        "date": metric.date.isoformat(),
                        "total_sessions": metric.total_sessions,
                        "total_messages": metric.total_messages,
                        "leads_captured": metric.leads_captured,
                        "recruiter_count": metric.recruiter_count,
                        "client_count": metric.client_count,
                        "curious_count": metric.curious_count,
                        "avg_engagement_score": metric.avg_engagement_score,
                        "top_technologies": metric.top_technologies or {},
                        "top_intents": metric.top_intents or {},
                    }
                    for metric in metrics
                ]

            except SQLAlchemyError as e:
                logger.error(f"❌ Error obteniendo métricas diarias: {e}")
                return []

    async def get_overall_metrics(self) -> AnalyticsMetrics:
        """
        Obtener métricas generales del sistema.

        Returns:
            AnalyticsMetrics: Métricas agregadas
        """
        async with await self.get_session() as db:
            try:
                # Obtener métricas básicas
                total_sessions_result = await db.execute(
                    select(func.count(ChatSession.session_id))
                )
                total_sessions = total_sessions_result.scalar()

                total_messages_result = await db.execute(
                    select(func.sum(ChatSession.total_messages))
                )
                total_messages = total_messages_result.scalar() or 0

                leads_captured_result = await db.execute(
                    select(func.count(ChatSession.session_id)).where(
                        ChatSession.data_captured == True
                    )
                )
                leads_captured = leads_captured_result.scalar()

                # Distribución por tipo de usuario
                recruiter_count_result = await db.execute(
                    select(func.count(ChatSession.session_id)).where(
                        ChatSession.user_type == "recruiter"
                    )
                )
                recruiter_count = recruiter_count_result.scalar()
                client_count_result = await db.execute(
                    select(func.count(ChatSession.session_id)).where(
                        ChatSession.user_type == "client"
                    )
                )
                client_count = client_count_result.scalar()

                curious_count_result = await db.execute(
                    select(func.count(ChatSession.session_id)).where(
                        ChatSession.user_type == "curious"
                    )
                )
                curious_count = curious_count_result.scalar()

                # Engagement promedio
                avg_engagement_result = await db.execute(
                    select(func.avg(ChatSession.engagement_score))
                )
                avg_engagement = avg_engagement_result.scalar() or 0.0

                # Tecnologías e intenciones más frecuentes
                technologies_count = {}
                intents_count = {}

                analytics_result = await db.execute(select(SessionAnalytics))
                analytics_query = analytics_result.scalars().all()
                for analytics in analytics_query:
                    if analytics.technologies_mentioned:
                        for tech in analytics.technologies_mentioned:
                            technologies_count[tech] = (
                                technologies_count.get(tech, 0) + 1
                            )

                    if analytics.intent_categories:
                        for intent in analytics.intent_categories:
                            intents_count[intent] = intents_count.get(intent, 0) + 1

                return AnalyticsMetrics(
                    total_sessions=total_sessions,
                    total_messages=total_messages,
                    leads_captured=leads_captured,
                    recruiter_count=recruiter_count,
                    client_count=client_count,
                    curious_count=curious_count,
                    avg_engagement_score=round(avg_engagement, 3),
                    top_technologies=dict(
                        sorted(
                            technologies_count.items(), key=lambda x: x[1], reverse=True
                        )[:10]
                    ),
                    top_intents=dict(
                        sorted(intents_count.items(), key=lambda x: x[1], reverse=True)[
                            :10
                        ]
                    ),
                )

            except SQLAlchemyError as e:
                logger.error(f"❌ Error obteniendo métricas generales: {e}")
                return AnalyticsMetrics(
                    total_sessions=0,
                    total_messages=0,
                    leads_captured=0,
                    recruiter_count=0,
                    client_count=0,
                    curious_count=0,
                    avg_engagement_score=0.0,
                    top_technologies={},
                    top_intents={},
                )

    async def save_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        response_time_ms: Optional[int] = None,
        sources_used: Optional[List[str]] = None,
        detected_language: Optional[str] = None,
        topics_mentioned: Optional[List[str]] = None,
    ) -> bool:
        """
        Guarda un mensaje individual en la base de datos.

        Args:
            session_id: ID de la sesión
            message_type: 'user' o 'bot'
            content: Contenido del mensaje
            response_time_ms: Tiempo de respuesta en milisegundos
            sources_used: Fuentes utilizadas para generar respuesta
            detected_language: Idioma detectado
            topics_mentioned: Temas mencionados en el mensaje

        Returns:
            bool: True si se guardó exitosamente
        """
        if settings.TESTING:
            logger.info(
                f"🧪 Modo testing - Simulando guardado de mensaje: {message_type}"
            )
            return True

        try:
            async with await self.get_session() as db:
                message = ChatMessage(
                    session_id=session_id,
                    message_type=message_type,
                    content=content,
                    response_time_ms=response_time_ms,
                    sources_used=sources_used,
                    detected_language=detected_language,
                    topics_mentioned=topics_mentioned,
                )

                db.add(message)
                await db.commit()

                logger.info(
                    f"✅ Mensaje guardado: {message_type} para sesión {session_id}"
                )
                return True

        except SQLAlchemyError as e:
            logger.error(f"❌ Error guardando mensaje: {e}")
            return False

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los mensajes de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Lista de mensajes con sus metadatos
        """
        if settings.TESTING:
            logger.info(
                f"🧪 Modo testing - Simulando obtención de mensajes para {session_id}"
            )
            return []

        try:
            async with await self.get_session() as db:
                result = await db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at)
                )
                messages = result.scalars().all()

                return [
                    {
                        "id": msg.id,
                        "message_type": msg.message_type,
                        "content": msg.content,
                        "response_time_ms": msg.response_time_ms,
                        "sources_used": msg.sources_used,
                        "detected_language": msg.detected_language,
                        "topics_mentioned": msg.topics_mentioned,
                        "created_at": msg.created_at,
                    }
                    for msg in messages
                ]

        except SQLAlchemyError as e:
            logger.error(f"❌ Error obteniendo mensajes de sesión {session_id}: {e}")
            return []

    async def save_conversation_pair(
        self,
        session_id: str,
        user_question: str,
        bot_response: str,
        response_time_ms: Optional[int] = None,
        sources_used: Optional[List[str]] = None,
        user_language: Optional[str] = None,
        bot_language: Optional[str] = None,
        topics_mentioned: Optional[List[str]] = None,
        technologies_detected: Optional[List[str]] = None,
        intent_category: Optional[str] = None,
        engagement_score: Optional[float] = None,
    ) -> bool:
        """
        Guarda un par de conversación (pregunta-respuesta) en la base de datos.

        Args:
            session_id: ID de la sesión
            user_question: Pregunta del usuario
            bot_response: Respuesta del bot
            response_time_ms: Tiempo de respuesta en milisegundos
            sources_used: Fuentes utilizadas para generar respuesta
            user_language: Idioma detectado del usuario
            bot_language: Idioma de la respuesta del bot
            topics_mentioned: Temas mencionados en la conversación
            technologies_detected: Tecnologías detectadas en la pregunta
            intent_category: Categoría de intención
            engagement_score: Score de engagement de esta conversación

        Returns:
            bool: True si se guardó exitosamente
        """
        if settings.TESTING:
            logger.info(f"🧪 Modo testing - Simulando guardado de par de conversación")
            return True

        try:
            async with await self.get_session() as db:
                # Asegurar que la sesión existe
                await self.get_or_create_session(session_id)

                conversation_pair = ConversationPair(
                    session_id=session_id,
                    user_question=user_question,
                    bot_response=bot_response,
                    response_time_ms=response_time_ms,
                    sources_used=sources_used,
                    user_language=user_language,
                    bot_language=bot_language,
                    topics_mentioned=topics_mentioned,
                    technologies_detected=technologies_detected,
                    intent_category=intent_category,
                    engagement_score=engagement_score,
                )

                db.add(conversation_pair)
                await db.commit()

                logger.info(f"✅ Par de conversación guardado para sesión {session_id}")
                return True

        except SQLAlchemyError as e:
            logger.error(f"❌ Error guardando par de conversación: {e}")
            return False

    async def get_conversation_pairs(
        self, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene pares de conversación, opcionalmente filtrados por sesión.

        Args:
            session_id: ID de la sesión (opcional)

        Returns:
            Lista de pares de conversación con sus metadatos
        """
        if settings.TESTING:
            logger.info(
                f"🧪 Modo testing - Simulando obtención de pares de conversación"
            )
            return []

        try:
            async with await self.get_session() as db:
                query = select(ConversationPair)
                if session_id:
                    query = query.where(ConversationPair.session_id == session_id)

                query = query.order_by(ConversationPair.created_at.desc())
                result = await db.execute(query)
                pairs = result.scalars().all()

                return [
                    {
                        "id": pair.id,
                        "session_id": pair.session_id,
                        "user_question": pair.user_question,
                        "bot_response": pair.bot_response,
                        "response_time_ms": pair.response_time_ms,
                        "sources_used": pair.sources_used,
                        "user_language": pair.user_language,
                        "bot_language": pair.bot_language,
                        "topics_mentioned": pair.topics_mentioned,
                        "technologies_detected": pair.technologies_detected,
                        "intent_category": pair.intent_category,
                        "engagement_score": pair.engagement_score,
                        "created_at": pair.created_at,
                    }
                    for pair in pairs
                ]

        except SQLAlchemyError as e:
            logger.error(f"❌ Error obteniendo pares de conversación: {e}")
            return []

    async def get_top_questions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene las preguntas más frecuentes para análisis de interés.

        Args:
            limit: Número máximo de resultados

        Returns:
            Lista de preguntas con conteos
        """
        if settings.TESTING:
            logger.info(f"🧪 Modo testing - Simulando obtención de preguntas top")
            return []

        try:
            async with await self.get_session() as db:
                # Usar SQL crudo para manejar unnest y remover nulos de forma segura
                from sqlalchemy import text

                sql = text(
                    """
                    SELECT 
                      cp.user_question AS user_question,
                      COUNT(cp.id) AS count,
                      array_remove(array_agg(cp.intent_category), NULL) AS intents,
                      array_remove(array_agg(DISTINCT tech.tech), NULL) AS technologies
                    FROM conversation_pairs cp
                    LEFT JOIN LATERAL unnest(COALESCE(cp.technologies_detected, ARRAY[]::text[])) AS tech(tech) ON TRUE
                    GROUP BY cp.user_question
                    ORDER BY COUNT(cp.id) DESC
                    LIMIT :limit
                    """
                )
                result = await db.execute(sql, {"limit": limit})
                rows = result.fetchall()

                return [
                    {
                        "question": r.user_question,
                        "count": r.count,
                        "intents": list(r.intents or []),
                        "technologies": list(r.technologies or []),
                    }
                    for r in rows
                ]

        except SQLAlchemyError as e:
            logger.error(f"❌ Error obteniendo preguntas top: {e}")
            return []


# Instancia global del servicio
analytics_service = AnalyticsService()
