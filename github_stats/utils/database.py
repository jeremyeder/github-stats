"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..models.base import Base
from .config import get_settings


def get_db_engine() -> Engine:
    """Create and return database engine."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=settings.log_level == "DEBUG",
    )


def get_db_session() -> sessionmaker[Session]:
    """Get database session factory."""
    engine = get_db_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope for database operations."""
    SessionLocal = get_db_session()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    engine = get_db_engine()
    Base.metadata.create_all(bind=engine)