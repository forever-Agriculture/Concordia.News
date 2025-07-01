# backend/parsers/nbc_parser.py
"""
NBC-specific parser for fetching and processing RSS feeds.

This module extends `BaseParser` to handle NBC RSS feeds, setting the source name to 'nbc' and
customizing category extraction for NBC-specific category schemes. It ensures reliability with
rate limiting (1–5s delays), cost efficiency (400 chars/article), and no fabricated data, logging
errors to `logs/nbc_errors.log`.

Dependencies:
    - parsers.base_parser: For base RSS parsing functionality.
    - src.news_utils: For logging and date handling (updated from src.utils).

Usage:
    >>> from parsers.nbc_parser import NBCParser
    >>> feeds = {'news': 'http://www.nbcnews.com/news/world?format=rss'}
    >>> parser = NBCParser(feeds)
    >>> parser.run()
    # Collects yesterday's NBC articles, logging errors to logs/nbc_errors.log
"""

from backend.parsers.base_parser import BaseParser


class NBCParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser specifically for NBC RSS feeds.

        Extends BaseParser to handle NBC-specific RSS feeds, setting the source name to 'nbc'
        for logging and article tracking. Configures feed URLs and delay parameters for rate limiting.

        Args:
            feeds (dict): A dictionary mapping NBC feed names to URLs
                         (e.g., {'news': 'http://www.nbcnews.com/news/world?format=rss'}).

        Example:
            >>> feeds = {'news': 'http://www.nbcnews.com/news/world?format=rss'}
            >>> parser = NBCParser(feeds)
            # Initializes a parser for NBC news
        """
        super().__init__(feeds)
        self.source_name = "nbc"

    def extract_categories(self, entry):
        """
        Extracts category tags from an NBC RSS entry using its category scheme.

        Overrides the base method to handle NBC-specific tag structures, filtering for tags
        with a 'category' scheme and returning the last part of the term after splitting by '/'.
        Ensures categories align with NBC metadata.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser for an NBC article.

        Returns:
            list[str]: A list of category terms (e.g., ['news', 'politics']).

        Example:
            >>> entry = {'tags': [{'term': 'news/category/politics', 'scheme': 'category'}]}
            >>> parser = NBCParser({'news': 'http://nbcnews.com/rss'})
            >>> parser.extract_categories(entry)
            ['politics']
        """
        return [
            tag.term.split("/")[-1]
            for tag in entry.get("tags", [])
            if hasattr(tag, "scheme") and "category" in tag.scheme
        ]

    def parse(self):
        """
        Parses RSS feed entries into a list of standardized article dictionaries.

        Processes the RSS feed entries stored in `self.articles` after `run()`, returning
        a list of dictionaries with keys like 'title', 'description', 'pub_date', 'link', and 'categories'.

        Returns:
            list[dict]: List of article dictionaries for use in collection.

        Example:
            >>> parser = NBCParser({'news': 'http://nbcnews.com/rss'})
            >>> parser.run()
            >>> articles = parser.parse()
            >>> print(articles[0]['title'])
            'Ukraine Conflict'
        """
        return self.articles
