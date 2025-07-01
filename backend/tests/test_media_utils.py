# backend/tests/test_media_utils.py
import pytest
from backend.src.media_utils import (
    init_media_database,
    save_media_source,
    get_media_source,
    calculate_media_bias,
)
import sqlite3
import os


def test_init_media_database(temp_db):
    """Test initialization of the media_sources database table.

    Verifies that calling init_media_database creates a table with expected columns
    like 'calculated_bias_score' and 'ownership_category' in the specified database.
    """
    init_media_database(temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(media_sources)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "calculated_bias_score" in columns
    assert "ownership_category" in columns
    conn.close()


def test_save_media_source(temp_db, sample_media_source):
    """Test saving a MediaSource to the database.

    Initializes the database and checks if the sample MediaSource is saved
    by querying the database and verifying the name matches.
    """
    init_media_database(temp_db)
    save_media_source(sample_media_source, temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM media_sources WHERE name = ?", (sample_media_source.name,)
    )
    result = cursor.fetchone()
    assert result[0] == "NBC News"
    conn.close()


def test_get_media_source(temp_db, sample_media_source):
    """Test retrieving a MediaSource from the database.

    Saves a sample MediaSource, retrieves it, and verifies key attributes
    match the original data, including name and bias score.
    """
    init_media_database(temp_db)
    save_media_source(sample_media_source, temp_db)
    retrieved = get_media_source("NBC News", temp_db)
    assert retrieved.name == "NBC News"
    assert retrieved.ownership_category == "Large Media Groups"
    assert retrieved.ad_fontes_bias == pytest.approx(-0.57, rel=1e-2)


def test_calculate_media_bias(temp_db, sample_media_source):
    """Test calculating media bias for a source.

    Saves a sample MediaSource and checks if calculate_media_bias returns
    a dictionary with a 'calculated_bias_score' within the expected range.
    """
    init_media_database(temp_db)
    save_media_source(sample_media_source, temp_db)
    bias_result = calculate_media_bias("NBC News", temp_db)
    assert "calculated_bias_score" in bias_result
    assert -5 <= bias_result["calculated_bias_score"] <= 5
