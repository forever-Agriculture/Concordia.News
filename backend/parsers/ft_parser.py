"""
Financial Times (FT) specific parser for fetching and processing RSS feeds.

This module extends `BaseParser` to handle Financial Times RSS feeds, setting the
source name to 'financial_times'. It relies on the base implementation for most
functionality as FT uses a standard RSS 2.0 format. Ensures reliability with
rate limiting (1–5s delays), cost efficiency (e.g., 400 chars/article), and no
fabricated data, logging errors to `logs/financial_times_errors.log`.

Dependencies:
    - backend.parsers.base_parser: For base RSS parsing functionality.

Usage:
    >>> from backend.parsers.ft_parser import FTParser
    >>> feeds = {'world': 'https://www.ft.com/world?format=rss'}
    >>> parser = FTParser(feeds)
    >>> parser.run()
    # Collects articles from the last time window, logging errors to logs/financial_times_errors.log
"""

from backend.parsers.base_parser import BaseParser
import logging


class FTParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser specifically for Financial Times RSS feeds.

        Extends BaseParser to handle FT-specific RSS feeds, setting the source name to
        'financial_times' for logging and article tracking. Configures feed URLs and delay
        parameters for rate limiting based on the base class defaults.

        Args:
            feeds (dict): A dictionary mapping FT feed names to URLs
                          (e.g., {'world': 'https://www.ft.com/world?format=rss'}).

        Example:
            >>> feeds = {'world': 'https://www.ft.com/world?format=rss'}
            >>> parser = FTParser(feeds)
            # Initializes a parser for FT world news
        """
        super().__init__(feeds)  # Pass feeds to base class
        self.source_name = "financial_times"  # Explicit source name

        # Configure a specific logger for this parser
        # (BaseParser currently creates a generic logger based on self.source_name, which is sufficient)
        self.logger = logging.getLogger(self.source_name)
        self.logger.info(f"Initialized FTParser with {len(feeds)} feeds.")

    # No need to override extract_categories or parse_entry as base implementation is suitable.
    # No need to override run as the base one handles fetching and filtering.

    def parse(self):
        """
        Returns the list of parsed articles collected by run().

        This method is called by rss_collector.py to retrieve articles after run().
        It simply returns the articles accumulated by the base class's run method.

        Returns:
            list[dict]: List of article dictionaries populated by run().

        Example:
            >>> parser = FTParser({'world': 'https://www.ft.com/world?format=rss'})
            >>> parser.run()
            >>> articles = parser.parse()
            >>> if articles: print(articles[0]['title'])
        """
        self.logger.info(f"Parsing complete. Returning {len(self.articles)} articles for {self.source_name}.")
        return self.articles 