"""
Esquemas Pydantic para los endpoints de chat.
Define los modelos de request y response.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

"""
Esquemas Pydantic para los endpoints de chat.
Define los modelos de request y response.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ChatRequest(BaseModel):
    """Request para enviar un mensaje al chatbot"""

    message: str = Field(
        ...,
        min_length=1,
        max_length=600,  # Límite óptimo para preguntas profesionales detalladas
        description="Mensaje del usuario",
    )

    @validator("message")
    def validate_message(cls, v):
        # Remover caracteres de control peligrosos
        v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)

        # Detectar posibles inyecciones
        injection_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"data:.*?base64",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(
                    "El mensaje contiene contenido potencialmente malicioso"
                )

        return v.strip()

    session_id: Optional[str] = Field(
        None,
        max_length=100,  # Prevenir session_id maliciosos
        description="ID de sesión para mantener contexto",
    )

    @validator("session_id")
    def validate_session_id(cls, v):
        if v is None:
            return v

        # Validar formato: solo alfanumérico, guiones y puntos
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError(
                "session_id debe contener solo caracteres alfanuméricos, puntos, guiones y guiones bajos"
            )

        # Prevenir patrones sospechosos
        suspicious_patterns = ["..", "--", "__", "script", "javascript", "eval"]
        if any(pattern in v.lower() for pattern in suspicious_patterns):
            raise ValueError("session_id contiene patrones no permitidos")

        return v

    # Campos adicionales para analytics y captura de datos
    email: Optional[str] = Field(None, description="Email del usuario (opcional)")
    user_type: Optional[str] = Field(
        None, description="Tipo de usuario: recruiter, client, curious"
    )
    gdpr_consent: Optional[bool] = Field(False, description="Consentimiento GDPR dado")

    @validator("user_type")
    def validate_user_type(cls, v):
        if v is not None and v not in ["recruiter", "client", "curious"]:
            raise ValueError("user_type debe ser: recruiter, client, o curious")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Cuál es tu experiencia con Python?",
                "session_id": "user-123-session-456",
                "email": "user@example.com",
                "user_type": "recruiter",
                "gdpr_consent": True,
            }
        }


class SourceDocument(BaseModel):
    """Documento fuente usado para generar la respuesta"""

    type: str = Field(
        ..., description="Tipo de documento (experience, education, skills, etc.)"
    )
    content_preview: Optional[str] = Field(None, description="Preview del contenido")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata adicional del documento"
    )


class ChatResponse(BaseModel):
    """Response del chatbot con la respuesta generada"""

    message: str = Field(..., description="Respuesta generada por el chatbot")
    sources: List[SourceDocument] = Field(
        default=[], description="Documentos fuente usados"
    )
    session_id: Optional[str] = Field(None, description="ID de sesión")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp de la respuesta"
    )
    model: str = Field(
        default="llama-3.3-70b-versatile", description="Modelo usado para generar"
    )

    # Campos adicionales para flujo de captura de datos
    action_type: str = Field(
        default="normal_response",
        description="Tipo de acción: show_welcome, request_data_capture, request_gdpr_consent, normal_response",
    )
    next_flow_state: str = Field(
        default="conversation_active", description="Siguiente estado del flujo"
    )
    requires_data_capture: bool = Field(
        default=False, description="Requiere captura de datos del usuario"
    )
    requires_gdpr_consent: bool = Field(
        default=False, description="Requiere consentimiento GDPR"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Tengo más de 15 años de experiencia en desarrollo de software, especializado en Python, Java y JavaScript...",
                "sources": [
                    {
                        "type": "experience",
                        "content_preview": "Empresa: InAdvance Consulting Group...",
                        "metadata": {
                            "company": "InAdvance",
                            "position": "Senior Software Engineer",
                        },
                    }
                ],
                "session_id": "user-123-session-456",
                "timestamp": "2025-01-15T10:30:00",
                "model": "llama-3.3-70b-versatile",
                "action_type": "normal_response",
                "next_flow_state": "conversation_active",
                "requires_data_capture": False,
                "requires_gdpr_consent": False,
            }
        }


class HealthResponse(BaseModel):
    """Response del health check endpoint"""

    status: str = Field(..., description="Estado del servicio")
    version: str = Field(..., description="Versión de la API")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-01-15T10:30:00",
            }
        }
