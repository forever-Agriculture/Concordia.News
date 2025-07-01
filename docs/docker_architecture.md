# Docker Architecture for Concordia

This document outlines the Docker architecture for the Concordia news sentiment analysis platform, including the current containerization approach, deployment strategy, and future scaling plans.

## Current Architecture

Concordia uses a multi-container Docker architecture to separate concerns and enable independent scaling of components. The system is designed for reliability, maintainability, and cost efficiency.

### Container Structure 
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  API Container  │     │ Scheduler/Worker│     │  Frontend/Nginx │
│  (FastAPI)      │     │  (Collectors &  │     │  (React + Web   │
│  (API Endpoints)│     │   Analyzers)    │     │   Server)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                        │
         └──────────────────────┼────────────────────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │  Shared Volume   │
                      │ (SQLite Database)│
                      └──────────────────┘


### Components

1. **API Container (`concordia-api`)**
   - Built from `Dockerfile.api`
   - Runs FastAPI application exposing REST endpoints
   - Handles requests for articles, analyses, and media sources
   - Direct access to the SQLite database via volume mount
   - Exposed on port 8000

2. **Scheduler/Worker Container (`concordia-scheduler`)**
   - Built from `Dockerfile.scheduler`
   - Runs the main scheduling logic via `scripts/run_scheduler.sh`.
   - Responsible for triggering periodic tasks for data collection, analysis, and maintenance.
   - Shares database access with API container via volume mount.
   - Not exposed to external network.
   - **Scheduled Tasks (Times in UTC):**
       - **Article Collection (`backend.rss_collector.py`):**
           - Runs every 2 hours on even-numbered hours (02, 04, 06, ..., 20, 22).
           - Triggered only if the script checks between XX:00 and XX:05 of these hours.
           - Includes a special pre-analysis collection run starting at 23:45.
           - *Purpose:* Gathers latest articles from configured RSS feeds.
       - **Article Analysis (`backend.rss_analyzer.py`):**
           - Runs once daily.
           - Triggered if the script checks between 00:00 and 00:05.
           - *Purpose:* Performs AI-driven analysis (bias, sentiment, narratives) on recently collected articles.
       - **Database Maintenance (`backend.db_maintenance.py`):**
           - Runs once daily.
           - Triggered immediately after a successful Article Analysis run finishes. The exact start time depends entirely on the duration of the analysis task.
           - *Purpose:* Performs cleanup tasks on the database (e.g., removing old articles, optimizing).
       - **Resource Logging:**
           - Runs continuously in the background within the container.
           - Logs CPU, Memory, and Disk usage to `/app/logs/resources.log` every 15 minutes.

3. **Frontend Container (`concordia-frontend`)**
   - Built from `Dockerfile.frontend`
   - Two-stage build process:
     - Stage 1: Node.js environment for building React application
     - Stage 2: Nginx for serving static assets
   - Communicates with API container via internal network
   - Exposed on port 80


### Data Management

- **SQLite Database**: Mounted as a volume (`./news_analysis.db:/app/news_analysis.db`) to both API and Scheduler containers
- **Data Directory**: Mounted as a volume (`./data:/app/data`) for storing additional data
- **Logs Directory**: Mounted as a volume (`./logs:/app/logs`) for centralized logging

### Working with the database locally for development
#### If the database is in WAL mode, some data might be in the WAL file rather than the main database file. Let's force a checkpoint:

##### Connect to the API container
docker exec -it concordia-api bash

##### Inside the container, run a Python script to checkpoint the database
python -c "import sqlite3; conn = sqlite3.connect('/app/news_analysis.db'); conn.execute('PRAGMA wal_checkpoint(FULL)'); conn.close()"

##### Exit the container
exit


### Networking

- All containers are connected to a custom bridge network (`concordia-network`)
- Only necessary ports are exposed to the host:
  - Port 80 for frontend
  - Port 8000 for API

### Environment Variables

- Stored in `.env` file (not committed to version control)
- Passed to containers via Docker Compose
- Include API keys, configuration parameters, and operational settings

### External Automation

-   **Container Restarts:** An external cron job managed on the host server restarts all Concordia containers daily at **22:30 UTC**.
    -   *Purpose:* Ensures containers are refreshed regularly, apply potential image updates if containers are recreated, and prevent potential long-term drift or memory issues. Note that collection *is* scheduled to run at 22:00 UTC, which should complete before the restart.


## Deployment Process

1. **Preparation**:
   - Run `scripts/prepare_db.sh` to create necessary directories and set permissions
   - Ensure `.env` file is properly configured

2. **Build and Start**:
   - `docker-compose build` to build all images
   - `docker-compose up -d` to start containers in detached mode

3. **Database Initialization**:
   - Initialize database schema
   - Add media sources data

4. **Verification**:
   - Check container status with `docker-compose ps`
   - Verify logs with `docker-compose logs`
   - Access frontend at http://localhost
   - Access API at http://localhost:8000


## Future Scaling Strategy

### Horizontal Scaling with SQLite

While SQLite is typically considered for single-instance deployments, Concordia's architecture allows for horizontal scaling through a read-heavy approach:

1. **Primary-Replica Model**:
   - Primary node handles all write operations
   - Read-only replicas serve query traffic
   - Periodic synchronization from primary to replicas

2. **Implementation Strategy**:
   ```
   ┌─────────────────┐
   │  Primary Node   │
   │ (API + Scheduler)│
   │  (Write Access) │
   └─────────────────┘
            │
            ▼
   ┌─────────────────┐
   │ SQLite Database │
   │    (Primary)    │
   └─────────────────┘
            │
            ▼
   ┌─────────────────┐
   │ Synchronization │
   │     Process     │
   └─────────────────┘
            │
            ▼
   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
   │  Read Replica 1 │     │  Read Replica 2 │     │  Read Replica 3 │
   │  (API Only)     │     │  (API Only)     │     │  (API Only)     │
   └─────────────────┘     └─────────────────┘     └─────────────────┘
   ```

3. **Synchronization Options**:
   - File-based replication using rsync or similar tools
   - SQLite's Online Backup API for atomic snapshots
   - WAL (Write-Ahead Logging) mode for concurrent read/write operations

4. **Load Balancing**:
   - Nginx or other load balancer to distribute read queries across replicas
   - Health checks to ensure replicas are up-to-date and responsive

### Database Evolution Path

As the system grows, a migration path to more scalable database solutions is planned:

1. **Short-term (Current)**: SQLite with volume mounts
   - Advantages: Simplicity, zero configuration, file-based replication
   - Limitations: scaling nuances

2. **Medium-term**: SQLite with read replicas
   - Advantages: Horizontal read scaling, maintained simplicity

## Monitoring and Maintenance

Current monitoring is log-based, but future enhancements will include:

1. **Health Checks**:
   - Already implemented in API container
   - To be extended to all containers

2. **Metrics Collection**:
   - Prometheus integration for container metrics
   - Custom metrics for application performance

3. **Automated Backups**:
   - Scheduled database backups to persistent storage
   - Retention policies for backup management

4. **Logging Infrastructure**:
   - ELK stack (Elasticsearch, Logstash, Kibana) or similar
   - Centralized log collection and analysis


## Conclusion

Concordia's Docker architecture provides a solid foundation for the current application needs while allowing for future growth. The separation of concerns between API, scheduler, and frontend containers enables independent scaling and maintenance. The SQLite database, while simple, offers a pragmatic approach to data storage with a clear path to more scalable solutions as the application evolves.

By leveraging Docker's containerization benefits, Concordia achieves reliability, reproducibility, and deployment simplicity while maintaining the flexibility to adapt to changing requirements and scale.

