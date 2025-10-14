"""
FastAPI application principal.
Configuración de la app, middlewares, CORS y routers.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1.endpoints import chat

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar Rate Limiter (protección anti-DoS)
limiter = Limiter(key_func=get_remote_address)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Chatbot RAG para portfolio profesional usando Groq, Vertex AI y pgvector",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Registrar Rate Limiter en la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    allowed_hosts=["*"]  # En producción, especificar hosts permitidos
)

# Incluir routers
app.include_router(
    chat.router,
    prefix=settings.API_V1_STR,
    tags=["chat"]
)


@app.on_event("startup")
async def startup_event():
    """Ejecutar al iniciar la aplicación"""
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"   Entorno: {'Production' if settings.CLOUD_SQL_CONNECTION_NAME else 'Development'}")
    logger.info(f"   GCP Project: {settings.GCP_PROJECT_ID}")
    logger.info(f"   LLM: {settings.GROQ_MODEL}")
    logger.info(f"   Embeddings: {settings.VERTEX_AI_EMBEDDING_MODEL}")
    logger.info(f"   Vector Collection: {settings.VECTOR_COLLECTION_NAME}")


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
        "api_v1": settings.API_V1_STR
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
            "message": str(exc) if settings.LOG_LEVEL == "DEBUG" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )

