#!/usr/bin/env python3
"""
Test RetailXAI with historical data from the last 2 months.
This script will collect YouTube transcripts and RSS feeds from the past 2 months
and run the full analysis pipeline.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yaml

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from youtube_collector import YouTubeCollector
from rss_collector import RSSCollector
from claude_processor import ClaudeProcessor
from database_manager import DatabaseManager
from entities import Company
import threading

def load_config():
    """Load configuration files."""
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    with open('config/companies.yaml', 'r') as f:
        companies_config = yaml.safe_load(f)
    
    return config, companies_config

def setup_database():
    """Initialize database connection."""
    db_config = {
        'host': 'localhost',
        'name': 'retailxai',
        'user': 'retailxbt_user',
        'password': 'Seattle2311',
        'min_connections': 1,
        'max_connections': 5,
        'connect_timeout': 10
    }
    
    db_manager = DatabaseManager(db_config)
    return db_manager

def create_test_companies(companies_config, db_manager):
    """Create test companies in the database."""
    companies = []
    
    for company_data in companies_config['companies']:
        company = Company(
            name=company_data['name'],
            youtube_channels=company_data.get('youtube_channels', []),
            rss_feed=company_data.get('rss_feed', ''),
            keywords=company_data.get('keywords', [])
        )
        
        # Insert company into database
        company_id = db_manager.insert_company(company)
        company.id = company_id
        companies.append(company)
        print(f"✅ Created company: {company.name} (ID: {company_id})")
    
    return companies

def collect_historical_youtube_data(companies, config, days_back=60):
    """Collect YouTube data from the last 2 months."""
    print(f"\n🎥 Collecting YouTube data from the last {days_back} days...")
    
    youtube_collector = YouTubeCollector(
        config['global']['api_keys']['youtube'],
        companies,
        threading.Event()
    )
    
    # Set the date range for historical collection
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    total_transcripts = 0
    
    for company in companies:
        print(f"\n🔍 Collecting YouTube data for {company.name}...")
        
        for channel_id in company.youtube_channels:
            try:
                # Search for videos from the last 2 months
                videos = youtube_collector._search_youtube(
                    f"{company.name} earnings call OR {company.name} investor relations",
                    max_results=20
                )
                
                # Filter videos by date
                recent_videos = []
                for video in videos:
                    try:
                        video_date = datetime.fromisoformat(video['publishedAt'].replace('Z', '+00:00'))
                        if start_date <= video_date <= end_date:
                            recent_videos.append(video)
                    except:
                        continue
                
                print(f"  📺 Found {len(recent_videos)} recent videos for channel {channel_id}")
                
                # Collect transcripts for recent videos
                for video in recent_videos:
                    try:
                        transcript = youtube_collector._get_transcript(video['videoId'])
                        if transcript:
                            # Store transcript in database
                            transcript_data = {
                                'company_id': company.id,
                                'video_id': video['videoId'],
                                'title': video['title'],
                                'content': transcript,
                                'published_at': video['publishedAt'],
                                'channel_id': channel_id
                            }
                            
                            # Insert transcript
                            transcript_id = youtube_collector.db_manager.insert_transcript(
                                company.id,
                                video['videoId'],
                                video['title'],
                                transcript,
                                video['publishedAt']
                            )
                            
                            total_transcripts += 1
                            print(f"    ✅ Collected transcript: {video['title'][:50]}...")
                            
                    except Exception as e:
                        print(f"    ❌ Error collecting transcript for {video['videoId']}: {e}")
                        continue
                        
            except Exception as e:
                print(f"  ❌ Error collecting YouTube data for {company.name}: {e}")
                continue
    
    print(f"\n🎉 Total transcripts collected: {total_transcripts}")
    return total_transcripts

def collect_historical_rss_data(companies, config, days_back=60):
    """Collect RSS data from the last 2 months."""
    print(f"\n📰 Collecting RSS data from the last {days_back} days...")
    
    rss_collector = RSSCollector(
        config['sources']['rss']['feeds'],
        companies,
        threading.Event()
    )
    
    total_articles = 0
    
    for company in companies:
        if not company.rss_feed:
            continue
            
        print(f"\n🔍 Collecting RSS data for {company.name}...")
        
        try:
            articles = rss_collector._fetch_rss_feed(company.rss_feed)
            
            # Filter articles by date
            recent_articles = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for article in articles:
                try:
                    article_date = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
                    if article_date >= cutoff_date:
                        recent_articles.append(article)
                except:
                    continue
            
            print(f"  📄 Found {len(recent_articles)} recent articles")
            
            # Store articles in database
            for article in recent_articles:
                try:
                    # Insert as transcript (RSS articles are treated as text content)
                    transcript_id = rss_collector.db_manager.insert_transcript(
                        company.id,
                        article.get('id', ''),
                        article['title'],
                        article['summary'],
                        article['published']
                    )
                    
                    total_articles += 1
                    print(f"    ✅ Collected article: {article['title'][:50]}...")
                    
                except Exception as e:
                    print(f"    ❌ Error storing article: {e}")
                    continue
                    
        except Exception as e:
            print(f"  ❌ Error collecting RSS data for {company.name}: {e}")
            continue
    
    print(f"\n🎉 Total articles collected: {total_articles}")
    return total_articles

def run_ai_analysis(companies, config, db_manager):
    """Run AI analysis on collected data."""
    print(f"\n🤖 Running AI analysis...")
    
    claude_processor = ClaudeProcessor(
        config['global']['api_keys']['claude'],
        config['global']['claude_model'],
        config['prompts'],
        threading.Event()
    )
    
    # Get all transcripts from the database
    conn = db_manager.pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.*, c.name as company_name 
                FROM transcripts t 
                JOIN companies c ON t.company_id = c.id 
                ORDER BY t.created_at DESC
            """)
            transcripts = cur.fetchall()
            
        print(f"📊 Found {len(transcripts)} transcripts to analyze")
        
        total_analyses = 0
        
        for transcript in transcripts:
            try:
                print(f"  🔍 Analyzing: {transcript[2][:50]}...")  # transcript[2] is title
                
                # Run sentiment analysis
                sentiment_result = claude_processor.analyze_transcript(
                    transcript[3],  # content
                    transcript[6]   # company_name
                )
                
                if sentiment_result:
                    # Store analysis in database
                    analysis_id = db_manager.insert_analysis(
                        transcript[1],  # company_id
                        transcript[0],  # transcript_id
                        'sentiment',
                        json.dumps(sentiment_result),
                        f"Sentiment analysis for {transcript[2]}"
                    )
                    
                    total_analyses += 1
                    print(f"    ✅ Analysis completed")
                
            except Exception as e:
                print(f"    ❌ Error analyzing transcript: {e}")
                continue
                
    finally:
        db_manager.pool.putconn(conn)
    
    print(f"\n🎉 Total analyses completed: {total_analyses}")
    return total_analyses

