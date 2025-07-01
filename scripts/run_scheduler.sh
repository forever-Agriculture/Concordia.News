#!/bin/bash

# --- Debugging Flags ---
# Exit immediately if a command exits with a non-zero status.
set -e
# Print commands and their arguments as they are executed.
# set -x # Uncomment this for EXTREMELY verbose debugging if needed

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Log file paths
COLLECTOR_LOG="/app/logs/collector.log"
ANALYZER_LOG="/app/logs/analyzer.log"
MAINTENANCE_LOG="/app/logs/maintenance.log"
HEALTH_LOG="/app/logs/health.log"
RESOURCE_LOG="/app/logs/resources.log"

# Function to log with timestamp
log() {
  # Ensure HEALTH_LOG is defined before using it
  local log_target=${2:-"/app/logs/health.log"} # Default to health log if $2 is empty
  echo "$(date -u +'%Y-%m-%d %H:%M:%S UTC') - $1" >> "$log_target"
}

# Function to check health of a process
check_health() {
  local process_name=$1
  local log_file=$2
  local exit_code=$3

  if [ $exit_code -eq 0 ]; then
    log "✅ $process_name completed successfully" $HEALTH_LOG
  else
    log "❌ $process_name failed with exit code $exit_code" $HEALTH_LOG
    # Note: with set -e, the script might exit before this if the command failed,
    # unless the command has || true appended.
  fi
}

# Function to log resource usage
log_resources() {
  # Get memory usage
  local mem_usage=$(free -m | grep Mem | awk '{print $3}')
  local mem_total=$(free -m | grep Mem | awk '{print $2}')
  local mem_percent=$(awk "BEGIN {printf \"%.2f\", ($mem_usage/$mem_total)*100}")

  # Get CPU usage
  local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')

  # Get disk usage
  local disk_usage=$(df -h / | awk 'NR==2 {print $5}')

  log "Memory: ${mem_usage}MB/${mem_total}MB (${mem_percent}%) | CPU: ${cpu_usage}% | Disk: ${disk_usage}" $RESOURCE_LOG
}

# Initialize health log
log "🚀 Scheduler started (Debug flags: set -e enabled)" $HEALTH_LOG

