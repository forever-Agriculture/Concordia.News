#!/bin/bash
# Switch to production environment

echo "Switching to PRODUCTION environment..."

# Update environment.js file
sed -i "s/const ENV = 'development';/const ENV = 'production';/" config/environment.js

echo "✅ Environment switched to production mode"
echo "➡️ Run 'npm run build' or 'docker compose build' to apply changes" 