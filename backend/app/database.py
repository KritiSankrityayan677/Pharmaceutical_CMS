"""
SQLAlchemy engine + session. Kept minimal on purpose - swap the URL
in .env to move between SQLite / Postgres / MySQL without code changes.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# SQLite needs check_same_thread=False for FastAPI's thread pool.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency - yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
