# backend/src/news_utils.py
"""
Utilities for news analysis database management, data cleaning, and date handling.

This module provides functions to initialize and connect to a SQLite database (`news_analysis.db`),
clean article text, prepare data for AI analysis, remove duplicates, unify date formats, and optimize
the database with VACUUM. It supports the news sentiment analysis project by ensuring data consistency,
performance, and cost efficiency (e.g., 400 chars/article, leveraging DeepSeek's caching for ~$0.0128
for 92 articles). Logs are written to `logs/db_maintenance.log` with INFO level, and console output
uses emojis for user feedback (e.g., 🛠️, ❌). Relies on SQLite, dateutil, BeautifulSoup, and logging,
assuming UTC for date handling.

Dependencies:
    - sqlite3: For database operations.
    - dateutil: For date parsing and unification.
    - BeautifulSoup (bs4): For HTML cleaning.
    - logging: For tracking operations.

Usage:
    >>> from src.news_utils import init_database, clean_article, vacuum_database
    >>> init_database()
    🛠️ Initialized database at news_analysis.db at 2025-02-26 22:45:00
    >>> cleaned, stats = clean_article({'title': 'News', 'description': '<p>Content</p>'})
"""

import html
import logging
import os
import random
import re
import sqlite3
from datetime import datetime

import dateutil
import dateutil.parser
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

# Configure logging to write INFO and ERROR messages to logs/db_maintenance.log
logging.basicConfig(
    level=logging.INFO,
    filename="logs/db_maintenance.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_database(db_path: str = "news_analysis.db") -> None:
    """
    Initialize the SQLite database with sources, articles, and analyses tables.

    Creates the database schema with tables for sources, articles, and analyses, including
    indexes for performance. Ensures sources table exists for relations, articles and analyses
    use source_id for foreign key constraints, and analyses includes bias_political_score.
    Also initializes the media_sources table by calling init_media_database.
    Logs initialization details with timestamps in UTC.

    Args:
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        None: Updates the database schema and logs the operation.

    Raises:
        sqlite3.Error: If database initialization fails due to disk I/O or other issues.

    Example:
        >>> init_database()
        🛠️ Initialized database at news_analysis.db at 2025-02-26 22:45:00
    """
    ensure_log_directory()
    try:
        # Verify write access to db_path directory
        db_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "."
        if not os.access(db_dir, os.W_OK):
            raise PermissionError(
                f"Cannot write to directory {db_dir} for database {db_path}"
            )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Base configuration - enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Performance optimizations for high load
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
        cursor.execute("PRAGMA temp_store=MEMORY")   # Store temporary tables in memory
        cursor.execute("PRAGMA mmap_size=30000000000")  # Memory-mapped I/O (30GB limit)
        cursor.execute("PRAGMA page_size=4096")      # Optimal page size for most SSDs
        cursor.execute("PRAGMA cache_size=-64000")   # 64MB cache (negative means KB)
        cursor.execute("PRAGMA foreign_keys=ON")     # Enforce referential integrity
        cursor.execute("PRAGMA busy_timeout=60000")  # 60-second timeout on busy database
        cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")  # Enable incremental vacuuming

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create articles table with source_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                source_id INTEGER NOT NULL,
                raw_title TEXT,
                raw_description TEXT,
                clean_content TEXT,
                categories TEXT,
                link TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                publication_date TEXT NOT NULL,  -- Unified format: YYYY-MM-DD HH:MM:SS in UTC
                FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE RESTRICT
            )
        """
        )

        # Create analyses table with source_id and bias_political_score
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                source_id INTEGER NOT NULL,
                analysis_date TEXT NOT NULL,
                numbers_of_articles INTEGER NOT NULL,
                main_narrative_theme_1 TEXT DEFAULT NULL,
                main_narrative_coverage_1 REAL DEFAULT 0.0,
                main_narrative_examples_1 TEXT DEFAULT NULL,
                main_narrative_theme_2 TEXT DEFAULT NULL,
                main_narrative_coverage_2 REAL DEFAULT 0.0,
                main_narrative_examples_2 TEXT DEFAULT NULL,
                main_narrative_theme_3 TEXT DEFAULT NULL,
                main_narrative_coverage_3 REAL DEFAULT 0.0,
                main_narrative_examples_3 TEXT DEFAULT NULL,
                main_narrative_theme_4 TEXT DEFAULT NULL,
                main_narrative_coverage_4 REAL DEFAULT 0.0,
                main_narrative_examples_4 TEXT DEFAULT NULL,
                main_narrative_theme_5 TEXT DEFAULT NULL,
                main_narrative_coverage_5 REAL DEFAULT 0.0,
                main_narrative_examples_5 TEXT DEFAULT NULL,
                main_narrative_confidence REAL DEFAULT 0.0,
                sentiment_positive_percentage REAL DEFAULT 0.0,
                sentiment_negative_percentage REAL DEFAULT 0.0,
                sentiment_neutral_percentage REAL DEFAULT 0.0,
                sentiment_confidence REAL DEFAULT 0.0,
                bias_political_score REAL DEFAULT 0.0,
                bias_political_leaning TEXT DEFAULT NULL,
                bias_supporting_evidence TEXT DEFAULT NULL,
                bias_confidence REAL DEFAULT 0.0,
                values_promoted_value_1 TEXT DEFAULT NULL,
                values_promoted_examples_1 TEXT DEFAULT NULL,
                values_promoted_value_2 TEXT DEFAULT NULL,
                values_promoted_examples_2 TEXT DEFAULT NULL,
                values_promoted_value_3 TEXT DEFAULT NULL,
                values_promoted_examples_3 TEXT DEFAULT NULL,
                values_promoted_confidence REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE RESTRICT
            )
        """
        )

        # Add indexes for articles
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles (source_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_articles_publication_date ON articles (publication_date)"
        )

        # Add indexes for analyses
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_source_id ON analyses (source_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_analysis_date ON analyses (analysis_date)"
        )

        conn.commit()
        conn.close()

        # Initialize media_sources table (import here to avoid circular import)
        from backend.src.media_utils import init_media_database

        init_media_database(db_path)

        kyiv_time = datetime.now(dateutil.tz.UTC)
        logger.info(f"🛠️ Initialized database at {db_path} at {kyiv_time}")
        print(
            f"🛠️ Initialized database at {db_path} at {kyiv_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database {db_path}: {str(e)}")
        raise sqlite3.Error(f"Failed to initialize database {db_path}: {str(e)}")
    except PermissionError as e:
        logger.error(str(e))
        raise


