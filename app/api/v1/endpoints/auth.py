"""
Endpoints de configuración y autenticación para frontend.
Maneja el intercambio de API Keys por tokens temporales.
"""

import logging
import secrets
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.schemas.auth import ConfigResponse, TokenExchangeRequest, TokenExchangeResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar Rate Limiter
limiter = Limiter(key_func=get_remote_address)


@router.get("/config", response_model=ConfigResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_public_config(request: Request) -> ConfigResponse:
    """
    Devuelve configuración pública para el frontend.
    No requiere autenticación - información pública.

    Args:
        request: Starlette Request (para rate limiting)

    Returns:
        ConfigResponse con configuración pública
    """
    try:
        logger.info("Solicitud de configuración pública")

        return ConfigResponse(
            public_api_key=settings.PUBLIC_API_KEY,
            frontend_api_key=settings.FRONTEND_API_KEY,
            api_base_url=f"https://{request.url.hostname}",
            version=settings.VERSION,
            environment="production" if settings.GCP_PROJECT_ID else "development",
        )

    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo configuración",
        )


@router.post(
    "/exchange-token",
    response_model=TokenExchangeResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/hour")  # Máximo 10 intercambios por hora
async def exchange_token(
    request: Request, token_request: TokenExchangeRequest
) -> TokenExchangeResponse:
    """
    Intercambia Frontend API Key por token temporal para acceso administrativo.

    Args:
        request: Starlette Request (para rate limiting)
        token_request: TokenExchangeRequest con Frontend API Key

    Returns:
        TokenExchangeResponse con token temporal
    """
    try:
        logger.info("Solicitud de intercambio de token")

        # Validar Frontend API Key
        if token_request.api_key != settings.FRONTEND_API_KEY:
            logger.warning(
                f"Intento de intercambio con API Key inválido: {token_request.api_key[:8]}..."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Frontend API Key inválido",
            )

        # Generar token temporal (1 hora de duración)
        temp_token = secrets.token_urlsafe(32)
        expires_in = 3600  # 1 hora
        expires_at = int(time.time()) + expires_in

        logger.info("Token temporal generado exitosamente")

        return TokenExchangeResponse(
            token=temp_token,
            expires_in=expires_in,
            expires_at=expires_at,
            token_type="Bearer",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en intercambio de token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno intercambiando token",
        )


@router.get("/auth/status", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_auth_status(request: Request) -> Dict[str, Any]:
    """
    Devuelve el estado de autenticación actual.
    Útil para debugging y monitoreo.

    Args:
        request: Starlette Request (para rate limiting)

    Returns:
        Dict con estado de autenticación
    """
    try:
        # Detectar tipo de autenticación basado en headers
        auth_header = request.headers.get("authorization", "")
        api_key_header = request.headers.get("x-api-key", "")

        auth_type = "none"
        if auth_header.startswith("Bearer "):
            auth_type = "service_account"
        elif api_key_header:
            auth_type = "api_key"

        return {
            "auth_type": auth_type,
            "environment": "production" if settings.GCP_PROJECT_ID else "development",
            "timestamp": int(time.time()),
            "rate_limit_remaining": "check_headers",  # Información del rate limiter
        }

    except Exception as e:
        logger.error(f"Error obteniendo estado de auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo estado de autenticación",
        )