# Main loop
while true; do
  # Start resource logging in background
  (
    while true; do
      log_resources
      sleep 900 # 15 minutes
    done
  ) &
  RESOURCE_PID=$!

  # Get current time (UTC)
  CURRENT_HOUR=$(date -u +%H)
  CURRENT_MINUTE=$(date -u +%M)
  current_hour_base10=$((10#$CURRENT_HOUR))
  current_minute_base10=$((10#$CURRENT_MINUTE))
  current_total_minutes=$(( current_hour_base10 * 60 + current_minute_base10 ))

  # --- Analysis Decision & Execution Block (Moved Up) ---
  # Check if we are within the analysis window (23:30 - 23:34 UTC)
  SHOULD_ANALYZE=false
  if [ $current_hour_base10 -eq 23 ] && \
     [ $current_minute_base10 -ge 30 ] && \
     [ $current_minute_base10 -lt 35 ]; then
    SHOULD_ANALYZE=true
    log "✅ Detected Analysis Window (23:30 UTC) - Running Analysis" $HEALTH_LOG # Adjusted log
    # --- Run Analyzer ---
    log "🧠 Starting daily article analysis" $ANALYZER_LOG
    python -m backend.rss_analyzer >> $ANALYZER_LOG 2>&1
    analyze_exit_code=$?
    check_health "Article analysis" $ANALYZER_LOG $analyze_exit_code

    # --- Run Maintenance (only if analysis succeeded) ---
    if [ $analyze_exit_code -eq 0 ]; then
        # --- Maintenance SKIPPED ---
        log "⏭️ Skipping database maintenance step for now." $HEALTH_LOG
        # log "🛠️ Starting database maintenance" $MAINTENANCE_LOG
        # python -m backend.db_maintenance >> $MAINTENANCE_LOG 2>&1
        # maint_exit_code=$?
        # check_health "Database maintenance" $MAINTENANCE_LOG $maint_exit_code
    else
        log "⚠️ Skipped database maintenance due to analysis failure (Exit Code: $analyze_exit_code)." $MAINTENANCE_LOG
    fi
    # Add a small sleep after analysis attempt to ensure loop progresses
    sleep 60 # Sleep for 1 minute after attempting analysis
  fi # End of analysis check

  # --- Collection Decision Logic ---
  # Only check for collection if analysis didn't just run
  SHOULD_COLLECT=false
  if [ "$SHOULD_ANALYZE" = false ]; then
      # Standard collection: First 5 mins of even hours (excluding midnight)
      if [ $((current_minute_base10 < 5)) -eq 1 ] && \
         [ $((current_hour_base10 % 2 == 0)) -eq 1 ] && \
         [ $current_hour_base10 -ne 0 ]; then
        SHOULD_COLLECT=true
      fi
      # Special pre-analysis collection: 23:05 - 23:14 UTC (Extended start, Earlier end)
      # Collection triggers if the time is between 23:05 and 23:14 inclusive.
      if [ $current_hour_base10 -eq 23 ] && \
         [ $current_minute_base10 -ge 5 ] && \
         [ $current_minute_base10 -lt 15 ]; then # End time changed from 30 to 15
        SHOULD_COLLECT=true
      fi
  fi

  # --- Collection Execution Block ---
  if [ "$SHOULD_COLLECT" = true ]; then
    log "🔄 Starting article collection" $COLLECTOR_LOG
    python -m backend.rss_collector >> $COLLECTOR_LOG 2>&1
    collect_exit_code=$?
    check_health "Article collection" $COLLECTOR_LOG $collect_exit_code # Log status to health log
    # Add a small sleep after collection attempt to ensure loop progresses
    sleep 60
  # --- Wait Calculation Block (Only if neither Analysis nor Collection ran) ---
  elif [ "$SHOULD_ANALYZE" = false ]; then
    # Find minutes until next even hour collection (02:00, 04:00... 22:00)
    next_collect_hour=$current_hour_base10
    while true; do
        next_collect_hour=$(( (next_collect_hour + 1) % 24 )) # Increment hour (wrap around 24)
        is_next_even=$(( next_collect_hour % 2 == 0 ))
        if [ $is_next_even -eq 1 ] && [ $next_collect_hour -ne 0 ]; then break; fi # Found next valid hour
        if [ $next_collect_hour -eq $current_hour_base10 ]; then log "⚠️ Error finding next collect hour!" $HEALTH_LOG; break; fi # Safety break
    done
    hours_diff_collect=$(( (next_collect_hour - current_hour_base10 + 24) % 24 ))
    minutes_until_next_collect=$(( hours_diff_collect * 60 - current_minute_base10 ))
    if [ $minutes_until_next_collect -le 0 ]; then minutes_until_next_collect=$(( minutes_until_next_collect + 24 * 60 )); fi

    # Find minutes until special collection window (Now starts at 23:05 UTC)
    target_special_collect_minute=$(( 23 * 60 + 5 )) # Target is the start of the window
    minutes_until_special_collect=$(( target_special_collect_minute - current_total_minutes ))
    if [ $minutes_until_special_collect -le 0 ]; then minutes_until_special_collect=$(( minutes_until_special_collect + 24 * 60 )); fi

    # Find minutes until analysis window (23:30 UTC)
    target_analysis_minute=$(( 23 * 60 + 30 ))
    minutes_until_analysis=$(( target_analysis_minute - current_total_minutes ))
    if [ $minutes_until_analysis -le 0 ]; then minutes_until_analysis=$(( minutes_until_analysis + 24 * 60 )); fi

    # Determine the minimum wait time until the *next* scheduled event
    wait_calc=$minutes_until_next_collect
    if [ $minutes_until_special_collect -lt $wait_calc ]; then wait_calc=$minutes_until_special_collect; fi
    if [ $minutes_until_analysis -lt $wait_calc ]; then wait_calc=$minutes_until_analysis; fi

    # Ensure we check at least every 5 minutes
    MINUTES_TO_WAIT=$wait_calc
    MAX_WAIT_MINUTES=5 # Max interval between checks
    if [ $MINUTES_TO_WAIT -le 0 ]; then MINUTES_TO_WAIT=1; fi # Wait at least 1 minute
    if [ $MINUTES_TO_WAIT -gt $MAX_WAIT_MINUTES ]; then MINUTES_TO_WAIT=$MAX_WAIT_MINUTES; fi

    # Log the intended wait time and when the next events are (updated target time)
    log "⏳ Next check in $MINUTES_TO_WAIT minutes. Next potential events: Even hour collect in $minutes_until_next_collect mins, 23:05 collect window start in $minutes_until_special_collect mins, 23:30 analysis in $minutes_until_analysis mins." $HEALTH_LOG

    # --- Sleep Execution ---
    sleep $((MINUTES_TO_WAIT * 60)) # Sleep uses seconds
  fi # End of if $SHOULD_COLLECT / elif not $SHOULD_ANALYZE

  # --- Resource PID Cleanup ---
  # Kill silently, don't need logs for this normally
  if [ ! -z "$RESOURCE_PID" ] && ps -p $RESOURCE_PID > /dev/null; then
      kill $RESOURCE_PID 2>/dev/null || true # Add || true to prevent exit on kill failure
  fi
  unset RESOURCE_PID
  # No logs needed for loop end/restart

done

# Script should never reach here in normal operation
log "🆘 Script exited main loop unexpectedly!" $HEALTH_LOG
exit 1 