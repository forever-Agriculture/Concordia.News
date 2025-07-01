# Concordia News Analysis - Server Management Guide

This document provides instructions for managing, monitoring, and maintaining the Concordia News Analysis application in production.

## Connecting to the Server

### SSH Connection

```bash
# Connect to the server with SSH
ssh root@157.180.73.159

# Or if using a custom SSH key
ssh -i /path/to/private_key root@157.180.73.159

# Navigate to the application directory 
cd /home/concordia/app
```


### Checking Server Status

Once connected, check the server's status:

```bash
# System uptime and load
uptime

# Disk usage
df -h

# Memory usage
free -m

# System overview (install if needed: apt install htop)
htop
```

## Docker Container Management

### Checking Container Status

```bash
# List all running containers
docker ps

# Include stopped containers
docker ps -a
```

### Container Logs

```bash
# View logs from all containers
docker compose logs

# View logs from a specific container
docker logs concordia-api
docker logs concordia-frontend
docker logs concordia-scheduler

# Follow logs in real-time
docker logs -f concordia-api
```

### Managing Containers

```bash
# Restart all containers
docker compose restart

# Restart a specific container
docker restart concordia-api

# Stop all containers
docker compose down

# Start all containers
docker compose up -d

# Check container resource usage
docker stats
```

## Application Logs

All application logs are stored in the `/home/concordia/app/logs` directory.

### Viewing Logs

```bash
# List all log files
ls -la /home/concordia/app/logs

# View a specific log file
cat /home/concordia/app/logs/api.log
cat /home/concordia/app/logs/collector.log
cat /home/concordia/app/logs/analyzer.log

# View the end of a log file
tail -n 100 /home/concordia/app/logs/api.log

# Follow log updates in real-time
tail -f /home/concordia/app/logs/collector.log
```

### Using Log Viewer Script

We provide a convenient script for viewing logs:

```bash
# View API logs
./scripts/monitoring/view_logs.sh api

# View collector logs with 100 lines
./scripts/monitoring/view_logs.sh -l 100 collector

# Follow analyzer logs in real-time
./scripts/monitoring/view_logs.sh -f analyzer

# View all logs
./scripts/monitoring/view_logs.sh all
```

## Monitoring the Application

### System Monitoring

```bash
# Run the system monitoring script
./scripts/monitoring/system_monitor.sh

# View the latest system report
cat /home/concordia/app/logs/system_report.txt
```

### Database Status

```bash
# Check database size
du -h /home/concordia/app/news_analysis.db

# Get record counts
sqlite3 /home/concordia/app/news_analysis.db "SELECT COUNT(*) FROM media_sources;"
sqlite3 /home/concordia/app/news_analysis.db "SELECT COUNT(*) FROM articles;"
sqlite3 /home/concordia/app/news_analysis.db "SELECT COUNT(*) FROM analyses;"
```

### API Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Or use the container management script
./scripts/monitoring/manage_containers.sh health
```

### Web Server Status

```bash
# Check Nginx status
systemctl status nginx

# Test Nginx configuration
nginx -t

# Check SSL certificates
certbot certificates
```

## Scheduled Tasks (Cron Jobs)

The following cron jobs are configured on the server:

1. **Health check** (every 5 minutes): Monitors application health and restarts containers if needed
2. **Container restart** (daily at **00:50 UTC**): Ensures API and Frontend containers are fresh after daily maintenance
3. **Database optimization** (daily at 3:30 AM UTC): Performs SQLite optimization
4. **System report generation** (daily at 8:00 AM UTC): Generates a system status report

### Viewing Cron Jobs

```bash
# View all configured cron jobs
crontab -l
```

### Modifying Cron Jobs

```bash
# Edit cron jobs
crontab -e
```

### Common Cron Jobs

#### Health check every 5 minutes
```crontab
*/5 * * * * /home/concordia/app/scripts/check_health.sh >> /home/concordia/app/logs/monitoring.log 2>&1
```

#### Daily container restart (API & Frontend)
```crontab
# Daily restart for Concordia API and Frontend after maintenance
50 0 * * * cd /home/concordia/app && /usr/bin/docker restart concordia-api concordia-frontend >> /home/concordia/app/logs/cron_restarts.log 2>&1
```

#### Daily database optimization (Example - may be handled by scheduler)
```crontab
# Example: If running separate optimization via cron (check if needed)
30 3 * * * cd /home/concordia/app && docker exec concordia-api python -c "import sqlite3; conn = sqlite3.connect('/app/news_analysis.db'); conn.execute('PRAGMA optimize'); conn.execute('PRAGMA wal_checkpoint(FULL)'); print('✅ Basic optimization complete'); conn.close()" >> /home/concordia/app/logs/db_maintenance_cron.log 2>&1
```

#### System report generation
```crontab
0 8 * * * /home/concordia/app/scripts/monitoring/system_monitor.sh >> /home/concordia/app/logs/daily_report.log 2>&1
```

## Database Management

### Database Backups

Automated daily backups are configured, but you can create manual backups:

```bash
# Create a manual backup
cp /home/concordia/app/news_analysis.db /home/concordia/backups/news_analysis_$(date +%Y%m%d).db
```

### Checking Database Integrity

```bash
# Check database integrity
sqlite3 /home/concordia/app/news_analysis.db "PRAGMA integrity_check;"
```

### Database Optimization

```bash
# Optimize the database
sqlite3 /home/concordia/app/news_analysis.db "PRAGMA optimize;"
sqlite3 /home/concordia/app/news_analysis.db "PRAGMA wal_checkpoint(FULL);"
```

## Updating the Application

When you need to update the application with new code:

```bash
# Go to the application directory
cd /home/concordia/app

