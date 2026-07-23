"""
Alembic environment configuration.

Configures Alembic to run against Freight's database using the same
connection URL and ORM metadata used by the application itself, so
migrations always match the current SQLAlchemy models in
`freight/models/`.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from freight.core.config import settings
from freight.db.base import Base

# Import every model so its table is registered on Base.metadata before
# Alembic compares it against the database.
import freight.models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Freight's own settings are the single source of truth for the
# database URL; never rely on a hardcoded value in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.POSTGRES_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine, so a
    database connection is not required to generate SQL scripts.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the migration
    context so migrations execute directly against the database.
    """

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()