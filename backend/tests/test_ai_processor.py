# backend/tests/test_ai_processor.py
import pytest
from backend.src.ai_processor import AIAnalyzer
from unittest.mock import patch, MagicMock
from datetime import datetime
import dateutil


@pytest.fixture
def analyzer():
    """Fixture providing an AIAnalyzer instance.

    Creates a mocked AIAnalyzer object for each test by mocking OpenAI client initialization,
    ensuring tests run without requiring an API key.
    """
    with patch("backend.src.ai_processor.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        analyzer = AIAnalyzer()
        analyzer.client = mock_client
        return analyzer


def test_init(analyzer):
    """Test AIAnalyzer initialization.

    Verifies that the AIAnalyzer is initialized with the correct
    chunk_size (60) and model ('deepseek-chat') attributes.
    """
    assert analyzer.chunk_size == 60
    assert analyzer.model == "deepseek-chat"


def test_prepare_content(analyzer, mock_context):
    """Test preparing content for analysis.

    Checks that _prepare_content constructs a dictionary with the
    correct source ('bbc') and number of articles (2) from the context.
    """
    content = analyzer._prepare_content(mock_context)
    assert content["source"] == "bbc"
    assert content["numbers_of_articles"] == 2


@patch("backend.src.ai_processor.OpenAI")
def test_analyze_articles(mock_openai, analyzer, mock_context):
    """Test analyzing articles with a mocked API response.

    Mocks the OpenAI client to return a response with 'numbers_of_articles=2',
    verifies that analyze_articles returns a non-null result, and
    checks the article count.
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="numbers_of_articles=2"))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    result = analyzer.analyze_articles(mock_context, "bbc")
    assert result is not None
    if result:
        assert int(result["numbers_of_articles"]) == 2
