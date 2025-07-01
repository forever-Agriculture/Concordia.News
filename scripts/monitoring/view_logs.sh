#!/bin/bash
# Concordia Log Viewer Script
# This script provides a simple interface to view application logs

LOG_DIR="/app/logs"
LINES=50

# Function to display usage information
function show_usage {
  echo "Concordia Log Viewer"
  echo "Usage: $0 [options] [log_name]"
  echo ""
  echo "Options:"
  echo "  -h, --help     Show this help message"
  echo "  -l, --lines N  Show N lines (default: 50)"
  echo "  -f, --follow   Follow the log (tail -f)"
  echo ""
  echo "Log names:"
  echo "  all            Show all logs"
  echo "  api            API server logs"
  echo "  collector      Article collector logs"
  echo "  analyzer       Article analyzer logs"
  echo "  media          Media sources logs"
  echo "  health         Health check logs"
  echo "  system         System report log"
  echo ""
  exit 0
}

# Parse arguments
FOLLOW=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_usage
      ;;
    -l|--lines)
      LINES="$2"
      shift 2
      ;;
    -f|--follow)
      FOLLOW=true
      shift
      ;;
    *)
      LOG_NAME="$1"
      shift
      ;;
  esac
done

# If no log name provided, show usage
if [ -z "$LOG_NAME" ]; then
  show_usage
fi

# Determine log file based on name
case "$LOG_NAME" in
  all)
    LOG_FILES="${LOG_DIR}/*.log"
    ;;
  api)
    LOG_FILES="${LOG_DIR}/api.log"
    ;;
  collector)
    LOG_FILES="${LOG_DIR}/collector.log"
    ;;
  analyzer)
    LOG_FILES="${LOG_DIR}/analyzer.log"
    ;;
  media)
    LOG_FILES="${LOG_DIR}/media.log"
    ;;
  health)
    LOG_FILES="${LOG_DIR}/health.log"
    ;;
  system)
    LOG_FILES="${LOG_DIR}/system_report.txt"
    ;;
  *)
    echo "Unknown log name: $LOG_NAME"
    show_usage
    ;;
esac

# Display logs
if $FOLLOW && [ "$LOG_NAME" != "all" ]; then
  echo "Showing last $LINES lines of $LOG_NAME log and following updates. Press Ctrl+C to exit."
  tail -n $LINES -f $LOG_FILES
else
  if [ "$LOG_NAME" = "all" ]; then
    echo "Showing last $LINES lines of all logs:"
    for LOG in ${LOG_DIR}/*.log; do
      if [ -f "$LOG" ]; then
        echo "=== $(basename $LOG) ==="
        tail -n $LINES "$LOG"
        echo ""
      fi
    done
  else
    echo "Showing last $LINES lines of $LOG_NAME log:"
    tail -n $LINES $LOG_FILES
  fi
fi