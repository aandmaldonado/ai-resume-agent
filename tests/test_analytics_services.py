#!/usr/bin/env python3
"""
Tests para verificar que los servicios de analytics funcionan correctamente.
"""
import logging
from datetime import datetime

import pytest

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_analytics_service_initialization():
    """Probar que el servicio de analytics se inicializa correctamente."""
    logger.info("🧪 Probando inicialización de AnalyticsService...")

    try:
        # Importar servicio
        from app.services.analytics_service import analytics_service

        # Verificar que el servicio existe
        assert analytics_service is not None
        logger.info("   ✅ AnalyticsService inicializado correctamente")

        logger.info("🎉 AnalyticsService funcionando correctamente!")

    except Exception as e:
        logger.error(f"❌ Error en AnalyticsService: {e}")
        raise


@pytest.mark.asyncio
async def test_gdpr_service_initialization():
    """Probar que el servicio GDPR se inicializa correctamente."""
    logger.info("🧪 Probando inicialización de GDPRService...")

    try:
        # Importar servicio
        from app.services.gdpr_service import gdpr_service

        # Verificar que el servicio existe
        assert gdpr_service is not None
        logger.info("   ✅ GDPRService inicializado correctamente")

        logger.info("🎉 GDPRService funcionando correctamente!")

    except Exception as e:
        logger.error(f"❌ Error en GDPRService: {e}")
        raise


@pytest.mark.asyncio
async def test_flow_controller_initialization():
    """Probar que el controlador de flujo se inicializa correctamente."""
    logger.info("🧪 Probando inicialización de FlowController...")

    try:
        # Importar servicio
        from app.services.flow_controller import flow_controller

        # Verificar que el servicio existe
        assert flow_controller is not None
        logger.info("   ✅ FlowController inicializado correctamente")

        # Verificar configuración del flujo
        flow_config = flow_controller.get_flow_configuration()
        assert "data_capture_after_messages" in flow_config
        assert "engagement_threshold" in flow_config
        assert "flow_states" in flow_config
        logger.info("   ✅ Configuración del flujo obtenida correctamente")

        logger.info("🎉 FlowController funcionando correctamente!")

    except Exception as e:
        logger.error(f"❌ Error en FlowController: {e}")
        raise


@pytest.mark.asyncio
async def test_analytics_patterns():
    """Probar los patrones de detección de tecnologías e intenciones."""
    logger.info("🧪 Probando patrones de analytics...")

    try:
        # Crear instancia temporal para probar métodos
        from app.services.analytics_service import AnalyticsService

        # Crear instancia sin inicializar DB
        temp_service = AnalyticsService()

        # Verificar que el servicio se creó correctamente
        assert temp_service is not None
        logger.info("   ✅ AnalyticsService creado correctamente")

        # Probar cálculo de engagement score (método que no depende de DB)
        score = temp_service._calculate_engagement_score(
            message_count=5,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        assert 0.0 <= score <= 1.0
        logger.info("   ✅ Cálculo de engagement score funcionando correctamente")

        logger.info("🎉 Patrones de analytics funcionando correctamente!")

    except Exception as e:
        logger.error(f"❌ Error en patrones de analytics: {e}")
        raise
