# docs/database.md

# Database Documentation: `news_analysis.db`

This document provides a detailed overview of the SQLite database (`news_analysis.db`) used in Concordia. The database stores news articles, their AI-generated analyses, and media source metadata, enabling the application to collect, analyze, present, and maintain data for insights on media narratives, sentiment, and biases.

## Overview

The `news_analysis.db` database is a SQLite database designed for cost efficiency, reliability, and scalability in the News Sentiment Analysis project. It supports the following key functionalities:

- **Article Storage**: Collects and stores news articles from RSS feeds of various sources (e.g., Fox News, BBC, NBC, DW).
- **Analysis Results**: Stores AI-generated analysis results (e.g., narratives, sentiment, bias) for articles, performed using the DeepSeek API.
- **Media Source Metadata**: Maintains metadata for media sources, including third-party bias ratings and calculated biases.
- **Relationships**: Uses foreign keys to link articles, analyses, and media sources to a central `sources` table for consistency.
- **Maintenance**: Supports scheduled maintenance tasks like vacuuming to optimize performance and reclaim space.

The database schema is defined and managed through several modules:

- `backend/src/news_utils.py`: Initializes the database, defines the `sources`, `articles`, and `analyses` tables, and provides functions for database operations (e.g., connection, vacuuming).
- `backend/src/media_utils.py`: Defines the `media_sources` table and provides functions for managing media source data.
- `backend/api.py`: Uses the database to serve article, analysis, and media source data via FastAPI endpoints.
- `backend/db_maintenance.py`: Performs scheduled maintenance tasks like vacuuming to optimize the database.

## Database Schema

The database consists of four main tables: `sources`, `articles`, `analyses`, and `media_sources`. Below is the schema for each table, including columns, data types, constraints, and indexes.

### 1. `sources` Table

The `sources` table serves as the central reference for news sources, mapping source names to unique identifiers (`source_id`) used across other tables.

#### Schema

| Column       | Type    | Constraints               | Description                                      |
|--------------|---------|---------------------------|--------------------------------------------------|
| `source_id`  | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier for each news source.          |
| `name`       | TEXT    | NOT NULL UNIQUE           | Name of the news source (e.g., "fox_news", "bbc"). |
| `created_at` | TEXT    | DEFAULT CURRENT_TIMESTAMP | Timestamp of when the source was added (ISO 8601 format, e.g., "2025-03-03 12:00:00"). |

#### Notes

- The `source_id` is auto-incremented to ensure unique identifiers for each source.
- The `name` column is lowercase and underscore-separated (e.g., "fox_news", "nbc"), enforced by validation in the `MediaSource` model (`src/models.py`).
- The table is initialized in both `src/news_utils.py` and `src/media_utils.py`, ensuring consistency across modules.

#### Usage

- Used in `rss_collector.py` to insert sources before saving articles.
- Used in `rss_analyzer.py` to query articles by source and save analysis results.
- Used in `src/media_utils.py` to link `media_sources` entries to their corresponding source names.
- Used in `api.py` to join with other tables (`articles`, `analyses`, `media_sources`) for serving data through API endpoints.

---

### 2. `articles` Table

The `articles` table stores news articles collected from RSS feeds, including raw and cleaned content, metadata, and publication details.

#### Schema

| Column            | Type    | Constraints                                              | Description                                      |
|-------------------|---------|----------------------------------------------------------|--------------------------------------------------|
| `id`              | TEXT    | PRIMARY KEY                                              | Unique identifier for the article (MD5 hash of title and description). |
| `source_id`       | INTEGER | NOT NULL, FOREIGN KEY (references `sources(source_id)` ON DELETE RESTRICT) | ID of the news source from the `sources` table. |
| `raw_title`       | TEXT    |                                                          | Original title of the article.                   |
| `raw_description` | TEXT    |                                                          | Original description of the article.             |
| `clean_content`   | TEXT    |                                                          | Cleaned and normalized article content (title + description, HTML removed). |
| `categories`      | TEXT    |                                                          | Comma-separated list of categories (e.g., "Politics,World"). |
| `link`            | TEXT    |                                                          | URL to the full article.                         |
| `created_at`      | TEXT    | DEFAULT CURRENT_TIMESTAMP                                | Timestamp of when the article was added (ISO 8601 format). |
| `publication_date`| TEXT    | NOT NULL                                                 | Publication date in unified UTC format ("YYYY-MM-DD HH:MM:SS"). |

