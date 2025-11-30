#!/bin/bash

# Daily scraper job script for NATO Opportunities
# This script runs the incremental scraper job and logs the results

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_ROOT="$( cd "$BACKEND_DIR/.." && pwd )"

# Set up paths
VENV_PATH="$BACKEND_DIR/venv"
PYTHON="$VENV_PATH/bin/python"
JOB_SCRIPT="$BACKEND_DIR/jobs/run_job.py"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/scraper_job.log"
ERROR_LOG="$LOG_DIR/scraper_job_error.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Activate virtual environment and run the job
cd "$BACKEND_DIR" || exit 1

# Run the job with timestamp
echo "========================================" >> "$LOG_FILE"
echo "Job started at: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

"$PYTHON" "$JOB_SCRIPT" incremental >> "$LOG_FILE" 2>> "$ERROR_LOG"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Job completed successfully at: $(date)" >> "$LOG_FILE"
else
    echo "Job failed with exit code $EXIT_CODE at: $(date)" >> "$LOG_FILE"
    echo "Check error log: $ERROR_LOG" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

exit $EXIT_CODE