def db_connection(db_path: str = "news_analysis.db") -> sqlite3.Connection:
    """
    Establishes an optimized connection to the SQLite database.

    Returns a SQLite connection configured with performance-optimized PRAGMAs and
    dictionary-like row access for high-load environments.
    
    Args:
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        sqlite3.Connection: A database connection object for queries.

    Raises:
        sqlite3.Error: If the database connection fails.

    Example:
        >>> conn = db_connection()
        >>> cursor = conn.cursor()
        >>> cursor.execute('SELECT * FROM articles LIMIT 1')
        >>> row = cursor.fetchone()
        >>> print(row['source_id'])
        1
    """
    conn = sqlite3.connect(db_path, timeout=60.0)  # Add 60-second connection timeout
    conn.row_factory = sqlite3.Row
    
    # Apply performance optimizations to this connection
    conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
    conn.execute("PRAGMA temp_store=MEMORY")   # Store temporary tables in memory
    conn.execute("PRAGMA cache_size=-64000")   # 64MB cache (negative means KB)
    conn.execute("PRAGMA foreign_keys=ON")     # Enforce referential integrity
    conn.execute("PRAGMA busy_timeout=60000")  # 60-second timeout on busy database
    
    return conn


def get_random_headers() -> dict:
    """
    Generates a random set of HTTP headers with diverse user agents and common
    browser headers to mimic real browsers more effectively.

    Returns a dictionary of headers, including a randomly selected user agent
    and typical browser headers, to reduce the likelihood of being blocked by
    servers sensitive to automated requests.

    Returns:
        dict: HTTP headers with keys like 'User-Agent', 'Accept', 'Accept-Language', etc.

    Example:
        >>> headers = get_random_headers()
        >>> print(headers['User-Agent'])
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...'
        >>> print(headers['Accept'])
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    """
    user_agents = [
        # Desktop - Windows Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", # Win 11
        # Desktop - Windows Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        # Desktop - Windows Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.51",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.97",
        # Desktop - macOS Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Desktop - macOS Firefox
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
        # Desktop - macOS Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        # Desktop - Linux Chrome/Firefox
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        # Mobile - Android Chrome
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.113 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.40 Mobile Safari/537.36", # Samsung S23 Ultra
        # Mobile - iOS Safari
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
        # --- Additional User Agents ---
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 OPR/95.0.0.0", # Opera
        "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36", # ChromeOS
    ]
    headers = {
        "User-Agent": random.choice(user_agents),
        # Updated Accept header to include newer image types and signed-exchange
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        # Keep common language preference
        "Accept-Language": "en-US,en;q=0.9", # Prioritize US English slightly
        # Keep standard encoding preferences
        "Accept-Encoding": "gzip, deflate, br",
        # Keep other common browser headers
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        # Add Cache-Control to suggest freshness preference
        "Cache-Control": "max-age=0",
    }
    return headers