#### Indexes

- `idx_articles_source_id`: On `source_id` to optimize queries filtering by source.
- `idx_articles_publication_date`: On `publication_date` to optimize date-based queries (e.g., in `rss_analyzer.py`).

#### Notes

- The `id` is generated as an MD5 hash of the article's title and description to ensure uniqueness (`rss_collector.py`).
- The `clean_content` is generated by `clean_article` in `src/news_utils.py`, removing HTML entities, tags, and excessive whitespace.
- The `publication_date` is standardized to UTC using `unify_date_format` (`src/news_utils.py`).
- The foreign key constraint ensures referential integrity with the `sources` table.

#### Usage

- Populated by `rss_collector.py` during article collection.
- Queried by `rss_analyzer.py` to fetch articles for analysis (e.g., articles from yesterday).
- Queried by the FastAPI endpoint `/articles` in `api.py` to serve article data to the frontend, with optional filters for `source` and `date`.

---

### 3. `analyses` Table

The `analyses` table stores AI-generated analysis results for articles, including narratives, sentiment, bias, and promoted values, aggregated by source and date.

#### Schema

| Column                          | Type    | Constraints                                              | Description                                      |
|---------------------------------|---------|----------------------------------------------------------|--------------------------------------------------|
| `id`                            | TEXT    | PRIMARY KEY                                              | Unique identifier for the analysis (MD5 hash).   |
| `source_id`                     | INTEGER | NOT NULL, FOREIGN KEY (references `sources(source_id)` ON DELETE RESTRICT) | ID of the news source from the `sources` table. |
| `analysis_date`                 | TEXT    | NOT NULL                                                 | Date of the analysis ("YYYY-MM-DD", e.g., "2025-03-02"). |
| `numbers_of_articles`           | INTEGER | NOT NULL                                                 | Number of articles analyzed.                     |
| `main_narrative_theme_1`        | TEXT    | DEFAULT NULL                                             | First identified narrative theme (e.g., "Conflict"). |
| `main_narrative_coverage_1`     | REAL    | DEFAULT 0.0                                              | Coverage percentage of the first theme (0.0–100.0). |
| `main_narrative_examples_1`     | TEXT    | DEFAULT NULL                                             | Comma-separated article titles exemplifying the first theme. |
| `main_narrative_theme_2`        | TEXT    | DEFAULT NULL                                             | Second narrative theme.                          |
| `main_narrative_coverage_2`     | REAL    | DEFAULT 0.0                                              | Coverage percentage of the second theme.         |
| `main_narrative_examples_2`     | TEXT    | DEFAULT NULL                                             | Examples for the second theme.                   |
| `main_narrative_theme_3`        | TEXT    | DEFAULT NULL                                             | Third narrative theme.                           |
| `main_narrative_coverage_3`     | REAL    | DEFAULT 0.0                                              | Coverage percentage of the third theme.          |
| `main_narrative_examples_3`     | TEXT    | DEFAULT NULL                                             | Examples for the third theme.                    |
| `main_narrative_theme_4`        | TEXT    | DEFAULT NULL                                             | Fourth narrative theme.                          |
| `main_narrative_coverage_4`     | REAL    | DEFAULT 0.0                                              | Coverage percentage of the fourth theme.         |
| `main_narrative_examples_4`     | TEXT    | DEFAULT NULL                                             | Examples for the fourth theme.                   |
| `main_narrative_theme_5`        | TEXT    | DEFAULT NULL                                             | Fifth narrative theme.                           |
| `main_narrative_coverage_5`     | REAL    | DEFAULT 0.0                                              | Coverage percentage of the fifth theme.          |
| `main_narrative_examples_5`     | TEXT    | DEFAULT NULL                                             | Examples for the fifth theme.                    |
| `main_narrative_confidence`     | REAL    | DEFAULT 0.0                                              | Confidence in narrative analysis (0.8–1.0).      |
| `sentiment_positive_percentage` | REAL    | DEFAULT 0.0                                              | Percentage of positive sentiment (0.0–100.0).    |
| `sentiment_negative_percentage` | REAL    | DEFAULT 0.0                                              | Percentage of negative sentiment (0.0–100.0).    |
| `sentiment_neutral_percentage`  | REAL    | DEFAULT 0.0                                              | Percentage of neutral sentiment (0.0–100.0).     |
| `sentiment_confidence`          | REAL    | DEFAULT 0.0                                              | Confidence in sentiment analysis (0.8–1.0).      |
| `bias_political_score`          | REAL    | DEFAULT 0.0                                              | Political bias score (-5.0 to +5.0).             |
| `bias_political_leaning`        | TEXT    | DEFAULT NULL                                             | Textual bias label (e.g., "Center-Left").        |
| `bias_supporting_evidence`      | TEXT    | DEFAULT NULL                                             | Evidence supporting the bias assessment.         |
| `bias_confidence`               | REAL    | DEFAULT 0.0                                              | Confidence in bias analysis (0.8–1.0).           |
| `values_promoted_value_1`       | TEXT    | DEFAULT NULL                                             | First promoted value (e.g., "Public Safety").    |
| `values_promoted_examples_1`    | TEXT    | DEFAULT NULL                                             | Examples for the first value.                    |
| `values_promoted_value_2`       | TEXT    | DEFAULT NULL                                             | Second promoted value.                           |
| `values_promoted_examples_2`    | TEXT    | DEFAULT NULL                                             | Examples for the second value.                   |
| `values_promoted_value_3`       | TEXT    | DEFAULT NULL                                             | Third promoted value.                            |
| `values_promoted_examples_3`    | TEXT    | DEFAULT NULL                                             | Examples for the third value.                    |
| `values_promoted_confidence`    | REAL    | DEFAULT 0.0                                              | Confidence in values analysis (0.8–1.0).         |
| `created_at`                    | TEXT    | DEFAULT CURRENT_TIMESTAMP                                | Timestamp of when the analysis was added (ISO 8601 format). |

