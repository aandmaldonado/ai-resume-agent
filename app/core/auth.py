"""
Módulo de autenticación para endpoints administrativos.
Implementa autenticación basada en Service Account para Cloud Run.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Security scheme para Swagger UI
security = HTTPBearer(auto_error=False)


async def verify_service_account_token(
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Verifica que la petición venga de un Service Account autorizado.
    Para Cloud Run, esto significa verificar el token de identidad.

    Args:
        authorization: Header Authorization con Bearer token

    Returns:
        bool: True si el token es válido

    Raises:
        HTTPException: Si el token es inválido o no se proporciona
    """
    if not authorization:
        logger.warning("Intento de acceso sin token de autorización")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido para acceso administrativo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # En Cloud Run, el token viene como "Bearer <token>"
    if not authorization.startswith("Bearer "):
        logger.warning("Formato de token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # TODO: Implementar verificación real del token JWT de GCP
    # Por ahora, usar API Key como fallback
    if token != settings.ADMIN_API_KEY:
        logger.warning(f"Intento de acceso con token inválido: {token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Acceso administrativo autorizado via Service Account")
    return True


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


async def verify_frontend_token(
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Verifica token temporal generado por el frontend.

    Args:
        authorization: Header Authorization con Bearer token

    Returns:
        bool: True si el token es válido

    Raises:
        HTTPException: Si el token es inválido o no se proporciona
    """
    if not authorization:
        logger.warning("Intento de acceso sin token de autorización")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        logger.warning("Formato de token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # TODO: Implementar verificación real del token temporal
    # Por ahora, aceptar cualquier token que empiece con "temp_"
    if not token.startswith("temp_"):
        logger.warning(f"Token temporal inválido: {token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token temporal inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Acceso autorizado via token temporal")
    return True


def get_api_key_dependency():
    """
    Retorna la dependencia de autenticación para TODOS los endpoints.
    Usa una sola API Key para todo el sistema.
    """
    return verify_api_key


async def verify_public_api_key(x_public_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verifica que el Public API Key sea válido para acceso al chat.

    Args:
        x_public_api_key: Public API Key enviado en el header X-Public-API-Key

    Returns:
        bool: True si el API Key es válido

    Raises:
        HTTPException: Si el API Key es inválido o no se proporciona
    """
    if not x_public_api_key:
        logger.warning("Intento de acceso sin Public API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Public API Key requerido para acceso al chat",
            headers={"WWW-Authenticate": "PublicApiKey"},
        )

    if x_public_api_key != settings.PUBLIC_API_KEY:
        logger.warning(
            f"Intento de acceso con Public API Key inválido: {x_public_api_key[:8]}..."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Public API Key inválido",
            headers={"WWW-Authenticate": "PublicApiKey"},
        )

    logger.info("Acceso al chat autorizado")
    return True


def get_frontend_dependency():
    """
    Retorna la dependencia de autenticación para frontend.
    Usa tokens temporales generados por /exchange-token.
    """
    return verify_frontend_token


def get_public_dependency():
    """
    Retorna la dependencia de autenticación para chat público.
    Usa Public API Key.
    """
    return verify_public_api_key
