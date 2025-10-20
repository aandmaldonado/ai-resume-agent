"""
Schemas de autenticación para intercambio de tokens y configuración.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ConfigResponse(BaseModel):
    """Respuesta con configuración pública para el frontend"""

    public_api_key: str = Field(..., description="API Key pública para acceso al chat")
    frontend_api_key: str = Field(..., description="API Key para intercambio de tokens")
    api_base_url: str = Field(..., description="URL base de la API")
    version: str = Field(..., description="Versión de la aplicación")
    environment: str = Field(..., description="Entorno: production o development")


class TokenExchangeRequest(BaseModel):
    """Request para intercambiar API Key por token temporal"""

    api_key: str = Field(..., description="Frontend API Key")


class TokenExchangeResponse(BaseModel):
    """Respuesta con token temporal para acceso administrativo"""

    token: str = Field(..., description="Token temporal")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    expires_at: int = Field(..., description="Timestamp de expiración")
    token_type: str = Field(default="Bearer", description="Tipo de token")


class AuthStatusResponse(BaseModel):
    """Estado de autenticación actual"""

    auth_type: str = Field(..., description="Tipo de autenticación detectado")
    environment: str = Field(..., description="Entorno actual")
    timestamp: int = Field(..., description="Timestamp actual")
    rate_limit_remaining: str = Field(..., description="Rate limit restante")
