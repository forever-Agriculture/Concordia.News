# backend/src/ai_processor.py
"""
AI processor for analyzing news articles using the DeepSeek API.

This module provides the `AIAnalyzer` class to process news articles in chunks (60/article, 400
chars each), sending them to the DeepSeek API for narrative, sentiment, bias, and values analysis.
It generates detailed reports in key-value format, ensuring cost efficiency (~$0.0128 for 92 articles
with caching), reliability with chunk and inter-source delays, and no fabricated data.
Logs errors to `logs/db_maintenance.log` with ERROR level, and prints progress with emojis (e.g., 🔍, ✅).

Dependencies:
    - openai: For DeepSeek API interactions.
    - tenacity: For retry logic on API errors.
    - logging: For error tracking.
    - dateutil: For date handling.
    - re: For text parsing.

Usage:
    >>> from src.ai_processor import AIAnalyzer
    >>> analyzer = AIAnalyzer()
    >>> context = {'source': 'bbc', 'articles': ['Ukraine repels...'], 'cursor': cursor}
    >>> analysis = analyzer.analyze_articles(context, 'bbc')
    🔍 Starting analysis for 1 bbc articles
    ⏳ Parsed chunk 1 for bbc, sleeping for delay seconds
    ✅ Completed analysis for bbc (1 articles) from February 23, 2025
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any

import dateutil
import dateutil.parser
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Configure logging to write ERROR messages to logs/db_maintenance.log
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class AIAnalyzer:
    """A class to analyze news articles using the DeepSeek API for narrative, sentiment, bias, and values."""

    def __init__(self) -> None:
        """
        Initialize the AI analyzer for news article processing using the DeepSeek API.

        Sets up an OpenAI client with DeepSeek API configuration, including base URL, API key,
        and timeout. Defines parameters for chunking articles and the prompt template for analysis.

        Attributes:
            client (OpenAI): OpenAI client configured for DeepSeek API.
            model (str): DeepSeek model name (default 'deepseek-chat').
            chunk_size (int): Maximum number of articles per API call (default 60, ~24,000 chars).
            prompt_template (str): Template for DeepSeek prompt with article data and rules.
            rules (str): Strict rules for analysis (e.g., 5 themes, no fabricated data).
            example (str): Example output for DeepSeek to follow.
        """
        self.client = OpenAI(
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            timeout=60.0,
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.chunk_size = 60  # Max articles per call to fit within 8192 tokens (~24,000 chars input with 400 chars/article)

        self.prompt_template = "\n".join(
            [
                # Persona and Task Description
                "You are a veteran media analyst with over 20 years of experience in journalism and media studies, specializing in identifying narratives, sentiment, bias, and cultural values in news reporting.",
                "You maintain strict political neutrality in your analysis, ensuring that you do not favor any political side, ideology, or group, focusing solely on objective insights.",
                "Your task is to analyze the following {source} articles from {analysis_date} and produce a DETAILED, SOURCE-SPECIFIC DAILY MEDIA REPORT in this EXACT key-value pair format, one per line:\n",
                # Expected Output Format
                "numbers_of_articles=[total]",
                "main_narrative_theme_1=[theme_name]",
                "main_narrative_coverage_1=[percentage]",
                "main_narrative_examples_1=[full_article_title1,full_article_title2,...]",
                "main_narrative_theme_2=[theme_name]",
                "main_narrative_coverage_2=[percentage]",
                "main_narrative_examples_2=[full_article_title1,full_article_title2,...]",
                "main_narrative_theme_3=[theme_name]",
                "main_narrative_coverage_3=[percentage]",
                "main_narrative_examples_3=[full_article_title1,full_article_title2,...]",
                "main_narrative_theme_4=[theme_name]",
                "main_narrative_coverage_4=[percentage]",
                "main_narrative_examples_4=[full_article_title1,full_article_title2,...]",
                "main_narrative_theme_5=[theme_name]",
                "main_narrative_coverage_5=[percentage]",
                "main_narrative_examples_5=[full_article_title1,full_article_title2,...]",
                "main_narrative_confidence=[float between 0.8 and 1.0]",
                "sentiment_positive_percentage=[percentage]",
                "sentiment_negative_percentage=[percentage]",
                "sentiment_neutral_percentage=[percentage]",
                "sentiment_confidence=[float between 0.8 and 1.0]",
                "bias_political_score=[float between -5 and 5, where -5 is far left and 5 is far right]",
                "bias_political_leaning=[label based on the following scale: -5: 'Far Left', -4: 'Left', -3: 'Center-Left', -2: 'Lean Left', -1: 'Slight Left', 0: 'Neutral', 1: 'Slight Right', 2: 'Lean Right', 3: 'Center-Right', 4: 'Right', 5: 'Far Right']",
                "bias_supporting_evidence=[evidence1,evidence2,...]",
                "bias_confidence=[float between 0.8 and 1.0]",
                "values_promoted_value_1=[value_name]",
                "values_promoted_examples_1=[full_article_title1,full_article_title2,...]",
                "values_promoted_value_2=[value_name]",
                "values_promoted_examples_2=[full_article_title1,full_article_title2,...]",
                "values_promoted_value_3=[value_name]",
                "values_promoted_examples_3=[full_article_title1,full_article_title2,...]",
                "values_promoted_confidence=[float between 0.8 and 1.0]\n",
                # Articles Section
                "ARTICLES (use full, untruncated titles in examples, based only on data from {analysis_date}, limited to 400 characters each):",
                "{articles}\n",
                # Rules and Example
                "STRICT RULES:",
                "{rules}\n",
                "FORMAT EXAMPLE:",
                "{example}",
            ]
        )

        self.rules = "".join(
            [
                "- Use the key-value pair format exactly as shown, one per line.\n",
                "- Include exactly 5 distinct, source-specific themes under main_narrative based on ALL articles, reflecting the overarching narrative, context, and bias of {source}’s articles from {analysis_date}.\n",
                "- Include exactly 3 values under values_promoted based on ALL articles, specific to {source} from {analysis_date}.\n",
                "- Confidence scores must be floats between 0.8 and 1.0.\n",
                "- Use full article titles from the articles in examples, comma-separated.\n",
                "- Ensure the analysis captures the overall narrative, context, and bias of {source} across all articles from {analysis_date}, not injecting current or unrelated topics.\n",
                "- Be concise (up to 300-350 words), summarizing key insights and full context from all {source}’s {analysis_date} articles.\n",
                "- Only include themes, biases, or values present in {source}’s {analysis_date} articles.\n",
                "- If API data is missing or empty, log the error, skip analysis, and return only numbers_of_articles with an error flag—DO NOT use defaults or fabricate data.\n",
                "- Provide all fields, leaving them empty (not defaults) if data is missing due to API failure.\n",
            ]
        )

        self.example = "\n".join(
            [
                "numbers_of_articles=19",
                "main_narrative_theme_1=Anti-Palestinian narratives",
                "main_narrative_coverage_1=25.0",
                "main_narrative_examples_1=Hamas breaks peace agreement with Israel",
                "main_narrative_theme_2=Russian invasion of Ukraine",
                "main_narrative_coverage_2=20.0",
                "main_narrative_examples_2=Ukraine succesfully repels Russian attack at Kharkiv",
                "main_narrative_theme_3=Illigal Imigration",
                "main_narrative_coverage_3=20.0",
                "main_narrative_examples_3=Illigal immigrants cause crime in the country",
                "main_narrative_theme_4=Environmental concerns",
                "main_narrative_coverage_4=15.0",
                "main_narrative_examples_4=What causes the global warming?",
                "main_narrative_theme_5=Pro-Trump narratives",
                "main_narrative_coverage_5=20.0",
                "main_narrative_examples_5=Successful economic policies from Trump decrease inflation",
                "main_narrative_confidence=0.9",
                "sentiment_positive_percentage=30.0",
                "sentiment_negative_percentage=50.0",
                "sentiment_neutral_percentage=20.0",
                "sentiment_confidence=0.85",
                "bias_political_score=4.5",
                "bias_political_leaning=Right",
                "bias_supporting_evidence=Emphasis on traditional values and illigal immigration",
                "bias_confidence=0.88",
                "values_promoted_value_1=Public Safety",
                "values_promoted_examples_1=New knife laws will make difference, says victim's sister",
                "values_promoted_value_2=Support for Ukraine",
                "values_promoted_examples_2=The president offers Ukraine military help to press Russia to negotiation table",
                "values_promoted_value_3=Freedom",
                "values_promoted_examples_3=The president wants to limit state's power over people",
                "values_promoted_confidence=0.87",
            ]
        )

    def _prepare_content(
        self, context: dict, chunk: list[str] = None, publication_date: str = None
    ) -> dict:
        """
        Prepares article content for DeepSeek API analysis, formatting it into a structured string.

        Takes a context dictionary and optional chunk of articles, extracting source, articles,
        analysis date, and count. Limits each article to 400 characters for cost efficiency and
        formats them for the prompt template.

        Args:
            context (dict): Context dictionary with 'source', 'articles', and optionally 'cursor'.
            chunk (list[str], optional): List of article texts to process. Defaults to None (uses context['articles']).
            publication_date (str, optional): Publication date in 'YYYY-MM-DD HH:MM:SS' UTC format. Defaults to None.

        Returns:
            dict: A dictionary with 'source', 'articles' (formatted string), 'analysis_date', and 'numbers_of_articles'.

        Example:
            >>> context = {'source': 'bbc', 'articles': ['Ukraine repels...', 'Immigration rises...'], 'cursor': cursor}
            >>> content = _prepare_content(context)
            >>> print(content['articles'])
            'Article 1: Ukraine repels... | Article 2: Immigration rises...'
        """
        analysis_date = self._get_analysis_date(context, publication_date)
        articles = chunk if chunk else context.get("articles", [])
        return {
            "source": context.get("source", "unknown"),
            "articles": "\n".join(
                f"Article {i+1}: {art[:400]}..."
                for i, art in enumerate(articles)
                if art
            )
            or "No articles found",
            "analysis_date": analysis_date,
            "numbers_of_articles": len(articles),
        }

    def _get_analysis_date(self, context: dict, publication_date: str = None) -> str:
        """
        Retrieves the analysis date from publication data or defaults to yesterday in UTC.

        Parses a unified 'YYYY-MM-DD HH:MM:SS' UTC publication_date or extracts it from article
        content, returning it formatted as 'Month DD, YYYY'. Falls back to yesterday's UTC date
        if parsing fails.

        Args:
            context (dict): Context dictionary with 'articles' for fallback parsing.
            publication_date (str, optional): Publication date in 'YYYY-MM-DD HH:MM:SS' UTC format. Defaults to None.

        Returns:
            str: The analysis date formatted as 'Month DD, YYYY' (e.g., 'February 23, 2025').

        Example:
            >>> context = {'articles': ['2025-02-23 14:58:00']}
            >>> date = _get_analysis_date(context, '2025-02-23 14:58:00')
            >>> print(date)
            'February 23, 2025'
        """
        if publication_date:
            try:
                parsed_date = datetime.strptime(
                    publication_date, "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=dateutil.tz.UTC)
                return parsed_date.strftime("%B %d, %Y")
            except ValueError as e:
                logger.warning(
                    f"Could not parse unified publication_date {publication_date}: {str(e)}"
                )
        if context and context.get("articles"):
            try:
                article = context["articles"][0]
                date_match = re.search(r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}", article)
                if date_match:
                    date_str = date_match.group()
                    parsed_date = datetime.strptime(
                        date_str, "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=dateutil.tz.UTC)
                    return parsed_date.strftime("%B %d, %Y")
            except Exception as e:
                logger.warning(f"Could not parse date from articles: {str(e)}")
        # Default to yesterday in UTC
        default_date = datetime.now(dateutil.tz.UTC) - timedelta(days=1)
        return default_date.strftime("%B %d, %Y")

    def _parse_response(self, response: str) -> dict:
        """
        Parses the DeepSeek API response into a structured dictionary.

        Takes a raw string response from the DeepSeek API, splitting it into key-value pairs
        and formatting it into a dictionary for analysis storage. Handles numeric parsing for
        percentages and confidences, logging errors for invalid formats.

        Args:
            response (str): The raw response string from the DeepSeek API in key-value format.

        Returns:
            dict: A dictionary with keys like 'numbers_of_articles', 'main_narrative_theme_1',
                  'main_narrative_coverage_1', etc., with appropriate data types.

        Raises:
            None: Logs warnings/errors but returns a default dictionary on failure.

        Example:
            >>> response = "numbers_of_articles=19\nmain_narrative_theme_1=Conflict\n..."
            >>> data = _parse_response(response)
            >>> print(data['main_narrative_theme_1'])
            'Conflict'
        """
        data = {
            "numbers_of_articles": "0",
            "main_narrative_theme_1": None,
            "main_narrative_coverage_1": "0.0",
            "main_narrative_examples_1": None,
            "main_narrative_theme_2": None,
            "main_narrative_coverage_2": "0.0",
            "main_narrative_examples_2": None,
            "main_narrative_theme_3": None,
            "main_narrative_coverage_3": "0.0",
            "main_narrative_examples_3": None,
            "main_narrative_theme_4": None,
            "main_narrative_coverage_4": "0.0",
            "main_narrative_examples_4": None,
            "main_narrative_theme_5": None,
            "main_narrative_coverage_5": "0.0",
            "main_narrative_examples_5": None,
            "main_narrative_confidence": "0.0",
            "sentiment_positive_percentage": "0.0",
            "sentiment_negative_percentage": "0.0",
            "sentiment_neutral_percentage": "0.0",
            "sentiment_confidence": "0.0",
            "bias_political_score": "0.0",
            "bias_political_leaning": None,
            "bias_supporting_evidence": None,
            "bias_confidence": "0.0",
            "values_promoted_value_1": None,
            "values_promoted_examples_1": None,
            "values_promoted_value_2": None,
            "values_promoted_examples_2": None,
            "values_promoted_value_3": None,
            "values_promoted_examples_3": None,
            "values_promoted_confidence": "0.0",
        }
        if not response.strip():
            logger.warning("Received empty response from API")
            return data

        try:
            lines = response.strip().split("\n")
            for line in lines:
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in data:
                        if key in [
                            "main_narrative_coverage_1",
                            "main_narrative_coverage_2",
                            "main_narrative_coverage_3",
                            "main_narrative_coverage_4",
                            "main_narrative_coverage_5",
                            "main_narrative_confidence",
                            "sentiment_positive_percentage",
                            "sentiment_negative_percentage",
                            "sentiment_neutral_percentage",
                            "sentiment_confidence",
                            "bias_political_score",
                            "bias_confidence",
                            "values_promoted_confidence",
                        ]:
                            value = value.rstrip("%").strip()
                            if not value:
                                data[key] = "0.0"
                            else:
                                try:
                                    # Ensure bias_political_score is within -5 to +5
                                    if key == "bias_political_score":
                                        score = float(value)
                                        # Clamp the score to the -5 to +5 range
                                        score = max(min(score, 5.0), -5.0)
                                        data[key] = str(score)
                                    else:
                                        data[key] = str(float(value))
                                except ValueError:
                                    logger.error(
                                        f"Invalid numeric format for {key}: {value}"
                                    )
                                    data[key] = "0.0"
                        else:
                            data[key] = value if value else None
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return data
        return data

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=120),
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError, Exception)),
        before_sleep=lambda retry_state: print(
            f"⛔ Retry attempt {retry_state.attempt_number} for {retry_state.args[1]} after {retry_state.wait} seconds"
        ),
    )
    def analyze_articles(
        self, context: dict[str, Any], source_name: str
    ) -> dict[str, Any]:
        """
        Analyzes a batch of articles using the DeepSeek API, handling chunking and retries.

        Processes articles in chunks of up to 60, sending them to the DeepSeek API for narrative,
        sentiment, bias, and values analysis. Applies no delay before the first chunk, a delay after
        a chunk only if there are more chunks to analyze for the same source, and an inter-source delay
        after all chunks. Retries on API errors and prints progress with emojis.

        Args:
            context (dict): Context dictionary with 'source', 'articles', and optionally 'cursor' for database access.
            source_name (str): The name of the news source (e.g., 'bbc', 'fox_news').

        Returns:
            dict: A dictionary containing analysis results (e.g., narratives, sentiment, bias, values)
                  or an error flag if analysis fails.

        Raises:
            ValueError: If no articles are provided or API response is empty.

        Example:
            >>> context = {'source': 'fox_news', 'articles': ['Ukraine repels...', '...'], 'cursor': cursor}
            >>> analysis = AIAnalyzer().analyze_articles(context, 'fox_news')
            🔍 Starting analysis for 2 fox_news articles
            ⏳ Parsed chunk 1 for fox_news, sleeping for delay seconds
            ⏳ Parsed chunk 2 for fox_news, sleeping for delay seconds
            ✅ Completed analysis for fox_news (2 articles) from February 24, 2025
        """
        try:
            articles = context.get("articles", [])
            if not articles:
                raise ValueError("No articles to analyze")

            publication_date = None
            if articles:
                cursor = context.get("cursor")
                if cursor:
                    cursor.execute(
                        """
                        SELECT a.publication_date 
                        FROM articles a
                        JOIN sources s ON a.source_id = s.source_id
                        WHERE s.name = ? AND a.clean_content = ?
                        LIMIT 1
                    """,
                        (source_name, articles[0]),
                    )
                    pub_date_row = cursor.fetchone()
                    if pub_date_row:
                        publication_date = pub_date_row["publication_date"]

            results = []
            num_chunks = (len(articles) + self.chunk_size - 1) // self.chunk_size
            for i in range(0, len(articles), self.chunk_size):
                chunk = articles[i : i + self.chunk_size]
                prepared = self._prepare_content(context, chunk, publication_date)
                formatted_prompt = self.prompt_template.format(
                    source=prepared["source"],
                    articles=prepared["articles"],
                    analysis_date=prepared["analysis_date"],
                    rules=self.rules,
                    example=self.example,
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": formatted_prompt}],
                    temperature=0.1,
                    max_tokens=1200,
                )
                raw_response = (
                    response.choices[0].message.content if response.choices else None
                )

                if not raw_response or not raw_response.strip():
                    raise ValueError("Empty or None API response for analysis")

                parsed = self._parse_response(raw_response)
                results.append(parsed)
                # Apply delay only if there are more chunks to process for this source
                if i + self.chunk_size < len(articles):
                    delay = int(os.getenv("INTER_SOURCE_DELAY", 120))
                    print(
                        f"⏳ Parsed chunk {i//self.chunk_size + 1} for {source_name}, sleeping for {delay}s"
                    )
                    time.sleep(delay)
                else:
                    print(
                        f"⏳ Parsed chunk {i//self.chunk_size + 1} for {source_name}, sleeping for 0s"
                    )

            if not results:
                raise ValueError("No successful analysis for any chunk")
            final_result = results[0]
            final_result["numbers_of_articles"] = str(len(articles))
            final_result["analysis_date"] = prepared["analysis_date"]
            print(
                f"✅ Completed analysis for {source_name} ({len(articles)} articles) from {final_result['analysis_date']}"
            )
            return final_result
        except Exception as e:
            print(f"❌ Analysis failed for {source_name}: {str(e)}")
            logger.error(f"Analysis failed for {source_name}: {str(e)}")
            if hasattr(e, "response") and e.response:
                logger.error(
                    f"API error details: Status={e.response.status_code}, Text={e.response.text[:500]}"
                )
            return {
                "error": str(e),
                "numbers_of_articles": len(articles),
                "analysis_date": self._get_analysis_date(context),
            }
