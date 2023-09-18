"""Module containing the Alembic environment configuration for Kiroshi."""

from logging.config import fileConfig

from sqlalchemy import create_engine

from alembic import context
from starbug.models.database import Base
from starbug.settings import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This function configures the Alembic context for 'offline' mode, which means that the migrations are run without a
    live database connection. Instead, the database URL is passed as a string to the context.configure() method.
    """
    url = settings.database_dsn
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This function configures the Alembic context for 'online' mode, which means that the migrations are run with a live
    database connection.
    """
    connectable = create_engine(settings.database_dsn)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
