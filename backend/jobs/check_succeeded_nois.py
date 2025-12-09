"""
Check for succeeded NOIs and mark them as inactive.

After all scrapers have run, this script checks if any NOI opportunities
have been succeeded by other opportunity types (typically IFIB, but could be
RFP, RFI, RFIP, etc.) with the same suffix in their opportunity code.

For example:
- NOI-ACT-SACT-26-16 is succeeded by IFIB-ACT-SACT-26-16
- Both have the same suffix: "ACT-SACT-26-16"

When an NOI is succeeded, it is marked as inactive (is_active = False)
so it no longer appears on the website, but remains in the database.
"""

from datetime import datetime
from typing import Dict, List, Tuple
from database.connection import SessionLocal
from models import Opportunity
from core.logging import get_logger

logger = get_logger(__name__)


def extract_suffix(opportunity_code: str) -> str:
    """
    Extract the suffix from an opportunity code.
    
    The suffix is everything after the first hyphen.
    For example:
    - "NOI-ACT-SACT-26-16" -> "ACT-SACT-26-16"
    - "IFIB-ACT-SACT-26-16" -> "ACT-SACT-26-16"
    
    Args:
        opportunity_code: Full opportunity code (e.g., "NOI-ACT-SACT-26-16")
        
    Returns:
        Suffix string (e.g., "ACT-SACT-26-16")
    """
    if not opportunity_code:
        return ""
    
    parts = opportunity_code.split("-", 1)
    if len(parts) > 1:
        return parts[1]  # Everything after the first hyphen
    return ""


def check_succeeded_nois() -> Dict[str, any]:
    """
    Check for NOI opportunities that have been succeeded by other opportunity types.
    
    Returns:
        Dictionary with results:
        - checked_count: Number of NOIs checked
        - succeeded_count: Number of NOIs marked as succeeded
        - succeeded_nois: List of succeeded NOI codes
        - timestamp: When the check completed
        - success: Whether the check completed successfully
    """
    start_time = datetime.utcnow()
    logger.info("=" * 80)
    logger.info("Starting succeeded NOI check", event_type="noi_check_start")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Get all active NOI opportunities
        active_nois = db.query(Opportunity).filter(
            Opportunity.opportunity_type == "NOI",
            Opportunity.is_active == True
        ).all()
        
        logger.info(f"Found {len(active_nois)} active NOI opportunities to check")
        
        succeeded_count = 0
        succeeded_nois = []
        
        for noi in active_nois:
            if not noi.opportunity_code:
                logger.warning(f"NOI with ID {noi.id} has no opportunity_code, skipping")
                continue
            
            # Extract suffix from NOI code
            suffix = extract_suffix(noi.opportunity_code)
            
            if not suffix:
                logger.warning(f"NOI {noi.opportunity_code} has no suffix, skipping")
                continue
            
            # Find active non-NOI opportunities with the same suffix
            succeeded_by = db.query(Opportunity).filter(
                Opportunity.opportunity_type != "NOI",
                Opportunity.is_active == True,
                Opportunity.opportunity_code.like(f"%-{suffix}")
            ).all()
            
            if succeeded_by:
                # This NOI has been succeeded
                succeeded_by_codes = [opp.opportunity_code for opp in succeeded_by]
                logger.info(
                    f"NOI {noi.opportunity_code} succeeded by: {', '.join(succeeded_by_codes)}"
                )
                
                # Mark NOI as inactive
                noi.is_active = False
                succeeded_count += 1
                succeeded_nois.append(noi.opportunity_code)
        
        # Commit all changes
        if succeeded_count > 0:
            db.commit()
            logger.info(f"Marked {succeeded_count} NOI(s) as inactive")
        else:
            logger.info("No succeeded NOIs found")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        results = {
            'checked_count': len(active_nois),
            'succeeded_count': succeeded_count,
            'succeeded_nois': succeeded_nois,
            'timestamp': end_time,
            'success': True,
            'duration_seconds': duration,
            'start_time': start_time,
            'end_time': end_time
        }
        
        logger.info("=" * 80)
        logger.info(
            f"Succeeded NOI check completed",
            event_type="noi_check_complete",
            checked_count=len(active_nois),
            succeeded_count=succeeded_count,
            duration_seconds=duration
        )
        logger.info(f"  Checked: {len(active_nois)} NOIs")
        logger.info(f"  Succeeded: {succeeded_count} NOIs")
        if succeeded_nois:
            logger.info(f"  Succeeded NOI codes: {', '.join(succeeded_nois)}")
        logger.info(f"  Duration: {duration:.2f} seconds")
        logger.info("=" * 80)
        
        return results
        
    except Exception as e:
        db.rollback()
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        error_msg = str(e)
        logger.error("=" * 80)
        logger.error(
            f"Succeeded NOI check failed: {error_msg}",
            event_type="noi_check_error",
            error=error_msg,
            duration_seconds=duration
        )
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        
        return {
            'checked_count': 0,
            'succeeded_count': 0,
            'succeeded_nois': [],
            'timestamp': end_time,
            'success': False,
            'error': error_msg,
            'duration_seconds': duration,
            'start_time': start_time,
            'end_time': end_time
        }
        
    finally:
        db.close()


if __name__ == "__main__":
    """Run the check directly from command line."""
    import sys
    
    results = check_succeeded_nois()
    
    if results['success']:
        print(f"\n✅ Succeeded NOI check completed")
        print(f"   Checked: {results['checked_count']} NOIs")
        print(f"   Succeeded: {results['succeeded_count']} NOIs")
        if results['succeeded_nois']:
            print(f"   Succeeded NOI codes: {', '.join(results['succeeded_nois'])}")
        print(f"   Duration: {results['duration_seconds']:.2f}s")
        sys.exit(0)
    else:
        print(f"\n❌ Succeeded NOI check failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)

