# backend/parsers/fox_parser.py
"""
Fox News-specific parser for fetching and processing RSS feeds.

This module extends `BaseParser` to handle Fox News RSS feeds, setting the source name to 'fox_news'
and customizing category extraction for Fox News-specific taxonomy schemes. It ensures reliability
with rate limiting (1–5s delays), cost efficiency (400 chars/article), and no fabricated data, logging
errors to `logs/fox_news_errors.log`.

Dependencies:
    - parsers.base_parser: For base RSS parsing functionality.
    - src.news_utils: For logging and date handling (updated from src.utils).

Usage:
    >>> from parsers.fox_parser import FoxParser
    >>> feeds = {'politics': 'http://feeds.foxnews.com/foxnews/politics'}
    >>> parser = FoxParser(feeds)
    >>> parser.run()
    # Collects yesterday's Fox News articles, logging errors to logs/fox_news_errors.log
"""

from backend.parsers.base_parser import BaseParser


class FoxParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser specifically for Fox News RSS feeds.

        Extends BaseParser to handle Fox News-specific RSS feeds, setting the source name to
        'fox_news' for logging and article tracking. Configures feed URLs and delay parameters
        for rate limiting.

        Args:
            feeds (dict): A dictionary mapping Fox News feed names to URLs
                         (e.g., {'politics': 'http://feeds.foxnews.com/foxnews/politics'}).

        Example:
            >>> feeds = {'politics': 'http://feeds.foxnews.com/foxnews/politics'}
            >>> parser = FoxParser(feeds)
            # Initializes a parser for Fox News political news
        """
        super().__init__(feeds)  # Pass feeds to base class
        self.source_name = "fox_news"  # Explicit source name

    def extract_categories(self, entry):
        """
        Extracts category tags from a Fox News RSS entry using its taxonomy scheme.

        Overrides the base method to handle Fox News-specific tag structures, filtering for
        tags with a 'taxonomy' scheme and returning the last part of the term after splitting
        by '/'. Ensures categories align with Fox News metadata.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser for a Fox News article.

        Returns:
            list[str]: A list of category terms (e.g., ['politics', 'world']).

        Example:
            >>> entry = {'tags': [{'term': 'news/taxonomy/politics', 'scheme': 'taxonomy'}]}
            >>> parser = FoxParser({'politics': 'http://foxnews.com/rss'})
            >>> parser.extract_categories(entry)
            ['politics']
        """
        return [
            tag.term.split("/")[-1]
            for tag in entry.get("tags", [])
            if hasattr(tag, "scheme") and "taxonomy" in tag.scheme
        ]

    def parse(self):
        """
        Parses RSS feed entries into a list of standardized article dictionaries.

        Processes the RSS feed entries stored in `self.articles` after `run()`, returning
        a list of dictionaries with keys like 'title', 'description', 'pub_date', 'link', and 'categories'.

        Returns:
            list[dict]: List of article dictionaries for use in collection.

        Example:
            >>> parser = FoxParser({'politics': 'http://foxnews.com/rss'})
            >>> parser.run()
            >>> articles = parser.parse()
            >>> print(articles[0]['title'])
            'Ukraine Conflict'
        """
        return self.articles
