"""
Configuración de Alembic para migraciones async con PostgreSQL.

¿Qué es Alembic?
    Es el sistema de migraciones de SQLAlchemy.
    Java equivalent: Flyway o Liquibase.

    Una migración es un archivo Python que describe UN cambio en la BD:
    "agregar columna X", "crear tabla Y", "renombrar columna Z".
    Alembic los aplica en orden y lleva un registro de cuáles ya se ejecutaron.

¿Por qué no usar create_all()?
    create_all() crea las tablas una vez, pero no sabe cómo MODIFICARLAS después.
    Si agregas una columna a un modelo, create_all() no hace nada en la BD existente.
    Alembic sí detecta el cambio y genera el ALTER TABLE correspondiente.

Comandos clave:
    uv run alembic revision --autogenerate -m "descripcion"  # generar migración
    uv run alembic upgrade head                               # aplicar todas
    uv run alembic downgrade -1                               # revertir última
    uv run alembic history                                    # ver historial
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Lee la configuración del alembic.ini
alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# ── IMPORTANTE: importar TODOS los modelos aquí ──────────────────────────────
# Alembic necesita conocer los modelos para detectar cambios automáticamente.
# Cada vez que agregues un nuevo modelo SQLAlchemy, impórtalo aquí.
from app.core.database import Base          # la Base de la que heredan los modelos
from app.core.config import settings        # para leer DATABASE_URL del .env
import app.infrastructure.models.user      # noqa: F401 — registra User en Base.metadata

# Le decimos a Alembic qué tablas existen para poder comparar contra la BD
target_metadata = Base.metadata

# Sobreescribir la URL con la del .env (tiene prioridad sobre alembic.ini)
alembic_config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Modo offline: genera el SQL sin conectarse a la BD.
    Útil para revisar qué SQL se va a ejecutar antes de aplicarlo.
    Comando: uv run alembic upgrade head --sql
    """
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Modo online con async: se conecta a PostgreSQL y aplica las migraciones.
    Usamos async_engine porque todo nuestro stack es async.
    """
    connectable = async_engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
