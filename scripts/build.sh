#!/bin/bash
# Build the application based on current environment

# Load environment config
ENV=$(grep "const ENV = " config/environment.js | cut -d "'" -f 2)

echo "Building for environment: $ENV"

if [ "$ENV" = "development" ]; then
  echo "Starting development build..."
  docker compose up --build
else
  echo "Starting production build..."
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
fi 