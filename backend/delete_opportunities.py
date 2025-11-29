"""
Script to delete all opportunities from the database.
"""

from database.session import get_db_session
from models import Opportunity
from core.logging import get_logger

logger = get_logger(__name__)


def delete_all_opportunities():
    """Delete all opportunities from the database."""
    db = get_db_session()
    try:
        count = db.query(Opportunity).count()
        logger.info(f"Found {count} opportunities in database")
        
        if count > 0:
            db.query(Opportunity).delete()
            db.commit()
            logger.info(f"✅ Deleted {count} opportunities from database")
        else:
            logger.info("No opportunities to delete")
        
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting opportunities: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    delete_all_opportunities()

