# backend/src/media_utils.py
"""
Utilities for media source management, bias calculation, and database operations.

This module provides functions to initialize and manage the SQLite database (`news_analysis.db`)
for media sources, save and retrieve MediaSource data (including third-party ratings and source identifiers),
calculate political bias, and ensure data consistency. It supports the news sentiment analysis project by ensuring
scalability, cost efficiency (e.g., 400 chars/article, leveraging DeepSeek's caching for ~$0.0128
for 92 articles), and reliability (e.g., delays for bias calculation, no fabricated data). Logs are written to
`logs/db_maintenance.log` with INFO level, and console output uses emojis for user feedback (e.g.,
🛠️, ❌). Relies on SQLite, Pydantic, dateutil, and logging, assuming UTC for date handling.

Dependencies:
    - sqlite3: For database operations.
    - pydantic: For data validation and serialization of media sources (version 2+).
    - dateutil: For timezone handling.
    - logging: For tracking operations.

Usage:
    >>> from src.media_utils import init_media_database, save_media_source, calculate_media_bias
    >>> init_media_database()
    🛠️ Initialized media source database schema
    >>> media = MediaSource(name="NBC News", source="nbc", country="USA", flag_emoji="🇺🇸", logo_url="https://www.nbcnews.com/resources/images/logo-dark.png", website="https://www.nbcnews.com")
    >>> save_media_source(media)
    💾 Saved media source: NBC News (last updated: 2025-02-26 22:40:00)
    >>> calculate_media_bias("NBC News")
    {'calculated_bias': 'Lean Left', 'calculated_bias_score': -2.57, 'bias_confidence': 0.85, 'raw_score': -2.57}
"""

import logging
import sqlite3
from datetime import datetime
from typing import Optional

import dateutil
from pydantic import ValidationError
from backend.src.news_utils import db_connection

from backend.src.models import MediaSource

