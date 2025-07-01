# Concordia: Harmony in the Noise

*Bringing clarity to media bias and narrative analysis*

## Project Overview

Concordia is a sophisticated media analysis platform that collects, processes, and analyzes news articles from diverse sources to uncover narratives, sentiment patterns, and political biases. By leveraging AI-powered analysis, Concordia provides transparent insights into how different media outlets cover the same events.

### Initial Setup

1. Clone the repository
2. Create a .env file with the required variables (look: .env.example)

### Create data and logs directories
./scripts/prepare_db.sh

### Build Docker Images
docker-compose build

### Start the Application
#### Launch all containers using Docker Compose:
docker-compose up -d

#### Stop all containers:
docker-compose down

# Commands

### Initialize database
docker exec -it concordia-api python -c "from backend.src.news_utils import init_database; init_database('/app/news_analysis.db')"

### Remove existing database
rm -f news_analysis.db && ./scripts/prepare_db.sh

### Add media data
docker exec -it concordia-api python -m backend.src.add_media_data

### Collect articles
docker exec -it concordia-api python -m backend.rss_collector

### Analyze articles
docker exec -it concordia-api python -m backend.rss_analyzer

### Vacuum database
docker exec -it concordia-api python -c "from backend.src.news_utils import vacuum_database; vacuum_database('/app/news_analysis.db')"

### Run tests
docker exec -it concordia-api pytest --cov=backend/src backend/tests/

### View specific service logs
docker-compose logs -f api
docker-compose logs -f scheduler
docker-compose logs -f frontend

### Access the application
- Frontend: http://localhost
- API: http://localhost:8000

# Key Features

- **Political Bias Spectrum**: Interactive visualization of media sources across the political spectrum
- **Sentiment Analysis**: Quantitative breakdown of emotional tone in news coverage
- **Narrative Identification**: AI-powered detection of main themes and framing in media coverage
- **Article Explorer**: Searchable repository of analyzed articles with bias and sentiment metrics
- **Dark Mode Interface**: Optimized for extended analysis sessions

## Architecture

Concordia is built with a modern, scalable architecture:

- **Frontend**: React with Tailwind CSS for responsive, elegant UI
- **Backend**: Python FastAPI for efficient, type-safe API endpoints
- **Database**: SQLite for lightweight, portable data storage
- **Analysis Engine**: DeepSeek AI integration for sophisticated content analysis
- **Data Collection**: Modular RSS parsers for reliable article gathering

## Data Sources

The platform currently analyzes content from several major news providers:

- NBC News
- BBC
- Fox News
- Deutsche Welle (DW)
- France 24

## Future Roadmap

- Expanded source coverage including more international outlets
- Advanced visualization tools for temporal trend analysis
- API access for researchers and third-party applications
- Natural language processing improvements for deeper narrative analysis
- Multi-language support for global media coverage

## License

© 2025 Concordia. All rights reserved.

*Harmony in the Noise: Analyzing media bias and narratives across the political spectrum.*

## Legal Disclaimer

Concordia is a news analysis platform that aggregates and analyzes content from various third-party news sources. We do not create, edit, or modify the original news content. The views, opinions, and factual assertions contained in the analyzed news articles are solely those of the original publishers and not of Concordia.

Our use of third-party news content for analysis purposes is protected under fair use doctrine. We respect the intellectual property rights of others and only display limited excerpts of news articles necessary for analysis purposes.

The information provided through our service is for general informational purposes only and should not be construed as legal advice. Users should consult with a qualified legal professional for advice specific to their situation.

## Environment Configuration

This project supports both development and production environments through a simple configuration system.

### Switching Environments

1. **Switch to development mode** (for local development only):
   ```bash
   ./scripts/switch-to-dev.sh
   ```

2. **Switch to production mode** (required for all production deployments):
   ```bash
   ./scripts/switch-to-prod.sh
   ```

3. **Build the application**:
   ```bash
   ./scripts/build.sh
   ```

The application will automatically use the appropriate settings based on the selected environment.

### ⚠️ IMPORTANT: Production Deployment Requirements

**Production mode MUST be enabled before deploying to a production server.**

Failing to enable production mode will result in:
- API connection errors (frontend will try to connect to localhost)
- Incorrect port mappings
- Missing optimizations for production use

### Current Environment

You can check the current environment by looking at `config/environment.js`. The line should read:
```javascript
const ENV = 'production'; // For production deployments
```

### Manual Deployment to Production Server

1. Switch to production mode locally:
   ```bash
   ./scripts/switch-to-prod.sh
   ```

2. Commit changes:
   ```bash
   git add config/environment.js
   git commit -m "Set environment to production for deployment"
   ```

3. Push to repository:
   ```bash
   git push
   ```

4. On production server:
   ```bash
   git pull
   ./scripts/build.sh
   ```

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js (for local development)
- Git

### Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd concordia
   ```

2. Choose environment (development by default):
   ```bash
   # For local development
   ./scripts/switch-to-dev.sh
   
   # For production testing
   ./scripts/switch-to-prod.sh
   ```

3. Build and start the application:
   ```bash
   ./scripts/build.sh
   ```

4. Access the application:
   - Development: http://localhost:3000
   - Production test: http://localhost:8080