# backend/parsers/bbc_parser.py
"""
BBC-specific parser for fetching and processing RSS feeds.

This module extends `BaseParser` to handle BBC RSS feeds, setting the source name to 'bbc' and
customizing category extraction for BBC-specific tag structures. It ensures reliability with
rate limiting (1–5s delays), cost efficiency (400 chars/article), and no fabricated data, logging
errors to `logs/bbc_errors.log`.

Dependencies:
    - parsers.base_parser: For base RSS parsing functionality.
    - src.news_utils: For logging and date handling (updated from src.utils).

Usage:
    >>> from parsers.bbc_parser import BBCParser
    >>> feeds = {'world': 'http://feeds.bbci.co.uk/news/rss.xml'}
    >>> parser = BBCParser(feeds)
    >>> parser.run()
    # Collects yesterday's BBC articles, logging errors to logs/bbc_errors.log
"""

from backend.parsers.base_parser import BaseParser


class BBCParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser specifically for BBC RSS feeds.

        Extends BaseParser to handle BBC-specific RSS feeds, setting the source name to 'bbc'
        for logging and article tracking.

        Args:
            feeds (dict): A dictionary mapping BBC feed names to URLs (e.g., {'world': 'http://feeds.bbci.co.uk/news/rss.xml'}).

        Example:
            >>> feeds = {'world': 'http://feeds.bbci.co.uk/news/rss.xml'}
            >>> parser = BBCParser(feeds)
            # Initializes a parser for BBC news
        """
        super().__init__(feeds)  # Pass feeds to base class
        self.source_name = "bbc"  # Explicit source name

    def extract_categories(self, entry):
        """
        Extracts category tags from a BBC RSS entry.

        Overrides the base method to handle BBC-specific tag formats, returning a list
        of category terms from the 'tags' field.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser for a BBC article.

        Returns:
            list[str]: A list of category terms (e.g., ['world', 'politics']).

        Example:
            >>> entry = {'tags': [{'term': 'world'}, {'term': 'politics'}]}
            >>> parser = BBCParser({'world': 'http://bbc.com/rss'})
            >>> parser.extract_categories(entry)
            ['world', 'politics']
        """
        return [tag.term for tag in entry.get("tags", []) if hasattr(tag, "term")]

    def parse(self):
        """
        Parses RSS feed entries into a list of standardized article dictionaries.

        Processes the RSS feed entries stored in `self.articles` after `run()`, returning
        a list of dictionaries with keys like 'title', 'description', 'pub_date', 'link', and 'categories'.

        Returns:
            list[dict]: List of article dictionaries for use in collection.

        Example:
            >>> parser = BBCParser({'world': 'http://bbc.com/rss'})
            >>> parser.run()
            >>> articles = parser.parse()
            >>> print(articles[0]['title'])
            'Ukraine Conflict'
        """
        return self.articles
