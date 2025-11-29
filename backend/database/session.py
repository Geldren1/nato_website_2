"""
Database session utilities.
"""

from database.connection import SessionLocal


def get_db_session():
    """
    Get a database session.
    Returns a session that should be closed after use.
    """
    return SessionLocal()

