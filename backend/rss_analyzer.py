# backend/rss_analyzer.py
"""
RSS analyzer for processing news articles and generating AI-based reports.

This module queries articles from yesterday in `news_analysis.db` (adjusted for local system time
assuming UTC for date filtering), analyzes them using the DeepSeek API via `AIAnalyzer`,
and stores results in the database. It ensures cost efficiency, reliability with inter-source
delays, logs progress and errors robustly, and continues processing even if one source fails AI analysis.
Prints progress with emojis (e.g., 🚀, ✅) and logs INFO/ERROR to `logs/analyzer.log`.

Dependencies:
    - yaml: For configuration parsing.
    - src.ai_processor: For AI analysis.
    - src.news_utils: For database connection.
    - tenacity: For API key verification retries.
    - logging: For error tracking.
    - dateutil: For timezone handling.
    - dotenv: For environment variables.
    - openai: For API key verification.

Usage:
    >>> python -m backend.rss_analyzer
    (Logs progress and errors to console and logs/analyzer.log)
"""

import hashlib
import logging
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

import dateutil.tz # Correct import for timezone
import yaml
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.src.ai_processor import AIAnalyzer
from backend.src.news_utils import db_connection

load_dotenv()

# Configure logging to write INFO messages to logs/analyzer.log
# Ensure the logs directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "analyzer.log")

# Use a file handler
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
# Use a stream handler for console output (optional, print statements also used)
# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging.INFO)

# Define formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S UTC')
file_handler.setFormatter(formatter)
# stream_handler.setFormatter(formatter) # If using stream handler

# Get root logger and add handlers
# Avoid adding handlers multiple times if script is re-run/imported
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    # logger.addHandler(stream_handler) # If using stream handler
    # logger.propagate = False # Allow propagation so pytest caplog can capture messages


def load_parsers(config_path: str = "config/parsers.yaml") -> List[str]:
    """
    Loads enabled news source names from a YAML configuration file.
    Logs errors if loading fails.
    """
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
            if "parsers" not in config:
                logger.error(f"Invalid format in {config_path}: 'parsers' key missing")
                raise ValueError("Invalid parsers.yaml format: 'parsers' key missing")
            sources = [
                parser["name"]
                for parser in config["parsers"]
                if parser.get("enabled", False)
            ]
            if not sources:
                 logger.warning(f"No enabled parsers found in {config_path}")
            return sources
    except FileNotFoundError:
        logger.error(f"Config file {config_path} not found")
        return []
    except Exception as e:
        logger.error(f"Error loading {config_path}: {str(e)}")
        return []


def _parse_percentage(value: str, field_name: str) -> float:
    """
    Parses a percentage string into a float, logging errors.
    Returns 0.0 for invalid or empty values.
    """
    if not value or not isinstance(value, str):
        # logger.warning(f"Parsing percentage for '{field_name}': Invalid type or empty value '{value}', defaulting to 0.0")
        return 0.0
    parsed_value = value.rstrip("%").strip()
    try:
        return float(parsed_value)
    except ValueError:
        logger.error(f"Parsing percentage for '{field_name}': Invalid numeric format '{value}', defaulting to 0.0")
        return 0.0


def _parse_float(value: str, field_name: str) -> float:
    """
    Parses a string into a float, logging errors.
    Returns 0.0 for invalid or empty values.
    """
    if not value or not isinstance(value, str):
        # logger.warning(f"Parsing float for '{field_name}': Invalid type or empty value '{value}', defaulting to 0.0")
        return 0.0
    parsed_value = value.strip()
    try:
        return float(parsed_value)
    except ValueError:
        logger.error(f"Parsing float for '{field_name}': Invalid numeric format '{value}', defaulting to 0.0")
        return 0.0

# Define retry behaviour specifically for API key check
retry_api_key_check = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception), # Retry on any exception during test call
    before_sleep=lambda retry_state: print(
        f"⛔ Retry attempt {retry_state.attempt_number} for API key verification after {retry_state.wait:.1f} seconds due to: {retry_state.outcome.exception()}"
    ),
    retry_error_callback=lambda retry_state: False # Return False if all retries fail
)

