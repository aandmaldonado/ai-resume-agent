"""
Configuración de la aplicación usando Pydantic Settings.
Lee variables de entorno y proporciona valores por defecto.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # Información del proyecto
    PROJECT_NAME: str = "AI Resume Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # GCP
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "europe-west1"  # Misma región que el portfolio

    # Google Gemini API (LLM alternativo)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Modelo más rápido y menos restrictivo
    GEMINI_TEMPERATURE: float = 0.4  # Más confianza para sintetizar respuestas STAR
    GEMINI_TOP_P: float = 0.7  # Ventana más amplia para construcción de frases
    GEMINI_MAX_TOKENS: int = 512  # Espacio suficiente para respuestas detalladas

    # Cloud SQL (PostgreSQL + pgvector)
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = None  # Para Cloud Run
    CLOUD_SQL_HOST: Optional[str] = "localhost"  # Para desarrollo local
    CLOUD_SQL_PORT: str = "5432"
    CLOUD_SQL_DB: str = "chatbot_db"
    CLOUD_SQL_USER: str = "postgres"
    CLOUD_SQL_PASSWORD: str = ""

    # Cloud Storage
    PORTFOLIO_BUCKET: str = "almapi-portfolio-data"
    PORTFOLIO_FILE: str = "portfolio.yaml"

    # Vector Store
    VECTOR_COLLECTION_NAME: str = "portfolio_knowledge"
    VECTOR_SEARCH_K: int = 5  # Top K documentos a recuperar (aumentado para preguntas complejas)

    # Conversational Memory
    MAX_CONVERSATION_HISTORY: int = 5  # Últimos N pares de mensajes a recordar
    SESSION_TIMEOUT_MINUTES: int = 60  # Limpiar sesiones inactivas después de 60 min

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "https://almapi.dev",
        "https://*.almapi.dev",
    ]

    # Cache para optimizar costos
    ENABLE_RESPONSE_CACHE: bool = True
    CACHE_TTL_MINUTES: int = 30  # Cache por 30 minutos
    MAX_CACHE_SIZE: int = 100  # Máximo 100 respuestas en cache

    # Rate Limiting (optimizado para costos)
    RATE_LIMIT_PER_MINUTE: int = 5  # Reducido para minimizar costos

    # Testing
    TESTING: bool = False

    # Analytics y Captura de Leads
    ENABLE_ANALYTICS: bool = True
    DATA_CAPTURE_AFTER_MESSAGES: int = 2  # Capturar datos después de N mensajes
    ENGAGEMENT_THRESHOLD: float = 0.6  # Umbral mínimo de engagement para captura
    MAX_DATA_CAPTURE_ATTEMPTS: int = (
        3  # Máximo número de intentos para captura de datos
    )
    MAX_GDPR_CONSENT_ATTEMPTS: int = 3  # Máximo número de intentos para GDPR


    # GDPR Compliance
    DATA_RETENTION_DAYS: int = 365  # Retención máxima de datos
    ANONYMIZE_AFTER_DAYS: int = 90  # Anonimizar después de N días sin actividad

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        """
        Construye la URL de la base de datos según el entorno.
        En Cloud Run usa Unix socket, en local usa TCP.
        """
        import logging
        import os
        logger = logging.getLogger(__name__)
        
        # Debug logging para variables de entorno (solo en desarrollo)
        if not self.CLOUD_SQL_CONNECTION_NAME:  # Solo en desarrollo local
            logger.debug(f"DEBUG: CLOUD_SQL_CONNECTION_NAME exists: {'CLOUD_SQL_CONNECTION_NAME' in os.environ}")
            logger.debug(f"DEBUG: CLOUD_SQL_CONNECTION_NAME value: {self.CLOUD_SQL_CONNECTION_NAME}")
            logger.debug(f"DEBUG: CLOUD_SQL_PASSWORD exists: {'CLOUD_SQL_PASSWORD' in os.environ}")
            logger.debug(f"DEBUG: CLOUD_SQL_PASSWORD length: {len(self.CLOUD_SQL_PASSWORD) if self.CLOUD_SQL_PASSWORD else 'Not Set'}")
            logger.debug(f"DEBUG: CLOUD_SQL_USER: {self.CLOUD_SQL_USER}")
            logger.debug(f"DEBUG: CLOUD_SQL_DB: {self.CLOUD_SQL_DB}")
        
        if self.CLOUD_SQL_CONNECTION_NAME:
            # Cloud Run con Cloud SQL Proxy (Unix socket)
            url = (
                f"postgresql://{self.CLOUD_SQL_USER}:{self.CLOUD_SQL_PASSWORD}@/"
                f"{self.CLOUD_SQL_DB}?host=/cloudsql/{self.CLOUD_SQL_CONNECTION_NAME}"
            )
            logger.debug(f"DEBUG: Using Cloud SQL Unix socket connection")
            return url
        else:
            # Desarrollo local o conexión directa
            url = (
                f"postgresql://{self.CLOUD_SQL_USER}:{self.CLOUD_SQL_PASSWORD}@"
                f"{self.CLOUD_SQL_HOST}:{self.CLOUD_SQL_PORT}/{self.CLOUD_SQL_DB}"
            )
            logger.debug(f"DEBUG: Using direct TCP connection")
            return url

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        Construye la URL asíncrona de la base de datos según el entorno.
        En Cloud Run usa Unix socket, en local usa TCP.
        """
        if self.CLOUD_SQL_CONNECTION_NAME:
            # Cloud Run con Cloud SQL Proxy (Unix socket)
            return (
                f"postgresql+asyncpg://{self.CLOUD_SQL_USER}:{self.CLOUD_SQL_PASSWORD}@/"
                f"{self.CLOUD_SQL_DB}?host=/cloudsql/{self.CLOUD_SQL_CONNECTION_NAME}"
            )
        else:
            # Desarrollo local o conexión directa
            return (
                f"postgresql+asyncpg://{self.CLOUD_SQL_USER}:{self.CLOUD_SQL_PASSWORD}@"
                f"{self.CLOUD_SQL_HOST}:{self.CLOUD_SQL_PORT}/{self.CLOUD_SQL_DB}"
            )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de settings
settings = Settings()
