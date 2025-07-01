"""
The Daily Wire specific parser for fetching and processing RSS feeds.

Extends BaseParser to handle The Daily Wire RSS feeds, setting the source name
to 'daily_wire'. Relies on the base implementation as the feed uses standard
RSS tags like <title>, <link>, <description>, <pubDate>, <content:encoded>.

Dependencies:
    - backend.parsers.base_parser: For base RSS parsing functionality.

Usage:
    >>> from backend.parsers.dailywire_parser import DailyWireParser
    >>> feeds = {'main': 'https://www.dailywire.com/feeds/rss.xml'}
    >>> parser = DailyWireParser(feeds)
    >>> parser.run()
    # Collects articles, logging errors to logs/daily_wire_errors.log
"""

import logging
import os
import feedparser
import requests
import time
import random
from backend.parsers.base_parser import BaseParser
from backend.src.news_utils import get_random_headers

class DailyWireParser(BaseParser):
    def __init__(self, feeds):
        """
        Initializes a parser for The Daily Wire RSS feeds.

        Args:
            feeds (dict): A dictionary mapping feed names to URLs.
                          Example: {'main': 'https://www.dailywire.com/feeds/rss.xml'}
        """
        # Initialize the BaseParser first
        super().__init__(feeds)

        # Set the specific source name *after* base initialization
        self.source_name = "daily_wire"

        # Configure a specific logger for this parser instance
        # Note: Log file path depends on BaseParser's logging setup.
        self.logger = logging.getLogger(self.source_name)
        # BaseParser's file handler might still log errors to base_errors.log
        # unless we explicitly add another handler here. For now, rely on the name.
        self.logger.info(f"Initialized DailyWireParser with {len(feeds)} feed(s).")

    # No override needed for extract_categories.
    # No override needed for parse_entry.
    # No override needed for run.

    def fetch_feed(self, url):
        """
        Overrides BaseParser.fetch_feed specifically for Daily Wire.
        Fetches content using requests, decodes as UTF-8 ignoring errors,
        and then parses with feedparser. Includes basic delay logic.
        """
        try:
            elapsed = time.time() - self.last_fetch_time
            delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
            if elapsed < delay:
                time.sleep(delay - elapsed)

            headers = get_random_headers()
            self.logger.info(f"Fetching URL (using requests): {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            content_string = response.content.decode('utf-8', errors='ignore')
            self.logger.debug(f"Successfully fetched and decoded content from {url}")
            self.last_fetch_time = time.time()

            feed = feedparser.parse(content_string)

            if feed.bozo:
                exception_details = getattr(feed, 'bozo_exception', 'Unknown feedparser error')
                self.logger.error(f"Feed parsing error (bozo): {exception_details} for URL {url}")
                raise ValueError(f"Feedparser bozo error: {exception_details}")

            self.logger.info(f"Successfully parsed feed, found {len(feed.entries)} entries for {url}")
            return feed
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Requests fetch failed for {url}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"General fetch_feed error for {url}: {str(e)}")
            raise

    def run(self):
        """
        Overrides BaseParser.run.
        Executes the RSS feed parsing process for all configured feeds.
        """
        self.articles = [] # Ensure articles list is reset
        for feed_name, url in self.feeds.items():
            try:
                # Call the overridden fetch_feed (defined above)
                feed = self.fetch_feed(url)

                if not feed.entries:
                    continue

                for i, entry in enumerate(feed.entries):
                    # Call inherited validation
                    is_valid = self.validate_entry(entry)
                    if not is_valid:
                        continue

                    # Call inherited time window check
                    pub_date_str = entry.get("published", "") # Use 'published' as per BaseParser logic
                    is_recent = self.is_within_time_window(pub_date_str)

                    if is_recent:
                        # Call the inherited parse_entry
                        article = self.parse_entry(entry, url)
                        self.articles.append(article)

            except Exception as e:
                # Log using this instance's logger
                self.logger.error(f"Failed to process feed '{feed_name}' ({url}): {str(e)}", exc_info=True)
                # Print for immediate visibility
                print(f"--- [{self.source_name}] ❌ ERROR processing feed '{feed_name}': {str(e)} ---")
                continue # Continue to the next feed if one fails

    def parse(self):
        """
        Returns the list of parsed articles collected by run().
        """
        self.logger.info(f"Parsing complete. Returning {len(self.articles)} articles for {self.source_name}.")
        return self.articles 