@retry_api_key_check
def verify_api_key(api_key: str) -> bool:
    """
    Verifies the DeepSeek API key by making a minimal test call.
    Relies on @retry_api_key_check decorator for retries.
    Returns True if successful, False if all retries fail.
    """
    # This function now only contains the core logic, retries handled by decorator
    try:
        test_client = OpenAI(
            base_url="https://api.deepseek.com/v1", api_key=api_key, timeout=30.0
        )
        test_client.chat.completions.create(
            model="deepseek-chat", # Use appropriate model name if different
            messages=[{"role": "system", "content": "Test: Return 'OK'"}],
            max_tokens=10,
        )
        return True # Success!
    except Exception as e:
        # Let the decorator handle logging the retry reason
        raise e # Re-raise exception to trigger retry


def format_analysis_date_for_db(date_str_human: str) -> str:
    """
    Converts a human-readable date string ("Month DD, YYYY") to DB format ("YYYY-MM-DD").
    Returns None if parsing fails.
    """
    try:
        date_obj = datetime.strptime(date_str_human, "%B %d, %Y")
        return date_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        logger.error(f"Could not format analysis date '{date_str_human}' for DB: {e}")
        return None

def _load_analysis_settings() -> str:
    """Loads the analysis target_day setting from config/time_settings.yaml."""
    config_path = "config/time_settings.yaml"
    default_strategy = "previous_day" # Default to the original behavior if config is missing/invalid
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
            strategy = config.get("analysis", {}).get("target_day", default_strategy)
            if strategy not in ["current_day", "previous_day"]:
                logger.warning(f"Invalid analysis:target_day '{strategy}' in {config_path}. Using default: '{default_strategy}'.")
                return default_strategy
            return strategy
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using default analysis strategy: '{default_strategy}'.")
        return default_strategy
    except (yaml.YAMLError, Exception) as e:
        logger.error(f"Error loading analysis settings from {config_path}: {e}. Using default: '{default_strategy}'.")
        return default_strategy

