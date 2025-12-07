"""
Daily scraper job for ACT RFI opportunities.

This job runs the ACT RFI scraper in incremental mode and returns
detailed results about what changed.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from scraper.scraper import NATOOpportunitiesScraper
from models import Opportunity
from services.email_notification_service import get_email_notification_service
from core.logging import get_logger

logger = get_logger(__name__)


async def run_daily_scraper_job_act_rfi(mode: str = "incremental") -> Dict[str, Any]:
    """
    Run the daily scraper job to check for new and updated ACT RFI opportunities.
    
    Args:
        mode: "full" (process all) or "incremental" (reconcile first)
    
    Returns:
        Dictionary with detailed results:
        - new: List of Opportunity objects that were newly created
        - amendments: List of Opportunity objects that were amended
        - unchanged_count: Number of opportunities that were unchanged
        - removed_count: Number of opportunities removed from website
        - processed_count: Total number of opportunities processed
        - timestamp: When the job completed
        - success: Whether the job completed successfully
        - error: Error message if job failed
    """
    start_time = datetime.utcnow()
    logger.info("=" * 80)
    logger.info("Starting daily scraper job for ACT-RFI", event_type="job_start", mode=mode)
    logger.info("=" * 80)
    
    try:
        scraper = NATOOpportunitiesScraper(config_name="ACT-RFI", use_llm=True)
        results = await scraper.scrape_all(mode=mode)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Add job metadata
        results['success'] = True
        results['error'] = None
        results['duration_seconds'] = duration
        results['start_time'] = start_time
        results['end_time'] = end_time
        
        logger.info("=" * 80)
        logger.info(
            f"Daily scraper job completed successfully (ACT-RFI)",
            event_type="job_complete",
            new_count=len(results.get('new', [])),
            amendments_count=len(results.get('amendments', [])),
            duration_seconds=duration
        )
        logger.info(f"  New opportunities: {len(results.get('new', []))}")
        logger.info(f"  Amended opportunities: {len(results.get('amendments', []))}")
        logger.info(f"  Unchanged: {results.get('unchanged_count', 0)}")
        logger.info(f"  Removed from website: {results.get('removed_count', 0)}")
        logger.info(f"  Duration: {duration:.2f} seconds")
        logger.info("=" * 80)
        
        # Send email notifications if there are changes
        new_opps = results.get('new', [])
        amended_opps = results.get('amendments', [])
        
        if new_opps or amended_opps:
            logger.info("=" * 80)
            logger.info("Sending email notifications...")
            logger.info("=" * 80)
            
            try:
                email_service = get_email_notification_service()
                email_results = email_service.send_notifications_for_changes(
                    new_opportunities=new_opps,
                    amended_opportunities=amended_opps
                )
                
                results['email_notifications'] = email_results
                
                logger.info("=" * 80)
                logger.info("Email notifications complete")
                logger.info(f"  Subscribers: {email_results.get('subscriber_count', 0)}")
                logger.info(f"  Summary emails: {email_results.get('sent', 0)} sent, {email_results.get('failed', 0)} failed")
                logger.info(f"  Content: {email_results.get('new_count', 0)} new, {email_results.get('amended_count', 0)} amended opportunities")
                logger.info("=" * 80)
            except Exception as e:
                logger.error(f"Error sending email notifications: {e}")
                results['email_notifications'] = {
                    "error": str(e),
                    "sent": 0,
                    "failed": 0
                }
        else:
            logger.info("No changes detected, skipping email notifications")
            results['email_notifications'] = None
        
        return results
        
    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        error_msg = str(e)
        logger.error("=" * 80)
        logger.error(
            f"Daily scraper job failed (ACT-RFI): {error_msg}",
            event_type="job_error",
            error=error_msg,
            duration_seconds=duration
        )
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        
        return {
            'new': [],
            'amendments': [],
            'unchanged_count': 0,
            'removed_count': 0,
            'processed_count': 0,
            'timestamp': end_time,
            'success': False,
            'error': error_msg,
            'duration_seconds': duration,
            'start_time': start_time,
            'end_time': end_time
        }


def run_job_sync_act_rfi(mode: str = "incremental") -> Dict[str, Any]:
    """
    Synchronous wrapper for the async job.
    Useful for cron jobs or command-line execution.
    
    Args:
        mode: "full" (process all) or "incremental" (reconcile first)
    
    Returns:
        Dictionary with job results
    """
    return asyncio.run(run_daily_scraper_job_act_rfi(mode=mode))


if __name__ == "__main__":
    """Run the job directly from command line."""
    import sys
    
    mode = "incremental"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    results = run_job_sync_act_rfi(mode=mode)
    
    if results['success']:
        print(f"\n✅ Job completed successfully (ACT-RFI)")
        print(f"   New: {len(results['new'])}")
        print(f"   Amended: {len(results['amendments'])}")
        print(f"   Duration: {results['duration_seconds']:.2f}s")
        sys.exit(0)
    else:
        print(f"\n❌ Job failed (ACT-RFI): {results.get('error', 'Unknown error')}")
        sys.exit(1)

