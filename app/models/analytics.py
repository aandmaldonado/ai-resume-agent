"""
Modelos SQLAlchemy para analytics y GDPR compliance.
Define las tablas de base de datos usando SQLAlchemy 2.0+ con estilo moderno.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class para todos los modelos SQLAlchemy.
    Usa SQLAlchemy 2.0+ con estilo moderno de type hints.
    """

    pass


class ChatSession(Base):
    """
    Modelo para sesiones de chat con datos de usuario.

    Almacena información básica de cada sesión de chat incluyendo
    datos de contacto del usuario y métricas de engagement.
    """

    __tablename__ = "chat_sessions"

    # Primary key
    session_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Datos de usuario (capturados gradualmente)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Tipo de usuario: recruiter, client, curious"
    )
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="NOW()", nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, server_default="NOW()", nullable=False
    )

    # Métricas de engagement
    total_messages: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    engagement_score: Mapped[float] = mapped_column(
        Float, server_default="0.0", nullable=False
    )

    # Estados de captura y consentimiento
    gdpr_consent_given: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    data_captured: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )

    # Relaciones
    analytics: Mapped[List["SessionAnalytics"]] = relationship(
        "SessionAnalytics", back_populates="session", cascade="all, delete-orphan"
    )
    consents: Mapped[List["GDPRConsent"]] = relationship(
        "GDPRConsent", back_populates="session", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "engagement_score >= 0.0 AND engagement_score <= 1.0",
            name="check_engagement_score_range",
        ),
        CheckConstraint("total_messages >= 0", name="check_total_messages_positive"),
        CheckConstraint(
            "user_type IN ('recruiter', 'client', 'curious') OR user_type IS NULL",
            name="check_user_type_valid",
        ),
        Index("idx_chat_sessions_email", "email"),
        Index("idx_chat_sessions_created_at", "created_at"),
        Index("idx_chat_sessions_user_type", "user_type"),
        Index("idx_chat_sessions_engagement", "engagement_score"),
    )

    def __repr__(self) -> str:
        return f"<ChatSession(session_id='{self.session_id}', user_type='{self.user_type}', messages={self.total_messages})>"


class SessionAnalytics(Base):
    """
    Modelo para métricas agregadas por sesión.

    Almacena métricas calculadas sin guardar contenido de mensajes
    para cumplir con GDPR y optimizar storage.
    """

    __tablename__ = "session_analytics"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    session_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Métricas de mensajes
    message_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Análisis de contenido (sin guardar texto)
    technologies_mentioned: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), nullable=True
    )
    intent_categories: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text),
        nullable=True,
        comment="Categorías de intención: experience, skills, projects",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="NOW()", nullable=False
    )

    # Relación
    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="analytics"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("message_count >= 0", name="check_message_count_positive"),
        CheckConstraint(
            "avg_response_time_ms >= 0", name="check_response_time_positive"
        ),
        Index("idx_session_analytics_session_id", "session_id"),
        Index("idx_session_analytics_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SessionAnalytics(session_id='{self.session_id}', messages={self.message_count})>"


class GDPRConsent(Base):
    """
    Modelo para registro de consentimientos GDPR.

    Almacena información detallada sobre consentimientos dados
    por usuarios para cumplir con regulaciones GDPR.
    """

    __tablename__ = "gdpr_consents"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    session_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Información del consentimiento
    consent_timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default="NOW()", nullable=False
    )
    consent_types: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text),
        nullable=True,
        comment="Tipos de consentimiento: email_storage, conversation_storage, analytics",
    )

    # Información técnica (para auditoría)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relación
    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="consents"
    )

    # Constraints
    __table_args__ = (
        Index("idx_gdpr_consents_session_id", "session_id"),
        Index("idx_gdpr_consents_timestamp", "consent_timestamp"),
    )

    def __repr__(self) -> str:
        return f"<GDPRConsent(session_id='{self.session_id}', timestamp={self.consent_timestamp})>"


class DailyAnalytics(Base):
    """
    Modelo para métricas agregadas diarias.

    Almacena métricas agregadas por día para dashboards
    y análisis de tendencias sin exponer datos individuales.
    """

    __tablename__ = "daily_analytics"

    # Primary key
    date: Mapped[date] = mapped_column(Date, primary_key=True)

    # Métricas de volumen
    total_sessions: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    total_messages: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    leads_captured: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )

    # Distribución por tipo de usuario
    recruiter_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    client_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    curious_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )

    # Métricas de calidad
    avg_engagement_score: Mapped[float] = mapped_column(
        Float, server_default="0.0", nullable=False
    )

    # Análisis de contenido agregado
    top_technologies: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB(astext_type=Text), nullable=True
    )
    top_intents: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB(astext_type=Text), nullable=True
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("total_sessions >= 0", name="check_total_sessions_positive"),
        CheckConstraint("total_messages >= 0", name="check_total_messages_positive"),
        CheckConstraint("leads_captured >= 0", name="check_leads_captured_positive"),
        CheckConstraint("recruiter_count >= 0", name="check_recruiter_count_positive"),
        CheckConstraint("client_count >= 0", name="check_client_count_positive"),
        CheckConstraint("curious_count >= 0", name="check_curious_count_positive"),
        CheckConstraint(
            "avg_engagement_score >= 0.0 AND avg_engagement_score <= 1.0",
            name="check_avg_engagement_score_range",
        ),
        Index("idx_daily_analytics_date", "date"),
    )

    def __repr__(self) -> str:
        return f"<DailyAnalytics(date={self.date}, sessions={self.total_sessions}, leads={self.leads_captured})>"
