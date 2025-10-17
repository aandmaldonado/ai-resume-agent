"""
Servicio GDPR para compliance y manejo de datos de usuarios.
Implementa derechos de acceso, portabilidad, eliminación y anonimización.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, create_engine, delete, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analytics import (
    Base,
    ChatSession,
    DailyAnalytics,
    GDPRConsent,
    SessionAnalytics,
)

logger = logging.getLogger(__name__)


class GDPRService:
    """
    Servicio para compliance GDPR.

    Implementa:
    - Registro de consentimientos
    - Derecho de acceso (obtener datos)
    - Derecho al olvido (eliminar datos)
    - Derecho de portabilidad (exportar datos)
    - Anonimización de datos
    """

    def __init__(self):
        """Inicializar el servicio GDPR."""
        self.engine = create_engine(
            settings.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        logger.info("✓ GDPRService inicializado")

    def get_session(self) -> Session:
        """Obtener sesión de base de datos."""
        return Session(self.engine)

    async def record_consent(
        self,
        session_id: str,
        consent_types: List[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Registrar consentimiento GDPR del usuario.

        Args:
            session_id: ID de la sesión
            consent_types: Tipos de consentimiento dados
            ip_address: IP del usuario (opcional)
            user_agent: User agent del navegador (opcional)

        Returns:
            bool: True si el registro fue exitoso
        """
        with self.get_session() as db:
            try:
                # Verificar que la sesión existe
                session = db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                ).scalar_one_or_none()

                if not session:
                    logger.warning(
                        f"⚠️ Sesión no encontrada para consentimiento: {session_id}"
                    )
                    return False

                # Crear registro de consentimiento
                consent = GDPRConsent(
                    session_id=session_id,
                    consent_types=consent_types,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

                db.add(consent)

                # Actualizar sesión
                session.gdpr_consent_given = True
                session.last_activity = datetime.utcnow()

                db.commit()

                logger.info(
                    f"✓ Consentimiento GDPR registrado para sesión: {session_id}"
                )
                return True

            except SQLAlchemyError as e:
                logger.error(
                    f"❌ Error registrando consentimiento para {session_id}: {e}"
                )
                db.rollback()
                return False

    async def get_user_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener todos los datos del usuario (derecho de acceso).

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con todos los datos del usuario o None si no existe
        """
        with self.get_session() as db:
            try:
                # Obtener sesión
                session = db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                ).scalar_one_or_none()

                if not session:
                    logger.warning(
                        f"⚠️ Sesión no encontrada para acceso a datos: {session_id}"
                    )
                    return None

                # Obtener analytics de la sesión
                analytics_query = (
                    db.execute(
                        select(SessionAnalytics).where(
                            SessionAnalytics.session_id == session_id
                        )
                    )
                    .scalars()
                    .all()
                )

                # Obtener consentimientos
                consents_query = (
                    db.execute(
                        select(GDPRConsent).where(GDPRConsent.session_id == session_id)
                    )
                    .scalars()
                    .all()
                )

                # Compilar datos del usuario
                user_data = {
                    "session_id": session.session_id,
                    "personal_data": {
                        "email": session.email,
                        "user_type": session.user_type,
                        "company": session.company,
                        "role": session.role,
                    },
                    "session_data": {
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "total_messages": session.total_messages,
                        "engagement_score": session.engagement_score,
                        "data_captured": session.data_captured,
                        "gdpr_consent_given": session.gdpr_consent_given,
                    },
                    "analytics_data": [
                        {
                            "message_count": analytics.message_count,
                            "avg_response_time_ms": analytics.avg_response_time_ms,
                            "technologies_mentioned": analytics.technologies_mentioned
                            or [],
                            "intent_categories": analytics.intent_categories or [],
                            "created_at": analytics.created_at.isoformat(),
                        }
                        for analytics in analytics_query
                    ],
                    "consent_data": [
                        {
                            "consent_types": consent.consent_types or [],
                            "consent_timestamp": consent.consent_timestamp.isoformat(),
                            "ip_address": consent.ip_address,
                            "user_agent": consent.user_agent,
                        }
                        for consent in consents_query
                    ],
                }

                logger.info(f"✓ Datos del usuario obtenidos para sesión: {session_id}")
                return user_data

            except SQLAlchemyError as e:
                logger.error(
                    f"❌ Error obteniendo datos del usuario para {session_id}: {e}"
                )
                return None

    async def delete_user_data(self, session_id: str) -> bool:
        """
        Eliminar todos los datos del usuario (derecho al olvido).

        Args:
            session_id: ID de la sesión

        Returns:
            bool: True si la eliminación fue exitosa
        """
        with self.get_session() as db:
            try:
                # Verificar que la sesión existe
                session = db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                ).scalar_one_or_none()

                if not session:
                    logger.warning(
                        f"⚠️ Sesión no encontrada para eliminación: {session_id}"
                    )
                    return False

                # Eliminar analytics de la sesión
                db.execute(
                    delete(SessionAnalytics).where(
                        SessionAnalytics.session_id == session_id
                    )
                )

                # Eliminar consentimientos
                db.execute(
                    delete(GDPRConsent).where(GDPRConsent.session_id == session_id)
                )

                # Eliminar la sesión
                db.execute(
                    delete(ChatSession).where(ChatSession.session_id == session_id)
                )

                db.commit()

                logger.info(f"✓ Datos del usuario eliminados para sesión: {session_id}")
                return True

            except SQLAlchemyError as e:
                logger.error(
                    f"❌ Error eliminando datos del usuario para {session_id}: {e}"
                )
                db.rollback()
                return False

    async def export_user_data(self, session_id: str) -> Optional[str]:
        """
        Exportar datos del usuario en formato JSON (derecho de portabilidad).

        Args:
            session_id: ID de la sesión

        Returns:
            JSON string con los datos del usuario o None si no existe
        """
        user_data = await self.get_user_data(session_id)

        if not user_data:
            return None

        try:
            # Agregar metadatos de exportación
            export_data = {
                "export_metadata": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "data_subject": session_id,
                    "format_version": "1.0",
                    "gdpr_compliant": True,
                },
                "user_data": user_data,
            }

            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)

            logger.info(f"✓ Datos del usuario exportados para sesión: {session_id}")
            return json_data

        except Exception as e:
            logger.error(f"❌ Error exportando datos del usuario para {session_id}: {e}")
            return None

    async def anonymize_session(self, session_id: str) -> bool:
        """
        Anonimizar una sesión manteniendo las métricas agregadas.

        Args:
            session_id: ID de la sesión

        Returns:
            bool: True si la anonimización fue exitosa
        """
        with self.get_session() as db:
            try:
                # Buscar sesión
                session = db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                ).scalar_one_or_none()

                if not session:
                    logger.warning(
                        f"⚠️ Sesión no encontrada para anonimización: {session_id}"
                    )
                    return False

                # Anonimizar datos personales
                session.email = None
                session.company = None
                session.role = None
                session.user_type = "anonymous"

                # Eliminar consentimientos (ya no son necesarios)
                db.execute(
                    delete(GDPRConsent).where(GDPRConsent.session_id == session_id)
                )

                db.commit()

                logger.info(f"✓ Sesión anonimizada: {session_id}")
                return True

            except SQLAlchemyError as e:
                logger.error(f"❌ Error anonimizando sesión {session_id}: {e}")
                db.rollback()
                return False

    async def cleanup_expired_data(self) -> int:
        """
        Limpiar datos expirados según políticas de retención.

        Returns:
            int: Número de sesiones procesadas
        """
        with self.get_session() as db:
            try:
                # Calcular fecha de expiración
                expiration_date = datetime.utcnow() - timedelta(
                    days=settings.DATA_RETENTION_DAYS
                )
                anonymization_date = datetime.utcnow() - timedelta(
                    days=settings.ANONYMIZE_AFTER_DAYS
                )

                processed_count = 0

                # Buscar sesiones para anonimizar (sin consentimiento, inactivas)
                sessions_to_anonymize = (
                    db.execute(
                        select(ChatSession).where(
                            and_(
                                ChatSession.last_activity < anonymization_date,
                                ChatSession.gdpr_consent_given == False,
                            )
                        )
                    )
                    .scalars()
                    .all()
                )

                for session in sessions_to_anonymize:
                    await self.anonymize_session(session.session_id)
                    processed_count += 1

                # Buscar sesiones para eliminar (muy antiguas sin consentimiento)
                sessions_to_delete = (
                    db.execute(
                        select(ChatSession).where(
                            and_(
                                ChatSession.created_at < expiration_date,
                                ChatSession.gdpr_consent_given == False,
                            )
                        )
                    )
                    .scalars()
                    .all()
                )

                for session in sessions_to_delete:
                    await self.delete_user_data(session.session_id)
                    processed_count += 1

                logger.info(
                    f"✓ Limpieza de datos completada: {processed_count} sesiones procesadas"
                )
                return processed_count

            except SQLAlchemyError as e:
                logger.error(f"❌ Error en limpieza de datos: {e}")
                return 0

    async def get_consent_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estado del consentimiento GDPR de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con estado del consentimiento o None si no existe
        """
        with self.get_session() as db:
            try:
                # Obtener sesión
                session = db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                ).scalar_one_or_none()

                if not session:
                    return None

                # Obtener último consentimiento
                latest_consent = db.execute(
                    select(GDPRConsent)
                    .where(GDPRConsent.session_id == session_id)
                    .order_by(GDPRConsent.consent_timestamp.desc())
                ).scalar_one_or_none()

                return {
                    "session_id": session_id,
                    "gdpr_consent_given": session.gdpr_consent_given,
                    "data_captured": session.data_captured,
                    "latest_consent": (
                        {
                            "consent_types": (
                                latest_consent.consent_types if latest_consent else []
                            ),
                            "consent_timestamp": (
                                latest_consent.consent_timestamp.isoformat()
                                if latest_consent
                                else None
                            ),
                            "ip_address": (
                                latest_consent.ip_address if latest_consent else None
                            ),
                        }
                        if latest_consent
                        else None
                    ),
                }

            except SQLAlchemyError as e:
                logger.error(
                    f"❌ Error obteniendo estado de consentimiento para {session_id}: {e}"
                )
                return None

    async def revoke_consent(self, session_id: str) -> bool:
        """
        Revocar consentimiento GDPR y anonimizar datos.

        Args:
            session_id: ID de la sesión

        Returns:
            bool: True si la revocación fue exitosa
        """
        with self.get_session() as db:
            try:
                # Buscar sesión
                session = db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                ).scalar_one_or_none()

                if not session:
                    logger.warning(
                        f"⚠️ Sesión no encontrada para revocación: {session_id}"
                    )
                    return False

                # Revocar consentimiento
                session.gdpr_consent_given = False
                session.last_activity = datetime.utcnow()

                # Eliminar consentimientos previos
                db.execute(
                    delete(GDPRConsent).where(GDPRConsent.session_id == session_id)
                )

                # Anonimizar datos personales
                session.email = None
                session.company = None
                session.role = None
                session.user_type = "anonymous"

                db.commit()

                logger.info(
                    f"✓ Consentimiento revocado y datos anonimizados para sesión: {session_id}"
                )
                return True

            except SQLAlchemyError as e:
                logger.error(f"❌ Error revocando consentimiento para {session_id}: {e}")
                db.rollback()
                return False


# Instancia global del servicio
gdpr_service = GDPRService()
