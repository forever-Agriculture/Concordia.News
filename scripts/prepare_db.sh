#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data
mkdir -p logs

# Ensure the database file exists and has the right permissions
touch news_analysis.db
chmod 666 news_analysis.db

echo "Database file prepared with correct permissions" 