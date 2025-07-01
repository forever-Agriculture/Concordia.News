"""
New York Times (NYT) specific parser for fetching and processing RSS feeds.

This module extends `BaseParser` to handle New York Times RSS feeds, setting the
source name to 'new_york_times'. It relies on the base implementation for most
functionality as NYT uses a standard RSS 2.0 format. Ensures reliability with
rate limiting (1–5s delays), cost efficiency (e.g., 400 chars/article), and no
fabricated data, logging errors to `logs/new_york_times_errors.log`.

Dependencies:
    - backend.parsers.base_parser: For base RSS parsing functionality.

Usage:
    >>> from backend.parsers.nyt_parser import NYTParser
    >>> feeds = {'homepage': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'}
    >>> parser = NYTParser(feeds)
    >>> parser.run()
    # Collects articles from the last time window, logging errors to logs/new_york_times_errors.log
"""

from backend.parsers.base_parser import BaseParser
import logging


class NYTParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser specifically for New York Times RSS feeds.

        Extends BaseParser to handle NYT-specific RSS feeds, setting the source name to
        'new_york_times' for logging and article tracking. Configures feed URLs and delay
        parameters for rate limiting based on the base class defaults.

        Args:
            feeds (dict): A dictionary mapping NYT feed names to URLs
                          (e.g., {'homepage': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'}).

        Example:
            >>> feeds = {'homepage': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'}
            >>> parser = NYTParser(feeds)
            # Initializes a parser for NYT homepage news
        """
        super().__init__(feeds)  # Pass feeds to base class
        self.source_name = "new_york_times"  # Explicit source name
        
        # Configure a specific logger for this parser if not already handled by BaseParser setup
        # (BaseParser currently creates a generic logger based on self.source_name, which is sufficient)
        self.logger = logging.getLogger(self.source_name) 
        self.logger.info(f"Initialized NYTParser with {len(feeds)} feeds.")

    # No need to override extract_categories if the base implementation works.
    # The base implementation extracts 'term' from entry.tags, which feedparser
    # usually populates from <category> elements.

    # No need to override parse_entry as the base one handles standard fields.

    # No need to override run as the base one handles fetching and filtering.

    def parse(self):
        """
        Returns the list of parsed articles collected by run().

        This method is called by rss_collector.py to retrieve articles after run().
        It simply returns the articles accumulated by the base class's run method.

        Returns:
            list[dict]: List of article dictionaries populated by run().

        Example:
            >>> parser = NYTParser({'homepage': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'})
            >>> parser.run()
            >>> articles = parser.parse()
            >>> if articles: print(articles[0]['title'])
        """
        self.logger.info(f"Parsing complete. Returning {len(self.articles)} articles for {self.source_name}.")
        return self.articles 