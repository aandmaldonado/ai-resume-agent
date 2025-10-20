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


def get_admin_dependency():
    """
    Retorna la dependencia de autenticación para endpoints administrativos.
    En Cloud Run usa Service Account, en local usa API Key.
    """
    # En Cloud Run, usar Service Account
    if settings.GCP_PROJECT_ID and settings.CLOUD_SQL_CONNECTION_NAME:
        return verify_service_account_token
    # En desarrollo local, usar API Key
    return verify_admin_api_key
