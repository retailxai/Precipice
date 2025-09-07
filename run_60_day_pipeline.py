#!/usr/bin/env python3
"""
RetailXAI 60-Day Data Pipeline
Comprehensive script to collect data from all sources for the last 60 days
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

class RetailXAIPipeline:
    def __init__(self, config, companies_config):
        """Initialize the 60-day pipeline."""
        self.config = config
        self.companies_config = companies_config
        self.stop_event = threading.Event()
        
        # Initialize database
        self.db_manager = self._setup_database()
        
        # Initialize collectors
        self.youtube_collector = YouTubeCollector(
            config['global']['api_keys']['youtube'],
            self._create_companies(),
            self.stop_event
        )
        
        self.rss_collector = RSSCollector(
            config['sources']['rss']['feeds'],
            self._create_companies(),
            self.stop_event
        )
        
        # Initialize AI processor
        self.claude_processor = ClaudeProcessor(
            config['global']['api_keys']['claude'],
            config['global']['claude_model'],
            config['prompts'],
            self.stop_event
        )
        
        # Statistics tracking
        self.stats = {
            'companies': 0,
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
        """Create company objects from config."""
        companies = []
        for company_data in self.companies_config['companies']:
            company = Company(
                name=company_data['name'],
                youtube_channels=company_data.get('youtube_channels', []),
                rss_feed=company_data.get('rss_feed', ''),
                keywords=company_data.get('keywords', [])
            )
            companies.append(company)
        return companies

    def collect_youtube_data(self, days_back=60):
        """Collect YouTube data for the last 60 days."""
        print(f"\n🎥 Collecting YouTube data for the last {days_back} days...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        total_transcripts = 0
        
        for company in self.youtube_collector.companies:
            print(f"\n🔍 Processing {company.name}...")
            
            for channel_id in company.youtube_channels:
                try:
                    print(f"  📺 Searching channel: {channel_id}")
                    
                    # Search for videos with multiple queries
                    search_queries = [
                        f"{company.name} earnings call",
                        f"{company.name} investor relations",
                        f"{company.name} quarterly results",
                        f"{company.name} financial results",
                        f"{company.name} Q4 2024",
                        f"{company.name} Q3 2024"
                    ]
                    
                    all_videos = []
                    for query in search_queries:
                        try:
                            videos = self.youtube_collector._search_youtube(query, max_results=10)
                            all_videos.extend(videos)
                            time.sleep(1)  # Rate limiting
                        except Exception as e:
                            print(f"    ⚠️  Query '{query}' failed: {e}")
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
                            print(f"    🎬 Processing: {video['title'][:50]}...")
                            
                            transcript = self.youtube_collector._get_transcript(video['videoId'])
                            if transcript and len(transcript.strip()) > 100:  # Minimum content length
                                
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
        
        for company in self.rss_collector.companies:
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
                        print(f"    📝 Processing: {article['title'][:50]}...")
                        
                        # Store as transcript (RSS articles are treated as text content)
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
                    
                    # Run multiple types of analysis
                    analyses_to_run = [
                        ('sentiment', self._analyze_sentiment),
                        ('competitor', self._analyze_competitors),
                        ('trends', self._analyze_trends),
                        ('insights', self._analyze_insights)
                    ]
                    
                    for analysis_type, analysis_func in analyses_to_run:
                        try:
                            result = analysis_func(transcript[4], transcript[6])  # content, company_name
                            
                            if result:
                                # Store analysis in database
                                analysis_id = self.db_manager.insert_analysis(
                                    transcript[1],  # company_id
                                    transcript[0],  # transcript_id
                                    analysis_type,
                                    json.dumps(result),
                                    f"{analysis_type.title()} analysis for {transcript[3][:50]}"
                                )
                                
                                total_analyses += 1
                                self.stats['analyses'] += 1
                                print(f"    ✅ {analysis_type.title()} analysis completed")
                            
                        except Exception as e:
                            print(f"    ⚠️  {analysis_type.title()} analysis failed: {e}")
                            self.stats['errors'] += 1
                            continue
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  ❌ Error analyzing transcript: {e}")
                    self.stats['errors'] += 1
                    continue
                    
        finally:
            self.db_manager.pool.putconn(conn)
        
        print(f"\n🎉 AI analysis completed: {total_analyses} analyses")
        return total_analyses

    def _analyze_sentiment(self, content, company_name):
        """Analyze sentiment of content."""
        try:
            return self.claude_processor.analyze_transcript(content, company_name)
        except:
            # Fallback to simple sentiment analysis
            from textblob import TextBlob
            blob = TextBlob(content)
            return {
                'sentiment': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity,
                'confidence': 0.7
            }

    def _analyze_competitors(self, content, company_name):
        """Analyze competitor mentions."""
        competitor_keywords = {
            'Walmart': ['Target', 'Amazon', 'Costco', 'Kroger'],
            'PepsiCo': ['Coca-Cola', 'Kraft Heinz', 'General Mills', 'Nestle']
        }
        
        competitors = competitor_keywords.get(company_name, [])
        mentions = []
        
        for competitor in competitors:
            if competitor.lower() in content.lower():
                mentions.append(competitor)
        
        return {
            'competitors_mentioned': mentions,
            'competitive_landscape': 'active' if mentions else 'neutral'
        }

    def _analyze_trends(self, content, company_name):
        """Analyze trends in content."""
        trend_categories = {
            'technology': ['AI', 'automation', 'digital', 'e-commerce', 'mobile'],
            'sustainability': ['green', 'sustainable', 'environment', 'ESG', 'carbon'],
            'consumer': ['consumer', 'customer', 'preference', 'behavior', 'experience'],
            'financial': ['revenue', 'profit', 'growth', 'margin', 'investment']
        }
        
        trends = {}
        for category, keywords in trend_categories.items():
            trend_score = sum(1 for keyword in keywords if keyword.lower() in content.lower())
            trends[category] = trend_score
        
        return {
            'trend_categories': trends,
            'dominant_trend': max(trends.items(), key=lambda x: x[1])[0] if any(trends.values()) else 'none'
        }

    def _analyze_insights(self, content, company_name):
        """Extract key insights from content."""
        # Simple keyword extraction and insight generation
        words = content.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only meaningful words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'key_insights': [word for word, freq in top_words if freq > 1],
            'content_length': len(content),
            'complexity_score': len(set(words)) / len(words) if words else 0
        }

    def generate_articles(self):
        """Generate articles from analyses."""
        print(f"\n📝 Generating articles from analyses...")
        
        # Get all analyses from database
        conn = self.db_manager.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.*, c.name as company_name, t.title as transcript_title
                    FROM analyses a 
                    JOIN transcripts t ON a.transcript_id = t.id
                    JOIN companies c ON t.company_id = c.id 
                    WHERE a.analysis_type = 'insights'
                    ORDER BY a.created_at DESC
                """)
                analyses = cur.fetchall()
                
            print(f"📊 Found {len(analyses)} analyses to process into articles")
            
            total_articles = 0
            
            for i, analysis in enumerate(analyses, 1):
                try:
                    print(f"  📝 Generating article {i}/{len(analyses)} for {analysis[6]}...")
                    
                    # Combine all analysis types for this transcript
                    analysis_data = json.loads(analysis[3])  # analysis_data column
                    
                    # Generate article
                    article_result = self.claude_processor.generate_article(
                        f"Analysis of {analysis[6]} - {analysis[7]}",
                        json.dumps(analysis_data),
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
        print("🚀 RetailXAI 60-Day Data Pipeline")
        print("=" * 60)
        print(f"📅 Collecting data from the last {days_back} days")
        print(f"🏢 Processing {len(self.companies_config['companies'])} companies")
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
        print("📊 PIPELINE COMPLETION SUMMARY")
        print("=" * 60)
        print(f"🏢 Companies Processed: {len(self.companies_config['companies'])}")
        print(f"🎥 YouTube Transcripts: {self.stats['youtube_transcripts']}")
        print(f"📰 RSS Articles: {self.stats['rss_articles']}")
        print(f"🤖 AI Analyses: {self.stats['analyses']}")
        print(f"📝 Generated Articles: {self.stats['articles']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⏱️  Total Duration: {duration}")
        print(f"📅 Data Period: Last 60 days")
        print("=" * 60)
        print("✅ Pipeline completed successfully!")

def main():
    """Main function to run the 60-day pipeline."""
    print("🚀 Starting RetailXAI 60-Day Data Pipeline")
    
    # Load environment variables
    load_dotenv('config/.env')
    
    # Load configuration
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    with open('config/companies.yaml', 'r') as f:
        companies_config = yaml.safe_load(f)
    
    # Initialize and run pipeline
    pipeline = RetailXAIPipeline(config, companies_config)
    results = pipeline.run_full_pipeline(days_back=60)
    
    if results:
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"📊 Results: {results}")
    else:
        print(f"\n❌ Pipeline failed. Please check the logs above.")

if __name__ == "__main__":
    main()
