# backend/rss_collector.py
"""
RSS article collector for news sources (NBC News, Fox News, BBC).

This module collects articles from RSS feeds for specified news sources, storing them in `news_analysis.db`.
It uses parsers from `parsers/` and utilities from `src/news_utils.py`, ensuring cost efficiency (400 chars/article,
leveraging DeepSeek's caching for ~$0.0128 for 92 articles), reliability (no delays beyond 1–5s for rate limiting, no fabricated data),
and scalability. Logs progress with emojis (e.g., 🚀, 🛠️) to console and `logs/db_maintenance.log`, assuming
Kyiv time (EET/UTC+2) for timestamps. Verifies sources against `media_sources` table using the `source` field.

Dependencies:
    - yaml: For configuration parsing.
    - src.news_utils: For database, cleaning, and deduplication.
    - src.media_utils: For media source verification.
    - parsers.base_parser: For RSS parsing.
    - logging: For error tracking.

Usage:
    >>> python rss_collector.py
    🚀 Starting article collection 🚀
    === Collecting nbc ===
    Removed 2 duplicates
    🧹 Cleaning Stats: {'html_entities': 0, 'html_tags': 0, 'whitespace_fixes': 0}
    💾 Saved 10 nbc articles
    ...
    ✅ Completed article collection: 64 articles collected at 2025-02-26 22:40:00
"""

import hashlib
import logging
from datetime import datetime
from importlib import import_module
from typing import Dict

import dateutil
import yaml

from backend.src.media_utils import get_all_media_sources
from backend.src.news_utils import (
    clean_article,
    db_connection,
    init_database,
    prepare_ai_input,
    remove_duplicates,
    unify_date_format,
)

# Configure logging to write INFO messages to logs/db_maintenance.log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_parsers(config_path: str = "config/parsers.yaml") -> list:
    """
    Loads and initializes enabled news source parsers from a YAML configuration file.

    Reads the 'parsers.yaml' file to instantiate parser classes (e.g., BBCParser, FoxParser)
    for enabled sources, applying their feed URLs and retry policies.

    Args:
        config_path (str, optional): Path to the YAML configuration file. Defaults to 'config/parsers.yaml'.

    Returns:
        list: A list of parser instances for enabled sources.

    Raises:
        FileNotFoundError: If the config file is missing.
        yaml.YAMLError: If the YAML file is malformed.
        ImportError: If a parser module or class cannot be imported.

    Example:
        >>> parsers = load_parsers()
        >>> print([p.source_name for p in parsers])
        ['fox_news', 'bbc', 'nbc']
    """
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        active_parsers = []
        for parser_config in config["parsers"]:
            if not parser_config["enabled"]:
                continue
            try:
                module = import_module(f"backend.{parser_config['module']}")
                parser_cls = getattr(module, parser_config["class"])
                feeds = {feed["name"]: feed["url"] for feed in parser_config["feeds"]}
                parser = parser_cls(feeds=feeds)
                parser.MIN_DELAY = parser_config["retry_policy"]["min_delay"]
                parser.MAX_DELAY = parser_config["retry_policy"]["max_delay"]
                active_parsers.append(parser)
            except Exception as e:
                logger.error(f"⚠️ Failed to load {parser_config['name']}: {str(e)}")
        return active_parsers
    except FileNotFoundError:
        logger.error(f"Config file {config_path} not found")
        return []
    except Exception as e:
        logger.error(f"Error loading parsers.yaml: {str(e)}")
        return []


