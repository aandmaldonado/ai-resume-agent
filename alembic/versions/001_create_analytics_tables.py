"""Create analytics tables

Revision ID: 001
Revises: 
Create Date: 2025-01-15 10:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Crear tablas de analytics y GDPR compliance.

    Tablas creadas:
    - chat_sessions: Datos básicos de cada sesión
    - session_analytics: Métricas agregadas por sesión
    - gdpr_consents: Registro de consentimientos GDPR
    - daily_analytics: Métricas agregadas diarias
    """

    # Tabla principal de sesiones de chat
    op.create_table(
        "chat_sessions",
        sa.Column("session_id", sa.VARCHAR(length=100), nullable=False),
        sa.Column("email", sa.VARCHAR(length=255), nullable=True),
        sa.Column(
            "user_type",
            sa.VARCHAR(length=50),
            nullable=True,
            comment="recruiter, client, curious",
        ),
        sa.Column("company", sa.VARCHAR(length=200), nullable=True),
        sa.Column("role", sa.VARCHAR(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "last_activity",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "total_messages", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "engagement_score",
            sa.FLOAT(),
            server_default=sa.text("0.0"),
            nullable=False,
        ),
        sa.Column(
            "gdpr_consent_given",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "data_captured",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("session_id"),
    )

    # Tabla de métricas por sesión (sin contenido de mensajes)
    op.create_table(
        "session_analytics",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.VARCHAR(length=100), nullable=False),
        sa.Column("message_count", sa.INTEGER(), nullable=True),
        sa.Column("avg_response_time_ms", sa.INTEGER(), nullable=True),
        sa.Column("technologies_mentioned", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column(
            "intent_categories",
            postgresql.ARRAY(sa.TEXT()),
            nullable=True,
            comment="experience, skills, projects",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.session_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Tabla de consentimientos GDPR
    op.create_table(
        "gdpr_consents",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.VARCHAR(length=100), nullable=False),
        sa.Column(
            "consent_timestamp",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("consent_types", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("ip_address", sa.VARCHAR(length=45), nullable=True),
        sa.Column("user_agent", sa.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.session_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Tabla de métricas agregadas diarias
    op.create_table(
        "daily_analytics",
        sa.Column("date", sa.DATE(), nullable=False),
        sa.Column(
            "total_sessions", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "total_messages", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "leads_captured", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "recruiter_count", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "client_count", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "curious_count", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "avg_engagement_score",
            sa.FLOAT(),
            server_default=sa.text("0.0"),
            nullable=False,
        ),
        sa.Column(
            "top_technologies", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "top_intents", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.PrimaryKeyConstraint("date"),
    )

    # Crear índices para optimizar queries frecuentes
    op.create_index("idx_chat_sessions_email", "chat_sessions", ["email"])
    op.create_index("idx_chat_sessions_created_at", "chat_sessions", ["created_at"])
    op.create_index("idx_chat_sessions_user_type", "chat_sessions", ["user_type"])
    op.create_index(
        "idx_chat_sessions_engagement", "chat_sessions", ["engagement_score"]
    )

    op.create_index(
        "idx_session_analytics_session_id", "session_analytics", ["session_id"]
    )
    op.create_index(
        "idx_session_analytics_created_at", "session_analytics", ["created_at"]
    )

    op.create_index("idx_gdpr_consents_session_id", "gdpr_consents", ["session_id"])
    op.create_index(
        "idx_gdpr_consents_timestamp", "gdpr_consents", ["consent_timestamp"]
    )

    op.create_index("idx_daily_analytics_date", "daily_analytics", ["date"])


def downgrade() -> None:
    """
    Eliminar tablas de analytics y GDPR compliance.
    """

    # Eliminar índices primero
    op.drop_index("idx_daily_analytics_date", table_name="daily_analytics")
    op.drop_index("idx_gdpr_consents_timestamp", table_name="gdpr_consents")
    op.drop_index("idx_gdpr_consents_session_id", table_name="gdpr_consents")
    op.drop_index("idx_session_analytics_created_at", table_name="session_analytics")
    op.drop_index("idx_session_analytics_session_id", table_name="session_analytics")
    op.drop_index("idx_chat_sessions_engagement", table_name="chat_sessions")
    op.drop_index("idx_chat_sessions_user_type", table_name="chat_sessions")
    op.drop_index("idx_chat_sessions_created_at", table_name="chat_sessions")
    op.drop_index("idx_chat_sessions_email", table_name="chat_sessions")

    # Eliminar tablas (en orden inverso por dependencias)
    op.drop_table("daily_analytics")
    op.drop_table("gdpr_consents")
    op.drop_table("session_analytics")
    op.drop_table("chat_sessions")
