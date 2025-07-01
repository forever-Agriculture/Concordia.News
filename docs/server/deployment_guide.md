# Concordia News Analysis - Deployment Guide

This document outlines the step-by-step process for deploying the Concordia News Analysis application to a production server.

## Prerequisites

- Ubuntu 24.04 LTS server
- Root access to the server
- Domain name (e.g., concordia.news)
- DNS access to configure domain records

## ⚠️ CRITICAL: Enable Production Mode

Before deploying, you MUST enable production mode in your local repository:

```bash
# Switch to production mode
./scripts/switch-to-prod.sh

# Commit the change
git add config/environment.js
git commit -m "Set environment to production for deployment"
git push
```

Failing to enable production mode will result in API connection errors, as the frontend will attempt to connect to localhost instead of the proper API endpoint.

## Deployment Checklist

Before starting deployment, verify these critical items:

- [ ] Production mode is enabled (run `./scripts/switch-to-prod.sh`)
- [ ] Set config/environment.js ENV to `production`
- [ ] Changes are committed to repository (`git commit -m "Set environment to production"`)
- [ ] Repository changes are pushed (`git push`)
- [ ] DeepSeek API key is available
- [ ] Domain name is registered and accessible
- [ ] Server is provisioned with Ubuntu 24.04 LTS

Proceeding without these prerequisites may result in deployment failures or incorrect configuration.

## 1. Server Setup

### 1.1. SSH Access

Configure SSH key authentication for secure access to your server:

```bash
# Generate a new SSH key if needed (on your local machine)
ssh-keygen -t ed25519 -C "concordia-deployment-key"

# Add your public key to the server's authorized_keys
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@your-server-ip
```

### 1.2. Basic Server Configuration

```bash
# Update system packages
apt update && apt upgrade -y

# Install required packages
apt install -y git curl wget nano ufw python3-pip

# Set up firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 2. Application Setup

### 2.1. Clone Repository

```bash
# Create application directory
mkdir -p /home/concordia/app
cd /home/concordia/app

# Clone the repository (via SSH or HTTPS)
# SSH (recommended if you've set up SSH keys with your Git provider):
git clone git@bitbucket.org:concordia_news/concordia.git .

# HTTPS (alternative):
git clone https://USERNAME@bitbucket.org/concordia_news/concordia.git .
```

### 2.2. Environment Configuration

```bash
# Create .env file from example
cp .env.example .env

# Edit the .env file with production values
nano .env
```

Essential environment variables to configure:
- `DEEPSEEK_API_KEY`: Your DeepSeek API key
- `DOMAIN_NAME`: Your domain (e.g., concordia.news)
- Any database configuration if using external databases

### 2.3. Docker Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose V2 (plugin format)
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose

# Verify installation
docker --version
docker compose version
```

## 3. Application Deployment

### 3.1. Directory Setup

```bash
# Create required directories
mkdir -p data logs
chmod -R 755 data logs

# Run the database preparation script
./scripts/prepare_db.sh
```

### 3.2. Docker Build and Run

```bash
# Build Docker containers
docker compose build

# Start containers in detached mode
docker compose up -d
```

### 3.3. Frontend URL Configuration

**IMPORTANT**: The frontend hardcodes API URLs during build. If you see API connection errors, you may need to modify the built JS files:

```bash
# Get into the frontend container
docker exec -it concordia-frontend /bin/sh

# Install necessary tools
apk add --no-cache grep sed

# Replace all instances of localhost:8000 with relative path
find /usr/share/nginx/html -name "*.js" -exec sed -i 's|http://localhost:8000|/api|g' {} \;

# Exit the container
exit

# Restart the frontend container
docker restart concordia-frontend
```

### 3.4. Database Initialization

```bash
# Initialize database schema
docker exec -it concordia-api python -c "from backend.src.news_utils import init_database; init_database('/app/news_analysis.db')"

# Add media sources data
docker exec -it concordia-api python -m backend.src.add_media_data
```

## 4. Web Server and SSL Setup

### 4.1. Nginx Installation

```bash
# Install Nginx and Certbot
apt install -y nginx certbot python3-certbot-nginx
```

### 4.2. Nginx Configuration

