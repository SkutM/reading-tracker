from logging.config import fileConfig
from alembic import context
import os
import sys

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

sys.path.append(os.path.join(os.getcwd(), "."))
sys.path.append(os.path.join(os.getcwd(), ".."))

from api.database import Base, engine 
from api.models import Book
from api import auth_models 

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    raise RuntimeError("Offline migrations are not supported; run alembic in online mode for Turso/libSQL.")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the app engine (Turso auth included)."""
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
