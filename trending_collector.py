import logging
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

import praw
import requests
import tweepy
from bs4 import BeautifulSoup
from newspaper import Article
from textblob import TextBlob

from entities import Company, Transcript

logger = logging.getLogger("RetailXAI.TrendingCollector")


class TrendingTopicsCollector:
    """Collects trending retail topics from Reddit, Twitter, and Google News."""

    def __init__(
        self,
        reddit_config: Dict[str, str],
        twitter_config: Dict[str, str],
        companies: List[Company],
        shutdown_event: Optional[threading.Event] = None,
    ):
        """Initialize TrendingTopicsCollector.

        Args:
            reddit_config: Reddit API configuration.
            twitter_config: Twitter API configuration.
            companies: List of Company entities for relevance filtering.
            shutdown_event: Event for graceful shutdown.
        """
        self.companies = companies
        self.shutdown_event = shutdown_event
        self.retail_keywords = [
            "retail", "ecommerce", "consumer", "shopping", "CPG", "brand",
            "sales", "revenue", "earnings", "profit", "market share",
            "supply chain", "inflation", "pricing", "inventory", "store",
            "customer", "loyalty", "subscription", "digital transformation"
        ]
        
        # Initialize APIs
        self.reddit = self._setup_reddit(reddit_config)
        self.twitter = self._setup_twitter(twitter_config)

    def _setup_reddit(self, config: Dict[str, str]) -> praw.Reddit:
        """Set up Reddit API client.

        Args:
            config: Reddit API credentials.

        Returns:
            Configured Reddit client.
        """
        try:
            return praw.Reddit(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                user_agent=config.get("user_agent", "RetailXAI/1.0"),
                read_only=True
            )
        except Exception as e:
            logger.error(f"Failed to setup Reddit API: {e}")
            return None

    def _setup_twitter(self, config: Dict[str, str]) -> tweepy.API:
        """Set up Twitter API client.

        Args:
            config: Twitter API credentials.

        Returns:
            Configured Twitter client.
        """
        try:
            auth = tweepy.OAuth1UserHandler(
                config["consumer_key"],
                config["consumer_secret"],
                config["access_token"],
                config["access_token_secret"]
            )
            return tweepy.API(auth, wait_on_rate_limit=True)
        except Exception as e:
            logger.error(f"Failed to setup Twitter API: {e}")
            return None

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping trending collection")
            return True
        return False

    def get_trending_topics(self) -> List[Transcript]:
        """Collect trending retail topics from all sources.

        Returns:
            List of Transcript entities with trending topics.
        """
        if self._check_shutdown():
            return []

        all_topics = []
        
        # Collect from Reddit
        reddit_topics = self._get_reddit_trends()
        all_topics.extend(reddit_topics)
        
        if self._check_shutdown():
            return all_topics

        # Collect from Twitter
        twitter_topics = self._get_twitter_trends()
        all_topics.extend(twitter_topics)
        
        if self._check_shutdown():
            return all_topics

        # Collect from Google News
        news_topics = self._get_google_news_trends()
        all_topics.extend(news_topics)

        # Score and filter topics
        scored_topics = self._score_and_filter_topics(all_topics)
        
        logger.info(f"Collected {len(scored_topics)} trending retail topics")
        return scored_topics

    def _get_reddit_trends(self) -> List[Dict]:
        """Get trending topics from Reddit.

        Returns:
            List of topic dictionaries.
        """
        topics = []
        if not self.reddit:
            return topics

        try:
            # Target retail-focused subreddits
            subreddits = [
                "retail", "ecommerce", "business", "investing", "stocks",
                "marketing", "entrepreneur", "smallbusiness", "CPG"
            ]
            
            for subreddit_name in subreddits:
                if self._check_shutdown():
                    break
                    
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    # Get hot posts from last 24 hours
                    for post in subreddit.hot(limit=20):
                        if self._check_shutdown():
                            break
                            
                        if self._is_retail_relevant(post.title + " " + post.selftext):
                            topics.append({
                                "title": post.title,
                                "content": post.selftext or post.title,
                                "source": "reddit",
                                "source_id": f"reddit_{post.id}",
                                "score": post.score,
                                "comments": post.num_comments,
                                "created_at": datetime.fromtimestamp(post.created_utc),
                                "url": f"https://reddit.com{post.permalink}"
                            })
                except Exception as e:
                    logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in Reddit trending collection: {e}")

        return topics

    def _get_twitter_trends(self) -> List[Dict]:
        """Get trending topics from Twitter.

        Returns:
            List of topic dictionaries.
        """
        topics = []
        if not self.twitter:
            return topics

        try:
            # Search for retail-related trending keywords
            for keyword in self.retail_keywords[:5]:  # Limit to avoid rate limits
                if self._check_shutdown():
                    break
                    
                try:
                    tweets = tweepy.Cursor(
                        self.twitter.search_tweets,
                        q=f"{keyword} -RT",  # Exclude retweets
                        result_type="popular",
                        lang="en",
                        since_id=None
                    ).items(10)
                    
                    for tweet in tweets:
                        if self._check_shutdown():
                            break
                            
                        if self._is_retail_relevant(tweet.text):
                            topics.append({
                                "title": tweet.text[:100] + "..." if len(tweet.text) > 100 else tweet.text,
                                "content": tweet.text,
                                "source": "twitter",
                                "source_id": f"twitter_{tweet.id}",
                                "score": tweet.retweet_count + tweet.favorite_count,
                                "comments": tweet.retweet_count,
                                "created_at": tweet.created_at,
                                "url": f"https://twitter.com/status/{tweet.id}"
                            })
                            
                except Exception as e:
                    logger.error(f"Error searching Twitter for '{keyword}': {e}")
                    continue
                    
                # Rate limiting
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error in Twitter trending collection: {e}")

        return topics

    def _get_google_news_trends(self) -> List[Dict]:
        """Get trending topics from Google News.

        Returns:
            List of topic dictionaries.
        """
        topics = []
        
        try:
            # Search for retail news
            search_terms = ["retail trends", "ecommerce news", "consumer spending", "CPG earnings"]
            
            for term in search_terms:
                if self._check_shutdown():
                    break
                    
                try:
                    # Use Google News RSS feed
                    url = f"https://news.google.com/rss/search?q={urlencode({'q': term})}&hl=en-US&gl=US&ceid=US:en"
                    
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')
                    
                    for item in items[:5]:  # Limit per search term
                        if self._check_shutdown():
                            break
                            
                        title = item.title.text if item.title else ""
                        link = item.link.text if item.link else ""
                        pub_date = item.pubDate.text if item.pubDate else ""
                        
                        # Extract full article content
                        article_content = self._extract_article_content(link)
                        
                        if self._is_retail_relevant(title + " " + article_content):
                            # Parse publication date
                            try:
                                created_at = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                            except:
                                created_at = datetime.now()
                            
                            topics.append({
                                "title": title,
                                "content": article_content or title,
                                "source": "google_news",
                                "source_id": f"news_{hash(link)}",
                                "score": self._estimate_news_score(title, article_content),
                                "comments": 0,
                                "created_at": created_at,
                                "url": link
                            })
                            
                except Exception as e:
                    logger.error(f"Error searching Google News for '{term}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in Google News trending collection: {e}")

        return topics

    def _extract_article_content(self, url: str) -> str:
        """Extract content from a news article URL.

        Args:
            url: Article URL.

        Returns:
            Extracted article text.
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text[:2000]  # Limit content length
        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return ""

    def _is_retail_relevant(self, text: str) -> bool:
        """Check if text is relevant to retail industry.

        Args:
            text: Text to check.

        Returns:
            True if retail-relevant, False otherwise.
        """
        text_lower = text.lower()
        
        # Check for retail keywords
        keyword_matches = sum(1 for keyword in self.retail_keywords if keyword in text_lower)
        
        # Check for company mentions
        company_matches = sum(1 for company in self.companies if company.name.lower() in text_lower)
        
        # Must have at least 2 keyword matches or 1 company match
        return keyword_matches >= 2 or company_matches >= 1

    def _estimate_news_score(self, title: str, content: str) -> int:
        """Estimate popularity score for news articles.

        Args:
            title: Article title.
            content: Article content.

        Returns:
            Estimated popularity score.
        """
        score = 0
        
        # Title sentiment and urgency indicators
        urgent_words = ["breaking", "urgent", "alert", "exclusive", "major", "significant"]
        score += sum(10 for word in urgent_words if word in title.lower())
        
        # Company mentions boost score
        for company in self.companies:
            if company.name.lower() in (title + " " + content).lower():
                score += 20
        
        # Content length indicates depth
        score += min(len(content) // 100, 50)
        
        return score

    def _score_and_filter_topics(self, topics: List[Dict]) -> List[Transcript]:
        """Score topics by popularity and convert to Transcript objects.

        Args:
            topics: Raw topic dictionaries.

        Returns:
            List of scored and filtered Transcript objects.
        """
        # Remove duplicates based on similar titles
        unique_topics = self._deduplicate_topics(topics)
        
        # Calculate composite popularity score
        for topic in unique_topics:
            popularity_score = self._calculate_popularity_score(topic)
            topic["popularity_score"] = popularity_score
        
        # Sort by popularity and take top topics
        sorted_topics = sorted(unique_topics, key=lambda x: x["popularity_score"], reverse=True)
        top_topics = sorted_topics[:20]  # Limit to top 20 trending topics
        
        # Convert to Transcript objects
        transcripts = []
        for topic in top_topics:
            # Determine company association
            company_name = self._match_company(topic["title"] + " " + topic["content"])
            
            transcript = Transcript(
                content=topic["content"],
                company=company_name or "General Retail",
                source_id=topic["source_id"],
                title=topic["title"],
                published_at=topic["created_at"],
                source_type=f"trending_{topic['source']}"
            )
            transcripts.append(transcript)
        
        return transcripts

    def _deduplicate_topics(self, topics: List[Dict]) -> List[Dict]:
        """Remove duplicate topics based on title similarity.

        Args:
            topics: List of topic dictionaries.

        Returns:
            Deduplicated list of topics.
        """
        unique_topics = []
        seen_titles = set()
        
        for topic in topics:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', topic["title"].lower())
            title_words = set(normalized_title.split())
            
            # Check if similar title already exists
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                # If 70% of words overlap, consider duplicate
                overlap = len(title_words.intersection(seen_words))
                if overlap / max(len(title_words), len(seen_words)) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles.add(normalized_title)
                unique_topics.append(topic)
        
        return unique_topics

    def _calculate_popularity_score(self, topic: Dict) -> int:
        """Calculate composite popularity score for a topic.

        Args:
            topic: Topic dictionary.

        Returns:
            Popularity score.
        """
        base_score = topic.get("score", 0)
        comments = topic.get("comments", 0)
        
        # Time decay - newer content gets higher score
        age_hours = (datetime.now() - topic["created_at"]).total_seconds() / 3600
        time_factor = max(0.1, 1 - (age_hours / 24))  # Decay over 24 hours
        
        # Source weight
        source_weights = {
            "reddit": 1.0,
            "twitter": 0.8,
            "google_news": 1.2  # News tends to be more authoritative
        }
        source_weight = source_weights.get(topic["source"], 1.0)
        
        # Content quality (sentiment analysis)
        content_text = topic["title"] + " " + topic["content"]
        sentiment = TextBlob(content_text).sentiment
        sentiment_boost = max(0, sentiment.polarity * 10)  # Positive sentiment boost
        
        # Company relevance boost
        company_boost = 0
        for company in self.companies:
            if company.name.lower() in content_text.lower():
                company_boost += 20
        
        final_score = int(
            (base_score + comments * 2 + sentiment_boost + company_boost) 
            * time_factor 
            * source_weight
        )
        
        return final_score

    def _match_company(self, text: str) -> Optional[str]:
        """Match text to a specific company.

        Args:
            text: Text to analyze.

        Returns:
            Company name if matched, None otherwise.
        """
        text_lower = text.lower()
        
        # Sort companies by name length (longer names first for better matching)
        sorted_companies = sorted(self.companies, key=lambda c: len(c.name), reverse=True)
        
        for company in sorted_companies:
            if company.name.lower() in text_lower:
                return company.name
            
            # Also check company keywords
            for keyword in company.keywords:
                if keyword.lower() in text_lower:
                    return company.name
        
        return None