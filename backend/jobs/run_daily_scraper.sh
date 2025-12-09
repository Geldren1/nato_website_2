#!/bin/bash

# Daily scraper job runner
# Runs all ACT scrapers sequentially

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

# Set up Python path
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

# Change to backend directory
cd "$BACKEND_DIR" || exit 1

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Find Python executable
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi

# Set up logging
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/scraper_job.log"
ERROR_LOG="$LOG_DIR/scraper_job_error.log"

# Log start time
echo "========================================" >> "$LOG_FILE"
echo "Daily scraper job started at: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# List of scrapers to run
SCRAPERS=("ACT-IFIB" "ACT-NOI" "ACT-RFI" "ACT-RFIP")

# Run each scraper
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
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ $SCRAPER scraper completed successfully at: $(date)" >> "$LOG_FILE"
    else
        echo "❌ $SCRAPER scraper failed with exit code $EXIT_CODE at: $(date)" >> "$LOG_FILE"
    fi
done

# Check for succeeded NOIs after all scrapers complete
echo "" >> "$LOG_FILE"
echo "--- Checking for succeeded NOIs ---" >> "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
"$PYTHON" -m jobs.check_succeeded_nois >> "$LOG_FILE" 2>> "$ERROR_LOG"
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Succeeded NOI check completed successfully at: $(date)" >> "$LOG_FILE"
else
    echo "❌ Succeeded NOI check failed with exit code $EXIT_CODE at: $(date)" >> "$LOG_FILE"
fi

# Log completion
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "All scrapers and checks completed at: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
