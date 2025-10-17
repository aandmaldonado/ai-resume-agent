"""
Schemas Pydantic para analytics y captura de datos.
Define los modelos de datos para requests, responses y métricas.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class SessionCreate(BaseModel):
    """Schema para crear una nueva sesión."""

    session_id: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    user_type: Optional[str] = Field(None, pattern="^(recruiter|client|curious)$")
    company: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=100)


class SessionUpdate(BaseModel):
    """Schema para actualizar una sesión existente."""

    email: Optional[EmailStr] = None
    user_type: Optional[str] = Field(None, pattern="^(recruiter|client|curious)$")
    company: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=100)
    data_captured: Optional[bool] = None
    gdpr_consent_given: Optional[bool] = None


class SessionResponse(BaseModel):
    """Schema para respuesta de sesión."""

    session_id: str
    email: Optional[str] = None
    user_type: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    total_messages: int
    engagement_score: float
    data_captured: bool
    gdpr_consent_given: bool

    class Config:
        from_attributes = True


class SessionAnalyticsCreate(BaseModel):
    """Schema para crear analytics de sesión."""

    session_id: str = Field(..., min_length=1, max_length=100)
    message_count: int = Field(..., ge=1)
    avg_response_time_ms: Optional[int] = Field(None, ge=0)
    technologies_mentioned: Optional[List[str]] = None
    intent_categories: Optional[List[str]] = None


class SessionAnalyticsResponse(BaseModel):
    """Schema para respuesta de analytics de sesión."""

    id: int
    session_id: str
    message_count: int
    avg_response_time_ms: Optional[int] = None
    technologies_mentioned: Optional[List[str]] = None
    intent_categories: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DataCaptureRequest(BaseModel):
    """Schema para solicitud de captura de datos."""

    session_id: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="Email del usuario")
    user_type: str = Field(
        ..., pattern="^(recruiter|client|curious)$", description="Tipo de usuario"
    )
    company: Optional[str] = Field(
        None, max_length=200, description="Empresa del usuario"
    )
    role: Optional[str] = Field(None, max_length=100, description="Rol del usuario")

    @validator("email")
    def validate_email_domain(cls, v):
        """Validar que el email tenga un dominio válido."""
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("Email debe tener un formato válido")
        return v.lower()


class DataCaptureResponse(BaseModel):
    """Schema para respuesta de captura de datos."""

    success: bool
    message: str
    session_id: str
    data_captured: bool
    next_action: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GDPRConsentRequest(BaseModel):
    """Schema para solicitud de consentimiento GDPR."""

    session_id: str = Field(..., min_length=1, max_length=100)
    consent_types: List[str] = Field(
        ..., min_items=1, description="Tipos de consentimiento"
    )
    ip_address: Optional[str] = Field(None, max_length=45, description="IP del usuario")
    user_agent: Optional[str] = Field(
        None, max_length=500, description="User agent del navegador"
    )

    @validator("consent_types")
    def validate_consent_types(cls, v):
        """Validar tipos de consentimiento."""
        valid_types = ["analytics", "marketing", "data_processing", "data_storage"]
        for consent_type in v:
            if consent_type not in valid_types:
                raise ValueError(f"Tipo de consentimiento inválido: {consent_type}")
        return v


class GDPRConsentResponse(BaseModel):
    """Schema para respuesta de consentimiento GDPR."""

    success: bool
    message: str
    session_id: str
    consent_given: bool
    consent_types: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GDPRDataRequest(BaseModel):
    """Schema para solicitud de datos GDPR."""

    session_id: str = Field(..., min_length=1, max_length=100)


class GDPRDataResponse(BaseModel):
    """Schema para respuesta de datos GDPR."""

    success: bool
    session_id: str
    user_data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class GDPRExportResponse(BaseModel):
    """Schema para respuesta de exportación GDPR."""

    success: bool
    session_id: str
    export_data: Optional[str] = None  # JSON string
    message: Optional[str] = None


class AnalyticsMetrics(BaseModel):
    """Schema para métricas generales de analytics."""

    total_sessions: int = Field(..., ge=0)
    total_messages: int = Field(..., ge=0)
    leads_captured: int = Field(..., ge=0)
    recruiter_count: int = Field(..., ge=0)
    client_count: int = Field(..., ge=0)
    curious_count: int = Field(..., ge=0)
    avg_engagement_score: float = Field(..., ge=0.0, le=1.0)
    top_technologies: Dict[str, int] = Field(default_factory=dict)
    top_intents: Dict[str, int] = Field(default_factory=dict)


class DailyAnalyticsResponse(BaseModel):
    """Schema para respuesta de analytics diarios."""

    date: date
    total_sessions: int = Field(..., ge=0)
    total_messages: int = Field(..., ge=0)
    leads_captured: int = Field(..., ge=0)
    recruiter_count: int = Field(..., ge=0)
    client_count: int = Field(..., ge=0)
    curious_count: int = Field(..., ge=0)
    avg_engagement_score: float = Field(..., ge=0.0, le=1.0)
    top_technologies: Dict[str, int] = Field(default_factory=dict)
    top_intents: Dict[str, int] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class FlowStateResponse(BaseModel):
    """Schema para respuesta de estado del flujo."""

    session_id: str
    current_state: str
    total_messages: int
    engagement_score: float
    data_captured: bool
    gdpr_consent_given: bool
    user_type: Optional[str] = None
    created_at: datetime
    last_activity: datetime


class FlowActionRequest(BaseModel):
    """Schema para solicitud de acción del flujo."""

    session_id: str = Field(..., min_length=1, max_length=100)
    action_type: str = Field(..., description="Tipo de acción a realizar")
    additional_data: Optional[Dict[str, Any]] = Field(
        None, description="Datos adicionales"
    )


class FlowActionResponse(BaseModel):
    """Schema para respuesta de acción del flujo."""

    success: bool
    session_id: str
    action_type: str
    new_state: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalyticsConfigResponse(BaseModel):
    """Schema para respuesta de configuración de analytics."""

    data_capture_after_messages: int
    engagement_threshold: float
    gdpr_consent_after_capture: bool
    min_session_duration_seconds: int
    flow_states: List[str]
    action_types: List[str]


class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""

    success: bool = False
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Schema para respuestas de éxito."""

    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None