#### Indexes

- `idx_analyses_source_id`: On `source_id` to optimize queries filtering by source.
- `idx_analyses_analysis_date`: On `analysis_date` to optimize date-based queries.

#### Notes

- The `id` is generated as an MD5 hash of the source name and timestamp (`rss_analyzer.py`).
- The `analysis_date` is derived from the DeepSeek API response and reformatted to "YYYY-MM-DD" (`rss_analyzer.py`).
- Narrative, sentiment, bias, and values fields are populated by the DeepSeek API via `AIAnalyzer` (`src/ai_processor.py`).
- The foreign key constraint ensures referential integrity with the `sources` table.

#### Usage

- Populated by `rss_analyzer.py` after analyzing articles.
- Queried by the FastAPI endpoint `/analyses` in `api.py` to serve analysis results to the frontend, with optional filters for `source` and `date`.

---

### 4. `media_sources` Table

The `media_sources` table stores metadata for media sources, including third-party bias ratings, calculated biases, and ownership details.

#### Schema

| Column                            | Type    | Constraints                                              | Description                                      |
|-----------------------------------|---------|----------------------------------------------------------|--------------------------------------------------|
| `id`                              | INTEGER | PRIMARY KEY AUTOINCREMENT                                | Unique identifier for the media source.          |
| `name`                            | TEXT    | UNIQUE NOT NULL                                          | Name of the media source (e.g., "NBC News").     |
| `source_id`                       | INTEGER | NOT NULL, FOREIGN KEY (references `sources(source_id)` ON DELETE RESTRICT) | ID of the news source from the `sources` table. |
| `country`                         | TEXT    | NOT NULL                                                 | Country of origin (e.g., "USA").                 |
| `flag_emoji`                      | TEXT    | NOT NULL                                                 | Unicode emoji flag (e.g., "🇺🇸").                |
| `logo_url`                        | TEXT    | NOT NULL                                                 | URL to the media source's logo.                  |
| `founded_year`                    | INTEGER |                                                          | Year the source was founded (optional).          |
| `website`                         | TEXT    | NOT NULL                                                 | Official website URL.                            |
| `description`                     | TEXT    |                                                          | Brief description of the media source (optional). |
| `owner`                           | TEXT    |                                                          | Owning entity (e.g., "Comcast Corporation").     |
| `ownership_category`              | TEXT    |                                                          | Ownership type (e.g., "Large Media Groups").     |
| `rationale_for_ownership`         | TEXT    |                                                          | Reasoning for ownership classification.          |
| `calculated_bias`                 | TEXT    |                                                          | Calculated bias label (e.g., "Lean Left").       |
| `calculated_bias_score`           | REAL    |                                                          | Calculated bias score (-5.0 to +5.0).            |
| `bias_confidence`                 | REAL    | DEFAULT 0.0                                              | Confidence in the calculated bias (0.0–1.0).     |
| `last_updated`                    | TEXT    |                                                          | Timestamp of the last update (UTC).               |
| `ad_fontes_bias`                  | REAL    |                                                          | Ad Fontes Media bias score (-5.0 to +5.0).       |
| `ad_fontes_reliability`           | REAL    |                                                          | Ad Fontes reliability score (0.0–1.0).           |
| `ad_fontes_rating_url`            | TEXT    |                                                          | URL to Ad Fontes rating details.                 |
| `ad_fontes_date_rated`            | TEXT    |                                                          | Date of Ad Fontes rating ("YYYY-MM-DD").         |
| `allsides_bias`                   | REAL    |                                                          | AllSides bias score (-5.0 to +5.0).              |
| `allsides_reliability`            | REAL    |                                                          | AllSides reliability score (0.0–1.0).            |
| `allsides_rating_url`             | TEXT    |                                                          | URL to AllSides rating details.                  |
| `allsides_date_rated`             | TEXT    |                                                          | Date of AllSides rating ("YYYY-MM-DD").          |
| `media_bias_fact_check_bias`      | REAL    |                                                          | Media Bias/Fact Check bias score (-5.0 to +5.0). |
| `media_bias_fact_check_reliability` | REAL  |                                                          | Media Bias/Fact Check reliability (0.0–1.0).     |
| `media_bias_fact_check_rating_url` | TEXT   |                                                          | URL to Media Bias/Fact Check rating details.     |
| `media_bias_fact_check_date_rated` | TEXT   |                                                          | Date of Media Bias/Fact Check rating ("YYYY-MM-DD"). |

