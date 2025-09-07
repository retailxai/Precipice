#!/usr/bin/env python3
"""
Test script for new data sources
Tests each collector individually to ensure they work correctly.
"""

import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors import (
    SECEDGARCollector,
    IRRSSCollector,
    TradeMediaCollector,
    GoogleNewsCollector,
    TranscriptCollector,
    YahooFinanceCollector,
    RedditCollector
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_sec_edgar():
    """Test SEC EDGAR collector."""
    print("\n🔍 Testing SEC EDGAR Collector...")
    
    cik_map = {
        'WMT': "0000104169",
        'TGT': "0000027419",
        'COST': "0000909832"
    }
    
    collector = SECEDGARCollector(cik_map)
    
    # Test single company
    result = collector.collect_company_facts('WMT')
    if result:
        print(f"✅ SEC EDGAR: Collected data for Walmart")
        print(f"   Revenue: {result['metadata']['financial_metrics'].get('revenue', 'N/A')}")
    else:
        print("❌ SEC EDGAR: Failed to collect data")
    
    return result is not None


def test_ir_rss():
    """Test IR RSS collector."""
    print("\n🔍 Testing IR RSS Collector...")
    
    feeds = [
        {
            'url': 'https://feeds.bbci.co.uk/news/rss.xml',  # Using working feed for test
            'company': 'BBC'
        }
    ]
    
    collector = IRRSSCollector(feeds)
    items = collector.collect_all_feeds()
    
    if items:
        print(f"✅ IR RSS: Collected {len(items)} items")
        print(f"   Sample: {items[0]['title'][:50]}...")
    else:
        print("❌ IR RSS: No items collected")
    
    return len(items) > 0


def test_trade_media():
    """Test trade media collector."""
    print("\n🔍 Testing Trade Media Collector...")
    
    feeds = [
        {
            'url': 'https://feeds.bbci.co.uk/news/rss.xml',  # Using working feed for test
            'publication': 'BBC News'
        }
    ]
    
    collector = TradeMediaCollector(feeds)
    items = collector.collect_all_feeds()
    
    if items:
        print(f"✅ Trade Media: Collected {len(items)} items")
        print(f"   Sample: {items[0]['title'][:50]}...")
    else:
        print("❌ Trade Media: No items collected")
    
    return len(items) > 0


def test_google_news():
    """Test Google News collector."""
    print("\n🔍 Testing Google News Collector...")
    
    queries = ['Walmart', 'Target']
    collector = GoogleNewsCollector(queries)
    items = collector.collect_all_queries()
    
    if items:
        print(f"✅ Google News: Collected {len(items)} items")
        print(f"   Sample: {items[0]['title'][:50]}...")
    else:
        print("❌ Google News: No items collected")
    
    return len(items) > 0


def test_transcripts():
    """Test transcript collector."""
    print("\n🔍 Testing Transcript Collector...")
    
    sources = [
        {'name': 'Motley Fool', 'base_url': 'https://www.fool.com/earnings-call-transcripts/'},
        {'name': 'Seeking Alpha', 'base_url': 'https://seekingalpha.com/earnings/earnings-call-transcripts'}
    ]
    
    collector = TranscriptCollector(sources)
    items = collector.collect_all_transcripts()
    
    if items:
        print(f"✅ Transcripts: Collected {len(items)} items")
        print(f"   Sample: {items[0]['title'][:50]}...")
    else:
        print("❌ Transcripts: No items collected")
    
    return len(items) > 0


def test_yahoo_finance():
    """Test Yahoo Finance collector."""
    print("\n🔍 Testing Yahoo Finance Collector...")
    
    symbols = ['WMT', 'TGT', 'COST']
    collector = YahooFinanceCollector(symbols)
    items = collector.collect_all_symbols()
    
    if items:
        print(f"✅ Yahoo Finance: Collected {len(items)} items")
        print(f"   Sample: {items[0]['title']}")
        print(f"   Price: {items[0]['metadata']['financial_metrics'].get('price', 'N/A')}")
    else:
        print("❌ Yahoo Finance: No items collected")
    
    return len(items) > 0


def test_reddit():
    """Test Reddit collector."""
    print("\n🔍 Testing Reddit Collector...")
    
    subreddit_queries = [
        {'subreddit': 'retail', 'query': 'Walmart'},
        {'subreddit': 'investing', 'query': 'Target'}
    ]
    
    collector = RedditCollector(subreddit_queries)
    items = collector.collect_all_subreddits()
    
    if items:
        print(f"✅ Reddit: Collected {len(items)} items")
        print(f"   Sample: {items[0]['title'][:50]}...")
    else:
        print("❌ Reddit: No items collected")
    
    return len(items) > 0


def main():
    """Run all tests."""
    print("🚀 Testing New Data Sources")
    print("=" * 50)
    
    tests = [
        ("SEC EDGAR", test_sec_edgar),
        ("IR RSS", test_ir_rss),
        ("Trade Media", test_trade_media),
        ("Google News", test_google_news),
        ("Transcripts", test_transcripts),
        ("Yahoo Finance", test_yahoo_finance),
        ("Reddit", test_reddit)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name}: Error - {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

