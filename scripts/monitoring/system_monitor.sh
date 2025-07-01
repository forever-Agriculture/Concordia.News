#!/bin/bash
# Concordia System Monitoring Script
# This script collects system metrics and application status information

# --- Configuration ---
# Use absolute path for the project root on the HOST system
APP_ROOT="/home/concordia/app" # ADJUST THIS if your project path is different!
LOG_DIR="${APP_ROOT}/logs"
# Use absolute path to the database on the HOST system
DB_PATH="${APP_ROOT}/news_analysis.db"
REPORT_PATH="${LOG_DIR}/system_report.txt"
# Use absolute path for sqlite3 binary for robustness in cron
SQLITE_CMD="/usr/bin/sqlite3" # ADJUST THIS if 'which sqlite3' shows a different path

# Create logs directory if it doesn't exist
mkdir -p ${LOG_DIR}

echo "=== Concordia System Status Report $(date) ===" > ${REPORT_PATH}
echo >> ${REPORT_PATH}

# System information
echo "=== System Information ===" >> ${REPORT_PATH}
echo "Hostname: $(hostname)" >> ${REPORT_PATH}
echo "Kernel: $(uname -r)" >> ${REPORT_PATH}
echo "Uptime: $(uptime -p)" >> ${REPORT_PATH}
echo >> ${REPORT_PATH}

# Resource usage
echo "=== Resource Usage ===" >> ${REPORT_PATH}
echo "CPU Load:" >> ${REPORT_PATH}
top -bn1 | grep "Cpu(s)" >> ${REPORT_PATH}
echo >> ${REPORT_PATH}
echo "Memory Usage:" >> ${REPORT_PATH}
free -h >> ${REPORT_PATH}
echo >> ${REPORT_PATH}
echo "Disk Usage:" >> ${REPORT_PATH}
df -h / >> ${REPORT_PATH}
echo >> ${REPORT_PATH}

# Docker status
echo "=== Docker Containers Status ===" >> ${REPORT_PATH}
# Ensure docker command is found (use absolute path if necessary)
/usr/bin/docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}" >> ${REPORT_PATH} 2>&1
echo >> ${REPORT_PATH}

# Database stats
echo "=== Database Statistics === (Host Path: ${DB_PATH})" >> ${REPORT_PATH}
# Check if DB file exists at the HOST path
if [ -f "${DB_PATH}" ]; then
  echo "Database size: $(du -h ${DB_PATH} | cut -f1)" >> ${REPORT_PATH}

  # Using sqlite3 to get data counts
  # Check if the specified sqlite3 command exists
  if command -v ${SQLITE_CMD} &> /dev/null; then
    echo "Media Sources: $(${SQLITE_CMD} ${DB_PATH} 'SELECT COUNT(*) FROM media_sources;')" >> ${REPORT_PATH}
    echo "Articles: $(${SQLITE_CMD} ${DB_PATH} 'SELECT COUNT(*) FROM articles;')" >> ${REPORT_PATH}
    echo "Analyses: $(${SQLITE_CMD} ${DB_PATH} 'SELECT COUNT(*) FROM analyses;')" >> ${REPORT_PATH}
    # Handle potential empty table for MAX(publication_date)
    latest_article=$(${SQLITE_CMD} ${DB_PATH} 'SELECT MAX(publication_date) FROM articles;')
    echo "Latest Article: ${latest_article:-N/A}" >> ${REPORT_PATH}
  else
    echo "${SQLITE_CMD} not available for DB statistics" >> ${REPORT_PATH}
  fi
else
  echo "Database file not found at host path ${DB_PATH}" >> ${REPORT_PATH}
fi
echo >> ${REPORT_PATH}

# Nginx status (if running)
# This part might be less relevant if Nginx only runs inside Docker
# Keeping it for now, but might need adjustment if systemctl isn't the right check
echo "=== Nginx Status === (Checking host systemctl)" >> ${REPORT_PATH}
if command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet nginx; then
        echo "Host Nginx is running (Note: Frontend uses Nginx in Docker)" >> ${REPORT_PATH}
        # Use absolute path for nginx if checking host config
        # /usr/sbin/nginx -t >> ${REPORT_PATH} 2>&1
    else
        echo "Host Nginx is not running" >> ${REPORT_PATH}
    fi
else
    echo "systemctl not available for Nginx check" >> ${REPORT_PATH}
fi
echo >> ${REPORT_PATH}

# SSL certificate info
echo "=== SSL Certificate Status === (Checking host certbot)" >> ${REPORT_PATH}
if command -v /usr/bin/certbot &> /dev/null; then
  /usr/bin/certbot certificates >> ${REPORT_PATH} 2>&1
else
  echo "Certbot not installed at /usr/bin/certbot" >> ${REPORT_PATH}
fi
echo >> ${REPORT_PATH}

# Recent errors from logs
echo "=== Recent Errors from Logs === (Searching in ${LOG_DIR})" >> ${REPORT_PATH}
if [ -d ${LOG_DIR} ]; then
  # Use find within the correct log directory
  error_lines=$(find ${LOG_DIR} -name "*.log" -type f -exec grep -i -H "ERROR\|FAIL\|Traceback" {} \; | tail -n 20)
  if [ -n "$error_lines" ]; then
    echo "$error_lines" >> ${REPORT_PATH}
  else
    echo "No recent errors/failures found in logs" >> ${REPORT_PATH}
  fi
else
  echo "Log directory ${LOG_DIR} not found" >> ${REPORT_PATH}
fi
echo >> ${REPORT_PATH}

# API health check
echo "=== API Health Check === (via localhost:8000)" >> ${REPORT_PATH}
# Ensure curl is available
if command -v /usr/bin/curl &> /dev/null; then
    API_HEALTH=$(/usr/bin/curl -s --max-time 5 http://localhost:8000/health 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$API_HEALTH" ]; then
      echo "API is responding:" >> ${REPORT_PATH}
      # Basic check if response looks like JSON before printing
      if [[ "$API_HEALTH" == \{* ]]; then
         echo "${API_HEALTH}" >> ${REPORT_PATH} # Consider piping to | jq . if jq is installed
      else
         echo "API response received, but format unexpected: ${API_HEALTH}" >> ${REPORT_PATH}
      fi
    else
      echo "API is not responding or timed out" >> ${REPORT_PATH}
    fi
else
    echo "curl not available at /usr/bin/curl" >> ${REPORT_PATH}
fi
echo >> ${REPORT_PATH}

echo "=== End of Report === $(date)" >> ${REPORT_PATH}

# Output report location (optional, cron usually handles output)
# echo "System report generated at ${REPORT_PATH}"

# Optional: If you want to display the report when run manually
cat ${REPORT_PATH}