"""
Trade Media RSS Collector
Collects retail industry news from trade publication RSS feeds.
"""

import logging
import time
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import re

logger = logging.getLogger("RetailXAI.TradeMediaCollector")


class TradeMediaCollector:
    """Collects retail industry news from trade publication RSS feeds."""

    def __init__(self, feeds: List[Dict], shutdown_event: Optional[threading.Event] = None):
        """Initialize trade media collector.
        
        Args:
            feeds: List of feed configurations with 'url' and 'publication' keys
            shutdown_event: Event for graceful shutdown
        """
        self.feeds = feeds
        self.shutdown_event = shutdown_event
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RetailXAI Data Collector (contact@retailxai.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping trade media operations")
            return True
        return False

    def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing tracking parameters."""
        if '?' in url:
            url = url.split('?')[0]
        return url

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def _extract_article_content(self, url: str) -> str:
        """Extract full article content from URL."""
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find main content area
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.main-content',
                '.story-body',
                '.article-body'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text()
                    break
            
            if not content:
                # Fallback to body text
                body = soup.find('body')
                if body:
                    content = body.get_text()
            
            return self._clean_text(content)
            
        except Exception as e:
            logger.warning(f"Error extracting content from {url}: {e}")
            return ""

    def _detect_retail_companies(self, text: str) -> List[str]:
        """Detect mentioned retail companies in text."""
        retail_companies = [
            'Walmart', 'Target', 'Costco', 'Kroger', 'Dollar General', 'Dollar Tree',
            'Amazon', 'BJ\'s', 'Five Below', 'Ollie\'s', 'Home Depot', 'Lowe\'s',
            'Best Buy', 'Macy\'s', 'Kohl\'s', 'Nordstrom', 'TJ Maxx', 'Ross',
            'Burlington', 'Marshalls', 'Sephora', 'Ulta', 'CVS', 'Walgreens'
        ]
        
        mentioned = []
        text_lower = text.lower()
        for company in retail_companies:
            if company.lower() in text_lower:
                mentioned.append(company)
        
        return mentioned

    def collect_feed(self, feed_config: Dict) -> List[Dict]:
        """Collect content from a single RSS feed.
        
        Args:
            feed_config: Feed configuration with 'url' and 'publication' keys
            
        Returns:
            List of collected items
        """
        if self._check_shutdown():
            return []
            
        feed_url = feed_config['url']
        publication = feed_config['publication']
        
        try:
            self._rate_limit()
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing issues for {feed_url}: {feed.bozo_exception}")
            
            items = []
            
            for entry in feed.entries:
                if self._check_shutdown():
                    break
                    
                try:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6]).isoformat()
                    else:
                        pub_date = datetime.now().isoformat()
                    
                    # Extract content
                    summary = ""
                    if hasattr(entry, 'summary'):
                        summary = self._clean_text(entry.summary)
                    elif hasattr(entry, 'description'):
                        summary = self._clean_text(entry.description)
                    
                    # Extract full article content
                    full_content = summary
                    if hasattr(entry, 'link') and entry.link:
                        article_content = self._extract_article_content(entry.link)
                        if article_content and len(article_content) > len(summary):
                            full_content = article_content
                    
                    # Detect mentioned companies
                    mentioned_companies = self._detect_retail_companies(full_content)
                    
                    item = {
                        'source': 'trade_rss',
                        'url': self._normalize_url(entry.link) if hasattr(entry, 'link') else '',
                        'title': self._clean_text(entry.title) if hasattr(entry, 'title') else '',
                        'published_at': pub_date,
                        'summary': summary[:500] if summary else '',  # Truncate summary
                        'metadata': {
                            'publication': publication,
                            'feed_url': feed_url,
                            'full_content': full_content,
                            'mentioned_companies': mentioned_companies,
                            'author': getattr(entry, 'author', ''),
                            'tags': getattr(entry, 'tags', [])
                        }
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Error processing entry from {feed_url}: {e}")
                    continue
            
            logger.info(f"Collected {len(items)} items from {publication}")
            return items
            
        except Exception as e:
            logger.error(f"Error collecting from {feed_url}: {e}")
            return []

    def collect_all_feeds(self) -> List[Dict]:
        """Collect content from all configured feeds.
        
        Returns:
            List of all collected items
        """
        if self._check_shutdown():
            return []
            
        all_items = []
        
        for feed_config in self.feeds:
            if self._check_shutdown():
                break
                
            items = self.collect_feed(feed_config)
            all_items.extend(items)
            
            # Delay between feeds
            time.sleep(1)
            
        logger.info(f"Collected {len(all_items)} total items from trade media feeds")
        return all_items

