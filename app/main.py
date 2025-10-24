"""
FastAPI application principal.
Configuración de la app, middlewares, CORS y routers.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.endpoints import analytics, chat
from app.core.config import settings
from app.services.rag_service import RAGService

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configurar Rate Limiter (protección anti-DoS)
limiter = Limiter(key_func=get_remote_address)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Chatbot RAG para portfolio profesional usando Gemini, HuggingFace y pgvector",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Registrar Rate Limiter en la app
app.state.limiter = limiter

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware (seguridad)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "testserver",  # Para tests
        "almapi.dev",
        "*.almapi.dev",
        "*.run.app",  # Cloud Run
        "*.googleusercontent.com",  # Cloud Run internal
    ],
)

# Incluir routers
app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["chat"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["analytics"])


@app.on_event("startup")
async def startup_event():
    """Ejecutar al iniciar la aplicación"""
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(
        f"   Entorno: {'Production' if settings.CLOUD_SQL_CONNECTION_NAME else 'Development'}"
    )
    logger.info(f"   GCP Project: {settings.GCP_PROJECT_ID}")
    logger.info(f"   LLM: {settings.GEMINI_MODEL}")
    logger.info(f"   Embeddings: HuggingFace (local)")
    logger.info(f"   Vector Collection: {settings.VECTOR_COLLECTION_NAME}")
    
    # Inicializar vector store con chunks enriquecidos
    try:
        logger.info("🚀 Inicializando vector store...")
        
        # Importar aquí para evitar imports circulares
        from scripts.setup.build_knowledge_base import load_and_prepare_chunks
        from scripts.setup.initialize_vector_store import initialize_vector_store
        
        # Cargar chunks enriquecidos
        chunks = load_and_prepare_chunks("data/portfolio.yaml")
        logger.info(f"✓ {len(chunks)} chunks enriquecidos cargados")
        
        # Inicializar vector store
        await initialize_vector_store(chunks)
        logger.info("✅ Vector store inicializado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando vector store: {e}")
        # No fallar la aplicación si hay error en vector store
        logger.warning("⚠️ Continuando sin vector store inicializado")


@app.on_event("shutdown")
async def shutdown_event():
    """Ejecutar al cerrar la aplicación"""
    logger.info("👋 Cerrando aplicación...")


@app.get("/", tags=["root"])
async def root():
    """
    Endpoint raíz del API.
    Retorna información básica del servicio.
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handler global de excepciones no capturadas.
    """
    logger.error(f"Error no capturado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": (
                str(exc) if settings.LOG_LEVEL == "DEBUG" else "An error occurred"
            ),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
