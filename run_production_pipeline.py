#!/usr/bin/env python3
"""
RetailXAI Production 60-Day Pipeline
Run this script on the production server to collect 60 days of data
and generate complete content pipeline.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yaml
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from youtube_collector import YouTubeCollector
from rss_collector import RSSCollector
from claude_processor import ClaudeProcessor
from database_manager import DatabaseManager
from entities import Company

class ProductionPipeline:
    def __init__(self):
        """Initialize the production pipeline."""
        # Load configuration
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        with open('config/companies.yaml', 'r') as f:
            self.companies_config = yaml.safe_load(f)
        
        self.stop_event = threading.Event()
        
        # Initialize database
        self.db_manager = self._setup_database()
        
        # Create companies
        self.companies = self._create_companies()
        
        # Initialize collectors
        self.youtube_collector = YouTubeCollector(
            self.config['global']['api_keys']['youtube'],
            self.companies,
            self.stop_event
        )
        
        self.rss_collector = RSSCollector(
            self.config['sources']['rss']['feeds'],
            self.companies,
            self.stop_event
        )
        
        # Initialize AI processor
        self.claude_processor = ClaudeProcessor(
            self.config['global']['api_keys']['claude'],
            self.config['global']['claude_model'],
            self.config['prompts'],
            self.stop_event
        )
        
        # Statistics
        self.stats = {
            'companies': len(self.companies),
            'youtube_transcripts': 0,
            'rss_articles': 0,
            'analyses': 0,
            'articles': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def _setup_database(self):
        """Setup database connection."""
        db_config = {
            'host': 'localhost',
            'name': 'retailxai',
            'user': 'retailxbt_user',
            'password': 'Seattle2311',
            'min_connections': 1,
            'max_connections': 5,
            'connect_timeout': 10
        }
        return DatabaseManager(db_config)

    def _create_companies(self):
        """Create company objects and ensure they exist in database."""
        companies = []
        
        for company_data in self.companies_config['companies']:
            company = Company(
                name=company_data['name'],
                youtube_channels=company_data.get('youtube_channels', []),
                rss_feed=company_data.get('rss_feed', ''),
                keywords=company_data.get('keywords', [])
            )
            
            # Check if company already exists
            conn = self.db_manager.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM companies WHERE name = %s", (company.name,))
                    result = cur.fetchone()
                    if result:
                        company.id = result[0]
                        print(f"✅ Company found: {company.name} (ID: {company.id})")
                    else:
                        # Insert new company
                        company_id = self.db_manager.insert_company(company)
                        company.id = company_id
                        print(f"✅ Company created: {company.name} (ID: {company_id})")
            finally:
                self.db_manager.pool.putconn(conn)
            
            companies.append(company)
        
        return companies

    def collect_youtube_data(self, days_back=60):
        """Collect YouTube data for the last 60 days."""
        print(f"\n🎥 Collecting YouTube data for the last {days_back} days...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        total_transcripts = 0
        
        for company in self.companies:
            print(f"\n🔍 Processing {company.name}...")
            
            for channel_id in company.youtube_channels:
                try:
                    print(f"  📺 Searching channel: {channel_id}")
                    
                    # Multiple search queries for better coverage
                    search_queries = [
                        f"{company.name} earnings call",
                        f"{company.name} investor relations",
                        f"{company.name} quarterly results",
                        f"{company.name} financial results",
                        f"{company.name} Q4 2024",
                        f"{company.name} Q3 2024",
                        f"{company.name} Q2 2024",
                        f"{company.name} Q1 2024"
                    ]
                    
                    all_videos = []
                    for query in search_queries:
                        try:
                            print(f"    🔍 Searching: {query}")
                            videos = self.youtube_collector._search_youtube(query, max_results=15)
                            all_videos.extend(videos)
                            time.sleep(1)  # Rate limiting
                        except Exception as e:
                            print(f"    ⚠️  Query failed: {e}")
                            continue
                    
                    # Remove duplicates
                    unique_videos = {}
                    for video in all_videos:
                        unique_videos[video['videoId']] = video
                    videos = list(unique_videos.values())
                    
                    # Filter videos by date
                    recent_videos = []
                    for video in videos:
                        try:
                            video_date = datetime.fromisoformat(video['publishedAt'].replace('Z', '+00:00'))
                            if start_date <= video_date <= end_date:
                                recent_videos.append(video)
                        except:
                            continue
                    
                    print(f"  📊 Found {len(recent_videos)} recent videos")
                    
                    # Collect transcripts
                    for video in recent_videos:
                        try:
                            print(f"    🎬 Processing: {video['title'][:60]}...")
                            
                            transcript = self.youtube_collector._get_transcript(video['videoId'])
                            if transcript and len(transcript.strip()) > 200:  # Minimum content length
                                
                                # Store in database
                                transcript_id = self.youtube_collector.db_manager.insert_transcript(
                                    company.id,
                                    video['videoId'],
                                    video['title'],
                                    transcript,
                                    video['publishedAt']
                                )
                                
                                total_transcripts += 1
                                self.stats['youtube_transcripts'] += 1
                                print(f"      ✅ Collected transcript (ID: {transcript_id})")
                                
                            else:
                                print(f"      ⚠️  No transcript available or too short")
                                
                        except Exception as e:
                            print(f"      ❌ Error collecting transcript: {e}")
                            self.stats['errors'] += 1
                            continue
                        
                        time.sleep(0.5)  # Rate limiting
                        
                except Exception as e:
                    print(f"  ❌ Error processing channel {channel_id}: {e}")
                    self.stats['errors'] += 1
                    continue
        
        print(f"\n🎉 YouTube collection completed: {total_transcripts} transcripts")
        return total_transcripts

    def collect_rss_data(self, days_back=60):
        """Collect RSS data for the last 60 days."""
        print(f"\n📰 Collecting RSS data for the last {days_back} days...")
        
        total_articles = 0
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for company in self.companies:
            if not company.rss_feed:
                continue
                
            print(f"\n🔍 Processing RSS feed for {company.name}...")
            print(f"  📡 Feed: {company.rss_feed}")
            
            try:
                articles = self.rss_collector._fetch_rss_feed(company.rss_feed)
                
                # Filter articles by date
                recent_articles = []
                for article in articles:
                    try:
                        article_date = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
                        if article_date >= cutoff_date:
                            recent_articles.append(article)
                    except:
                        continue
                
                print(f"  📄 Found {len(recent_articles)} recent articles")
                
                # Store articles
                for article in recent_articles:
                    try:
                        print(f"    📝 Processing: {article['title'][:60]}...")
                        
                        # Store as transcript
                        transcript_id = self.rss_collector.db_manager.insert_transcript(
                            company.id,
                            article.get('id', ''),
                            article['title'],
                            article['summary'],
                            article['published']
                        )
                        
                        total_articles += 1
                        self.stats['rss_articles'] += 1
                        print(f"      ✅ Collected article (ID: {transcript_id})")
                        
                    except Exception as e:
                        print(f"      ❌ Error storing article: {e}")
                        self.stats['errors'] += 1
                        continue
                        
            except Exception as e:
                print(f"  ❌ Error processing RSS feed: {e}")
                self.stats['errors'] += 1
                continue
        
        print(f"\n🎉 RSS collection completed: {total_articles} articles")
        return total_articles

    def run_ai_analysis(self):
        """Run AI analysis on all collected data."""
        print(f"\n🤖 Running AI analysis on collected data...")
        
        # Get all transcripts from database
        conn = self.db_manager.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.*, c.name as company_name 
                    FROM transcripts t 
                    JOIN companies c ON t.company_id = c.id 
                    ORDER BY t.published_at DESC
                """)
                transcripts = cur.fetchall()
                
            print(f"📊 Found {len(transcripts)} transcripts to analyze")
            
            total_analyses = 0
            
            for i, transcript in enumerate(transcripts, 1):
                try:
                    print(f"  🔍 Analyzing transcript {i}/{len(transcripts)}: {transcript[3][:50]}...")
                    
                    # Run sentiment analysis
                    try:
                        sentiment_result = self.claude_processor.analyze_transcript(
                            transcript[4],  # content
                            transcript[6]   # company_name
                        )
                        
                        if sentiment_result:
                            analysis_id = self.db_manager.insert_analysis(
                                transcript[1],  # company_id
                                transcript[0],  # transcript_id
                                'sentiment',
                                json.dumps(sentiment_result),
                                f"Sentiment analysis for {transcript[3][:50]}"
                            )
                            
                            total_analyses += 1
                            self.stats['analyses'] += 1
                            print(f"    ✅ Sentiment analysis completed")
                        
                    except Exception as e:
                        print(f"    ⚠️  Sentiment analysis failed: {e}")
                        self.stats['errors'] += 1
                    
                    # Run competitor analysis
                    try:
                        competitor_result = self._analyze_competitors(transcript[4], transcript[6])
                        
                        if competitor_result:
                            analysis_id = self.db_manager.insert_analysis(
                                transcript[1],
                                transcript[0],
                                'competitor',
                                json.dumps(competitor_result),
                                f"Competitor analysis for {transcript[3][:50]}"
                            )
                            
                            total_analyses += 1
                            self.stats['analyses'] += 1
                            print(f"    ✅ Competitor analysis completed")
                        
                    except Exception as e:
                        print(f"    ⚠️  Competitor analysis failed: {e}")
                        self.stats['errors'] += 1
                    
                    # Run trend analysis
                    try:
                        trend_result = self._analyze_trends(transcript[4], transcript[6])
                        
                        if trend_result:
                            analysis_id = self.db_manager.insert_analysis(
                                transcript[1],
                                transcript[0],
                                'trends',
                                json.dumps(trend_result),
                                f"Trend analysis for {transcript[3][:50]}"
                            )
                            
                            total_analyses += 1
                            self.stats['analyses'] += 1
                            print(f"    ✅ Trend analysis completed")
                        
                    except Exception as e:
                        print(f"    ⚠️  Trend analysis failed: {e}")
                        self.stats['errors'] += 1
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"  ❌ Error analyzing transcript: {e}")
                    self.stats['errors'] += 1
                    continue
                    
        finally:
            self.db_manager.pool.putconn(conn)
        
        print(f"\n🎉 AI analysis completed: {total_analyses} analyses")
        return total_analyses

    def _analyze_competitors(self, content, company_name):
        """Analyze competitor mentions."""
        competitor_keywords = {
            'Walmart': ['Target', 'Amazon', 'Costco', 'Kroger', 'Best Buy'],
            'PepsiCo': ['Coca-Cola', 'Kraft Heinz', 'General Mills', 'Nestle', 'Unilever']
        }
        
        competitors = competitor_keywords.get(company_name, [])
        mentions = []
        
        for competitor in competitors:
            if competitor.lower() in content.lower():
                mentions.append(competitor)
        
        return {
            'competitors_mentioned': mentions,
            'competitive_landscape': 'active' if mentions else 'neutral',
            'analysis_date': datetime.now().isoformat()
        }

    def _analyze_trends(self, content, company_name):
        """Analyze trends in content."""
        trend_categories = {
            'technology': ['AI', 'automation', 'digital', 'e-commerce', 'mobile', 'cloud'],
            'sustainability': ['green', 'sustainable', 'environment', 'ESG', 'carbon', 'renewable'],
            'consumer': ['consumer', 'customer', 'preference', 'behavior', 'experience', 'loyalty'],
            'financial': ['revenue', 'profit', 'growth', 'margin', 'investment', 'earnings'],
            'operations': ['supply chain', 'logistics', 'efficiency', 'cost', 'optimization']
        }
        
        trends = {}
        for category, keywords in trend_categories.items():
            trend_score = sum(1 for keyword in keywords if keyword.lower() in content.lower())
            trends[category] = trend_score
        
        return {
            'trend_categories': trends,
            'dominant_trend': max(trends.items(), key=lambda x: x[1])[0] if any(trends.values()) else 'none',
            'analysis_date': datetime.now().isoformat()
        }

    def generate_articles(self):
        """Generate articles from analyses."""
        print(f"\n📝 Generating articles from analyses...")
        
        # Get all sentiment analyses from database
        conn = self.db_manager.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.*, c.name as company_name, t.title as transcript_title
                    FROM analyses a 
                    JOIN transcripts t ON a.transcript_id = t.id
                    JOIN companies c ON t.company_id = c.id 
                    WHERE a.analysis_type = 'sentiment'
                    ORDER BY a.created_at DESC
                """)
                analyses = cur.fetchall()
                
            print(f"📊 Found {len(analyses)} analyses to process into articles")
            
            total_articles = 0
            
            for i, analysis in enumerate(analyses, 1):
                try:
                    print(f"  📝 Generating article {i}/{len(analyses)} for {analysis[6]}...")
                    
                    # Get all analyses for this transcript
                    with conn.cursor() as cur2:
                        cur2.execute("""
                            SELECT analysis_type, analysis_data 
                            FROM analyses 
                            WHERE transcript_id = %s
                        """, (analysis[2],))
                        all_analyses = cur2.fetchall()
                    
                    # Combine all analysis data
                    combined_analysis = {}
                    for analysis_type, analysis_data in all_analyses:
                        combined_analysis[analysis_type] = json.loads(analysis_data)
                    
                    # Generate article
                    article_result = self.claude_processor.generate_article(
                        f"RetailXAI Analysis: {analysis[6]} - {analysis[7]}",
                        json.dumps(combined_analysis),
                        "RetailXAI 60-Day Analysis"
                    )
                    
                    if article_result:
                        # Store article in database
                        article_id = self.db_manager.insert_article(
                            analysis[1],  # company_id
                            analysis[0],  # analysis_id
                            article_result.get('headline', f"Analysis: {analysis[6]}"),
                            article_result.get('body', ''),
                            json.dumps(article_result)
                        )
                        
                        total_articles += 1
                        self.stats['articles'] += 1
                        print(f"    ✅ Article generated (ID: {article_id})")
                    
                except Exception as e:
                    print(f"    ❌ Error generating article: {e}")
                    self.stats['errors'] += 1
                    continue
                    
        finally:
            self.db_manager.pool.putconn(conn)
        
        print(f"\n🎉 Article generation completed: {total_articles} articles")
        return total_articles

    def run_full_pipeline(self, days_back=60):
        """Run the complete 60-day data pipeline."""
        print("🚀 RetailXAI Production 60-Day Data Pipeline")
        print("=" * 60)
        print(f"📅 Collecting data from the last {days_back} days")
        print(f"🏢 Processing {len(self.companies)} companies")
        print(f"🖥️  Running on production server")
        print("=" * 60)
        
        try:
            # Step 1: Collect YouTube data
            youtube_count = self.collect_youtube_data(days_back)
            
            # Step 2: Collect RSS data
            rss_count = self.collect_rss_data(days_back)
            
            # Step 3: Run AI analysis
            analysis_count = self.run_ai_analysis()
            
            # Step 4: Generate articles
            article_count = self.generate_articles()
            
            # Final statistics
            self._print_final_stats()
            
            return {
                'youtube_transcripts': youtube_count,
                'rss_articles': rss_count,
                'analyses': analysis_count,
                'articles': article_count,
                'errors': self.stats['errors']
            }
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            return None

    def _print_final_stats(self):
        """Print final pipeline statistics."""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        
        print("\n" + "=" * 60)
        print("📊 PRODUCTION PIPELINE COMPLETION SUMMARY")
        print("=" * 60)
        print(f"🏢 Companies Processed: {self.stats['companies']}")
        print(f"🎥 YouTube Transcripts: {self.stats['youtube_transcripts']}")
        print(f"📰 RSS Articles: {self.stats['rss_articles']}")
        print(f"🤖 AI Analyses: {self.stats['analyses']}")
        print(f"📝 Generated Articles: {self.stats['articles']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⏱️  Total Duration: {duration}")
        print(f"📅 Data Period: Last 60 days")
        print(f"🖥️  Server: Production (143.198.14.56)")
        print("=" * 60)
        print("✅ Production pipeline completed successfully!")
        print("🌐 View results at: http://143.198.14.56:5000")

def main():
    """Main function to run the production pipeline."""
    print("🚀 Starting RetailXAI Production 60-Day Data Pipeline")
    
    # Load environment variables
    load_dotenv('config/.env')
    
    # Initialize and run pipeline
    pipeline = ProductionPipeline()
    results = pipeline.run_full_pipeline(days_back=60)
    
    if results:
        print(f"\n🎉 Production pipeline completed successfully!")
        print(f"📊 Results: {results}")
        print(f"🌐 View your staging site at: http://143.198.14.56:5000")
    else:
        print(f"\n❌ Production pipeline failed. Please check the logs above.")

if __name__ == "__main__":
    main()
