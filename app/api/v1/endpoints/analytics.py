"""
Endpoints de analytics y GDPR para captura de datos y compliance.
Maneja la captura de leads, consentimientos GDPR y métricas.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.auth_real import get_frontend_dependency
from app.core.config import settings
from app.schemas.analytics import (
    AnalyticsConfigResponse,
    AnalyticsMetrics,
    DailyAnalyticsResponse,
    DataCaptureRequest,
    DataCaptureResponse,
    ErrorResponse,
    FlowActionRequest,
    FlowActionResponse,
    FlowStateResponse,
    GDPRConsentRequest,
    GDPRConsentResponse,
    GDPRDataRequest,
    GDPRDataResponse,
    GDPRExportResponse,
    SuccessResponse,
)
from app.services.analytics_service import analytics_service
from app.services.flow_controller import ActionType, flow_controller
from app.services.gdpr_service import gdpr_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar Rate Limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# ENDPOINTS DE CAPTURA DE DATOS
# ============================================================================


@router.post(
    "/capture-data", response_model=DataCaptureResponse, status_code=status.HTTP_200_OK
)
@limiter.limit("10/minute")  # Límite más estricto para captura de datos
async def capture_user_data(
    request: Request,
    data_request: DataCaptureRequest,
    _: bool = Depends(get_frontend_dependency()),
) -> DataCaptureResponse:
    """
    Capturar datos del usuario (email, tipo de usuario, empresa, rol).

    Args:
        request: Starlette Request (para rate limiting)
        data_request: DataCaptureRequest con los datos del usuario

    Returns:
        DataCaptureResponse con el resultado de la captura
    """
    try:
        logger.info(
            f"Captura de datos solicitada para sesión: {data_request.session_id}"
        )

        # Procesar captura de datos usando flow controller
        success, next_state, data = await flow_controller.process_data_capture(
            session_id=data_request.session_id,
            email=data_request.email,
            user_type=data_request.user_type,
            company=data_request.company,
            role=data_request.role,
        )

        if success:
            return DataCaptureResponse(
                success=True,
                message="Datos capturados exitosamente",
                session_id=data_request.session_id,
                data_captured=True,
                next_action=next_state.value,
            )
        else:
            return DataCaptureResponse(
                success=False,
                message="Error capturando datos del usuario",
                session_id=data_request.session_id,
                data_captured=False,
                next_action="retry",
            )

    except Exception as e:
        logger.error(
            f"Error en captura de datos para sesión {data_request.session_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno capturando datos del usuario",
        )


# ============================================================================
# ENDPOINTS GDPR
# ============================================================================


@router.post(
    "/gdpr/consent", response_model=GDPRConsentResponse, status_code=status.HTTP_200_OK
)
@limiter.limit("5/minute")  # Límite muy estricto para consentimientos
async def record_gdpr_consent(
    request: Request,
    consent_request: GDPRConsentRequest,
    _: bool = Depends(get_frontend_dependency()),
) -> GDPRConsentResponse:
    """
    Registrar consentimiento GDPR del usuario.

    Args:
        request: Starlette Request (para rate limiting)
        consent_request: GDPRConsentRequest con el consentimiento

    Returns:
        GDPRConsentResponse con el resultado del registro
    """
    try:
        logger.info(
            f"Consentimiento GDPR solicitado para sesión: {consent_request.session_id}"
        )

        # Obtener IP y User Agent del request
        ip_address = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "")

        # Procesar consentimiento usando flow controller
        success, next_state, data = await flow_controller.process_gdpr_consent(
            session_id=consent_request.session_id,
            consent_types=consent_request.consent_types,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if success:
            return GDPRConsentResponse(
                success=True,
                message="Consentimiento GDPR registrado exitosamente",
                session_id=consent_request.session_id,
                consent_given=True,
                consent_types=consent_request.consent_types,
            )
        else:
            return GDPRConsentResponse(
                success=False,
                message="Error registrando consentimiento GDPR",
                session_id=consent_request.session_id,
                consent_given=False,
                consent_types=[],
            )

    except Exception as e:
        logger.error(
            f"Error registrando consentimiento GDPR para sesión {consent_request.session_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno registrando consentimiento GDPR",
        )


@router.get(
    "/gdpr/data/{session_id}",
    response_model=GDPRDataResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def get_user_data(
    request: Request, session_id: str, _: bool = Depends(get_frontend_dependency())
) -> GDPRDataResponse:
    """
    Obtener todos los datos del usuario (derecho de acceso GDPR).
    Requiere autenticación administrativa.

    Args:
        request: Starlette Request (para rate limiting)
        session_id: ID de la sesión

    Returns:
        GDPRDataResponse con los datos del usuario
    """
    try:
        logger.info(f"Solicitud de datos GDPR para sesión: {session_id}")

        # Obtener datos del usuario
        user_data = await gdpr_service.get_user_data(session_id)

        if user_data:
            return GDPRDataResponse(
                success=True,
                session_id=session_id,
                user_data=user_data,
                message="Datos del usuario obtenidos exitosamente",
            )
        else:
            return GDPRDataResponse(
                success=False,
                session_id=session_id,
                user_data=None,
                message="Sesión no encontrada",
            )

    except Exception as e:
        logger.error(f"Error obteniendo datos GDPR para sesión {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo datos del usuario",
        )


@router.delete(
    "/gdpr/data/{session_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/minute")  # Límite muy estricto para eliminación
async def delete_user_data(
    request: Request, session_id: str, _: bool = Depends(get_frontend_dependency())
) -> SuccessResponse:
    """
    Eliminar todos los datos del usuario (derecho al olvido GDPR).

    Args:
        request: Starlette Request (para rate limiting)
        session_id: ID de la sesión

    Returns:
        SuccessResponse con el resultado de la eliminación
    """
    try:
        logger.info(f"Solicitud de eliminación GDPR para sesión: {session_id}")

        # Eliminar datos del usuario
        success = await gdpr_service.delete_user_data(session_id)

        if success:
            return SuccessResponse(message="Datos del usuario eliminados exitosamente")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando datos GDPR para sesión {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno eliminando datos del usuario",
        )


@router.get(
    "/gdpr/export/{session_id}",
    response_model=GDPRExportResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/minute")  # Límite muy estricto para exportación
async def export_user_data(
    request: Request, session_id: str, _: bool = Depends(get_frontend_dependency())
) -> GDPRExportResponse:
    """
    Exportar datos del usuario en formato JSON (derecho de portabilidad GDPR).

    Args:
        request: Starlette Request (para rate limiting)
        session_id: ID de la sesión

    Returns:
        GDPRExportResponse con los datos exportados
    """
    try:
        logger.info(f"Solicitud de exportación GDPR para sesión: {session_id}")

        # Exportar datos del usuario
        export_data = await gdpr_service.export_user_data(session_id)

        if export_data:
            return GDPRExportResponse(
                success=True,
                session_id=session_id,
                export_data=export_data,
                message="Datos del usuario exportados exitosamente",
            )
        else:
            return GDPRExportResponse(
                success=False,
                session_id=session_id,
                export_data=None,
                message="Sesión no encontrada",
            )

    except Exception as e:
        logger.error(f"Error exportando datos GDPR para sesión {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno exportando datos del usuario",
        )


# ============================================================================
# ENDPOINTS DE FLUJO
# ============================================================================


@router.get(
    "/flow/state/{session_id}",
    response_model=FlowStateResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("20/minute")
async def get_flow_state(request: Request, session_id: str) -> FlowStateResponse:
    """
    Obtener el estado actual del flujo para una sesión.

    Args:
        request: Starlette Request (para rate limiting)
        session_id: ID de la sesión

    Returns:
        FlowStateResponse con el estado del flujo
    """
    try:
        logger.info(f"Solicitud de estado de flujo para sesión: {session_id}")

        # Obtener estado del flujo
        flow_state = await flow_controller.get_flow_state(session_id)

        if flow_state:
            return FlowStateResponse(**flow_state)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado de flujo para sesión {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo estado del flujo",
        )


@router.post(
    "/flow/action", response_model=FlowActionResponse, status_code=status.HTTP_200_OK
)
@limiter.limit("10/minute")
async def handle_flow_action(
    request: Request, action_request: FlowActionRequest
) -> FlowActionResponse:
    """
    Manejar una acción específica del flujo.

    Args:
        request: Starlette Request (para rate limiting)
        action_request: FlowActionRequest con la acción a realizar

    Returns:
        FlowActionResponse con el resultado de la acción
    """
    try:
        logger.info(
            f"Acción de flujo solicitada para sesión: {action_request.session_id}"
        )

        # Convertir string a ActionType enum
        try:
            action_type = ActionType(action_request.action_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de acción inválido: {action_request.action_type}",
            )

        # Manejar acción del flujo
        result = await flow_controller.handle_flow_transition(
            session_id=action_request.session_id,
            action_type=action_type,
            additional_data=action_request.additional_data,
        )

        return FlowActionResponse(
            success=result.get("success", True),
            session_id=action_request.session_id,
            action_type=action_request.action_type,
            new_state=result.get("new_state"),
            data=result.get("data"),
            message=result.get("message", "Acción procesada exitosamente"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error manejando acción de flujo para sesión {action_request.session_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno manejando acción del flujo",
        )


@router.get(
    "/flow/config",
    response_model=AnalyticsConfigResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def get_flow_configuration(request: Request) -> AnalyticsConfigResponse:
    """
    Obtener configuración del flujo de analytics.

    Args:
        request: Starlette Request (para rate limiting)

    Returns:
        AnalyticsConfigResponse con la configuración del flujo
    """
    try:
        config = flow_controller.get_flow_configuration()
        return AnalyticsConfigResponse(**config)

    except Exception as e:
        logger.error(f"Error obteniendo configuración del flujo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo configuración del flujo",
        )


# ============================================================================
# ENDPOINTS DE MÉTRICAS (ADMIN)
# ============================================================================


@router.get("/metrics", response_model=AnalyticsMetrics, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_overall_metrics(
    request: Request, _: bool = Depends(get_frontend_dependency())
) -> AnalyticsMetrics:
    """
    Obtener métricas generales del sistema (endpoint admin).
    Requiere autenticación administrativa.

    Args:
        request: Starlette Request (para rate limiting)

    Returns:
        AnalyticsMetrics con las métricas generales
    """
    try:
        logger.info("Solicitud de métricas generales")

        # Obtener métricas generales
        metrics = await analytics_service.get_overall_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Error obteniendo métricas generales: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo métricas generales",
        )


@router.get(
    "/metrics/daily",
    response_model=List[DailyAnalyticsResponse],
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
async def get_daily_metrics(
    request: Request, days: int = 30, _: bool = Depends(get_frontend_dependency())
) -> List[DailyAnalyticsResponse]:
    """
    Obtener métricas diarias de los últimos N días (endpoint admin).
    Requiere autenticación administrativa.

    Args:
        request: Starlette Request (para rate limiting)
        days: Número de días a obtener (máximo 90)

    Returns:
        List[DailyAnalyticsResponse] con las métricas diarias
    """
    try:
        # Limitar días a un máximo razonable
        days = min(days, 90)

        logger.info(f"Solicitud de métricas diarias para {days} días")

        # Obtener métricas diarias
        daily_metrics = await analytics_service.get_daily_metrics(days=days)

        return [DailyAnalyticsResponse(**metric) for metric in daily_metrics]

    except Exception as e:
        logger.error(f"Error obteniendo métricas diarias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo métricas diarias",
        )


@router.post(
    "/metrics/aggregate", response_model=SuccessResponse, status_code=status.HTTP_200_OK
)
@limiter.limit("5/minute")  # Límite estricto para agregación
async def aggregate_daily_metrics(request: Request) -> SuccessResponse:
    """
    Agregar métricas diarias para el día actual (endpoint admin).

    Args:
        request: Starlette Request (para rate limiting)

    Returns:
        SuccessResponse con el resultado de la agregación
    """
    try:
        logger.info("Solicitud de agregación de métricas diarias")

        # Agregar métricas diarias
        success = await analytics_service.aggregate_daily_metrics()

        if success:
            return SuccessResponse(message="Métricas diarias agregadas exitosamente")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error agregando métricas diarias",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error agregando métricas diarias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno agregando métricas diarias",
        )


# ============================================================================
# ENDPOINTS DE UTILIDAD
# ============================================================================


@router.get("/health", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def analytics_health_check() -> SuccessResponse:
    """
    Health check específico para el módulo de analytics.

    Returns:
        SuccessResponse con el estado del módulo
    """
    try:
        # Verificar que los servicios están inicializados
        if analytics_service and gdpr_service and flow_controller:
            return SuccessResponse(
                message="Módulo de analytics funcionando correctamente"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicios de analytics no inicializados",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en health check de analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error interno en health check de analytics",
        )
