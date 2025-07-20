import logging
import threading
from typing import List, Optional
import datetime
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from entities import Company, Transcript

logger = logging.getLogger("RetailXAI.RSSCollector")


class RSSCollector:
    """Collects press releases from RSS feeds."""

    def __init__(self, feeds: List[str], companies: List[Company], shutdown_event: Optional[threading.Event] = None):
        """Initialize RSSCollector with feeds and companies.

        Args:
            feeds: List of RSS feed URLs.
            companies: List of Company entities.
            shutdown_event: Event for graceful shutdown.
        """
        self.feeds = feeds
        self.companies = companies
        self.shutdown_event = shutdown_event

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping RSS operations")
            return True
        return False

    def get_transcripts(self) -> List[Transcript]:
        """Fetch recent press releases from RSS feeds.

        Returns:
            List of Transcript entities.
        """
        if self._check_shutdown():
            return []

        transcripts = []
        for feed_url in self.feeds:
            if self._check_shutdown():
                break
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    if self._check_shutdown():
                        break
                    if self._is_recent(entry.get("published_parsed")):
                        company_name = self._match_company(entry.get("title", ""))
                        content = self._extract_full_content(entry.get("link", ""))
                        if content and company_name:
                            transcripts.append(
                                Transcript(
                                    content=content,
                                    company=company_name,
                                    source_id=entry.get("link", ""),
                                    title=entry.get("title", ""),
                                    published_at=self._parse_published_time(entry.get("published", "")),
                                    source_type="rss",
                                )
                            )
            except Exception as e:
                logger.error(f"Error processing feed {feed_url}: {e}")
        logger.info(f"Collected {len(transcripts)} press releases")
        return transcripts

    def _match_company(self, title: str) -> Optional[str]:
        """Match a press release title to a company name.

        Args:
            title: Press release title.

        Returns:
            Company name if matched, None otherwise.
        """
        for company in self.companies:
            if company.name.lower() in title.lower():
                return company.name
        return None

    def _extract_full_content(self, url: str) -> str:
        """Extract full content from a press release URL.

        Args:
            url: Press release URL.

        Returns:
            Extracted content or empty string if failed.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            content_selectors = [
                ".press-release-content",
                ".news-content",
                "article",
                ".entry-content",
            ]
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    return content.get_text(strip=True)[:5000]
            return soup.get_text(strip=True)[:5000]
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""

    def _is_recent(self, published_struct) -> bool:
        """Check if a feed item is recent (within 48 hours).

        Args:
            published_struct: Parsed publication time.

        Returns:
            True if recent, False otherwise.
        """
        if not published_struct:
            return False
        try:
            published_time = time.mktime(published_struct)
            age_seconds = time.time() - published_time
            return age_seconds < (48 * 3600)
        except Exception as e:
            logger.error(f"Error parsing published date: {e}")
            return False

    def _parse_published_time(self, published: str) -> datetime.datetime:
        """Parse published time from RSS feed.

        Args:
            published: Published time string.

        Returns:
            Parsed datetime or current time if parsing fails.
        """
        try:
            return datetime.datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            return datetime.datetime.now()
