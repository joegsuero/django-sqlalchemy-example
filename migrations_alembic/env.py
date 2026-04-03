"""
migrations_alembic/env.py

Alembic environment: connects migration runner to Django settings
and SQLAlchemy models.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ══ Bootstrap Django ════════════════════════════════════════════════════════════
# Ensure the project root is on sys.path so Django settings can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

# ══ Import all model metadata ═══════════════════════════════════════════════════
# IMPORTANT: Import every Base/metadata that contains models you want
# Alembic to manage. If you add a new app with SA models, import it here.
from blog.models import metadata as blog_metadata  # noqa: E402

# Combine all metadata objects into one target for Alembic
# If you have multiple apps, combine them:
# from myapp.models import metadata as myapp_metadata
# target_metadata = [blog_metadata, myapp_metadata]
target_metadata = blog_metadata

# ══ Alembic config ═══════════════════════════════════════════════════════════════
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    """Get DB URL from Django settings (single source of truth)."""
    from sa_core.database import get_sync_url
    return get_sync_url()


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generates SQL without a live connection).
    Useful for generating SQL scripts to review before applying.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,          # Detect column type changes
        compare_server_default=True, # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (applies directly to the database).
    """
    from sqlalchemy import create_engine
    connectable = create_engine(get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
