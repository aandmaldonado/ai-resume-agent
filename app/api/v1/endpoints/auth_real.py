"""
Endpoints de autenticación real para frontend autorizado.
Solo el frontend autorizado puede obtener tokens JWT.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.auth_real import create_access_token, verify_token
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Clave secreta para el frontend (debe ser muy segura)
FRONTEND_SECRET_KEY = "frontend-secret-key-super-secreta-cambiar-en-produccion"


@router.post("/get-token", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")  # Límite estricto para obtener tokens
async def get_frontend_token(request: Request) -> JSONResponse:
    """
    Endpoint para que el frontend autorizado obtenga un token JWT.
    Requiere una clave secreta del frontend.

    Args:
        request: Starlette Request (para rate limiting)

    Returns:
        JSONResponse con el token JWT

    Raises:
        HTTPException: Si la clave secreta es inválida
    """
    try:
        # Obtener la clave secreta del header
        frontend_key = request.headers.get("X-Frontend-Secret")

        if not frontend_key:
            logger.warning("Intento de obtener token sin clave secreta")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clave secreta del frontend requerida",
                headers={"WWW-Authenticate": "FrontendSecret"},
            )

        if frontend_key != FRONTEND_SECRET_KEY:
            logger.warning(
                f"Intento de obtener token con clave secreta inválida: {frontend_key[:8]}..."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clave secreta del frontend inválida",
                headers={"WWW-Authenticate": "FrontendSecret"},
            )

        # Crear token JWT para el frontend
        token_data = {
            "type": "frontend",
            "client": "authorized_frontend",
            "issued_at": datetime.utcnow().isoformat(),
        }

        access_token = create_access_token(token_data)

        logger.info("Token JWT generado exitosamente para frontend autorizado")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 24 * 60 * 60,  # 24 horas en segundos
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado generando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno generando token",
        )


@router.post("/refresh-token", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")  # Límite más generoso para refresh
async def refresh_token(request: Request) -> JSONResponse:
    """
    Endpoint para refrescar un token JWT existente.
    Requiere un token válido para refrescar.

    Args:
        request: Starlette Request (para rate limiting)

    Returns:
        JSONResponse con el nuevo token JWT

    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        # Obtener el token del header
        authorization = request.headers.get("Authorization")

        if not authorization:
            logger.warning("Intento de refresh sin token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token requerido para refresh",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extraer token del header "Bearer <token>"
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Esquema de autenticación inválido")
        except ValueError:
            logger.warning("Formato de autorización inválido en refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato de autorización inválido. Use: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verificar el token existente
        payload = verify_token(token)

        # Verificar que sea del frontend autorizado
        if payload.get("type") != "frontend":
            logger.warning("Token no es del frontend autorizado en refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no autorizado para refresh",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Crear nuevo token con los mismos datos
        new_token_data = {
            "type": "frontend",
            "client": "authorized_frontend",
            "issued_at": datetime.utcnow().isoformat(),
            "refreshed_from": payload.get("issued_at"),
        }

        new_access_token = create_access_token(new_token_data)

        logger.info("Token JWT refrescado exitosamente")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 24 * 60 * 60,  # 24 horas en segundos
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado refrescando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno refrescando token",
        )
