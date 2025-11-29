"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Create engine
if settings.database_url.startswith("sqlite"):
    # SQLite specific configuration
    # Use pool_pre_ping to check connections before using them
    # Use NullPool to avoid connection pooling issues with SQLite
    from sqlalchemy.pool import NullPool
    engine = create_engine(
        settings.database_url,
        connect_args={
            "check_same_thread": False,  # Needed for SQLite with FastAPI
            "timeout": 20.0  # Wait up to 20 seconds for database lock
        },
        poolclass=NullPool,  # Don't pool connections for SQLite
        echo=settings.debug  # Set to True for SQL query logging in debug mode
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Verify connections before using them
        pool_size=5,  # Connection pool size
        max_overflow=10,  # Maximum overflow connections
        echo=settings.debug  # Set to True for SQL query logging in debug mode
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """
    Dependency function to get database session.
    Use this in FastAPI route dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

