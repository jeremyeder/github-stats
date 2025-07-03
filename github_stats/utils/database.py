"""Database connection and session management."""

from collections.abc import Generator
from contextlib import contextmanager

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
    session_local = get_db_session()
    db = session_local()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_has_data() -> dict[str, int]:
    """Check if database has existing data.

    Returns:
        Dictionary with counts of each data type
    """
    from ..models.interactions import Interaction, Organization, Repository

    counts = {"organizations": 0, "repositories": 0, "interactions": 0}

    try:
        with get_db() as db:
            counts["organizations"] = db.query(Organization).count()
            counts["repositories"] = db.query(Repository).count()
            counts["interactions"] = db.query(Interaction).count()
    except Exception:
        # Database doesn't exist yet or has no tables
        pass

    return counts


def init_db() -> None:
    """Initialize database tables."""
    engine = get_db_engine()
    Base.metadata.create_all(bind=engine)
