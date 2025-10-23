"""
Configuración de Alembic para migraciones de base de datos.
Maneja la conexión a Cloud SQL PostgreSQL y configuración de migraciones.
"""
import logging
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Cargar variables de entorno desde .env
load_dotenv()

from app.core.config import settings
from app.core.secrets import get_database_password

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.models.analytics import Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url() -> str:
    """
    Construye la URL de conexión a la base de datos.
    Maneja tanto Cloud Run (Cloud SQL) como desarrollo local.
    """
    try:
        # Intentar obtener password desde Secret Manager o variables de entorno
        password = get_database_password()

        if settings.CLOUD_SQL_CONNECTION_NAME:
            # Cloud Run - usar Cloud SQL Proxy
            logger.info("Configurando conexión para Cloud Run")
            return f"postgresql://{settings.CLOUD_SQL_USER}:{password}@/{settings.CLOUD_SQL_DB}?host=/cloudsql/{settings.CLOUD_SQL_CONNECTION_NAME}"
        else:
            # Desarrollo local
            logger.info("Configurando conexión para desarrollo local")
            return f"postgresql://{settings.CLOUD_SQL_USER}:{password}@{settings.CLOUD_SQL_HOST}:{settings.CLOUD_SQL_PORT}/{settings.CLOUD_SQL_DB}"

    except Exception as e:
        logger.error(f"Error construyendo URL de base de datos: {e}")
        raise


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Configurar la URL de conexión
    database_url = get_database_url()

    # Configurar el engine con parámetros optimizados
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Usar NullPool para migraciones
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
