"""
Parser for France24 RSS feeds.

This module defines France24Parser, a subclass of BaseParser, for parsing France24's RSS feeds.
It extracts categories from the 'category' element and handles France24's specific date format.
Supports cost efficiency, reliability, and scalability.
Logs errors to 'logs/france24_errors.log'.

Dependencies:
    - parsers.base_parser: Base class for RSS parsing.
    - dateutil: For date parsing and handling.
"""

from backend.parsers.base_parser import BaseParser
from datetime import datetime
import dateutil


class France24Parser(BaseParser):
    """Parser for France24 RSS feeds.

    Extends BaseParser to handle France24's RSS feeds, specifically extracting
    categories from the 'category' element and handling France24's date format.
    """

    def __init__(self, feeds):
        """
        Initializes the France24Parser with feed URLs and sets the source name.

        Args:
            feeds (dict): A dictionary mapping feed names to URLs.
        """
        super().__init__(feeds)
        self.source_name = "france"

    def extract_categories(self, entry):
        """
        Extract categories from a France24 RSS entry.

        Retrieves categories from the 'category' element or falls back to 'tags'.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser.

        Returns:
            list: A list of category strings.
        """
        # France24 uses the 'category' element for categories
        if hasattr(entry, "category") and entry.category:
            return [entry.category]
        # Fallback to tags if category is not available
        return super().extract_categories(entry)

    def parse_entry(self, entry, rss_feed_url: str):
        """
        Parses an RSS feed entry into a standardized article dictionary.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser.
            rss_feed_url (str): The URL of the RSS feed the entry came from.

        Returns:
            dict: A dictionary representing the article.
        """
        # Get the source from the dc:creator element if available
        source_name = entry.get("dc_creator", "FRANCE 24")
        
        # Extract description and clean it
        description = entry.get("description", "").strip()
        
        # Extract the publication date
        published_date = entry.get("published", "")
        unified_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if published_date:
            try:
                parsed_date = dateutil.parser.parse(published_date)
                unified_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                self.logger.error(
                    f"Failed to parse published date for {entry.get('title', 'Unknown')}: {published_date} - {str(e)}"
                )

        return {
            "title": entry.get("title", ""),
            "description": description,
            "link": entry.link,
            "published": published_date,
            "publication_date": unified_date,
            "categories": self.extract_categories(entry),
            "source": self.source_name,
            "feed_url": rss_feed_url,
        } 