def generate_articles(companies, config, db_manager):
    """Generate articles from analyses."""
    print(f"\n📝 Generating articles...")
    
    claude_processor = ClaudeProcessor(
        config['global']['api_keys']['claude'],
        config['global']['claude_model'],
        config['prompts'],
        threading.Event()
    )
    
    # Get all analyses from the database
    conn = db_manager.pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.*, c.name as company_name 
                FROM analyses a 
                JOIN companies c ON a.company_id = c.id 
                ORDER BY a.created_at DESC
            """)
            analyses = cur.fetchall()
            
        print(f"📊 Found {len(analyses)} analyses to process")
        
        total_articles = 0
        
        for analysis in analyses:
            try:
                print(f"  📝 Generating article for: {analysis[6][:50]}...")  # company_name
                
                # Generate article
                article_result = claude_processor.generate_article(
                    f"Analysis of {analysis[6]}",
                    json.dumps(json.loads(analysis[3])),  # analysis_data
                    "RetailXAI Historical Analysis"
                )
                
                if article_result:
                    # Store article in database
                    article_id = db_manager.insert_article(
                        analysis[1],  # company_id
                        analysis[0],  # analysis_id
                        article_result.get('headline', 'Untitled'),
                        article_result.get('body', ''),
                        json.dumps(article_result)
                    )
                    
                    total_articles += 1
                    print(f"    ✅ Article generated: {article_result.get('headline', 'Untitled')[:50]}...")
                
            except Exception as e:
                print(f"    ❌ Error generating article: {e}")
                continue
                
    finally:
        db_manager.pool.putconn(conn)
    
    print(f"\n🎉 Total articles generated: {total_articles}")
    return total_articles

def main():
    """Main function to run historical data test."""
    print("🚀 RetailXAI Historical Data Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('config/.env')
    
    # Load configuration
    config, companies_config = load_config()
    
    # Setup database
    print("\n🗄️ Setting up database...")
    db_manager = setup_database()
    
    # Create test companies
    print("\n🏢 Creating test companies...")
    companies = create_test_companies(companies_config, db_manager)
    
    # Collect historical YouTube data
    youtube_transcripts = collect_historical_youtube_data(companies, config, days_back=60)
    
    # Collect historical RSS data
    rss_articles = collect_historical_rss_data(companies, config, days_back=60)
    
    # Run AI analysis
    analyses = run_ai_analysis(companies, config, db_manager)
    
    # Generate articles
    articles = generate_articles(companies, config, db_manager)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 HISTORICAL DATA TEST SUMMARY")
    print("=" * 50)
    print(f"🏢 Companies: {len(companies)}")
    print(f"🎥 YouTube Transcripts: {youtube_transcripts}")
    print(f"📰 RSS Articles: {rss_articles}")
    print(f"🤖 AI Analyses: {analyses}")
    print(f"📝 Generated Articles: {articles}")
    print(f"📅 Time Period: Last 60 days")
    print("\n✅ Historical data test completed!")
    print("\n🌐 You can now view the results at: http://your-server-ip:5000")

if __name__ == "__main__":
    main()

