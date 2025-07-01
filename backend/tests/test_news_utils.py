# backend/tests/test_news_utils.py
import pytest
from backend.src.news_utils import (
    init_database,
    clean_article,
    remove_duplicates,
    unify_date_format,
    vacuum_database,
)
from bs4 import BeautifulSoup
import sqlite3
import dateutil
import datetime


@pytest.mark.parametrize(
    "article, expected",
    [
        (
            {"title": "Test & Article", "description": "<p>Content & More</p>"},
            "Test & Article. Content & More",
        ),
        ({"title": "", "description": "<div>Empty</div>"}, ". Empty"),
    ],
)
def test_clean_article(article, expected):
    """Test cleaning article text.

    Verifies that clean_article processes the input article dictionary
    and returns a cleaned string containing the expected text.
    """
    cleaned, _ = clean_article(article)
    assert expected in cleaned


def test_remove_duplicates():
    """Test removing duplicate articles.

    Checks that remove_duplicates reduces a list of articles by removing
    duplicates based on title and description, leaving unique entries.
    """
    articles = [
        {"title": "Dup", "description": "Same"},
        {"title": "Dup", "description": "Same"},
        {"title": "Unique", "description": "Diff"},
    ]
    unique = remove_duplicates(articles)
    assert len(unique) == 2


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("Sun, 23 Feb 2025 14:58:00 -0500", "2025-02-23 19:58:00"),
        (
            "Invalid",
            datetime.datetime.now(dateutil.tz.UTC).strftime("%Y-%m-%d %H:%M:%S"),
        ),
    ],
)
def test_unify_date_format(date_str, expected):
    """Test unifying date formats.

    Verifies that unify_date_format converts various date strings
    into a standardized UTC format, matching the expected date prefix.
    """
    unified = unify_date_format(date_str)
    assert unified.startswith(expected[:10])


def test_vacuum_database(temp_db):
    """Test vacuuming the database.

    Initializes a database, creates a test table, inserts data,
    and runs vacuum_database to ensure the operation completes without errors.
    """
    init_database(temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test_table (id INTEGER)")
    cursor.execute("INSERT INTO test_table (id) VALUES (1)")
    conn.commit()
    vacuum_database(temp_db)
    conn.close()
