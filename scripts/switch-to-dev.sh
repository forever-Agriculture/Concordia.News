#!/bin/bash
# Switch to development environment

echo "Switching to DEVELOPMENT environment..."

# Update environment.js file
sed -i "s/const ENV = 'production';/const ENV = 'development';/" config/environment.js

echo "✅ Environment switched to development mode"
echo "➡️ Run 'npm run build' or 'docker compose up' to apply changes" 