# Pull the latest changes
git pull

# Rebuild and restart containers
docker compose down
docker compose build
docker compose up -d

# Check logs for any issues
docker compose logs

# Run the system monitor to verify everything is working
./scripts/monitoring/system_monitor.sh
```

## Troubleshooting Common Issues

### API Not Responding

```bash
# Check API logs
docker logs concordia-api

# Check API container status
docker inspect concordia-api

# Restart API container
docker restart concordia-api
```

### Frontend Issues

```bash
# Check frontend logs
docker logs concordia-frontend

# Restart frontend container
docker restart concordia-frontend

# Verify Nginx configuration
nginx -t
```

### Database Issues

```bash
# Check database logs
cat /home/concordia/app/logs/db_maintenance.log

# Check database size and permissions
ls -la /home/concordia/app/news_analysis.db

# Restore from backup if necessary
# For local file backups (if configured):
# cp /home/concordia/backups/news_analysis_YYYYMMDD.db /home/concordia/app/news_analysis.db
# For Hetzner server backups, use the Cloud Console to restore the server snapshot.
# Remember to re-deploy code changes after a Hetzner restore.
```

### High Disk Usage

If you notice disk space filling up rapidly (`df -h` shows high usage), the most common cause is the accumulation of unused Docker images and build cache from previous deployments.

**Diagnosis:**

```bash
# Check Docker's own disk usage summary
docker system df
```
*Look for high "RECLAIMABLE" percentages for Images and Build Cache.*

**Solution:**

Prune unused Docker resources. This command safely removes dangling images, unused networks, build cache, and (with the `-a` flag) all unused images (not just dangling ones).

```bash
# Prune unused Docker images, build cache, and networks
docker system prune -a -f
```

**Prevention (Optional but Recommended):**

To prevent this from happening regularly, consider adding a weekly cron job to prune Docker resources automatically during off-peak hours.

```bash
# Example: Add via 'crontab -e' to run weekly on Sunday at 4:05 AM
5 4 * * 0 /usr/bin/docker system prune -a -f >> /home/concordia/app/logs/docker_prune.log 2>&1
```

### SSL Certificate Issues

```bash
# Check certificate status
certbot certificates

# Test certificate renewal
certbot renew --dry-run

# Force certificate renewal
certbot renew --force-renewal
```

## Security Best Practices

1. **SSH Access**: Only use SSH key authentication, disable password login
2. **Firewall**: Ensure ufw is properly configured (ports 22, 80, 443 only)
3. **Updates**: Regularly update system packages (`apt update && apt upgrade`)
4. **Log Monitoring**: Regularly check logs for suspicious activity
5. **Backups**: Maintain regular database and system backups

## Hetzner Cloud Console

For server-level management:

1. Access the [Hetzner Cloud Console](https://console.hetzner.cloud/)
2. Navigate to your project and server
3. Use the following features:
   - **Metrics**: Monitor CPU, RAM, disk, and network usage
   - **Backups**: Configure and manage server backups
   - **Snapshots**: Create server snapshots before major changes
   - **Rescue**: Access rescue mode if server becomes inaccessible
   - **Firewall**: Manage firewall rules at the cloud level

## Contact and Support

For issues with the Concordia application, contact:
- Project maintainer: [Your Name and Contact Information]
- Repository: [Repository URL]

For server infrastructure issues, contact:
- Server administrator: [Admin Name and Contact]
- Hetzner Support: [Hetzner Support URL]