# Configure logging to write INFO and ERROR messages to logs/db_maintenance.log
logging.basicConfig(
    level=logging.INFO,
    filename="logs/db_maintenance.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_media_database(db_path: str = "news_analysis.db") -> None:
    """
    Initializes or verifies the SQLite database schema for media sources.

    Creates or updates the `sources` and `media_sources` tables to include third-party rating fields,
    source identifier, and calculated_bias_score, ensuring compatibility with the MediaSource model.
    Allows SQLite to create `sqlite_sequence` for AUTOINCREMENT. Uses source_id for relations between
    tables. Supports ownership categories such as 'Large Media Groups', 'Private Investment Firms',
    'Individual Ownership', 'Government', 'Corporate Entities', 'Independently Operated', 'Unclassified',
    or 'Unverified'. Uses SQLite for cost efficiency and reliability.

    Args:
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        None: Updates the database schema or logs errors.

    Example:
        >>> init_media_database()
        🛠️ Initialized media source database schema
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Define the expected columns for media_sources
            expected_columns = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "name TEXT UNIQUE NOT NULL",
                "source_id INTEGER NOT NULL",
                "country TEXT NOT NULL",
                "flag_emoji TEXT NOT NULL",
                "logo_url TEXT NOT NULL",
                "founded_year INTEGER",
                "website TEXT NOT NULL",
                "description TEXT",
                "owner TEXT",
                "ownership_category TEXT",
                "rationale_for_ownership TEXT",
                "calculated_bias TEXT",
                "calculated_bias_score REAL",
                "bias_confidence REAL DEFAULT 0.0",
                "last_updated TEXT",
                "ad_fontes_bias REAL",
                "ad_fontes_reliability REAL",
                "ad_fontes_rating_url TEXT",
                "ad_fontes_date_rated TEXT",
                "allsides_bias REAL",
                "allsides_reliability REAL",
                "allsides_rating_url TEXT",
                "allsides_date_rated TEXT",
                "media_bias_fact_check_bias REAL",
                "media_bias_fact_check_reliability REAL",
                "media_bias_fact_check_rating_url TEXT",
                "media_bias_fact_check_date_rated TEXT",
                "FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE RESTRICT",
            ]

            # Check if media_sources table exists
            cursor.execute("PRAGMA table_info(media_sources)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Create table if it doesn't exist
            if not existing_columns:
                cursor.execute(
                    """
                    CREATE TABLE media_sources (
                        {}
                    )
                """.format(
                        ", ".join(expected_columns)
                    )
                )
            else:
                # Add missing columns if they don't exist
                for column_def in expected_columns[:-1]:  # Skip FOREIGN KEY for ALTER
                    column_name = column_def.split()[0]
                    if column_name not in existing_columns:
                        alter_sql = f"ALTER TABLE media_sources ADD COLUMN {column_def}"
                        cursor.execute(alter_sql)
                        print(
                            f"🛠️ Added missing column {column_name} to media_sources table"
                        )

            conn.commit()
            print("🛠️ Initialized media source database schema")
    except sqlite3.Error as e:
        print(f"❌ Failed to initialize media database: {str(e)}")
        logger.error(f"Database error initializing media schema: {str(e)}")


def save_media_source(media: MediaSource, db_path: str = "news_analysis.db") -> None:
    """
    Saves a MediaSource to the SQLite database, handling validation and updates with an automatic last_updated timestamp.

    Validates the Pydantic model, then inserts or updates the media source in `news_analysis.db`.
    Automatically sets last_updated to the current time in UTC, and stores third-party
    ratings, source identifier, and calculated_bias_score. Uses source_id for relations with the sources table.

    Args:
        media (MediaSource): Pydantic model instance of the media source.
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        None: Updates the database or logs errors.

    Example:
        >>> media = MediaSource(name="NBC News", source="nbc", country="USA", flag_emoji="🇺🇸", logo_url="https://www.nbcnews.com/resources/images/logo-dark.png", website="https://www.nbcnews.com")
        >>> save_media_source(media)
        💾 Saved media source: NBC News (last updated: 2025-02-26 22:40:00)
    """
    from backend.src.news_utils import (
        db_connection,
    )  # Import here to avoid circular import

    try:
        current_time = datetime.now(dateutil.tz.UTC)
        media.last_updated = current_time  # Automatically set last_updated in UTC
        with db_connection(
            db_path
        ) as conn:  # Use db_connection to ensure row_factory is set
            cursor = conn.cursor()
            # Check if the source exists, insert only if it doesn't
            cursor.execute(
                "SELECT source_id FROM sources WHERE name = ?", (media.source,)
            )
            source_row = cursor.fetchone()
            if source_row:
                source_id = source_row["source_id"]
            else:
                cursor.execute(
                    "INSERT INTO sources (name) VALUES (?)",
                    (media.source,),
                )
                cursor.execute(
                    "SELECT source_id FROM sources WHERE name = ?", (media.source,)
                )
                source_id = cursor.fetchone()["source_id"]

            cursor.execute(
                """
                INSERT OR REPLACE INTO media_sources (
                    name, source_id, country, flag_emoji, logo_url, founded_year, website, description,
                    owner, ownership_category, rationale_for_ownership, calculated_bias, calculated_bias_score,
                    bias_confidence, last_updated,
                    ad_fontes_bias, ad_fontes_reliability, ad_fontes_rating_url, ad_fontes_date_rated,
                    allsides_bias, allsides_reliability, allsides_rating_url, allsides_date_rated,
                    media_bias_fact_check_bias, media_bias_fact_check_reliability,
                    media_bias_fact_check_rating_url, media_bias_fact_check_date_rated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    media.name,
                    source_id,
                    media.country,
                    media.flag_emoji,
                    str(media.logo_url),
                    media.founded_year,
                    str(media.website),
                    media.description,
                    media.owner,
                    media.ownership_category,
                    media.rationale_for_ownership,
                    media.calculated_bias,
                    media.calculated_bias_score,
                    media.bias_confidence,
                    media.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
                    media.ad_fontes_bias,
                    media.ad_fontes_reliability,
                    (
                        str(media.ad_fontes_rating_url)
                        if media.ad_fontes_rating_url
                        else None
                    ),
                    (
                        media.ad_fontes_date_rated.strftime("%Y-%m-%d")
                        if media.ad_fontes_date_rated
                        else None
                    ),
                    media.allsides_bias,
                    media.allsides_reliability,
                    (
                        str(media.allsides_rating_url)
                        if media.allsides_rating_url
                        else None
                    ),
                    (
                        media.allsides_date_rated.strftime("%Y-%m-%d")
                        if media.allsides_date_rated
                        else None
                    ),
                    media.media_bias_fact_check_bias,
                    media.media_bias_fact_check_reliability,
                    (
                        str(media.media_bias_fact_check_rating_url)
                        if media.media_bias_fact_check_rating_url
                        else None
                    ),
                    (
                        media.media_bias_fact_check_date_rated.strftime("%Y-%m-%d")
                        if media.media_bias_fact_check_date_rated
                        else None
                    ),
                ),
            )
            conn.commit()
            print(
                f"💾 Saved media source: {media.name} (last updated: {media.last_updated.strftime('%Y-%m-%d %H:%M:%S')})"
            )
    except (sqlite3.Error, ValidationError) as e:
        print(f"❌ Failed to save media source {media.name}: {str(e)}")
        logger.error(f"Database or validation error saving media source: {str(e)}")


