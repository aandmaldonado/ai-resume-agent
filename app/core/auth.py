"""
Módulo de autenticación para endpoints administrativos.
Implementa autenticación basada en API Key para proteger endpoints sensibles.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Security scheme para Swagger UI
security = HTTPBearer(auto_error=False)


async def verify_admin_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verifica que el API Key proporcionado sea válido para acceso administrativo.

    Args:
        x_api_key: API Key enviado en el header X-API-Key

    Returns:
        bool: True si el API Key es válido

    Raises:
        HTTPException: Si el API Key es inválido o no se proporciona
    """
    if not x_api_key:
        logger.warning("Intento de acceso sin API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key requerido para acceso administrativo",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if x_api_key != settings.ADMIN_API_KEY:
        logger.warning(f"Intento de acceso con API Key inválido: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválido",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.info("Acceso administrativo autorizado")
    return True


async def verify_admin_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Header(None),
) -> bool:
    """
    Verifica token Bearer para acceso administrativo (alternativa).

    Args:
        credentials: Credenciales Bearer del header Authorization

    Returns:
        bool: True si el token es válido

    Raises:
        HTTPException: Si el token es inválido o no se proporciona
    """
    if not credentials:
        logger.warning("Intento de acceso sin token Bearer")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer requerido para acceso administrativo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.ADMIN_API_KEY:
        logger.warning(
            f"Intento de acceso con token inválido: {credentials.credentials[:8]}..."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Acceso administrativo autorizado via Bearer")
    return True


def get_admin_dependency():
    """
    Retorna la dependencia de autenticación para endpoints administrativos.
    Por defecto usa X-API-Key header.
    """
    return verify_admin_api_key