#### Notes

- The `source_id` links to the `sources` table, ensuring consistency with article and analysis data.
- Fields like `calculated_bias` and `calculated_bias_score` are computed by `calculate_media_bias` (`src/media_utils.py`) based on third-party ratings.
- The `ownership_category` is validated to be one of: "Large Media Groups", "Private Investment Firms", "Individual Ownership", "Government", "Corporate Entities", "Independently Operated", "Unclassified", or "Unverified" (`src/models.py`).
- The `last_updated` timestamp uses UTC.

#### Usage

- Populated by `src/add_media_data.py` when initializing media sources.
- Updated by `calculate_media_bias` in `src/media_utils.py` when recalculating biases.
- Queried by the FastAPI endpoint `/media_sources` in `api.py` to serve media source data to the frontend.

---

## Relationships

The database uses foreign keys to establish relationships between tables:

- **`sources` to `articles`**: The `source_id` in `articles` references `sources(source_id)`, linking each article to its source. The `ON DELETE RESTRICT` constraint prevents deleting a source if it has associated articles.
- **`sources` to `analyses`**: The `source_id` in `analyses` references `sources(source_id)`, linking each analysis to its source. The `ON DELETE RESTRICT` constraint applies here as well.
- **`sources` to `media_sources`**: The `source_id` in `media_sources` references `sources(source_id)`, linking each media source to its identifier in the `sources` table.

