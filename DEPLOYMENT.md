# Concordia Deployment Notes

- Server IP: 157.180.73.159
- Domain: concordia.news
- Deployment Date: [Today's Date]

## Services
- Frontend: https://concordia.news
- API: https://concordia.news/api

## Maintenance & Scheduling
- **Internal Scheduler (in Docker):**
    - Collection: Every even hour (02:00, 04:00,... 22:00 UTC) & Daily at 23:15 UTC
    - Analysis: Daily at 23:30 UTC (DeepSeek off-peak)
- **Host Cron Jobs:**
    - Health checks: Every 5 minutes
    - Daily container restart: 01:31 UTC
    - Daily database optimization: 02:30 UTC
- Logs stored in /home/concordia/app/logs/

## Updates
To update the application:
1. Pull changes: `git pull`
2. Rebuild containers: `docker compose build`
3. Restart containers: `docker compose down && docker compose up -d`
