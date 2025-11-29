"""
Initialize database and create tables.
"""

from database.connection import Base, engine
from models import Opportunity


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()