def clean_article(article: dict) -> tuple[str, dict]:
    """
    Cleans and normalizes article text by removing HTML entities, tags, and excessive whitespace.

    Processes article titles and descriptions, unescaping HTML entities, stripping HTML tags,
    and normalizing whitespace for AI processing. Tracks cleaning stats for monitoring.

    Args:
        article (dict): A dictionary containing article data with 'title' and 'description' keys.

    Returns:
        tuple[str, dict]: A tuple of (cleaned_text, stats), where cleaned_text is the normalized
                         content and stats tracks operations (html_entities, html_tags, whitespace_fixes).

    Example:
        >>> article = {'title': 'Ukraine & Russia', 'description': '<p>War...</p>'}
        >>> cleaned, stats = clean_article(article)
        >>> print(cleaned)
        'Ukraine & Russia. War...'
        >>> print(stats)
        {'html_entities': 1, 'html_tags': 1, 'whitespace_fixes': 0}
    """
    stats = {"html_entities": 0, "html_tags": 0, "whitespace_fixes": 0}
    content = f"{article.get('title', '')}. {article.get('description', '')}"
    decoded_content = html.unescape(content)
    stats["html_entities"] = len(re.findall(r"&\w+;", content))
    soup = BeautifulSoup(decoded_content, "html.parser")
    clean_text = soup.get_text()
    stats["html_tags"] = len(soup.find_all())
    cleaned_text = re.sub(r"\s+", " ", clean_text).strip()
    stats["whitespace_fixes"] = len(clean_text.split()) - len(cleaned_text.split())
    return cleaned_text, stats


def prepare_ai_input(cleaned_article: str, categories: list[str] = None) -> dict:
    """
    Prepares article data for AI analysis by structuring content and metadata.

    Formats cleaned article text and optional categories into a dictionary suitable
    for input into the DeepSeek AI API, ensuring compatibility with narrative analysis.

    Args:
        cleaned_article (str): The cleaned and normalized article text.
        categories (list[str], optional): List of category tags for the article. Defaults to None.

    Returns:
        dict: A dictionary with 'content' and 'metadata' keys, where 'metadata' includes 'categories'.

    Example:
        >>> text = 'Ukraine repels Russian forces'
        >>> categories = ['Conflict', 'Ukraine']
        >>> input_data = prepare_ai_input(text, categories)
        >>> print(input_data)
        {'content': 'Ukraine repels Russian forces', 'metadata': {'categories': ['Conflict', 'Ukraine']}}
    """
    return {
        "content": cleaned_article,
        "metadata": {"categories": categories if categories else []},
    }


