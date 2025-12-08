"""
Script to run the daily scraper job.
Can be used by cron or run manually.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.daily_scraper_job import run_job_sync
from core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point for the job."""
    mode = "incremental"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode not in ["incremental", "full"]:
            print(f"Invalid mode: {mode}. Use 'incremental' or 'full'")
            sys.exit(1)
    
    results = run_job_sync(mode=mode)
    
    if results['success']:
        logger.info("Job completed successfully")
        sys.exit(0)
    else:
        logger.error(f"Job failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

