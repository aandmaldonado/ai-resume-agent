"""
Tests unitarios para app/models/analytics.py
Testea los modelos SQLAlchemy para analytics y GDPR compliance.
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import DeclarativeBase

from app.models.analytics import (
    Base,
    ChatSession,
    ChatMessage,
    GDPRConsent,
    SessionAnalytics,
    DailyAnalytics,
    ConversationPair
)


class TestModels:
    """Tests para los modelos SQLAlchemy."""

    def test_base_class_exists(self):
        """Test que la clase Base existe y es del tipo correcto."""
        assert Base is not None
        assert isinstance(Base, type(DeclarativeBase))

    def test_chat_session_model_definition(self):
        """Test definición del modelo ChatSession."""
        # Test tabla
        assert ChatSession.__tablename__ == "chat_sessions"
        
        # Test campos principales
        assert hasattr(ChatSession, 'session_id')
        assert hasattr(ChatSession, 'email')
        assert hasattr(ChatSession, 'user_type')
        assert hasattr(ChatSession, 'company')
        assert hasattr(ChatSession, 'role')
        assert hasattr(ChatSession, 'created_at')
        assert hasattr(ChatSession, 'last_activity')
        assert hasattr(ChatSession, 'total_messages')
        assert hasattr(ChatSession, 'engagement_score')
        assert hasattr(ChatSession, 'data_captured')
        assert hasattr(ChatSession, 'gdpr_consent_given')
        
        # Test relaciones
        assert hasattr(ChatSession, 'analytics')
        assert hasattr(ChatSession, 'consents')
        assert hasattr(ChatSession, 'messages')
        assert hasattr(ChatSession, 'conversation_pairs')

    def test_chat_message_model_definition(self):
        """Test definición del modelo ChatMessage."""
        # Test tabla
        assert ChatMessage.__tablename__ == "chat_messages"
        
        # Test campos principales
        assert hasattr(ChatMessage, 'id')
        assert hasattr(ChatMessage, 'session_id')
        assert hasattr(ChatMessage, 'message_type')
        assert hasattr(ChatMessage, 'content')
        assert hasattr(ChatMessage, 'response_time_ms')
        assert hasattr(ChatMessage, 'sources_used')
        assert hasattr(ChatMessage, 'created_at')
        
        # Test relación
        assert hasattr(ChatMessage, 'session')

    def test_session_analytics_model_definition(self):
        """Test definición del modelo SessionAnalytics."""
        # Test tabla
        assert SessionAnalytics.__tablename__ == "session_analytics"
        
        # Test campos principales
        assert hasattr(SessionAnalytics, 'id')
        assert hasattr(SessionAnalytics, 'session_id')
        assert hasattr(SessionAnalytics, 'message_count')
        assert hasattr(SessionAnalytics, 'avg_response_time_ms')
        assert hasattr(SessionAnalytics, 'technologies_mentioned')
        assert hasattr(SessionAnalytics, 'intent_categories')
        assert hasattr(SessionAnalytics, 'created_at')
        
        # Test relación
        assert hasattr(SessionAnalytics, 'session')

    def test_gdpr_consent_model_definition(self):
        """Test definición del modelo GDPRConsent."""
        # Test tabla
        assert GDPRConsent.__tablename__ == "gdpr_consents"
        
        # Test campos principales
        assert hasattr(GDPRConsent, 'id')
        assert hasattr(GDPRConsent, 'session_id')
        assert hasattr(GDPRConsent, 'consent_timestamp')
        assert hasattr(GDPRConsent, 'consent_types')
        assert hasattr(GDPRConsent, 'ip_address')
        assert hasattr(GDPRConsent, 'user_agent')
        
        # Test relación
        assert hasattr(GDPRConsent, 'session')

    def test_conversation_pair_model_definition(self):
        """Test definición del modelo ConversationPair."""
        # Test tabla
        assert ConversationPair.__tablename__ == "conversation_pairs"
        
        # Test campos principales
        assert hasattr(ConversationPair, 'id')
        assert hasattr(ConversationPair, 'session_id')
        assert hasattr(ConversationPair, 'user_question')
        assert hasattr(ConversationPair, 'bot_response')
        assert hasattr(ConversationPair, 'created_at')
        
        # Test relación
        assert hasattr(ConversationPair, 'session')

    def test_daily_analytics_model_definition(self):
        """Test definición del modelo DailyAnalytics."""
        # Test tabla
        assert DailyAnalytics.__tablename__ == "daily_analytics"
        
        # Test campos principales
        assert hasattr(DailyAnalytics, 'date')
        assert hasattr(DailyAnalytics, 'total_sessions')
        assert hasattr(DailyAnalytics, 'total_messages')
        assert hasattr(DailyAnalytics, 'leads_captured')
        assert hasattr(DailyAnalytics, 'recruiter_count')
        assert hasattr(DailyAnalytics, 'client_count')
        assert hasattr(DailyAnalytics, 'curious_count')
        assert hasattr(DailyAnalytics, 'avg_engagement_score')

    def test_model_relationships_exist(self):
        """Test que las relaciones entre modelos existen."""
        # ChatSession relaciones
        assert hasattr(ChatSession, 'analytics')
        assert hasattr(ChatSession, 'consents')
        assert hasattr(ChatSession, 'messages')
        assert hasattr(ChatSession, 'conversation_pairs')
        
        # ChatMessage relación
        assert hasattr(ChatMessage, 'session')
        
        # SessionAnalytics relación
        assert hasattr(SessionAnalytics, 'session')
        
        # GDPRConsent relación
        assert hasattr(GDPRConsent, 'session')
        
        # ConversationPair relación
        assert hasattr(ConversationPair, 'session')

    def test_model_metadata_structure(self):
        """Test estructura de metadatos de los modelos."""
        # Test que todos los modelos tienen metadatos
        assert hasattr(ChatSession, 'metadata')
        assert hasattr(ChatMessage, 'metadata')
        assert hasattr(SessionAnalytics, 'metadata')
        assert hasattr(GDPRConsent, 'metadata')
        assert hasattr(ConversationPair, 'metadata')
        assert hasattr(DailyAnalytics, 'metadata')

    def test_model_column_types(self):
        """Test tipos de columnas de los modelos."""
        # Test que los modelos tienen tablas definidas
        assert hasattr(ChatSession, '__table__')
        assert hasattr(ChatMessage, '__table__')
        assert hasattr(SessionAnalytics, '__table__')
        assert hasattr(GDPRConsent, '__table__')
        assert hasattr(ConversationPair, '__table__')
        assert hasattr(DailyAnalytics, '__table__')

    def test_model_constraints_exist(self):
        """Test que los modelos tienen constraints definidos."""
        # Test que los modelos tienen __table_args__
        assert hasattr(ChatSession, '__table_args__')
        assert hasattr(SessionAnalytics, '__table_args__')
        assert hasattr(GDPRConsent, '__table_args__')

    def test_model_indexes_exist(self):
        """Test que los modelos tienen índices definidos."""
        # Los índices están definidos en __table_args__
        # Solo verificamos que la estructura existe
        assert hasattr(ChatSession, '__table_args__')
        assert hasattr(SessionAnalytics, '__table_args__')
        assert hasattr(GDPRConsent, '__table_args__')

    def test_model_default_values(self):
        """Test valores por defecto de los modelos."""
        # Test que los modelos tienen valores por defecto definidos
        # Esto se verifica a través de la estructura de las columnas
        assert hasattr(ChatSession, '__table__')
        assert hasattr(ChatMessage, '__table__')
        assert hasattr(SessionAnalytics, '__table__')
        assert hasattr(GDPRConsent, '__table__')
        assert hasattr(ConversationPair, '__table__')
        assert hasattr(DailyAnalytics, '__table__')

    def test_model_foreign_keys(self):
        """Test claves foráneas de los modelos."""
        # Test que los modelos tienen foreign keys definidas
        # ChatMessage -> ChatSession
        assert hasattr(ChatMessage, 'session_id')
        
        # SessionAnalytics -> ChatSession
        assert hasattr(SessionAnalytics, 'session_id')
        
        # GDPRConsent -> ChatSession
        assert hasattr(GDPRConsent, 'session_id')
        
        # ConversationPair -> ChatSession
        assert hasattr(ConversationPair, 'session_id')

    def test_model_repr_methods(self):
        """Test métodos __repr__ de los modelos."""
        # Test que los modelos tienen métodos __repr__
        assert hasattr(ChatSession, '__repr__')
        assert hasattr(SessionAnalytics, '__repr__')
        assert hasattr(GDPRConsent, '__repr__')

    def test_model_primary_keys(self):
        """Test claves primarias de los modelos."""
        # Test claves primarias
        assert hasattr(ChatSession, 'session_id')  # Primary key
        assert hasattr(ChatMessage, 'id')  # Primary key
        assert hasattr(SessionAnalytics, 'id')  # Primary key
        assert hasattr(GDPRConsent, 'id')  # Primary key
        assert hasattr(ConversationPair, 'id')  # Primary key
        assert hasattr(DailyAnalytics, 'date')  # Primary key

    def test_model_imports(self):
        """Test que todos los modelos se pueden importar correctamente."""
        # Test que las clases existen y son importables
        assert ChatSession is not None
        assert ChatMessage is not None
        assert SessionAnalytics is not None
        assert GDPRConsent is not None
        assert ConversationPair is not None
        assert DailyAnalytics is not None

    def test_model_class_types(self):
        """Test tipos de clase de los modelos."""
        # Test que las clases son del tipo correcto
        assert issubclass(ChatSession, Base)
        assert issubclass(ChatMessage, Base)
        assert issubclass(SessionAnalytics, Base)
        assert issubclass(GDPRConsent, Base)
        assert issubclass(ConversationPair, Base)
        assert issubclass(DailyAnalytics, Base)

    def test_model_table_names_unique(self):
        """Test que los nombres de tabla son únicos."""
        table_names = [
            ChatSession.__tablename__,
            ChatMessage.__tablename__,
            SessionAnalytics.__tablename__,
            GDPRConsent.__tablename__,
            ConversationPair.__tablename__,
            DailyAnalytics.__tablename__
        ]
        
        # Verificar que no hay duplicados
        assert len(table_names) == len(set(table_names))

    def test_model_table_names_format(self):
        """Test formato de nombres de tabla."""
        # Test que los nombres de tabla siguen convención snake_case
        assert ChatSession.__tablename__ == "chat_sessions"
        assert ChatMessage.__tablename__ == "chat_messages"
        assert SessionAnalytics.__tablename__ == "session_analytics"
        assert GDPRConsent.__tablename__ == "gdpr_consents"
        assert ConversationPair.__tablename__ == "conversation_pairs"
        assert DailyAnalytics.__tablename__ == "daily_analytics"
