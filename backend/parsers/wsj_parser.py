"""
Wall Street Journal (WSJ) specific parser for fetching and processing RSS feeds.

This module extends `BaseParser` to handle Wall Street Journal RSS feeds, setting the
source name to 'wsj'. It relies on the base implementation for most
functionality as WSJ uses a standard RSS 2.0 format. Ensures reliability with
rate limiting (1–5s delays), cost efficiency (e.g., 400 chars/article), and no
fabricated data, logging errors to `logs/wsj_errors.log`.

Dependencies:
    - backend.parsers.base_parser: For base RSS parsing functionality.

Usage:
    >>> from backend.parsers.wsj_parser import WSJParser
    >>> feeds = {'opinion': 'https://feeds.content.dowjones.io/public/rss/RSSOpinion'}
    >>> parser = WSJParser(feeds)
    >>> parser.run()
    # Collects articles from the last time window, logging errors to logs/wsj_errors.log
"""

from backend.parsers.base_parser import BaseParser
import logging


class WSJParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser specifically for Wall Street Journal RSS feeds.

        Extends BaseParser to handle WSJ-specific RSS feeds, setting the source name to
        'wsj' for logging and article tracking. Configures feed URLs and delay
        parameters for rate limiting based on the base class defaults.

        Args:
            feeds (dict): A dictionary mapping WSJ feed names to URLs
                          (e.g., {'opinion': 'https://feeds.content.dowjones.io/public/rss/RSSOpinion'}).

        Example:
            >>> feeds = {'opinion': 'https://feeds.content.dowjones.io/public/rss/RSSOpinion'}
            >>> parser = WSJParser(feeds)
            # Initializes a parser for WSJ opinion news
        """
        super().__init__(feeds)  # Pass feeds to base class
        self.source_name = "wsj"  # Explicit source name

        # Configure a specific logger for this parser
        # BaseParser handles log file creation based on source_name
        self.logger = logging.getLogger(self.source_name)
        self.logger.info(f"Initialized WSJParser with {len(feeds)} feeds.")

    # No need to override extract_categories if the base implementation works.
    # WSJ feed uses standard <pubDate>, <title>, <description> elements.

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
            >>> parser = WSJParser({'opinion': 'https://feeds.content.dowjones.io/public/rss/RSSOpinion'})
            >>> parser.run()
            >>> articles = parser.parse()
            >>> if articles: print(articles[0]['title'])
        """
        self.logger.info(f"Parsing complete. Returning {len(self.articles)} articles for {self.source_name}.")
        return self.articles 