def collect_articles() -> Dict[str, int]:
    """
    Collects news articles from enabled sources and stores them in the database.

    Loads parsers, fetches RSS feeds, cleans and deduplicates articles, and saves them to
    'news_analysis.db'. Verifies sources against `media_sources` using the `source` field. Prints
    progress with emojis and logs errors. Uses source_id for relations with the sources table.

    Returns:
        dict: A dictionary mapping source names to the number of articles saved.

    Example:
        >>> collect_articles()
        🚀 Starting article collection 🚀
        === Collecting nbc ===
        Removed 2 duplicates
        🧹 Cleaning Stats: {'html_entities': 0, 'html_tags': 0, 'whitespace_fixes': 0}
        💾 Saved 10 nbc articles
        {'nbc': 10, 'fox_news': 40, 'bbc': 14}
    """
    print("🚀 Starting article collection 🚀")
    sources = load_parsers()
    init_database()

    all_sources_data = {}
    for parser in sources:
        print(f"\n=== Collecting {parser.source_name} ===")
        # Verify source exists in media_sources using the source field
        media_source = next(
            (ms for ms in get_all_media_sources() if ms.source == parser.source_name),
            None,
        )
        if not media_source:
            print(
                f"⚠️ Source {parser.source_name} not found in media_sources, skipping collection"
            )
            logger.warning(f"Source {parser.source_name} not found in media_sources")
            continue

        try:
            parser.articles = []
            parser.run()
            raw_articles = parser.parse()
            deduped = remove_duplicates(raw_articles)
            print(f"Removed {len(raw_articles) - len(deduped)} duplicates")

            cleaning_stats = {
                "html_entities": 0,
                "html_tags": 0,
                "whitespace_fixes": 0,
            }

            with db_connection() as conn:
                cursor = conn.cursor()
                # Check if the source exists, insert only if it doesn't
                cursor.execute(
                    "SELECT source_id FROM sources WHERE name = ?",
                    (parser.source_name,),
                )
                source_row = cursor.fetchone()
                if source_row:
                    source_id = source_row["source_id"]
                else:
                    cursor.execute(
                        "INSERT INTO sources (name) VALUES (?)",
                        (parser.source_name,),
                    )
                    cursor.execute(
                        "SELECT source_id FROM sources WHERE name = ?",
                        (parser.source_name,),
                    )
                    source_id = cursor.fetchone()["source_id"]

                cleaned_count = 0
                for article in deduped:
                    cleaned_art, stats = clean_article(
                        {
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                        }
                    )
                    categories = article.get("categories", [])
                    if not categories and "feed_url" in article:
                        feed_name = next(
                            (
                                name
                                for name, url in parser.feeds.items()
                                if url == article["feed_url"]
                            ),
                            "unknown",
                        )
                        categories = [feed_name]
                    if not categories:
                        logger.warning(
                            f"No categories found for article: {article.get('title', 'Unknown')}"
                        )
                    ai_input = prepare_ai_input(cleaned_art, categories=categories)
                    cleaning_stats["html_entities"] += stats["html_entities"]
                    cleaning_stats["html_tags"] += stats["html_tags"]
                    cleaning_stats["whitespace_fixes"] += stats["whitespace_fixes"]
                    article_id = hashlib.md5(
                        f"{article['title']}{article['description']}".encode()
                    ).hexdigest()
                    unified_pub_date = unify_date_format(
                        article.get("publication_date", "")
                    )
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO articles 
                                     (id, source_id, raw_title, raw_description, 
                                      clean_content, categories, link, publication_date)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            article_id,
                            source_id,
                            article.get("title", ""),
                            article.get("description", ""),
                            ai_input["content"],
                            ",".join(ai_input["metadata"]["categories"]),
                            article.get("link", ""),
                            unified_pub_date,
                        ),
                    )
                    cleaned_count += 1
                conn.commit()
                print(f"🧹 Cleaning Stats: {cleaning_stats}")
                print(f"💾 Saved {cleaned_count} {parser.source_name} articles")
                all_sources_data[parser.source_name] = cleaned_count
        except Exception as e:
            print(f"❌ Collection error: {str(e)}")
            logger.error(f"Collection error for {parser.source_name}: {str(e)}")
            continue

    timestamp = datetime.now(dateutil.tz.UTC).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    print(
        f"✅ Completed article collection: {sum(all_sources_data.values())} articles collected at {timestamp}"
    )
    logger.info(
        f"Completed article collection: {sum(all_sources_data.values())} articles at {timestamp}"
    )
    return all_sources_data


if __name__ == "__main__":
    collect_articles()
