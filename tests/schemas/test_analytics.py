"""
Tests unitarios simples para app/schemas/analytics.py
Testea que los esquemas se pueden importar y crear correctamente.
"""

import pytest
from datetime import date, datetime

from app.schemas.analytics import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    DataCaptureRequest,
    GDPRConsentRequest,
    GDPRDataRequest,
    AnalyticsMetrics,
    DailyAnalyticsResponse,
    SuccessResponse,
    ErrorResponse,
)


class TestAnalyticsSchemas:
    """Tests simples para esquemas de analytics."""

    def test_session_create_valid(self):
        """Test SessionCreate con datos válidos."""
        session = SessionCreate(
            session_id="test-session-123",
            email="test@example.com",
            user_type="recruiter",
            company="Test Corp",
            role="HR Manager"
        )
        assert session.session_id == "test-session-123"
        assert session.email == "test@example.com"
        assert session.user_type == "recruiter"

    def test_session_create_minimal(self):
        """Test SessionCreate con datos mínimos."""
        session = SessionCreate(session_id="minimal-session")
        assert session.session_id == "minimal-session"
        assert session.email is None
        assert session.user_type is None

    def test_session_create_invalid_user_type(self):
        """Test SessionCreate con user_type inválido."""
        with pytest.raises(Exception):
            SessionCreate(session_id="invalid-type", user_type="invalid")

    def test_session_update_valid(self):
        """Test SessionUpdate con datos válidos."""
        update = SessionUpdate(
            email="updated@example.com",
            user_type="client",
            data_captured=True
        )
        assert update.email == "updated@example.com"
        assert update.user_type == "client"
        assert update.data_captured is True

    def test_session_response_valid(self):
        """Test SessionResponse con datos válidos."""
        response = SessionResponse(
            session_id="resp-session-123",
            email="resp@example.com",
            user_type="curious",
            company="Resp Co",
            role="User",
            created_at=datetime.now(),
            last_activity=datetime.now(),
            total_messages=5,
            engagement_score=0.75,
            data_captured=True,
            gdpr_consent_given=True
        )
        assert response.session_id == "resp-session-123"
        assert response.total_messages == 5

    def test_data_capture_request_valid(self):
        """Test DataCaptureRequest con datos válidos."""
        request = DataCaptureRequest(
            session_id="capture-session-123",
            email="capture@example.com",
            user_type="recruiter",
            company="Capture Inc",
            role="Recruiter"
        )
        assert request.session_id == "capture-session-123"
        assert request.email == "capture@example.com"

    def test_data_capture_request_invalid_user_type(self):
        """Test DataCaptureRequest con user_type inválido."""
        with pytest.raises(Exception):
            DataCaptureRequest(
                session_id="invalid-capture",
                email="a@b.com",
                user_type="invalid",
                company="X",
                role="Y"
            )

    def test_gdpr_consent_request_valid(self):
        """Test GDPRConsentRequest con datos válidos."""
        request = GDPRConsentRequest(
            session_id="test-session-123",
            consent_types=["analytics", "marketing"]
        )
        assert request.session_id == "test-session-123"
        assert "analytics" in request.consent_types

    def test_gdpr_data_request_valid(self):
        """Test GDPRDataRequest con datos válidos."""
        request = GDPRDataRequest(
            session_id="test-session-123"
        )
        assert request.session_id == "test-session-123"

    def test_analytics_metrics_valid(self):
        """Test AnalyticsMetrics con datos válidos."""
        metrics = AnalyticsMetrics(
            total_sessions=100,
            total_messages=500,
            leads_captured=20,
            recruiter_count=10,
            client_count=5,
            curious_count=5,
            avg_engagement_score=0.75,
            data_capture_rate=0.5,
            gdpr_compliance_rate=0.9
        )
        assert metrics.total_sessions == 100
        assert metrics.leads_captured == 20

    def test_daily_analytics_response_valid(self):
        """Test DailyAnalyticsResponse con datos válidos."""
        response = DailyAnalyticsResponse(
            date=date.today(),
            total_sessions=10,
            total_messages=50,
            leads_captured=2,
            recruiter_count=1,
            client_count=1,
            curious_count=0,
            avg_engagement_score=0.8
        )
        assert response.total_sessions == 10
        assert response.leads_captured == 2

    def test_success_response_valid(self):
        """Test SuccessResponse con datos válidos."""
        response = SuccessResponse(
            success=True,
            message="Operation successful"
        )
        assert response.success is True
        assert response.message == "Operation successful"

    def test_error_response_valid(self):
        """Test ErrorResponse con datos válidos."""
        response = ErrorResponse(
            error="Something went wrong",
            message="Something went wrong",
            details={"code": 500, "info": "Internal error"}
        )
        assert response.error == "Something went wrong"
        assert response.message == "Something went wrong"
        assert response.details["code"] == 500

    def test_session_create_field_types(self):
        """Test tipos de campos en SessionCreate."""
        session = SessionCreate(session_id="test", email="test@example.com")
        assert isinstance(session.session_id, str)
        assert isinstance(session.email, str)

    def test_session_update_field_types(self):
        """Test tipos de campos en SessionUpdate."""
        update = SessionUpdate(email="test@example.com", data_captured=True)
        assert isinstance(update.email, str)
        assert isinstance(update.data_captured, bool)

    def test_analytics_metrics_field_types(self):
        """Test tipos de campos en AnalyticsMetrics."""
        metrics = AnalyticsMetrics(
            total_sessions=100,
            total_messages=500,
            leads_captured=20,
            recruiter_count=10,
            client_count=5,
            curious_count=5,
            avg_engagement_score=0.75,
            data_capture_rate=0.5,
            gdpr_compliance_rate=0.9
        )
        assert isinstance(metrics.total_sessions, int)
        assert isinstance(metrics.avg_engagement_score, float)

    def test_schema_serialization(self):
        """Test serialización de esquemas."""
        session = SessionCreate(session_id="test", email="test@example.com")
        json_data = session.model_dump_json()
        assert json_data is not None
        assert "test" in json_data

    def test_schema_deserialization(self):
        """Test deserialización de esquemas."""
        data = {
            "session_id": "test",
            "email": "test@example.com",
            "user_type": "recruiter"
        }
        session = SessionCreate(**data)
        assert session.session_id == "test"
        assert session.email == "test@example.com"

    def test_optional_fields(self):
        """Test campos opcionales en esquemas."""
        session = SessionCreate(session_id="test")
        assert session.email is None
        assert session.user_type is None
        assert session.company is None
        assert session.role is None

    def test_required_fields(self):
        """Test campos requeridos en esquemas."""
        # SessionCreate requiere session_id
        with pytest.raises(Exception):
            SessionCreate()

        # GDPRDataRequest requiere session_id
        with pytest.raises(Exception):
            GDPRDataRequest()

    def test_validation_constraints(self):
        """Test constraints de validación."""
        # Engagement score debe estar entre 0 y 1
        with pytest.raises(Exception):
            SessionResponse(
                session_id="test",
                created_at=datetime.now(),
                last_activity=datetime.now(),
                engagement_score=1.5
            )

    def test_list_fields(self):
        """Test campos de tipo lista."""
        request = GDPRConsentRequest(
            session_id="test",
            consent_types=["analytics", "marketing"]
        )
        assert isinstance(request.consent_types, list)
        assert len(request.consent_types) == 2

    def test_dict_fields(self):
        """Test campos de tipo diccionario."""
        response = ErrorResponse(
            error="Error",
            message="Error",
            details={"code": 500, "info": "Internal error"}
        )
        assert isinstance(response.details, dict)
        assert response.details["code"] == 500