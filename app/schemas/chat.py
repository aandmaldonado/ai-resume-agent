"""
Esquemas Pydantic para los endpoints de chat.
Define los modelos de request y response.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request para enviar un mensaje al chatbot"""
    message: str = Field(..., min_length=1, max_length=500, description="Mensaje del usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión para mantener contexto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Cuál es tu experiencia con Python?",
                "session_id": "user-123-session-456"
            }
        }


class SourceDocument(BaseModel):
    """Documento fuente usado para generar la respuesta"""
    type: str = Field(..., description="Tipo de documento (experience, education, skills, etc.)")
    content_preview: Optional[str] = Field(None, description="Preview del contenido")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional del documento")


class ChatResponse(BaseModel):
    """Response del chatbot con la respuesta generada"""
    message: str = Field(..., description="Respuesta generada por el chatbot")
    sources: List[SourceDocument] = Field(default=[], description="Documentos fuente usados")
    session_id: Optional[str] = Field(None, description="ID de sesión")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la respuesta")
    model: str = Field(default="llama-3.1-70b", description="Modelo usado para generar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Tengo más de 15 años de experiencia en desarrollo de software, especializado en Python, Java y JavaScript...",
                "sources": [
                    {
                        "type": "experience",
                        "content_preview": "Empresa: InAdvance Consulting Group...",
                        "metadata": {"company": "InAdvance", "position": "Senior Software Engineer"}
                    }
                ],
                "session_id": "user-123-session-456",
                "timestamp": "2025-01-15T10:30:00",
                "model": "llama-3.1-70b"
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
                "timestamp": "2025-01-15T10:30:00"
            }
        }

