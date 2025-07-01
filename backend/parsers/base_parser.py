# backend/parsers/base_parser.py
"""
Base parser for fetching and processing RSS feeds from news sources.

This module defines a `BaseParser` class for collecting news articles from RSS feeds, handling
rate limiting, retries, and validation. It supports sources like Fox News, BBC, NBC ... filtering
for yesterday's articles (e.g., February 23, 2025, for February 24, 2025 runs), and logging errors
to source-specific log files (e.g., `logs/fox_news_errors.log`). Ensures reliability with
inter-source and chunk delays, cost efficiency (x chars/article), and no fabricated data.

Dependencies:
    - feedparser: For RSS parsing.
    - dateutil: For date validation.
    - tenacity: For retry logic on network errors.
    - src.utils: For HTTP headers and logging.

Usage:
    >>> from parsers.base_parser import BaseParser
    >>> feeds = {'world': 'http://example.com/rss'}
    >>> parser = BaseParser(feeds)
    >>> parser.run()
    # Collects yesterday's articles, logging errors to logs/base_errors.log
"""

import feedparser
import dateutil.parser
from datetime import datetime, timedelta
import logging
import time
import random
import socket
from urllib.error import URLError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from backend.src.news_utils import get_random_headers, unify_date_format
import yaml

retry_logger = logging.getLogger("retry")
retry_logger.setLevel(logging.WARNING)


