"""
Tests for the date selection logic in the RSS Analyzer module (backend.rss_analyzer).
Focuses on ensuring the correct date (current vs previous) is used based on configuration.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import dateutil.tz

# Import the function to test
from backend.rss_analyzer import analyze_articles

# Define a fixed UTC time for consistent testing
MOCK_UTC_NOW = datetime(2024, 4, 9, 23, 30, 0, tzinfo=dateutil.tz.UTC)
CURRENT_DAY_STR = MOCK_UTC_NOW.strftime("%Y-%m-%d") # "2024-04-09"
PREVIOUS_DAY_STR = (MOCK_UTC_NOW - timedelta(days=1)).strftime("%Y-%m-%d") # "2024-04-08"


# Helper function to run analyze_articles with necessary mocks
# It isolates the date calculation and query part
@patch('backend.rss_analyzer.AIAnalyzer')
@patch('backend.rss_analyzer.db_connection')
@patch('backend.rss_analyzer.load_parsers')
@patch('backend.rss_analyzer.verify_api_key')
@patch('backend.rss_analyzer.datetime')
def run_analyze_articles_mocked(mock_dt, mock_verify_key, mock_load_parsers, mock_db_conn, mock_ai_analyzer):
    """
    Sets up mocks for analyze_articles to test date logic.
    Mocks datetime, API key check, parser loading, DB connection, and AIAnalyzer.
    Returns the mocked DB cursor to inspect calls.
    """
    # Mock datetime.now(UTC) to return our fixed time
    mock_dt.now.return_value = MOCK_UTC_NOW
    # Ensure datetime constructor still works if needed elsewhere
    mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

    # Assume API key is valid
    mock_verify_key.return_value = True

    # Provide a dummy source list
    mock_load_parsers.return_value = ['test_source']

    # Mock DB connection context manager and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Return no articles to stop processing early after the query
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor
    # Simulate entering the 'with db_connection()' block
    mock_db_conn.return_value.__enter__.return_value = mock_conn

    # Mock the AI Analyzer instance
    mock_ai_analyzer.return_value = MagicMock()

    # Run the main function (which will use the patched _load_analysis_settings)
    analyze_articles()

    # Return the mock cursor for inspection
    return mock_cursor

# Test Case 1: Verify 'current_day' strategy uses the current date
@patch('backend.rss_analyzer._load_analysis_settings', return_value="current_day")
def test_analyze_articles_uses_current_day(mock_load_settings, caplog):
    """
    Verify analyze_articles queries for the current day's date
    when _load_analysis_settings returns 'current_day'.
    """
    mock_cursor = run_analyze_articles_mocked()

    # Check logs confirm the strategy and the date being queried
    assert "Using analysis date strategy: 'current_day'" in caplog.text
    assert f"Querying articles published on {CURRENT_DAY_STR} UTC" in caplog.text

    # Find the specific SQL query execution call for articles
    query_call = None
    for call in mock_cursor.execute.call_args_list:
        # Identify the query by a unique part of its string
        if "SELECT s.source_id, s.name AS source_name" in call.args[0]:
            query_call = call
            break

    assert query_call is not None, "Article query execution not found in mock calls"
    # Check the date parameter used in the WHERE clause (it's the first element in the tuple args[1])
    assert query_call.args[1][0] == CURRENT_DAY_STR


# Test Case 2: Verify 'previous_day' strategy uses the previous date
@patch('backend.rss_analyzer._load_analysis_settings', return_value="previous_day")
def test_analyze_articles_uses_previous_day(mock_load_settings, caplog):
    """
    Verify analyze_articles queries for the previous day's date
    when _load_analysis_settings returns 'previous_day'.
    """
    mock_cursor = run_analyze_articles_mocked()

    # Check logs confirm the strategy and the date being queried
    assert "Using analysis date strategy: 'previous_day'" in caplog.text
    assert f"Querying articles published on {PREVIOUS_DAY_STR} UTC" in caplog.text

    # Find the specific SQL query execution call for articles
    query_call = None
    for call in mock_cursor.execute.call_args_list:
        if "SELECT s.source_id, s.name AS source_name" in call.args[0]:
            query_call = call
            break

    assert query_call is not None, "Article query execution not found in mock calls"
    # Check the date parameter used in the WHERE clause
    assert query_call.args[1][0] == PREVIOUS_DAY_STR 