These relationships ensure data consistency across the application, with `sources` acting as the central hub.

## Constraints and Validation

### Primary Keys

- `sources(source_id)`: Auto-incremented integer.
- `articles(id)`: MD5 hash of article title and description.
- `analyses(id)`: MD5 hash of source name and timestamp.
- `media_sources(id)`: Auto-incremented integer.

### Foreign Keys

- `articles(source_id)` → `sources(source_id)`
- `analyses(source_id)` → `sources(source_id)`
- `media_sources(source_id)` → `sources(source_id)`

### Uniqueness Constraints

- `sources(name)`: Ensures no duplicate source names.
- `media_sources(name)`: Ensures no duplicate media source names.

### Validation (via `MediaSource` Model in `src/models.py`)

- `source`: Must be lowercase with underscores (e.g., "fox_news").
- `flag_emoji`: Must be a valid Unicode emoji.
- `ownership_category`: Must be one of the predefined categories.
- Bias scores (`ad_fontes_bias`, `allsides_bias`, etc.): Must be between -5.0 and +5.0.
- Reliability scores (`ad_fontes_reliability`, etc.): Must be between 0.0 and 1.0.

## Database Management Utilities

The application includes utilities for managing the database, defined in `src/news_utils.py`, `src/media_utils.py`, and `db_maintenance.py`.

### From `src/news_utils.py`

- **`init_database(db_path)`**:
  - Initializes the database, creating the `sources`, `articles`, and `analyses` tables.
  - Adds indexes for performance.
  - Calls `init_media_database` to create the `media_sources` table.
  - Logs operations to `logs/db_maintenance.log`.

- **`db_connection(db_path)`**:
  - Establishes a SQLite connection with dictionary-like row access (`row_factory = sqlite3.Row`).
  - Used across the application for database queries.

- **`vacuum_database(db_path)`**:
  - Performs a `VACUUM` operation to optimize the database, reclaiming unused space and reducing fragmentation.
  - Logs success or failure to `logs/db_maintenance.log`.

- **`ensure_log_directory()`**:
  - Ensures the `logs` directory exists and is writable for logging database operations.

### From `src/media_utils.py`

- **`init_media_database(db_path)`**:
  - Initializes the `media_sources` table, ensuring all required columns are present.
  - Dynamically adds missing columns if the table already exists.

- **`save_media_source(media, db_path)`**:
  - Saves or updates a `MediaSource` instance in the `media_sources` table.
  - Automatically sets `last_updated` to the current UTC time.

- **`get_media_source(name, db_path)`**:
  - Retrieves a `MediaSource` instance by name, returning a Pydantic model.

- **`get_all_media_sources(db_path)`**:
  - Retrieves all media sources as a list of `MediaSource` instances.

### From `db_maintenance.py`

- **Scheduled Vacuuming**:
  - Uses the `schedule` library to run `vacuum_database` weekly on Sundays at midnight UTC.
  - Logs operations to `logs/db_maintenance.log` with emoji-enhanced feedback (e.g., 🛠️ for success, ❌ for errors).
  - Ensures continuous operation until stopped by the user (Ctrl+C).

## Usage in the Application

The database is integral to the application's workflow:

- **Article Collection (`rss_collector.py`)**:
  - Inserts sources into the `sources` table if they don't exist.
  - Saves articles to the `articles` table after cleaning and deduplication.
  - Verifies sources against the `media_sources` table before collection.

- **Article Analysis (`rss_analyzer.py`)**:
  - Queries the `articles` table for articles from yesterday (based on `publication_date`).
  - Saves analysis results to the `analyses` table, linked to the appropriate `source_id`.

