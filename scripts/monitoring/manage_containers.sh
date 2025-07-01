#!/bin/bash
# Concordia Container Management Script
# This script provides utilities for managing Docker containers

# Function to display usage information
function show_usage {
  echo "Concordia Container Management Utility"
  echo "Usage: $0 [command]"
  echo ""
  echo "Commands:"
  echo "  status         Show status of all containers"
  echo "  logs           Show logs from all containers"
  echo "  restart        Restart all containers"
  echo "  restart-api    Restart only the API container"
  echo "  restart-front  Restart only the frontend container"
  echo "  restart-sched  Restart only the scheduler container"
  echo "  stats          Show container resource usage"
  echo "  health         Run API health check"
  echo ""
  exit 0
}

# Check if docker is available
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed or not in PATH"
  exit 1
fi

# Parse command
if [ -z "$1" ]; then
  show_usage
fi

COMMAND="$1"

# Execute requested command
case "$COMMAND" in
  status)
    echo "=== Container Status ==="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
  logs)
    echo "=== Container Logs ==="
    docker compose logs --tail=50
    ;;
  restart)
    echo "=== Restarting All Containers ==="
    docker compose restart
    ;;
  restart-api)
    echo "=== Restarting API Container ==="
    docker restart concordia-api
    ;;
  restart-front)
    echo "=== Restarting Frontend Container ==="
    docker restart concordia-frontend
    ;;
  restart-sched)
    echo "=== Restarting Scheduler Container ==="
    docker restart concordia-scheduler
    ;;
  stats)
    echo "=== Container Resource Usage ==="
    docker stats --no-stream
    ;;
  health)
    echo "=== API Health Check ==="
    curl -s http://localhost:8000/health | json_pp
    ;;
  *)
    echo "Unknown command: $COMMAND"
    show_usage
    ;;
esac