```bash
# Create Nginx configuration
nano /etc/nginx/sites-available/concordia
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name concordia.news www.concordia.news;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
ln -s /etc/nginx/sites-available/concordia /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 4.3. DNS Configuration

Before proceeding with SSL, configure DNS records at your domain registrar:

1. Add A record for root domain (`concordia.news`) pointing to your server IP
2. Add A record for www subdomain (`www.concordia.news`) pointing to your server IP

### 4.4. SSL Certificate

```bash
# Obtain and install SSL certificate with Certbot
certbot --nginx -d concordia.news -d www.concordia.news
```

## 5. Maintenance Setup

### 5.1. Health Check Script

```bash
mkdir -p /home/concordia/app/scripts
nano /home/concordia/app/scripts/check_health.sh
```

Add this content:

```bash
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
```

Make it executable:

```bash
chmod +x /home/concordia/app/scripts/check_health.sh
```

### 5.2. Cron Jobs

```bash
crontab -e
```

Add these lines:

```crontab
# Check health every 5 minutes
*/5 * * * * /home/concordia/app/scripts/check_health.sh >> /home/concordia/app/logs/monitoring.log 2>&1

# Daily container restart at 01:31 UTC
31 1 * * * cd /home/concordia/app && docker compose restart

# Daily basic DB optimization at 02:30 UTC
30 2 * * * cd /home/concordia/app && docker exec concordia-api python -c "import sqlite3; conn = sqlite3.connect('/app/news_analysis.db'); conn.execute('PRAGMA optimize'); conn.execute('PRAGMA wal_checkpoint(FULL)'); print('✅ Basic optimization complete'); conn.close()" >> /home/concordia/app/logs/db_maintenance.log 2>&1
```

## 6. Troubleshooting

### 6.1. API Connection Issues

If the frontend can't connect to the API:
- Check that Nginx proxy configuration is correct
- Verify the API container is running: `docker ps`
- Check API logs: `docker logs concordia-api`
- Test API directly: `curl http://localhost:8000/health`
- Modify hardcoded API URLs in frontend JS files (see section 3.3)

### 6.2. SSL Certificate Issues

If Certbot fails to obtain certificates:
- Verify your DNS records are correctly set up and propagated
- Check that ports 80 and 443 are open and accessible
- Ensure Nginx is running correctly

### 6.3. Database Issues

If the application fails to start due to database issues:
- Check database initialization logs
- Verify SQLite file permissions: `ls -la /home/concordia/app/news_analysis.db`
- Manually run initialization scripts if needed

## 7. Updating the Application

To update the application:

```bash
# Pull the latest changes
cd /home/concordia/app
git pull

# Rebuild and restart containers
docker compose down
docker compose build
docker compose up -d

# Check for any database migrations or updates needed
docker exec -it concordia-api python -c "from backend.src.news_utils import init_database; init_database('/app/news_analysis.db')"
```

## 8. Backup Strategy

### 8.1. Database Backup

```bash
# Create backup directory
mkdir -p /home/concordia/backups

# Add backup cron job
echo "0 4 * * * sqlite3 /home/concordia/app/news_analysis.db '.backup /home/concordia/backups/news_analysis_\$(date +\%Y\%m\%d).db'" >> /var/spool/cron/crontabs/root
```

### 8.2. Log Rotation

```bash
# Install logrotate if not present
apt install -y logrotate

# Create logrotate configuration
nano /etc/logrotate.d/concordia
```

Add this content:

/home/concordia/app/logs/.log {
daily
rotate 14
compress
delaycompress
missingok
notifempty
create 0640 root root
}


## Known Issues and Their Solutions

1. **Frontend API Connection Issues**: Frontend JS files often have hardcoded localhost:8000 URLs that need to be replaced after building.

2. **Nginx/SSL Configuration**: When setting up Nginx with SSL, make sure to start with a basic HTTP configuration first, then add SSL with Certbot.

3. **Docker Compose Version**: Docker Compose V2 uses the `docker compose` command format (with space), while V1 uses `docker-compose` (with hyphen).

4. **Favicon Redirect Loop**: If you see favicon.ico redirect errors, you can add a specific location block in Nginx to serve a static favicon.