- **API Endpoints (`api.py`)**:
  - The `/articles` endpoint queries the `articles` table to serve article data, with optional filters for `source` and `date`.
  - The `/analyses` endpoint queries the `analyses` table to serve analysis results, with optional filters for `source` and `date`.
  - The `/media_sources` endpoint queries the `media_sources` table to serve media source metadata.

- **Database Maintenance (`db_maintenance.py`)**:
  - Periodically vacuums the database to optimize performance and reclaim space.
  - Uses `vacuum_database` from `src/news_utils.py` to execute the maintenance task.

## Performance and Optimization

- **Indexes**: Added to frequently queried columns (`source_id`, `publication_date`, `analysis_date`) to improve query performance.
- **WAL Mode**: Enabled via `PRAGMA journal_mode=WAL` in `init_database` for better concurrency and performance.
- **VACUUM**: The `vacuum_database` function, scheduled via `db_maintenance.py`, helps maintain database efficiency by reducing fragmentation.
- **Data Cleaning**: Articles are cleaned to a maximum of 400 characters to optimize DeepSeek API costs (~$0.0128 for 92 articles with caching).

## Logging

Database operations are logged to `logs/db_maintenance.log` with the following levels:

- **INFO**: Successful operations (e.g., database initialization, vacuuming, article saving).
- **ERROR**: Failures (e.g., database connection errors, schema creation issues).
- Console output includes emoji-enhanced feedback (e.g., 🛠️ for initialization, ❌ for errors).

## Working with the database locally for development
### If the database is in WAL mode, some data might be in the WAL file rather than the main database file. Let's force a checkpoint:

#### Connect to the API container
docker exec -it concordia-api bash

#### Inside the container, run a Python script to checkpoint the database
python -c "import sqlite3; conn = sqlite3.connect('/app/news_analysis.db'); conn.execute('PRAGMA wal_checkpoint(FULL)'); conn.close()"

#### Exit the container
exit

## Future Improvements

- **Add More Indexes**: Based on query performance analysis (e.g., on `categories` in `articles`).
- **Schema Evolution**: Add support for additional metadata (e.g., article authors, sentiment trends over time).
- **Backup Mechanism**: Implement automated backups to prevent data loss.

## Scheduling and Monitoring

The Concordia platform uses a sophisticated scheduling system to collect and analyze news articles efficiently:

### Collection and Analysis Schedule (Inside `concordia-scheduler` container)

- **Article Collection**:
  - Runs during the first 5 minutes of every even hour, *except* midnight (02:00, 04:00, ..., 22:00 UTC).
  - Special pre-analysis collection window: **23:15 - 23:29 UTC** daily.
  - Each collection looks back 2 hours and 15 minutes (configurable in `config/time_settings.yaml`) to prevent missing articles due to timing variations.

- **Article Analysis**:
  - Runs once daily, starting between **23:30 and 23:34 UTC**.
  - Uses the freshest data, including articles gathered during the 23:15 collection.
  - Aligned with DeepSeek API off-peak hours (16:30-00:30 UTC) for cost savings.

- **Database Maintenance (Internal)**:
  - Currently **skipped** within the scheduler script. Optimization is handled by a host cron job.

This schedule ensures:
1. Regular collection of fresh articles throughout the day.
2. A dedicated collection right before analysis for current data.
3. Overlapping lookback periods to prevent missing articles.
4. No database contention between collection and analysis processes.
5. Efficient use of system resources and API cost optimization.

### Host Server Cron Jobs

These jobs run directly on the host machine:

- **Health Checks**: Runs **every 5 minutes** (`scripts/check_health.sh`). Verifies container status and basic API health. Logs to `logs/monitoring.log`.
- **Container Restart**: Runs **daily at 01:31 UTC**. Restarts all application containers.
- **Database Optimization**: Runs **daily at 02:30 UTC**. Executes `PRAGMA optimize` and `PRAGMA wal_checkpoint(FULL)` on the database. Logs to `logs/db_maintenance.log`.