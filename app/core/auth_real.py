"""
Sistema de autenticación real con JWT para frontend autorizado.
Solo el frontend autorizado puede obtener tokens y acceder a los endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Header, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# Clave secreta para JWT (debe ser muy segura)
JWT_SECRET_KEY = "tu-jwt-secret-key-super-secreta-cambiar-en-produccion"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def create_access_token(data: dict) -> str:
    """
    Crear un token JWT para el frontend autorizado.

    Args:
        data: Datos a incluir en el token

    Returns:
        str: Token JWT codificado
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.info("Token JWT creado exitosamente")
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verificar y decodificar un token JWT.

    Args:
        token: Token JWT a verificar

    Returns:
        dict: Datos decodificados del token

    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        logger.info("Token JWT verificado exitosamente")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        logger.warning("Token JWT inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_frontend_token(authorization: Optional[str] = Header(None)) -> bool:
    """
    Verificar que el token JWT sea válido para el frontend autorizado.

    Args:
        authorization: Header Authorization con Bearer token

    Returns:
        bool: True si el token es válido

    Raises:
        HTTPException: Si el token es inválido o no se proporciona
    """
    if not authorization:
        logger.warning("Intento de acceso sin token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido para acceder a este endpoint",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extraer token del header "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Esquema de autenticación inválido")

    except ValueError:
        logger.warning("Formato de autorización inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de autorización inválido. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar el token
    payload = verify_token(token)

    # Verificar que sea del frontend autorizado
    if payload.get("type") != "frontend":
        logger.warning("Token no es del frontend autorizado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no autorizado para este endpoint",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Acceso autorizado con token JWT válido")
    return True


def get_frontend_dependency():
    """
    Retorna la dependencia de autenticación para el frontend autorizado.
    Usa tokens JWT para autenticación real.
    """
    return verify_frontend_token
