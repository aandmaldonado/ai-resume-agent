"""
Sistema de autenticación simplificado con una sola API Key para todos los endpoints.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verifica que el API Key sea válido para TODOS los endpoints.

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
            detail="API Key requerido para acceder a este endpoint",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if x_api_key != settings.API_KEY:
        logger.warning(f"Intento de acceso con API Key inválido: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválido",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.info("Acceso autorizado con API Key válida")
    return True


def get_api_key_dependency():
    """
    Retorna la dependencia de autenticación para TODOS los endpoints.
    Usa una sola API Key para todo el sistema.
    """
    return verify_api_key
