"""
Earnings Call Transcript Collector
Collects earnings call transcripts from various sources.
"""

import logging
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import re
import urllib.parse

logger = logging.getLogger("RetailXAI.TranscriptCollector")


class TranscriptCollector:
    """Collects earnings call transcripts from various sources."""

    def __init__(self, sources: List[Dict], shutdown_event: Optional[threading.Event] = None):
        """Initialize transcript collector.
        
        Args:
            sources: List of source configurations with 'name' and 'base_url' keys
            shutdown_event: Event for graceful shutdown
        """
        self.sources = sources
        self.shutdown_event = shutdown_event
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RetailXAI Data Collector (contact@retailxai.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 5.0  # 5 seconds between requests

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping transcript operations")
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

    def _extract_company_from_title(self, title: str) -> str:
        """Extract company name from transcript title."""
        retail_companies = [
            'Walmart', 'Target', 'Costco', 'Kroger', 'Dollar General', 'Dollar Tree',
            'Amazon', 'BJ\'s', 'Five Below', 'Ollie\'s', 'Home Depot', 'Lowe\'s',
            'Best Buy', 'Macy\'s', 'Kohl\'s', 'Nordstrom', 'TJ Maxx', 'Ross',
            'Burlington', 'Marshalls', 'Sephora', 'Ulta', 'CVS', 'Walgreens'
        ]
        
        title_lower = title.lower()
        for company in retail_companies:
            if company.lower() in title_lower:
                return company
        
        return "Unknown"

    def _extract_quarter_from_title(self, title: str) -> str:
        """Extract quarter information from transcript title."""
        quarter_patterns = [
            r'Q[1-4]\s*\d{4}',
            r'Q[1-4]\s*20\d{2}',
            r'first\s+quarter\s+20\d{2}',
            r'second\s+quarter\s+20\d{2}',
            r'third\s+quarter\s+20\d{2}',
            r'fourth\s+quarter\s+20\d{2}'
        ]
        
        for pattern in quarter_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group()
        
        return "Unknown"

    def _extract_transcript_content(self, url: str) -> str:
        """Extract transcript content from URL."""
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find transcript content
            content_selectors = [
                '.transcript-content',
                '.earnings-transcript',
                '.call-transcript',
                '.transcript',
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main'
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
            logger.warning(f"Error extracting transcript content from {url}: {e}")
            return ""

    def collect_motley_fool_transcripts(self) -> List[Dict]:
        """Collect transcripts from Motley Fool."""
        if self._check_shutdown():
            return []
            
        base_url = "https://www.fool.com/earnings-call-transcripts/"
        items = []
        
        try:
            self._rate_limit()
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find transcript links
            transcript_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'earnings-call-transcript' in href.lower():
                    if href.startswith('/'):
                        href = 'https://www.fool.com' + href
                    transcript_links.append(href)
            
            # Process each transcript
            for url in transcript_links[:10]:  # Limit to first 10
                if self._check_shutdown():
                    break
                    
                try:
                    self._rate_limit()
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract title
                    title = ""
                    title_element = soup.find('h1')
                    if title_element:
                        title = self._clean_text(title_element.get_text())
                    
                    # Extract content
                    content = self._extract_transcript_content(url)
                    
                    if title and content:
                        company = self._extract_company_from_title(title)
                        quarter = self._extract_quarter_from_title(title)
                        
                        item = {
                            'source': 'transcript',
                            'url': self._normalize_url(url),
                            'title': title,
                            'published_at': datetime.now().isoformat(),
                            'summary': content[:500] if content else '',
                            'metadata': {
                                'source_name': 'Motley Fool',
                                'company': company,
                                'quarter': quarter,
                                'full_content': content,
                                'url': url
                            }
                        }
                        
                        items.append(item)
                        
                except Exception as e:
                    logger.warning(f"Error processing Motley Fool transcript {url}: {e}")
                    continue
            
            logger.info(f"Collected {len(items)} transcripts from Motley Fool")
            return items
            
        except Exception as e:
            logger.error(f"Error collecting Motley Fool transcripts: {e}")
            return []

    def collect_seeking_alpha_transcripts(self) -> List[Dict]:
        """Collect transcripts from Seeking Alpha."""
        if self._check_shutdown():
            return []
            
        base_url = "https://seekingalpha.com/earnings/earnings-call-transcripts"
        items = []
        
        try:
            self._rate_limit()
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find transcript links
            transcript_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'earnings-call-transcript' in href.lower():
                    if href.startswith('/'):
                        href = 'https://seekingalpha.com' + href
                    transcript_links.append(href)
            
            # Process each transcript
            for url in transcript_links[:10]:  # Limit to first 10
                if self._check_shutdown():
                    break
                    
                try:
                    self._rate_limit()
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract title
                    title = ""
                    title_element = soup.find('h1')
                    if title_element:
                        title = self._clean_text(title_element.get_text())
                    
                    # Extract content
                    content = self._extract_transcript_content(url)
                    
                    if title and content:
                        company = self._extract_company_from_title(title)
                        quarter = self._extract_quarter_from_title(title)
                        
                        item = {
                            'source': 'transcript',
                            'url': self._normalize_url(url),
                            'title': title,
                            'published_at': datetime.now().isoformat(),
                            'summary': content[:500] if content else '',
                            'metadata': {
                                'source_name': 'Seeking Alpha',
                                'company': company,
                                'quarter': quarter,
                                'full_content': content,
                                'url': url
                            }
                        }
                        
                        items.append(item)
                        
                except Exception as e:
                    logger.warning(f"Error processing Seeking Alpha transcript {url}: {e}")
                    continue
            
            logger.info(f"Collected {len(items)} transcripts from Seeking Alpha")
            return items
            
        except Exception as e:
            logger.error(f"Error collecting Seeking Alpha transcripts: {e}")
            return []

    def collect_all_transcripts(self) -> List[Dict]:
        """Collect transcripts from all configured sources.
        
        Returns:
            List of all collected items
        """
        if self._check_shutdown():
            return []
            
        all_items = []
        
        # Collect from Motley Fool
        motley_fool_items = self.collect_motley_fool_transcripts()
        all_items.extend(motley_fool_items)
        
        # Collect from Seeking Alpha
        seeking_alpha_items = self.collect_seeking_alpha_transcripts()
        all_items.extend(seeking_alpha_items)
        
        logger.info(f"Collected {len(all_items)} total transcripts")
        return all_items

