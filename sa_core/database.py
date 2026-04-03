"""
sa_core/database.py

Central SQLAlchemy engine and session management.
Supports sync and async, SQLite and PostgreSQL.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from django.conf import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# URL builders
# ═══════════════════════════════════════════════════════════════════════════════

_SYNC_DRIVERS = {
    "django.db.backends.postgresql": "postgresql+psycopg2",
    "django.db.backends.mysql": "mysql+pymysql",
    "django.db.backends.sqlite3": "sqlite",
}

_ASYNC_DRIVERS = {
    "django.db.backends.postgresql": "postgresql+asyncpg",
    "django.db.backends.mysql": "mysql+aiomysql",
    "django.db.backends.sqlite3": "sqlite+aiosqlite",
}


def _build_url(driver_map: dict) -> str:
    db = settings.DATABASES["default"]
    backend = driver_map.get(db["ENGINE"], "sqlite")

    if backend == "sqlite":
        path = str(db["NAME"])
        return f"sqlite:///{path}"
    
    if backend == "sqlite+aiosqlite":
        path = str(db["NAME"])
        return f"sqlite+aiosqlite:///{path}"

    credentials = db.get("USER", "")
    if db.get("PASSWORD"):
        credentials += f":{db['PASSWORD']}"

    host = db.get("HOST", "localhost")
    port = f":{db['PORT']}" if db.get("PORT") else ""

    return f"{backend}://{credentials}@{host}{port}/{db['NAME']}"


def get_sync_url() -> str:
    return _build_url(_SYNC_DRIVERS)


def get_async_url() -> str:
    return _build_url(_ASYNC_DRIVERS)


# ═══════════════════════════════════════════════════════════════════════════════
# Engine factory
# ═══════════════════════════════════════════════════════════════════════════════

def _engine_kwargs(url: str, is_async: bool = False) -> dict:
    """Build engine kwargs appropriate for the database backend."""
    is_sqlite = "sqlite" in url
    kwargs: dict = {"echo": False}  # Never auto-echo; use logging config instead

    if is_sqlite:
        kwargs["poolclass"] = StaticPool
        if not is_async:
            kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            {
                "pool_size": getattr(settings, "SA_POOL_SIZE", 10),
                "max_overflow": getattr(settings, "SA_MAX_OVERFLOW", 20),
                "pool_timeout": getattr(settings, "SA_POOL_TIMEOUT", 30),
                "pool_recycle": getattr(settings, "SA_POOL_RECYCLE", 1800),
                "pool_pre_ping": True,
            }
        )

    return kwargs


def create_sync_engine() -> Engine:
    url = get_sync_url()
    return create_engine(url, **_engine_kwargs(url))


def create_async_engine_instance() -> AsyncEngine:
    url = get_async_url()
    return create_async_engine(url, **_engine_kwargs(url, is_async=True))


# ═══════════════════════════════════════════════════════════════════════════════
# Global instances (created once at import)
# ═══════════════════════════════════════════════════════════════════════════════

engine: Engine = create_sync_engine()
async_engine: AsyncEngine = create_async_engine_instance()

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Context managers
# ═══════════════════════════════════════════════════════════════════════════════

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Sync context manager. Use in regular Django views and management commands.

    Usage:
        with get_session() as session:
            articles = session.execute(select(Article)).scalars().all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager. Use in Django async views.

    Usage:
        async with get_async_session() as session:
            result = await session.execute(select(Article))
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════════════════════════

def check_connection() -> bool:
    """Verify the database connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        return False


# Backwards compatibility
def get_database_url() -> str:
    """Build SQLAlchemy connection string from Django settings."""
    return get_sync_url()


def get_db_session() -> Session:
    """Get a new SQLAlchemy session. Caller is responsible for closing."""
    return SessionLocal()