class BaseParser:
    def __init__(self, feeds):
        """
        Initializes a base parser for fetching and parsing RSS feeds from news sources.

        Sets up the parser with a dictionary of feed URLs, source name, and delay parameters for
        rate limiting. Configures logging for errors to a source-specific log file and tracks the
        last fetch time for rate limiting.

        Args:
            feeds (dict): A dictionary mapping feed names to URLs (e.g., {'world': 'http://example.com/rss'}).

        Attributes:
            feeds (dict): Feed URLs for parsing.
            articles (list): List to store parsed articles.
            source_name (str): Name of the news source (default 'base', overridden by subclasses).
            MIN_DELAY (int): Minimum delay between fetches (default 1 second).
            MAX_DELAY (int): Maximum delay between fetches (default 5 seconds).
            last_fetch_time (float): Timestamp of the last fetch for rate limiting.
            lookback_hours (int): Number of hours to look back for article collection.
        """
        self.feeds = feeds
        self.articles = []
        self.source_name = "base"
        self.MIN_DELAY = 1
        self.MAX_DELAY = 5
        self.last_fetch_time = 0
        self.lookback_hours = self._load_time_settings()

        logging.basicConfig(
            filename=f"logs/{self.source_name}_errors.log", level=logging.ERROR
        )
        self.logger = logging.getLogger(self.source_name)

    def is_yesterday(self, publication_date: str) -> bool:
        """
        Determines if a publication date is from yesterday in UTC.

        Parses the publication date string and compares it to yesterday's date in UTC,
        returning True if it matches. Logs errors for parsing failures.

        Args:
            publication_date (str): The date string in any parseable format (e.g., 'Sun, 23 Feb 2025 14:58:00 GMT').

        Returns:
            bool: True if the date is yesterday in UTC, False otherwise or on parsing error.

        Example:
            >>> parser = BaseParser({'world': 'http://example.com'})
            >>> date = 'Sun, 23 Feb 2025 14:58:00 GMT'
            >>> parser.is_yesterday(date)
            True  # If today is Feb 24, 2025
        """
        try:
            pub_date = dateutil.parser.parse(publication_date).astimezone(
                dateutil.tz.UTC
            )
            yesterday = datetime.now(dateutil.tz.UTC) - timedelta(days=1)
            return pub_date.date() == yesterday.date()
        except Exception as e:
            self.logger.error(f"Date parsing error: {publication_date} - {str(e)}")
            return False

    def extract_categories(self, entry):
        """
        Extracts category tags from an RSS feed entry.

        Retrieves category terms from the 'tags' field of an RSS entry, returning a list
        of strings. Subclasses can override for source-specific behavior.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser.

        Returns:
            list[str]: A list of category terms (e.g., ['world', 'politics']).

        Example:
            >>> entry = {'tags': [{'term': 'world'}, {'term': 'politics'}]}
            >>> parser.extract_categories(entry)
            ['world', 'politics']
        """
        return [
            tag.term
            for tag in entry.get("tags", [])
            if hasattr(tag, "term") and tag.term
        ]

    def validate_entry(self, entry):
        """
        Validates an RSS feed entry for required fields.

        Checks if an entry has both a title and link, logging errors for invalid entries.
        Returns False for invalid entries, preventing processing.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser.

        Returns:
            bool: True if the entry is valid, False otherwise.

        Example:
            >>> entry = {'title': 'News', 'link': 'http://example.com'}
            >>> parser.validate_entry(entry)
            True
            >>> entry = {'title': ''}  # No link
            >>> parser.validate_entry(entry)
            False
        """
        if not entry.get("title") or not entry.get("link"):
            self.logger.error(f"Invalid entry: Missing title/link - {entry}")
            return False
        return True

    def parse_entry(self, entry, rss_feed_url: str):
        """
        Parses an RSS feed entry into a standardized article dictionary.

        Converts an RSS entry into a dictionary with keys for title, description, link,
        publication date, categories, source, and feed URL, using a unified date format.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser.
            rss_feed_url (str): The URL of the RSS feed the entry came from.

        Returns:
            dict: A dictionary representing the article with keys:
                  'title', 'description', 'link', 'published', 'publication_date', 'categories', 'source', 'feed_url'.

        Example:
            >>> entry = {'title': 'Ukraine Conflict', 'link': 'http://example.com', 'published': 'Sun, 23 Feb 2025 14:58:00 GMT'}
            >>> parser.parse_entry(entry, 'http://bbc.com/rss')
            {'title': 'Ukraine Conflict', 'description': '', 'link': 'http://example.com',
             'published': 'Sun, 23 Feb 2025 14:58:00 GMT', 'publication_date': '2025-02-23 14:58:00',
             'categories': [], 'source': 'base', 'feed_url': 'http://bbc.com/rss'}
        """
        return {
            "title": entry.get("title", ""),
            "description": entry.get("description", ""),
            "link": entry.link,
            "published": entry.get("published", ""),
            "publication_date": unify_date_format(entry.get("published", "")),
            "categories": self.extract_categories(entry),
            "source": self.source_name,
            "feed_url": rss_feed_url,
        }

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (TimeoutError, socket.gaierror, URLError, ConnectionResetError)
        ),
        before_sleep=before_sleep_log(retry_logger, logging.WARNING),
        reraise=True,
    )
    def fetch_feed(self, url):
        """
        Fetches and parses an RSS feed with retry logic for network errors.

        Uses feedparser to retrieve and parse an RSS feed, applying random delays and
        random headers to avoid rate limiting. Retries up to X times on network errors,
        logging warnings for retries and errors for failures.

        Args:
            url (str): The URL of the RSS feed to fetch.

        Returns:
            feedparser.FeedParserDict: The parsed RSS feed data.

        Raises:
            TimeoutError: If the fetch times out after retries.
            socket.gaierror: If the host is unreachable.
            URLError: If the URL is invalid or inaccessible.
            ConnectionResetError: If the connection is unexpectedly closed.

        Example:
            >>> parser = BaseParser({'world': 'http://bbc.com/rss'})
            >>> feed = parser.fetch_feed('http://bbc.com/rss')
            >>> len(feed.entries)
            10
        """
        try:
            elapsed = time.time() - self.last_fetch_time
            delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)

            if elapsed < delay:
                time.sleep(delay - elapsed)

            headers = get_random_headers()
            feed = feedparser.parse(url, request_headers=headers)
            self.last_fetch_time = time.time()

            if feed.bozo:
                self.logger.error(f"Feed parsing error: {feed.bozo_exception}")
                raise feed.bozo_exception

            return feed

        except Exception as e:
            self.logger.error(f"Fetch failed: {str(e)}")
            raise

    def run(self):
        """
        Executes the RSS feed parsing process for all configured feeds.

        Fetches and processes each feed, filtering for yesterday's articles, validating
        entries, and storing them in the `articles` list. Logs errors for failed feeds.

        Returns:
            None: Updates `self.articles` with parsed articles.

        Example:
            >>> parser = BaseParser({'world': 'http://bbc.com/rss'})
            >>> parser.run()
            # Populates parser.articles with yesterday's BBC articles
        """
        self.articles = []
        for feed_name, url in self.feeds.items():
            try:
                feed = self.fetch_feed(url)
                for entry in feed.entries:
                    if not self.validate_entry(entry):
                        continue
                    if self.is_within_time_window(entry.get("published", "")):
                        article = self.parse_entry(entry, url)
                        self.articles.append(article)
            except Exception as e:
                self.logger.error(f"Failed to process {feed_name}: {str(e)}")
                continue

    def parse(self):
        """
        Returns the list of parsed articles collected by run().

        This method is called by rss_collector.py to retrieve articles after run().
        Subclasses can override this method if additional parsing is needed.

        Returns:
            list[dict]: List of article dictionaries populated by run().
        """
        return self.articles

    def _load_time_settings(self):
        """
        Load time settings from configuration file.
        
        Returns:
            int: Number of hours to look back for article collection (default 20 if config not found).
        """
        try:
            with open("config/time_settings.yaml", "r") as file:
                config = yaml.safe_load(file)
                return config.get("collection", {}).get("lookback_hours", 20)
        except (FileNotFoundError, yaml.YAMLError):
            # Return default value if config file is missing or invalid
            return 20

    def is_within_time_window(self, date_str):
        """
        Check if a date string is within the configured time window from now.
        
        Handles timezone-aware and naive datetime objects consistently by
        converting all dates to UTC before comparison.
        
        Args:
            date_str (str): Date string to check.
            
        Returns:
            bool: True if the date is within the time window, False otherwise.
        """
        try:
            # Parse the date string
            article_date = dateutil.parser.parse(date_str)
            
            # Ensure the article date is timezone-aware (convert to UTC if not)
            if article_date.tzinfo is None:
                article_date = article_date.replace(tzinfo=dateutil.tz.UTC)
            else:
                article_date = article_date.astimezone(dateutil.tz.UTC)
            
            # Get current time in UTC
            now = datetime.now(dateutil.tz.UTC)
            
            # Calculate the cutoff time (now - lookback_hours)
            cutoff_time = now - timedelta(hours=self.lookback_hours)
            
            # Check if the article date is after the cutoff time
            return article_date >= cutoff_time
        except Exception as e:
            self.logger.error(f"Date parsing error: {str(e)} for date {date_str}")
            return False
