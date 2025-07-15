#!/usr/bin/env python3
"""Test script for the trending topics collector."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to path to import our modules
sys.path.append('.')

from entities import Company
from trending_collector import TrendingTopicsCollector

def create_test_companies():
    """Create test companies for the collector."""
    return [
        Company(
            name="Amazon",
            youtube_channels=["amazon"],
            rss_feed=None,
            keywords=["amazon", "aws", "ecommerce", "prime"]
        ),
        Company(
            name="Walmart",
            youtube_channels=["walmart"],
            rss_feed=None,
            keywords=["walmart", "retail", "supercenter"]
        ),
        Company(
            name="Target",
            youtube_channels=["target"],
            rss_feed=None,
            keywords=["target", "bullseye", "retail"]
        )
    ]

def test_trending_collector():
    """Test the trending topics collector."""
    print("Testing Trending Topics Collector...")
    
    # Load environment variables
    load_dotenv("config/.env")
    
    # Create test configuration
    reddit_config = {
        "client_id": os.getenv("REDDIT_CLIENT_ID", "test_id"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "test_secret"),
        "user_agent": "RetailXAI/1.0"
    }
    
    twitter_config = {
        "consumer_key": os.getenv("TWITTER_CONSUMER_KEY", "test_key"),
        "consumer_secret": os.getenv("TWITTER_CONSUMER_SECRET", "test_secret"),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN", "test_token"),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "test_token_secret")
    }
    
    companies = create_test_companies()
    
    # Initialize collector
    try:
        collector = TrendingTopicsCollector(
            reddit_config=reddit_config,
            twitter_config=twitter_config,
            companies=companies
        )
        print("✓ Trending collector initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize trending collector: {e}")
        return False
    
    # Test individual methods without API calls
    print("\nTesting utility methods...")
    
    # Test retail relevance detection
    test_texts = [
        "Amazon reports strong retail sales growth",
        "New ecommerce trends emerging in CPG sector",
        "Random text about sports",
        "Walmart earnings show consumer spending patterns"
    ]
    
    for text in test_texts:
        is_relevant = collector._is_retail_relevant(text)
        print(f"  '{text[:50]}...' -> Relevant: {is_relevant}")
    
    # Test company matching
    test_company_texts = [
        "Amazon announces new fulfillment centers",
        "Target introduces new loyalty program",
        "General retail market discussion"
    ]
    
    for text in test_company_texts:
        company = collector._match_company(text)
        print(f"  '{text}' -> Company: {company}")
    
    # Test deduplication
    test_topics = [
        {"title": "Amazon sales growth", "content": "content1", "source": "test", "score": 10, "comments": 5, "created_at": datetime.now()},
        {"title": "Amazon sales increase", "content": "content2", "source": "test", "score": 8, "comments": 3, "created_at": datetime.now()},
        {"title": "Walmart earnings report", "content": "content3", "source": "test", "score": 15, "comments": 10, "created_at": datetime.now()}
    ]
    
    unique_topics = collector._deduplicate_topics(test_topics)
    print(f"\nDeduplication test: {len(test_topics)} -> {len(unique_topics)} topics")
    
    # Test scoring
    for topic in unique_topics:
        score = collector._calculate_popularity_score(topic)
        print(f"  '{topic['title']}' -> Score: {score}")
    
    print("\n✓ All utility method tests completed successfully")
    
    # Note about API testing
    print("\nNote: To test API functionality, ensure you have valid credentials in config/.env:")
    print("- REDDIT_CLIENT_ID")
    print("- REDDIT_CLIENT_SECRET") 
    print("- TWITTER_CONSUMER_KEY")
    print("- TWITTER_CONSUMER_SECRET")
    print("- TWITTER_ACCESS_TOKEN")
    print("- TWITTER_ACCESS_TOKEN_SECRET")
    
    return True

if __name__ == "__main__":
    success = test_trending_collector()
    if success:
        print("\n✓ Trending collector test completed successfully!")
    else:
        print("\n✗ Trending collector test failed!")
        sys.exit(1)