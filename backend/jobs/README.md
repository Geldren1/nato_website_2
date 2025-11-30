# Automated Scraper Jobs

This directory contains scheduled jobs for automated opportunity updates.

## Daily Scraper Job

The `daily_scraper_job.py` runs the ACT IFIB scraper in incremental mode and returns detailed results about what changed.

### Usage

**Run manually:**
```bash
cd backend
python jobs/run_job.py [incremental|full]
```

Or directly:
```bash
cd backend
python -m jobs.daily_scraper_job [incremental|full]
```

**From Python code:**
```python
from jobs.daily_scraper_job import run_daily_scraper_job, run_job_sync

# Async version
results = await run_daily_scraper_job(mode="incremental")

# Sync version (for cron jobs)
results = run_job_sync(mode="incremental")
```

### Return Value

The job returns a dictionary with the following structure:

```python
{
    'new': List[Opportunity],           # Newly created opportunities
    'amendments': List[Opportunity],     # Amended opportunities
    'unchanged_count': int,              # Count of unchanged opportunities
    'removed_count': int,                # Count of opportunities removed from website
    'processed_count': int,              # Total processed
    'timestamp': datetime,               # When job completed
    'success': bool,                     # Whether job succeeded
    'error': str | None,                 # Error message if failed
    'duration_seconds': float,           # Job execution time
    'start_time': datetime,              # When job started
    'end_time': datetime                 # When job ended
}
```

### Setting Up Cron Job

To run this job daily via cron:

1. Make the script executable:
   ```bash
   chmod +x backend/jobs/run_job.py
   ```

2. Add to crontab (runs daily at 2 AM):
   ```bash
   0 2 * * * cd /path/to/nato_website_2/backend && /path/to/venv/bin/python jobs/run_job.py incremental >> /path/to/logs/scraper_job.log 2>&1
   ```

### Notes

- The job runs in `incremental` mode by default, which only processes new and amended opportunities
- Use `full` mode to process all opportunities from scratch
- The job handles errors gracefully and returns success/failure status
- All results are logged with structured logging