# --- Main Analysis Function ---
def analyze_articles() -> None:
    """
    Analyzes news articles from enabled sources, generating reports using the DeepSeek API.
    Logs detailed progress and errors, ensuring continuation even if one source fails AI analysis.
    Determines target analysis date based on config/time_settings.yaml (analysis:target_day).
    """
    print("🚀 Starting article analysis script 🚀")
    logger.info("🚀 Starting article analysis script 🚀")
    analyzer = AIAnalyzer() # Initialize AI Analyzer

    # --- Load Analysis Date Strategy ---
    analysis_strategy = _load_analysis_settings()
    print(f"ℹ️ Using analysis date strategy: '{analysis_strategy}'")
    logger.info(f"Using analysis date strategy: '{analysis_strategy}'")

    # --- API Key Verification ---
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ FATAL: DEEPSEEK_API_KEY environment variable not set. Exiting.")
        logger.critical("DEEPSEEK_API_KEY environment variable not set. Exiting.")
        return

    print("⚠️ Verifying DeepSeek API key...")
    logger.info("Verifying DeepSeek API key...")
    key_is_valid = verify_api_key(api_key) # verify_api_key now returns bool after retries

    if key_is_valid:
        print("✅ DeepSeek API key is valid")
        logger.info("DeepSeek API key is valid")
    else:
        # Log warning but continue - maybe API is down but key is okay? Or maybe key is bad.
        print("⚠️ API key verification failed after multiple retries. Proceeding cautiously...")
        logger.warning("API key verification failed after multiple retries. Proceeding cautiously...")


    # --- Load Sources ---
    parser_sources = load_parsers()
    if not parser_sources:
        print("⚠️ No enabled parsers found in config/parsers.yaml. Exiting.")
        logger.warning("No enabled parsers found in config/parsers.yaml. Exiting.")
        return
    print(f"ℹ️ Will attempt to analyze sources: {parser_sources}")
    logger.info(f"Will attempt to analyze sources: {parser_sources}")

    # --- Database Connection and Schema ---
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            print("🛠️ Creating or verifying 'analyses' table schema...")
            logger.info("Creating or verifying 'analyses' table schema...")
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
                    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE RESTRICT,
                    UNIQUE(source_id, analysis_date) -- Prevent duplicate entries for same source/date
                )
                """
            )
            print("✅ Schema verified/created.")
            logger.info("Schema verified/created.")

            # --- Determine Target Date for Query based on Strategy ---
            utc_now = datetime.now(dateutil.tz.UTC)
            if analysis_strategy == "current_day":
                # Analyze articles published on the same UTC date the script is running
                target_date_utc = utc_now
                logger.info("Targeting CURRENT UTC day for analysis.")
            else: # Default or "previous_day"
                # Analyze articles published on the UTC date before the script started running
                target_date_utc = utc_now - timedelta(days=1)
                logger.info("Targeting PREVIOUS UTC day for analysis.")

            target_date_str = target_date_utc.strftime("%Y-%m-%d")
            print(f"🔍 Querying articles published on {target_date_str} UTC for sources: {parser_sources}")
            logger.info(f"Querying articles published on {target_date_str} UTC for sources: {parser_sources}")

            # --- Query Execution (uses target_date_str) ---
            cursor.execute(
                """
                SELECT s.source_id, s.name AS source_name, a.clean_content, a.publication_date
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                WHERE strftime('%Y-%m-%d', a.publication_date) = ? AND s.name IN ({})
                """.format(','.join('?'*len(parser_sources))),
                (target_date_str, *parser_sources),
            )
            # Group articles by source name
            source_articles_map = defaultdict(list)
            # Store source_id and a representative publication date per source
            source_context_map = {}
            for row in cursor.fetchall(): # Use fetchall to process after query completion
                source_name = row["source_name"]
                source_articles_map[source_name].append(row["clean_content"])
                if source_name not in source_context_map:
                    source_context_map[source_name] = {
                        "source_id": row["source_id"],
                        "publication_date": row["publication_date"] # Store one date for context
                    }

            total_sources_found = len(source_articles_map)
            if total_sources_found == 0:
                print(f"⚠️ No articles found in DB for defined parsers published on {target_date_str} UTC. Exiting.")
                logger.warning(f"No articles found in DB for defined parsers published on {target_date_str} UTC. Exiting.")
                return

            print(f"ℹ️ Found articles for {total_sources_found} sources published on {target_date_str} UTC.")
            logger.info(f"Found articles for {total_sources_found} sources published on {target_date_str} UTC.")
            inter_source_delay = int(os.getenv("INTER_SOURCE_DELAY", 120))
            print(f"⏳ Using inter-source delay of {inter_source_delay} seconds between source analyses.")
            logger.info(f"Using inter-source delay of {inter_source_delay} seconds between source analyses.")

            sources_processed_count = 0
            # --- Process Each Source ---
            for source_name, articles in source_articles_map.items():
                sources_processed_count += 1
                log_prefix = f"[{sources_processed_count}/{total_sources_found}] Source='{source_name}' Date='{target_date_str}'"
                num_articles = len(articles)

                print(f"\n{log_prefix}: -------- START PROCESSING [{num_articles} articles] --------")
                logger.info(f"{log_prefix}: Start processing {num_articles} articles.")

                # --- Skip if 0 articles for this source ---
                if num_articles == 0:
                    # This case shouldn't happen with how we queried, but good to keep
                    print(f"{log_prefix}: Skipping analysis, 0 articles found for this source.")
                    logger.warning(f"{log_prefix}: Skipping analysis, 0 articles found for this source.")
                else:
                    source_id = source_context_map[source_name]["source_id"]
                    publication_date_for_ai = source_context_map[source_name]["publication_date"]

                    # --- Call AI Analyzer within a try block ---
                    try:
                        print(f"{log_prefix}: Calling AIAnalyzer.analyze_articles...")
                        logger.info(f"{log_prefix}: Calling AIAnalyzer.analyze_articles...")
                        ai_context = {
                            "source": source_name,
                            "articles": articles,
                            "publication_date": publication_date_for_ai, # Pass date for analysis context
                            "cursor": cursor # Pass cursor if AIAnalyzer needs it (check AIAnalyzer code)
                        }
                        analysis_result = analyzer.analyze_articles(ai_context, source_name)

                        # --- Handle AI Result ---
                        if "error" in analysis_result:
                            error_message = analysis_result.get('error', 'Unknown AI Error')
                            analysis_date_human = analysis_result.get("analysis_date", "Unknown Date")
                            print(f"{log_prefix}: ❌ AI analysis FAILED. Date='{analysis_date_human}', Error='{error_message}'.")
                            logger.error(f"{log_prefix}: AI analysis FAILED. Date='{analysis_date_human}', Error='{error_message}'.")
                            print(f"{log_prefix}: --> CONTINUING TO NEXT SOURCE <--")
                            logger.info(f"{log_prefix}: Continuing to next source after AI failure.")
                            # No DB record saved on AI failure

                        else:
                            # --- Process and Save Successful Analysis ---
                            print(f"{log_prefix}: ✅ AI analysis SUCCEEDED.")
                            logger.info(f"{log_prefix}: AI analysis SUCCEEDED.")
                            analysis_date_db = target_date_str # Use the date we queried for
                            if not analysis_date_db:
                                print(f"{log_prefix}: ❌ Skipping save, could not format analysis date '{target_date_str}' for DB.")
                                logger.error(f"{log_prefix}: Skipping save, could not format analysis date '{target_date_str}' for DB.")
                                # Continue to next source if date formatting fails
                            else:
                                # Build values list for INSERT (35 fields in order)
                                values_list = [
                                    hashlib.md5(f"{source_name}{analysis_date_db}{datetime.now()}".encode()).hexdigest(), # Unique ID
                                    source_id,
                                    analysis_date_db,
                                    int(analysis_result.get("numbers_of_articles", num_articles)),
                                    analysis_result.get("main_narrative_theme_1"),
                                    _parse_percentage(analysis_result.get("main_narrative_coverage_1"), "narrative_coverage_1"),
                                    analysis_result.get("main_narrative_examples_1"),
                                    analysis_result.get("main_narrative_theme_2"),
                                    _parse_percentage(analysis_result.get("main_narrative_coverage_2"), "narrative_coverage_2"),
                                    analysis_result.get("main_narrative_examples_2"),
                                    analysis_result.get("main_narrative_theme_3"),
                                    _parse_percentage(analysis_result.get("main_narrative_coverage_3"), "narrative_coverage_3"),
                                    analysis_result.get("main_narrative_examples_3"),
                                    analysis_result.get("main_narrative_theme_4"),
                                    _parse_percentage(analysis_result.get("main_narrative_coverage_4"), "narrative_coverage_4"),
                                    analysis_result.get("main_narrative_examples_4"),
                                    analysis_result.get("main_narrative_theme_5"),
                                    _parse_percentage(analysis_result.get("main_narrative_coverage_5"), "narrative_coverage_5"),
                                    analysis_result.get("main_narrative_examples_5"),
                                    _parse_float(analysis_result.get("main_narrative_confidence"), "narrative_confidence"),
                                    _parse_percentage(analysis_result.get("sentiment_positive_percentage"), "sentiment_positive"),
                                    _parse_percentage(analysis_result.get("sentiment_negative_percentage"), "sentiment_negative"),
                                    _parse_percentage(analysis_result.get("sentiment_neutral_percentage"), "sentiment_neutral"),
                                    _parse_float(analysis_result.get("sentiment_confidence"), "sentiment_confidence"),
                                    _parse_float(analysis_result.get("bias_political_score"), "bias_score"),
                                    analysis_result.get("bias_political_leaning"),
                                    analysis_result.get("bias_supporting_evidence"),
                                    _parse_float(analysis_result.get("bias_confidence"), "bias_confidence"),
                                    analysis_result.get("values_promoted_value_1"),
                                    analysis_result.get("values_promoted_examples_1"),
                                    analysis_result.get("values_promoted_value_2"),
                                    analysis_result.get("values_promoted_examples_2"),
                                    analysis_result.get("values_promoted_value_3"),
                                    analysis_result.get("values_promoted_examples_3"),
                                    _parse_float(analysis_result.get("values_promoted_confidence"), "values_confidence"),
                                ]

                                try:
                                    # --- Insert the Record ---
                                    placeholders = ', '.join(['?'] * 35) # 35 columns
                                    insert_sql = f"""
                                        INSERT OR REPLACE INTO analyses (
                                            id, source_id, analysis_date, numbers_of_articles,
                                            main_narrative_theme_1, main_narrative_coverage_1, main_narrative_examples_1,
                                            main_narrative_theme_2, main_narrative_coverage_2, main_narrative_examples_2,
                                            main_narrative_theme_3, main_narrative_coverage_3, main_narrative_examples_3,
                                            main_narrative_theme_4, main_narrative_coverage_4, main_narrative_examples_4,
                                            main_narrative_theme_5, main_narrative_coverage_5, main_narrative_examples_5,
                                            main_narrative_confidence,
                                            sentiment_positive_percentage, sentiment_negative_percentage, sentiment_neutral_percentage,
                                            sentiment_confidence,
                                            bias_political_score,
                                            bias_political_leaning, bias_supporting_evidence, bias_confidence,
                                            values_promoted_value_1, values_promoted_examples_1,
                                            values_promoted_value_2, values_promoted_examples_2,
                                            values_promoted_value_3, values_promoted_examples_3,
                                            values_promoted_confidence
                                        ) VALUES ({placeholders})
                                        """
                                    print(f"{log_prefix}: 🛠️ Saving analysis to DB...")
                                    logger.info(f"{log_prefix}: Saving analysis to DB...")
                                    cursor.execute(insert_sql, tuple(values_list)) # Use tuple
                                    conn.commit()
                                    print(f"{log_prefix}: 💾 Analysis saved successfully.")
                                    logger.info(f"{log_prefix}: Analysis saved successfully.")

                                except sqlite3.Error as db_error:
                                    print(f"{log_prefix}: ❌ Database insert FAILED: {str(db_error)}")
                                    logger.error(f"{log_prefix}: Database insert FAILED: {str(db_error)}")
                                    # Continue to next source even if DB save fails

                    except Exception as e: # Catch unexpected errors during AI call or parsing for this source
                         print(f"{log_prefix}: ❌ Unhandled exception during processing: {str(e)}")
                         logger.exception(f"{log_prefix}: Unhandled exception processing source:") # Log stack trace
                         print(f"{log_prefix}: --> CONTINUING TO NEXT SOURCE <--")
                         logger.info(f"{log_prefix}: Continuing to next source after unhandled exception.")
                         # Continue to the next source

                # --- Apply inter-source delay ---
                # This runs after successful save OR after logging AI failure/exception and continuing
                if sources_processed_count < total_sources_found:
                     print(f"{log_prefix}: ⏳ Sleeping for {inter_source_delay} seconds before next source...")
                     logger.info(f"{log_prefix}: Sleeping for {inter_source_delay} seconds before next source...")
                     time.sleep(inter_source_delay)

                print(f"{log_prefix}: -------- END PROCESSING --------")
                logger.info(f"{log_prefix}: End processing.")

    # --- Catch DB Connection Error ---
    except sqlite3.Error as conn_error:
        print(f"❌ Failed to connect to or operate on database: {str(conn_error)}")
        logger.critical(f"Failed to connect to or operate on database: {str(conn_error)}")
    except Exception as general_error:
        print(f"❌ An unexpected error occurred during analysis: {str(general_error)}")
        logger.exception("An unexpected error occurred during analysis:") # Log stack trace

    print("\n✅ Article analysis script finished.")
    logger.info("✅ Article analysis script finished.")


if __name__ == "__main__":
    analyze_articles()
