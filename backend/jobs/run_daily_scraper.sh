#!/bin/bash

# Daily scraper job script for NATO Opportunities
# This script runs all ACT scrapers (IFIB, NOI, RFI, RFIP) in incremental mode and logs the results

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_ROOT="$( cd "$BACKEND_DIR/.." && pwd )"

# Set up paths
VENV_PATH="$BACKEND_DIR/venv"
PYTHON="$VENV_PATH/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/scraper_job.log"
ERROR_LOG="$LOG_DIR/scraper_job_error.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Activate virtual environment
cd "$BACKEND_DIR" || exit 1

# Run all four scrapers
SCRAPERS=("ACT-IFIB" "ACT-NOI" "ACT-RFI" "ACT-RFIP")
TOTAL_EXIT_CODE=0

# Run the job with timestamp
echo "========================================" >> "$LOG_FILE"
echo "Job started at: $(date)" >> "$LOG_FILE"
echo "Running scrapers: ${SCRAPERS[*]}" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

for SCRAPER in "${SCRAPERS[@]}"; do
    echo "" >> "$LOG_FILE"
    echo "--- Running $SCRAPER scraper ---" >> "$LOG_FILE"
    echo "Started at: $(date)" >> "$LOG_FILE"
    
    case $SCRAPER in
        "ACT-IFIB")
            "$PYTHON" -m jobs.daily_scraper_job_act_ifib incremental >> "$LOG_FILE" 2>> "$ERROR_LOG"
            ;;
        "ACT-NOI")
            "$PYTHON" -m jobs.daily_scraper_job_act_noi incremental >> "$LOG_FILE" 2>> "$ERROR_LOG"
            ;;
        "ACT-RFI")
            "$PYTHON" -m jobs.daily_scraper_job_act_rfi incremental >> "$LOG_FILE" 2>> "$ERROR_LOG"
            ;;
        "ACT-RFIP")
            "$PYTHON" -m jobs.daily_scraper_job_act_rfip incremental >> "$LOG_FILE" 2>> "$ERROR_LOG"
            ;;
    esac
    
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        TOTAL_EXIT_CODE=$EXIT_CODE
        echo "❌ $SCRAPER scraper failed with exit code $EXIT_CODE at: $(date)" >> "$LOG_FILE"
    else
        echo "✅ $SCRAPER scraper completed successfully at: $(date)" >> "$LOG_FILE"
    fi
done

echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
if [ $TOTAL_EXIT_CODE -eq 0 ]; then
    echo "All scrapers completed successfully at: $(date)" >> "$LOG_FILE"
else
    echo "Some scrapers failed. Check error log: $ERROR_LOG" >> "$LOG_FILE"
fi
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $TOTAL_EXIT_CODE

