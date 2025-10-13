"""
Configuración de la aplicación usando Pydantic Settings.
Lee variables de entorno y proporciona valores por defecto.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Información del proyecto
    PROJECT_NAME: str = "AI Resume Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # GCP
    GCP_PROJECT_ID: str
    GCP_REGION: str = "europe-west1"  # Misma región que el portfolio
    
    # Groq API (LLM gratis)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Modelo actualizado
    GROQ_TEMPERATURE: float = 0.7
    GROQ_MAX_TOKENS: int = 1024
    
    # Vertex AI (Embeddings gratis)
    VERTEX_AI_EMBEDDING_MODEL: str = "textembedding-gecko@003"  # Versión más reciente
    VERTEX_AI_EMBEDDING_LOCATION: str = "us-central1"  # Región con embeddings disponibles
    
    # Cloud SQL (PostgreSQL + pgvector)
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = None  # Para Cloud Run
    CLOUD_SQL_HOST: Optional[str] = "localhost"  # Para desarrollo local
    CLOUD_SQL_PORT: str = "5432"
    CLOUD_SQL_DB: str = "chatbot_db"
    CLOUD_SQL_USER: str = "postgres"
    CLOUD_SQL_PASSWORD: str
    
    # Cloud Storage
    PORTFOLIO_BUCKET: str = "almapi-portfolio-data"
    PORTFOLIO_FILE: str = "portfolio.yaml"
    
    # Vector Store
    VECTOR_COLLECTION_NAME: str = "portfolio_knowledge"
    VECTOR_SEARCH_K: int = 3  # Top K documentos a recuperar
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://almapi.dev",
        "https://*.almapi.dev"
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def database_url(self) -> str:
        """
        Construye la URL de la base de datos según el entorno.
        En Cloud Run usa Unix socket, en local usa TCP.
        """
        if self.CLOUD_SQL_CONNECTION_NAME:
            # Cloud Run con Cloud SQL Proxy (Unix socket)
            return (
                f"postgresql://{self.CLOUD_SQL_USER}:{self.CLOUD_SQL_PASSWORD}@/"
                f"{self.CLOUD_SQL_DB}?host=/cloudsql/{self.CLOUD_SQL_CONNECTION_NAME}"
            )
        else:
            # Desarrollo local o conexión directa
            return (
                f"postgresql://{self.CLOUD_SQL_USER}:{self.CLOUD_SQL_PASSWORD}@"
                f"{self.CLOUD_SQL_HOST}:{self.CLOUD_SQL_PORT}/{self.CLOUD_SQL_DB}"
            )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de settings
settings = Settings()

