"""
Core database module for SQLAlchemy engine and session management.
This module creates the engine from Django settings and provides session management.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from django.conf import settings


def get_database_url() -> str:
    """Build SQLAlchemy connection string from Django settings."""
    db = settings.DATABASES['default']
    
    engine_map = {
        'django.db.backends.postgresql': 'postgresql+psycopg2',
        'django.db.backends.mysql': 'mysql+pymysql',
        'django.db.backends.sqlite3': 'sqlite',
    }
    backend = engine_map.get(db['ENGINE'], 'sqlite')

    if backend == 'sqlite':
        db_path = str(db['NAME'])
        if not db_path.startswith('/') and not db_path.startswith('C:'):
            from pathlib import Path
            db_path = str(Path(settings.BASE_DIR) / db_path)
        return f"sqlite:///{db_path}"

    password = db.get('PASSWORD', '')
    if password:
        password = f":{password}"
    
    host = db.get('HOST', 'localhost')
    port = db.get('PORT', '')
    if port:
        port = f":{port}"
    
    return f"{backend}://{db.get('USER', '')}{password}@{host}{port}/{db['NAME']}"


def create_engine_from_settings() -> Engine:
    """Create SQLAlchemy engine from Django settings."""
    url = get_database_url()
    
    engine_kwargs = {
        'echo': settings.DEBUG,
    }

    if 'sqlite' in url:
        engine_kwargs.update({
            'poolclass': StaticPool,
            'connect_args': {'check_same_thread': False},
        })
    else:
        engine_kwargs.update({
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 1800,
            'pool_pre_ping': True,
        })

    return create_engine(url, **engine_kwargs)


# Global engine instance
engine = create_engine_from_settings()

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for SQLAlchemy sessions.
    Provides automatic commit/rollback and cleanup.
    
    Usage:
        with get_session() as session:
            result = session.execute(select(Article))
            articles = result.scalars().all()
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


def get_db_session() -> Session:
    """
    Get a new SQLAlchemy session.
    Caller is responsible for closing the session.
    """
    return SessionLocal()
