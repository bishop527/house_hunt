#!/bin/bash
# run_commute_collection.sh
# Wrapper script to run commute data collection via cron

# ===== CONFIGURATION =====
# UPDATE THIS PATH to match your system
PROJECT_DIR="/home/ad23883/workspace/house_hunt"

# If using a virtual environment, UPDATE THIS PATH
# VENV_DIR="$PROJECT_DIR/venv"

# ===== SCRIPT LOGIC =====
# Change to project directory
cd "$PROJECT_DIR" || {
    echo "$(date): ERROR - Cannot access $PROJECT_DIR" >&2
    exit 1
}

# Activate virtual environment if it exists (uncomment if needed)
# if [ -d "$VENV_DIR" ]; then
#     source "$VENV_DIR/bin/activate"
# fi

# Run main.py with commute flag and quiet mode
# --quiet suppresses console output (logs to file only)
#/usr/bin/python3 main.py --commute --quiet
/usr/bin/python3 main.py --commute

EXIT_CODE=$?

# Log completion status to cron-specific log
if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date): Commute collection completed successfully" >> \
        Data/Results/cron.log
else
    echo "$(date): Commute collection FAILED (exit code: $EXIT_CODE)" \
        >> Data/Results/cron.log
fi

exit $EXIT_CODE