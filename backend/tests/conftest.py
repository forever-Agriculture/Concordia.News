# backend/tests/conftest.py
import sys
import os
import pytest
import sqlite3
from backend.src.models import MediaSource
from datetime import datetime
import dateutil
from unittest.mock import MagicMock
import yaml
from backend.parsers.base_parser import BaseParser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load parser configuration
with open("config/parsers.yaml", "r") as file:
    parsers_config = yaml.safe_load(file)


@pytest.fixture(scope="function")
def temp_db():
    """Fixture providing a temporary database path for testing.

    Creates a temporary database file ('test_news_analysis.db') for each test function,
    yielding the path for use and cleaning it up afterward by removing the file.
    """
    db_path = "test_news_analysis.db"
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_media_source():
    """Fixture providing a sample MediaSource instance for testing.

    Returns a preconfigured MediaSource object for NBC News with typical attributes,
    including name, bias scores, and metadata, for use in database tests.
    """
    return MediaSource(
        name="NBC News",
        source="nbc",
        country="USA",
        flag_emoji="🇺🇸",
        logo_url="https://www.nbcnews.com/resources/images/logo-dark.png",
        website="https://www.nbcnews.com",
        owner="Comcast Corporation",
        ownership_category="Large Media Groups",
        rationale_for_ownership="Test rationale",
        ad_fontes_bias=-0.57,
        ad_fontes_reliability=0.9,
        ad_fontes_rating_url="https://adfontesmedia.com/nbc-news-bias/",
        ad_fontes_date_rated=datetime(2025, 2, 1),
        allsides_bias=-4.50,
        allsides_reliability=0.75,
        allsides_rating_url="https://www.allsides.com/nbc-news/",
        allsides_date_rated=datetime(2025, 2, 1),
        media_bias_fact_check_bias=-1.80,
        media_bias_fact_check_reliability=0.9,
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/nbc-news/",
        media_bias_fact_check_date_rated=datetime(2025, 2, 1),
    )


@pytest.fixture
def mock_context():
    """Fixture providing a mock context dictionary for AI analysis testing.

    Returns a dictionary with a source, articles list, and a mock cursor,
    simulating the context passed to the AIAnalyzer for testing purposes.
    """
    return {
        "source": "bbc",
        "articles": ["Test article 1...", "Test article 2..."],
        "cursor": MagicMock(),
    }


@pytest.fixture
def kyiv_tz():
    """Fixture providing the Kyiv timezone (EET/UTC+2) for date-related tests.

    Returns the timezone object for Europe/Kyiv using dateutil,
    used to handle date comparisons in a Kyiv-specific context.
    """
    return dateutil.tz.gettz("Europe/Kyiv")


@pytest.fixture
def base_parser():
    """Fixture providing a BaseParser instance.

    Creates a BaseParser instance using the 'world' feed URL for BBC from parsers.yaml.
    Assumes BaseParser accepts a single feed dictionary argument. If timezone or
    other parameters are required, adjust the constructor call accordingly
    (e.g., passing tz=kyiv_tz if supported).
    """
    bbc_config = next(p for p in parsers_config["parsers"] if p["name"] == "bbc")
    return BaseParser({feed["name"]: feed["url"] for feed in bbc_config["feeds"]})