def get_media_source(
    name: str, db_path: str = "news_analysis.db"
) -> Optional[MediaSource]:
    """
    Retrieves a MediaSource from the SQLite database by name, returning a Pydantic model.

    Validates and converts SQLite data to a MediaSource instance for use in the app, including
    third-party ratings, source identifier, and calculated_bias_score. Uses source_id for relations
    with the sources table. Supports ownership categories such as 'Large Media Groups', 'Private
    Investment Firms', 'Individual Ownership', 'Government', 'Corporate Entities', 'Independently
    Operated', 'Unclassified', or 'Unverified'.

    Args:
        name (str): Name of the media source (e.g., "NBC News").
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        Optional[MediaSource]: Pydantic model instance if found, None otherwise.

    Example:
        >>> media = get_media_source("NBC News")
        >>> print(media.name)
        'NBC News'
    """
    try:
        with db_connection(
            db_path
        ) as conn:  # Use db_connection to ensure row_factory is set
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ms.name, s.name as source, ms.country, ms.flag_emoji, ms.logo_url, ms.founded_year,
                       ms.website, ms.description, ms.owner, ms.ownership_category, ms.rationale_for_ownership,
                       ms.calculated_bias, ms.calculated_bias_score, ms.bias_confidence, ms.last_updated,
                       ms.ad_fontes_bias, ms.ad_fontes_reliability, ms.ad_fontes_rating_url,
                       ms.ad_fontes_date_rated, ms.allsides_bias, ms.allsides_reliability,
                       ms.allsides_rating_url, ms.allsides_date_rated, ms.media_bias_fact_check_bias,
                       ms.media_bias_fact_check_reliability, ms.media_bias_fact_check_rating_url,
                       ms.media_bias_fact_check_date_rated
                FROM media_sources ms
                JOIN sources s ON ms.source_id = s.source_id
                WHERE ms.name = ?
            """,
                (name,),
            )
            row = cursor.fetchone()
            if row:
                return MediaSource(
                    name=row["name"],
                    source=row["source"],
                    country=row["country"],
                    flag_emoji=row["flag_emoji"],
                    logo_url=row["logo_url"],
                    founded_year=row["founded_year"],
                    website=row["website"],
                    description=row["description"],
                    owner=row["owner"],
                    ownership_category=row["ownership_category"],
                    rationale_for_ownership=row["rationale_for_ownership"],
                    calculated_bias=row["calculated_bias"],
                    calculated_bias_score=(
                        row["calculated_bias_score"]
                        if row["calculated_bias_score"] is not None
                        else None
                    ),
                    bias_confidence=row["bias_confidence"],
                    last_updated=(
                        datetime.strptime(
                            row["last_updated"], "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=dateutil.tz.UTC)
                        if row["last_updated"]
                        else None
                    ),
                    ad_fontes_bias=(
                        row["ad_fontes_bias"]
                        if row["ad_fontes_bias"] is not None
                        else None
                    ),
                    ad_fontes_reliability=(
                        row["ad_fontes_reliability"]
                        if row["ad_fontes_reliability"] is not None
                        else None
                    ),
                    ad_fontes_rating_url=(
                        row["ad_fontes_rating_url"]
                        if row["ad_fontes_rating_url"]
                        else None
                    ),
                    ad_fontes_date_rated=(
                        datetime.strptime(row["ad_fontes_date_rated"], "%Y-%m-%d")
                        if row["ad_fontes_date_rated"]
                        else None
                    ),
                    allsides_bias=(
                        row["allsides_bias"]
                        if row["allsides_bias"] is not None
                        else None
                    ),
                    allsides_reliability=(
                        row["allsides_reliability"]
                        if row["allsides_reliability"] is not None
                        else None
                    ),
                    allsides_rating_url=(
                        row["allsides_rating_url"]
                        if row["allsides_rating_url"]
                        else None
                    ),
                    allsides_date_rated=(
                        datetime.strptime(row["allsides_date_rated"], "%Y-%m-%d")
                        if row["allsides_date_rated"]
                        else None
                    ),
                    media_bias_fact_check_bias=(
                        row["media_bias_fact_check_bias"]
                        if row["media_bias_fact_check_bias"] is not None
                        else None
                    ),
                    media_bias_fact_check_reliability=(
                        row["media_bias_fact_check_reliability"]
                        if row["media_bias_fact_check_reliability"] is not None
                        else None
                    ),
                    media_bias_fact_check_rating_url=(
                        row["media_bias_fact_check_rating_url"]
                        if row["media_bias_fact_check_rating_url"]
                        else None
                    ),
                    media_bias_fact_check_date_rated=(
                        datetime.strptime(
                            row["media_bias_fact_check_date_rated"], "%Y-%m-%d"
                        )
                        if row["media_bias_fact_check_date_rated"]
                        else None
                    ),
                )
            return None
    except sqlite3.Error as e:
        print(f"❌ Failed to retrieve media source {name}: {str(e)}")
        logger.error(f"Database error retrieving media source: {str(e)}")
        return None


def calculate_media_bias(
    media_name: str, db_path: str = "news_analysis.db"
) -> Optional[dict]:
    """
    Calculates the averaged political bias and confidence for a media source based on third-party ratings.

    Uses ratings stored directly in the media_sources table, weighting scores by reliability. Maps the
    numerical average to a textual bias category and calculates a numeric bias score on a -5 to +5 scale.
    Updates the MediaSource in the database, automatically setting last_updated to the current time in UTC.
    Rounds the raw_score to 2 decimal places. Ensures a single save to avoid duplicates.

    Args:
        media_name (str): Name of the media source (e.g., "NBC News").
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        dict: Contains 'calculated_bias' (text, e.g., "Center-Left"), 'calculated_bias_score' (float, -5.0 to +5.0),
              'bias_confidence' (float 0.0–1.0), and 'raw_score' (float, -5.0 to +5.0, rounded to 2 decimal places)
              if ratings exist; None if no ratings.

    Example:
        >>> bias = calculate_media_bias("NBC News")
        >>> print(bias['calculated_bias'])
        'Lean Left'
        >>> print(bias['calculated_bias_score'])
        -2.57
    """
    media = get_media_source(media_name, db_path)
    if not media:
        return None

    # Fetch ratings directly from media_sources
    ratings = [
        (
            ("ad_fontes", media.ad_fontes_bias, media.ad_fontes_reliability)
            if media.ad_fontes_bias is not None
            and media.ad_fontes_reliability is not None
            else None
        ),
        (
            ("allsides", media.allsides_bias, media.allsides_reliability)
            if media.allsides_bias is not None
            and media.allsides_reliability is not None
            else None
        ),
        (
            (
                "media_bias_fact_check",
                media.media_bias_fact_check_bias,
                media.media_bias_fact_check_reliability,
            )
            if media.media_bias_fact_check_bias is not None
            and media.media_bias_fact_check_reliability is not None
            else None
        ),
    ]
    ratings = [r for r in ratings if r is not None]

    if not ratings:
        return None

    # Aggregate weighted scores and total weight
    weighted_scores = []
    total_weight = 0
    for rating_service, bias_score, reliability_score in ratings:
        if bias_score is not None and reliability_score is not None:
            weight = reliability_score  # Use reliability as weight (0.0–1.0)
            weighted_scores.append(bias_score * weight)
            total_weight += weight

    if total_weight == 0:
        return None

    # Calculate weighted average bias score (exact value)
    average_score = sum(weighted_scores) / total_weight

    # Calculate confidence based on the proportion of total possible reliability
    max_possible_weight = (
        len(ratings) * 1.0
    )  # Maximum reliability if all ratings are 1.0
    confidence = min(total_weight / max_possible_weight, 1.0)  # Cap at 1.0

    # Map numerical score to textual bias category
    BIAS_MAPPING = {
        -5: "Far Left",
        -4: "Left",
        -3: "Center-Left",
        -2: "Lean Left",
        -1: "Slight Left",
        0: "Neutral",
        1: "Slight Right",
        2: "Lean Right",
        3: "Center-Right",
        4: "Right",
        5: "Far Right",
    }

    # Find the closest bias category based on the average score
    closest_score = min(BIAS_MAPPING.keys(), key=lambda x: abs(x - average_score))
    calculated_bias = BIAS_MAPPING[closest_score]

    # Round the raw_score to 2 decimal places for return and storage
    calculated_bias_score = round(average_score, 2)

    # Update the media source with new bias, score, and confidence
    media.calculated_bias = calculated_bias
    media.calculated_bias_score = calculated_bias_score
    media.bias_confidence = round(confidence, 2)
    media.last_updated = datetime.now(dateutil.tz.UTC)
    save_media_source(media, db_path)

    return {
        "calculated_bias": calculated_bias,
        "calculated_bias_score": calculated_bias_score,
        "bias_confidence": round(confidence, 2),
        "raw_score": calculated_bias_score,
    }


def get_all_media_sources(db_path: str = "news_analysis.db") -> list[MediaSource]:
    """
    Retrieves all MediaSource instances from the SQLite database.

    Queries the `media_sources` table and returns a list of MediaSource objects for all entries,
    joining with the `sources` table to retrieve the source name.

    Args:
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        list[MediaSource]: List of MediaSource instances.

    Example:
        >>> sources = get_all_media_sources()
        >>> print(sources[0].name)
        'NBC News'
    """
    try:
        with db_connection(
            db_path
        ) as conn:  # Use db_connection to ensure row_factory is set
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ms.name, s.name as source, ms.country, ms.flag_emoji, ms.logo_url,
                       ms.founded_year, ms.website, ms.description, ms.owner, ms.ownership_category,
                       ms.rationale_for_ownership, ms.calculated_bias, ms.calculated_bias_score,
                       ms.bias_confidence, ms.last_updated, ms.ad_fontes_bias, ms.ad_fontes_reliability,
                       ms.ad_fontes_rating_url, ms.ad_fontes_date_rated, ms.allsides_bias,
                       ms.allsides_reliability, ms.allsides_rating_url, ms.allsides_date_rated,
                       ms.media_bias_fact_check_bias, ms.media_bias_fact_check_reliability,
                       ms.media_bias_fact_check_rating_url, ms.media_bias_fact_check_date_rated
                FROM media_sources ms
                JOIN sources s ON ms.source_id = s.source_id
            """
            )
            media_sources = []
            for row in cursor.fetchall():
                media_sources.append(
                    MediaSource(
                        name=row["name"],
                        source=row["source"],
                        country=row["country"],
                        flag_emoji=row["flag_emoji"],
                        logo_url=row["logo_url"],
                        founded_year=row["founded_year"],
                        website=row["website"],
                        description=row["description"],
                        owner=row["owner"],
                        ownership_category=row["ownership_category"],
                        rationale_for_ownership=row["rationale_for_ownership"],
                        calculated_bias=row["calculated_bias"],
                        calculated_bias_score=(
                            row["calculated_bias_score"]
                            if row["calculated_bias_score"] is not None
                            else None
                        ),
                        bias_confidence=row["bias_confidence"],
                        last_updated=(
                            datetime.strptime(
                                row["last_updated"], "%Y-%m-%d %H:%M:%S"
                            ).replace(tzinfo=dateutil.tz.UTC)
                            if row["last_updated"]
                            else None
                        ),
                        ad_fontes_bias=(
                            row["ad_fontes_bias"]
                            if row["ad_fontes_bias"] is not None
                            else None
                        ),
                        ad_fontes_reliability=(
                            row["ad_fontes_reliability"]
                            if row["ad_fontes_reliability"] is not None
                            else None
                        ),
                        ad_fontes_rating_url=(
                            row["ad_fontes_rating_url"]
                            if row["ad_fontes_rating_url"]
                            else None
                        ),
                        ad_fontes_date_rated=(
                            datetime.strptime(row["ad_fontes_date_rated"], "%Y-%m-%d")
                            if row["ad_fontes_date_rated"]
                            else None
                        ),
                        allsides_bias=(
                            row["allsides_bias"]
                            if row["allsides_bias"] is not None
                            else None
                        ),
                        allsides_reliability=(
                            row["allsides_reliability"]
                            if row["allsides_reliability"] is not None
                            else None
                        ),
                        allsides_rating_url=(
                            row["allsides_rating_url"]
                            if row["allsides_rating_url"]
                            else None
                        ),
                        allsides_date_rated=(
                            datetime.strptime(row["allsides_date_rated"], "%Y-%m-%d")
                            if row["allsides_date_rated"]
                            else None
                        ),
                        media_bias_fact_check_bias=(
                            row["media_bias_fact_check_bias"]
                            if row["media_bias_fact_check_bias"] is not None
                            else None
                        ),
                        media_bias_fact_check_reliability=(
                            row["media_bias_fact_check_reliability"]
                            if row["media_bias_fact_check_reliability"] is not None
                            else None
                        ),
                        media_bias_fact_check_rating_url=(
                            row["media_bias_fact_check_rating_url"]
                            if row["media_bias_fact_check_rating_url"]
                            else None
                        ),
                        media_bias_fact_check_date_rated=(
                            datetime.strptime(
                                row["media_bias_fact_check_date_rated"], "%Y-%m-%d"
                            )
                            if row["media_bias_fact_check_date_rated"]
                            else None
                        ),
                    )
                )
            return media_sources
    except sqlite3.Error as e:
        print(f"❌ Failed to retrieve media sources: {str(e)}")
        logger.error(f"Database error retrieving media sources: {str(e)}")
        return []
