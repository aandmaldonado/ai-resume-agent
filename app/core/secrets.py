"""
Gestión de secretos usando Google Cloud Secret Manager.
Fallback a variables de entorno para desarrollo local.
"""

import logging
from typing import Optional

from google.api_core import exceptions as gcp_exceptions
from google.cloud import secretmanager

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecretManager:
    """Cliente para Google Cloud Secret Manager con fallback a variables de entorno"""

    def __init__(self):
        self.client = None
        try:
            self.client = secretmanager.SecretManagerServiceClient()
            logger.info("✓ Secret Manager client inicializado")
        except Exception as e:
            logger.warning(
                f"⚠️ Secret Manager no disponible: {e}. Usando variables de entorno."
            )

    def get_secret(self, secret_name: str, default_value: Optional[str] = None) -> str:
        """
        Obtiene un secreto de Secret Manager o variable de entorno.

        Args:
            secret_name: Nombre del secreto en Secret Manager
            default_value: Valor por defecto si no se encuentra

        Returns:
            Valor del secreto o variable de entorno

        Raises:
            ValueError: Si no se encuentra el secreto y no hay valor por defecto
        """
        # Primero intentar con Secret Manager
        if self.client:
            try:
                secret_path = f"projects/{settings.GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
                response = self.client.access_secret_version(
                    request={"name": secret_path}
                )
                secret_value = response.payload.data.decode("UTF-8")
                logger.debug(f"✓ Secreto '{secret_name}' obtenido de Secret Manager")
                return secret_value
            except gcp_exceptions.NotFound:
                logger.warning(
                    f"⚠️ Secreto '{secret_name}' no encontrado en Secret Manager"
                )
            except Exception as e:
                logger.warning(f"⚠️ Error accediendo a Secret Manager: {e}")

        # Fallback a variable de entorno
        import os

        env_var_name = secret_name.upper().replace("-", "_")
        env_value = os.getenv(env_var_name)

        if env_value:
            logger.debug(f"✓ Usando variable de entorno '{env_var_name}'")
            return env_value

        # Último recurso: valor por defecto
        if default_value is not None:
            logger.warning(f"⚠️ Usando valor por defecto para '{secret_name}'")
            return default_value

        raise ValueError(
            f"No se pudo obtener el secreto '{secret_name}' de ninguna fuente"
        )


# Instancia global
secret_manager = SecretManager()


def get_database_password() -> str:
    """Obtiene la contraseña de la base de datos"""
    return secret_manager.get_secret("CLOUD_SQL_PASSWORD")


def get_gcp_project_id() -> str:
    """Obtiene el Project ID de GCP"""
    return secret_manager.get_secret("GCP_PROJECT_ID", default_value="ai-resume-agent")
