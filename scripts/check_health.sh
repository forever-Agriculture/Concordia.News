#!/bin/bash

# Check if containers are running
CONTAINERS=$(docker ps -q --filter "name=concordia")
if [ -z "$CONTAINERS" ]; then
  echo "ERROR: No Concordia containers running!"
  cd /home/concordia/app && docker compose up -d
fi

# Check API health
HEALTH=$(curl -s http://localhost:8000/health)
if [[ $HEALTH != *"healthy"* ]]; then
  echo "ERROR: API health check failed!"
  docker restart concordia-api
fi