def remove_duplicates(articles: list[dict]) -> list[dict]:
    """
    Removes duplicate articles based on title and description to ensure unique entries.

    Compares articles using a hash of title and description, keeping only the first occurrence
    to avoid redundancy in the database or analysis.

    Args:
        articles (list[dict]): List of article dictionaries with 'title' and 'description' keys.

    Returns:
        list[dict]: A list of unique article dictionaries.

    Example:
        >>> articles = [{'title': 'Ukraine War', 'description': 'Details...'},
        ...             {'title': 'Ukraine War', 'description': 'Details...'}]
        >>> unique = remove_duplicates(articles)
        >>> len(unique)
        1
    """
    seen = set()
    unique_articles = []
    for article in articles:
        identifier = f"{article.get('title', '')}{article.get('description', '')}"
        if identifier not in seen:
            seen.add(identifier)
            unique_articles.append(article)
    return unique_articles


def unify_date_format(date_str: str) -> str:
    """
    Converts various date formats to a unified 'YYYY-MM-DD HH:MM:SS' UTC format.

    Parses date strings (e.g., 'Sun, 23 Feb 2025 14:58:00 -0500') using dateutil.parser,
    converts them to UTC, and formats them consistently for database storage. Logs warnings
    for parsing failures and falls back to the current UTC time if necessary.

    Args:
        date_str (str): The date string in any parseable format (e.g., RSS date formats).

    Returns:
        str: A standardized date string in 'YYYY-MM-DD HH:MM:SS' format in UTC.

    Raises:
        None: Logs warnings for parsing errors but returns a fallback date.

    Example:
        >>> date = 'Sun, 23 Feb 2025 14:58:00 -0500'
        >>> unified = unify_date_format(date)
        >>> print(unified)
        '2025-02-23 19:58:00'
    """
    try:
        parsed_date = dateutil.parser.parse(date_str)
        return parsed_date.astimezone(dateutil.tz.UTC).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.warning(f"⚠️ Could not parse date {date_str}: {str(e)}")
        return datetime.now(dateutil.tz.UTC).strftime("%Y-%m-%d %H:%M:%S")


def vacuum_database(db_path: str = "news_analysis.db") -> None:
    """
    Performs a VACUUM operation on the SQLite database to optimize and reclaim space.

    Rebuilds the database file to remove unused space, reduce fragmentation, and improve
    performance. Ensures the logs directory exists, logs successful operations with INFO level,
    and prints emoji-enhanced feedback to the console. Logs errors if the operation fails.

    Args:
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Raises:
        sqlite3.Error: If the VACUUM operation fails due to database issues.

    Example:
        >>> vacuum_database()
        🛠️ Successfully vacuumed database at news_analysis.db at 2025-02-26 22:45:00
    """
    ensure_log_directory()
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("VACUUM")
            kyiv_time = datetime.now(dateutil.tz.UTC)
            success_message = (
                f"🛠️ Successfully vacuumed database at {db_path} at {kyiv_time}"
            )
            logger.info(success_message)
            print(success_message)
    except sqlite3.Error as e:
        kyiv_time = datetime.now(dateutil.tz.UTC)
        error_message = (
            f"❌ Failed to vacuum database {db_path} at {kyiv_time}: {str(e)}"
        )
        logger.error(error_message)
        print(error_message)
        raise


def ensure_log_directory() -> None:
    """
    Ensures the logs directory exists with proper permissions for logging.

    Creates the 'logs' directory if it doesn't exist, setting permissions to 755 (read/write/execute
    for owner, read/execute for others), and verifies write access for the current user.

    Raises:
        PermissionError: If the log directory cannot be made writable by the current user.

    Example:
        >>> ensure_log_directory()
        # Creates 'logs/' if it doesn't exist, ensuring write permissions
    """
    log_dir = os.path.dirname("logs/db_maintenance.log")
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, mode=0o755)
    os.chmod(log_dir, 0o755)
    if not os.access(log_dir, os.W_OK):
        raise PermissionError(
            f"Log directory {log_dir} is not writable by user {os.getlogin()}"
        )
