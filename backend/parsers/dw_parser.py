# backend/parsers/dw_parser.py
"""
Parser for Deutsche Welle (DW) RSS feeds.

This module defines DWParser, a subclass of BaseParser, for parsing DW's RDF RSS 1.0 feeds.
It extracts categories from <dc:subject> tags, ensuring compatibility with DW's feed structure.
Supports cost efficiency (400 chars/article), reliability (300s delays), and scalability.
Logs errors to 'logs/dw_errors.log'.

Dependencies:
    - parsers.base_parser: Base class for RSS parsing.
    - feedparser: For RSS parsing.
"""

from backend.parsers.base_parser import BaseParser
from datetime import datetime
import dateutil


class DWParser(BaseParser):
    """Parser for Deutsche Welle (DW) RSS feeds.

    Extends BaseParser to handle DW's RDF RSS 1.0 feeds, specifically extracting
    categories from <dc:subject> tags. Overrides run to handle publication dates
    using 'updated' as a fallback due to feedparser's mapping of <dc:date>.
    """

    def __init__(self, feeds):
        """
        Initializes the DWParser with feed URLs and sets the source name.

        Args:
            feeds (dict): A dictionary mapping feed names to URLs (e.g., {'general': 'https://rss.dw.com/rdf/rss-en-all'}).
        """
        super().__init__(feeds)
        self.source_name = "dw"

    def extract_categories(self, entry):
        """
        Extract categories from a DW RSS entry.

        Retrieves categories from 'dc_subject' (mapped from <dc:subject>) or falls back to 'tags'.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser.

        Returns:
            list: A list of category strings.
        """
        if hasattr(entry, "dc_subject") and entry.dc_subject:
            return [entry.dc_subject]
        return [tag.get("term") for tag in entry.get("tags", []) if tag.get("term")]

    def run(self):
        """
        Executes the RSS feed parsing process for DW feeds.

        Fetches and processes each feed, applying validation and date filtering.
        Uses 'updated' as a fallback for publication date due to feedparser's mapping behavior.

        Returns:
            None: Updates `self.articles` with parsed articles.
        """
        self.articles = []
        current_date = datetime.now(dateutil.tz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        for feed_name, url in self.feeds.items():
            try:
                feed = self.fetch_feed(url)
                self.logger.info(
                    f"Fetched {len(feed.entries)} entries from {feed_name} feed ({url})"
                )
                for entry in feed.entries:
                    if not self.validate_entry(entry):
                        self.logger.info(
                            f"Skipped entry in {feed_name}: Invalid entry - {entry.get('title', 'Unknown')}"
                        )
                        continue

                    # Use 'updated' as the publication date since <dc:date> is mapped there
                    published_date = entry.get(
                        "published", entry.get("updated", current_date)
                    )
                    if published_date == current_date:
                        self.logger.warning(
                            f"Missing publication date for entry in {feed_name}, using current date: {entry.get('title', 'Unknown')}"
                        )
                    else:
                        try:
                            parsed_date = dateutil.parser.parse(published_date)
                            published_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                            entry["published"] = published_date
                        except Exception as e:
                            self.logger.error(
                                f"Failed to parse date in {feed_name}: {published_date} - {str(e)} - {entry.get('title', 'Unknown')}"
                            )
                            entry["published"] = current_date
                            published_date = current_date

                    if not self.is_within_time_window(published_date):
                        self.logger.info(
                            f"Skipped entry in {feed_name}: Not within time window (published: {published_date}) - {entry.get('title', 'Unknown')}"
                        )
                        continue

                    article = self.parse_entry(entry, url)
                    self.articles.append(article)
            except Exception as e:
                self.logger.error(f"Failed to process {feed_name}: {str(e)}")
                continue
        self.logger.info(
            f"Collected {len(self.articles)} articles for DW after filtering"
        )

    def parse_entry(self, entry, rss_feed_url: str):
        """
        Parses an RSS feed entry into a standardized article dictionary.

        Args:
            entry (feedparser.FeedParserDict): An RSS entry object from feedparser.
            rss_feed_url (str): The URL of the RSS feed the entry came from.

        Returns:
            dict: A dictionary representing the article.
        """
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
            "description": entry.get("description", ""),
            "link": entry.link,
            "published": published_date,
            "publication_date": unified_date,
            "categories": self.extract_categories(entry),
            "source": self.source_name,
            "feed_url": rss_feed_url,
        }
