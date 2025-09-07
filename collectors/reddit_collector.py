"""
Reddit Mentions Collector
Collects retail company mentions from Reddit subreddits.
"""

import logging
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import json
import urllib.parse

logger = logging.getLogger("RetailXAI.RedditCollector")


class RedditCollector:
    """Collects retail company mentions from Reddit subreddits."""

    def __init__(self, subreddit_queries: List[Dict], shutdown_event: Optional[threading.Event] = None):
        """Initialize Reddit collector.
        
        Args:
            subreddit_queries: List of subreddit-query pairs
            shutdown_event: Event for graceful shutdown
        """
        self.subreddit_queries = subreddit_queries
        self.shutdown_event = shutdown_event
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RetailXAI Data Collector (contact@retailxai.com)',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 3.0  # 3 seconds between requests

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping Reddit operations")
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
        
        # Remove Reddit markdown
        text = text.replace('**', '').replace('*', '')
        text = text.replace('~~', '').replace('`', '')
        
        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

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

    def collect_subreddit_query(self, subreddit: str, query: str) -> List[Dict]:
        """Collect mentions from a specific subreddit and query.
        
        Args:
            subreddit: Subreddit name (without r/)
            query: Search query
            
        Returns:
            List of collected items
        """
        if self._check_shutdown():
            return []
            
        # Build Reddit search URL
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={encoded_query}&restrict_sr=on&sort=new&t=week"
        
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or 'children' not in data['data']:
                logger.warning(f"No data found for subreddit {subreddit} with query {query}")
                return []
            
            items = []
            
            for post in data['data']['children']:
                if self._check_shutdown():
                    break
                    
                try:
                    post_data = post['data']
                    
                    # Parse creation date
                    created_utc = post_data.get('created_utc', 0)
                    if created_utc:
                        pub_date = datetime.fromtimestamp(created_utc).isoformat()
                    else:
                        pub_date = datetime.now().isoformat()
                    
                    # Extract content
                    title = self._clean_text(post_data.get('title', ''))
                    selftext = self._clean_text(post_data.get('selftext', ''))
                    
                    # Combine title and selftext for full content
                    full_content = f"{title}\n\n{selftext}".strip()
                    
                    # Detect mentioned companies
                    mentioned_companies = self._detect_retail_companies(full_content)
                    
                    # Build Reddit URL
                    reddit_url = f"https://www.reddit.com{post_data.get('permalink', '')}"
                    
                    item = {
                        'source': 'reddit',
                        'url': self._normalize_url(reddit_url),
                        'title': title,
                        'published_at': pub_date,
                        'summary': selftext[:500] if selftext else title[:500],
                        'metadata': {
                            'subreddit': subreddit,
                            'query': query,
                            'full_content': full_content,
                            'mentioned_companies': mentioned_companies,
                            'author': post_data.get('author', ''),
                            'score': post_data.get('score', 0),
                            'num_comments': post_data.get('num_comments', 0),
                            'permalink': post_data.get('permalink', ''),
                            'upvote_ratio': post_data.get('upvote_ratio', 0),
                            'is_self': post_data.get('is_self', False),
                            'over_18': post_data.get('over_18', False),
                            'spoiler': post_data.get('spoiler', False),
                            'locked': post_data.get('locked', False),
                            'stickied': post_data.get('stickied', False)
                        }
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Error processing Reddit post: {e}")
                    continue
            
            logger.info(f"Collected {len(items)} items from r/{subreddit} with query '{query}'")
            return items
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Reddit data from r/{subreddit}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error collecting Reddit data from r/{subreddit}: {e}")
            return []

    def collect_all_subreddits(self) -> List[Dict]:
        """Collect mentions from all configured subreddits and queries.
        
        Returns:
            List of all collected items
        """
        if self._check_shutdown():
            return []
            
        all_items = []
        
        for config in self.subreddit_queries:
            if self._check_shutdown():
                break
                
            subreddit = config['subreddit']
            query = config['query']
            
            items = self.collect_subreddit_query(subreddit, query)
            all_items.extend(items)
            
            # Delay between subreddit queries
            time.sleep(2)
            
        logger.info(f"Collected {len(all_items)} total items from Reddit")
        return all_items

