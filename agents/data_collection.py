import json
import logging
import re
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp

# Optional imports with graceful fallbacks
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from .base_agent import BaseAgent, AgentConfig, AgentResult
from entities import Company, Transcript

logger = logging.getLogger("RetailXAI.DataCollection")


class LinkedInAgent(BaseAgent):
    """Agent for collecting LinkedIn posts from company pages."""

    def __init__(self, config: AgentConfig, companies: List[Company], shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.companies = companies
        self.api_key = config.config.get('api_key')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'X-Restli-Protocol-Version': '2.0.0'
        }

    def validate_config(self) -> bool:
        """Validate LinkedIn agent configuration."""
        if not self.api_key:
            self.logger.error("LinkedIn API key not provided")
            return False
        return True

    async def execute(self) -> AgentResult:
        """Execute LinkedIn data collection."""
        if not self.validate_config():
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error="Invalid configuration"
            )

        collected_posts = []
        
        try:
            for company in self.companies:
                if self._check_shutdown():
                    break
                    
                posts = await self._fetch_company_posts(company)
                collected_posts.extend(posts)
                
            self.logger.info(f"Collected {len(collected_posts)} LinkedIn posts")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=collected_posts
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _fetch_company_posts(self, company: Company) -> List[Transcript]:
        """Fetch recent posts from a company's LinkedIn page."""
        posts = []
        
        # Simulate LinkedIn API call (actual implementation would use LinkedIn API)
        # For demo purposes, creating sample data structure
        sample_posts = [
            {
                'id': f'linkedin_{company.name.lower()}_001',
                'text': f'Sample LinkedIn post from {company.name} about retail trends and innovation.',
                'created_time': datetime.now().isoformat(),
                'title': f'{company.name} - LinkedIn Update'
            }
        ]
        
        for post_data in sample_posts:
            transcript = Transcript(
                content=post_data['text'],
                company=company.name,
                source_id=post_data['id'],
                title=post_data['title'],
                published_at=datetime.fromisoformat(post_data['created_time'].replace('Z', '+00:00')),
                source_type='linkedin'
            )
            posts.append(transcript)
            
        return posts


class NewsAPIAgent(BaseAgent):
    """Agent for collecting news articles from News API."""

    def __init__(self, config: AgentConfig, companies: List[Company], shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.companies = companies
        self.api_key = config.config.get('api_key')
        self.base_url = 'https://newsapi.org/v2'

    def validate_config(self) -> bool:
        """Validate News API agent configuration."""
        if not self.api_key:
            self.logger.error("News API key not provided")
            return False
        return True

    async def execute(self) -> AgentResult:
        """Execute news collection."""
        if not self.validate_config():
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error="Invalid configuration"
            )

        collected_articles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for company in self.companies:
                    if self._check_shutdown():
                        break
                        
                    articles = await self._fetch_company_news(session, company)
                    collected_articles.extend(articles)
                    
            self.logger.info(f"Collected {len(collected_articles)} news articles")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=collected_articles
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _fetch_company_news(self, session: aiohttp.ClientSession, company: Company) -> List[Transcript]:
        """Fetch recent news articles about a company."""
        articles = []
        
        params = {
            'q': f'"{company.name}" AND (earnings OR retail OR financial)',
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 10,
            'apiKey': self.api_key
        }
        
        try:
            async with session.get(f'{self.base_url}/everything', params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for article in data.get('articles', []):
                        if article.get('content') and len(article['content']) > 100:
                            transcript = Transcript(
                                content=article['content'],
                                company=company.name,
                                source_id=article['url'],
                                title=article['title'],
                                published_at=datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')),
                                source_type='news_api'
                            )
                            articles.append(transcript)
                else:
                    self.logger.warning(f"News API request failed: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Error fetching news for {company.name}: {e}")
            
        return articles


class RedditAgent(BaseAgent):
    """Agent for collecting Reddit posts about companies."""

    def __init__(self, config: AgentConfig, companies: List[Company], shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.companies = companies
        self.client_id = config.config.get('client_id')
        self.client_secret = config.config.get('client_secret')
        self.user_agent = config.config.get('user_agent', 'RetailXAI:1.0')
        self.subreddits = config.config.get('subreddits', ['investing', 'stocks', 'business'])

    def validate_config(self) -> bool:
        """Validate Reddit agent configuration."""
        if not PRAW_AVAILABLE:
            self.logger.error("PRAW library not available - install with: pip install praw")
            return False
        if not self.client_id or not self.client_secret:
            self.logger.error("Reddit API credentials not provided")
            return False
        return True

    async def execute(self) -> AgentResult:
        """Execute Reddit data collection."""
        if not self.validate_config():
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error="Invalid configuration"
            )

        collected_posts = []
        
        try:
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            
            for company in self.companies:
                if self._check_shutdown():
                    break
                    
                posts = await self._fetch_company_reddit_posts(reddit, company)
                collected_posts.extend(posts)
                
            self.logger.info(f"Collected {len(collected_posts)} Reddit posts")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=collected_posts
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _fetch_company_reddit_posts(self, reddit, company: Company) -> List[Transcript]:
        """Fetch Reddit posts mentioning a company."""
        posts = []
        
        for subreddit_name in self.subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Search for posts mentioning the company
                for submission in subreddit.search(company.name, time_filter='week', limit=10):
                    if len(submission.selftext) > 50:  # Only get substantial posts
                        transcript = Transcript(
                            content=submission.selftext,
                            company=company.name,
                            source_id=submission.id,
                            title=submission.title,
                            published_at=datetime.fromtimestamp(submission.created_utc),
                            source_type='reddit'
                        )
                        posts.append(transcript)
                        
            except Exception as e:
                self.logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                
        return posts


class EarningsAgent(BaseAgent):
    """Agent specifically for collecting earnings call transcripts and financial documents."""

    def __init__(self, config: AgentConfig, companies: List[Company], shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.companies = companies
        self.sec_api_key = config.config.get('sec_api_key')
        self.earnings_sources = config.config.get('earnings_sources', [
            'https://www.sec.gov/cgi-bin/browse-edgar',
            'https://seekingalpha.com/earnings'
        ])

    def validate_config(self) -> bool:
        """Validate earnings agent configuration."""
        return True  # Can work without API keys using public sources

    async def execute(self) -> AgentResult:
        """Execute earnings data collection."""
        collected_documents = []
        
        try:
            for company in self.companies:
                if self._check_shutdown():
                    break
                    
                documents = await self._fetch_earnings_documents(company)
                collected_documents.extend(documents)
                
            self.logger.info(f"Collected {len(collected_documents)} earnings documents")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=collected_documents
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _fetch_earnings_documents(self, company: Company) -> List[Transcript]:
        """Fetch recent earnings documents for a company."""
        documents = []
        
        # Simulate earnings document collection
        # In real implementation, this would scrape SEC filings, earnings call sites, etc.
        sample_earnings = {
            'content': f'Q4 2024 Earnings Call Transcript for {company.name}. Revenue growth of 8% year-over-year driven by strong consumer demand and operational efficiency improvements.',
            'source_id': f'earnings_{company.name.lower()}_q4_2024',
            'title': f'{company.name} Q4 2024 Earnings Call',
            'published_at': datetime.now() - timedelta(days=7)
        }
        
        transcript = Transcript(
            content=sample_earnings['content'],
            company=company.name,
            source_id=sample_earnings['source_id'],
            title=sample_earnings['title'],
            published_at=sample_earnings['published_at'],
            source_type='earnings_call'
        )
        documents.append(transcript)
        
        return documents