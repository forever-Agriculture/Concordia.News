"""
The Christian Post specific parser for fetching and processing RSS feeds.

Extends BaseParser to handle The Christian Post RSS feeds, setting the source name
to 'christian_post'. Relies on the base implementation as the feed uses standard
RSS tags.

Dependencies:
    - backend.parsers.base_parser: For base RSS parsing functionality.

Usage:
    >>> from backend.parsers.christianpost_parser import ChristianPostParser
    >>> feeds = {'world': 'https://www.christianpost.com/category/world/rss'}
    >>> parser = ChristianPostParser(feeds)
    >>> parser.run()
    # Collects articles, logging errors to logs/christian_post_errors.log
"""

import logging
from backend.parsers.base_parser import BaseParser

class ChristianPostParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser for The Christian Post RSS feeds.

        Args:
            feeds (dict): A dictionary mapping feed names to URLs.
        """
        super().__init__(feeds)
        self.source_name = "christian_post"
        self.logger = logging.getLogger(self.source_name)
        self.logger.info(f"Initialized ChristianPostParser with {len(feeds)} feed(s).")

    # No overrides needed for standard RSS structure.

    def parse(self):
        """
        Returns the list of parsed articles collected by run().
        """
        self.logger.info(f"Parsing complete. Returning {len(self.articles)} articles for {self.source_name}.")
        return self.articles 