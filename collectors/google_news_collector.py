"""
Google News RSS Collector
Collects retail company news from Google News RSS feeds.
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
import urllib.parse

logger = logging.getLogger("RetailXAI.GoogleNewsCollector")


class GoogleNewsCollector:
    """Collects retail company news from Google News RSS feeds."""

    def __init__(self, queries: List[str], shutdown_event: Optional[threading.Event] = None):
        """Initialize Google News collector.
        
        Args:
            queries: List of search queries for retail companies
            shutdown_event: Event for graceful shutdown
        """
        self.queries = queries
        self.shutdown_event = shutdown_event
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 3.0  # 3 seconds between requests

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping Google News operations")
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
        """Normalize URL by removing tracking parameters and following redirects."""
        try:
            # Remove Google News tracking parameters
            if 'google.com' in url:
                # Extract the actual URL from Google News redirect
                if 'url=' in url:
                    url = urllib.parse.unquote(url.split('url=')[1].split('&')[0])
            
            # Remove common tracking parameters
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'fbclid', 'gclid']
            if '?' in url:
                base_url, params = url.split('?', 1)
                param_dict = urllib.parse.parse_qs(params)
                for param in tracking_params:
                    param_dict.pop(param, None)
                if param_dict:
                    url = base_url + '?' + urllib.parse.urlencode(param_dict, doseq=True)
                else:
                    url = base_url
            
            return url
        except Exception as e:
            logger.warning(f"Error normalizing URL {url}: {e}")
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
            response = self.session.get(url, timeout=30, allow_redirects=True)
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
                '.article-body',
                '.article-text',
                '.post-body'
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

    def collect_query(self, query: str) -> List[Dict]:
        """Collect news for a single search query.
        
        Args:
            query: Search query string
            
        Returns:
            List of collected items
        """
        if self._check_shutdown():
            return []
            
        # Build Google News RSS URL
        encoded_query = urllib.parse.quote_plus(query)
        feed_url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=en-US&gl=US&ceid=US:en"
        
        try:
            self._rate_limit()
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing issues for query '{query}': {feed.bozo_exception}")
            
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
                    
                    # Extract source information
                    source = ""
                    if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                        source = entry.source.title
                    
                    item = {
                        'source': 'gnews',
                        'url': self._normalize_url(entry.link) if hasattr(entry, 'link') else '',
                        'title': self._clean_text(entry.title) if hasattr(entry, 'title') else '',
                        'published_at': pub_date,
                        'summary': summary[:500] if summary else '',  # Truncate summary
                        'metadata': {
                            'query': query,
                            'feed_url': feed_url,
                            'full_content': full_content,
                            'mentioned_companies': mentioned_companies,
                            'news_source': source,
                            'author': getattr(entry, 'author', ''),
                            'tags': getattr(entry, 'tags', [])
                        }
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Error processing entry for query '{query}': {e}")
                    continue
            
            logger.info(f"Collected {len(items)} items for query: {query}")
            return items
            
        except Exception as e:
            logger.error(f"Error collecting news for query '{query}': {e}")
            return []

    def collect_all_queries(self) -> List[Dict]:
        """Collect news for all configured queries.
        
        Returns:
            List of all collected items
        """
        if self._check_shutdown():
            return []
            
        all_items = []
        
        for query in self.queries:
            if self._check_shutdown():
                break
                
            items = self.collect_query(query)
            all_items.extend(items)
            
            # Delay between queries
            time.sleep(2)
            
        logger.info(f"Collected {len(all_items)} total items from Google News")
        return all_items

