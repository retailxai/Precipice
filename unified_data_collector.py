"""
Unified Data Collector
Integrates all new data sources into the existing Precipice system.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yaml
import os

from collectors import (
    SECEDGARCollector,
    IRRSSCollector,
    TradeMediaCollector,
    GoogleNewsCollector,
    TranscriptCollector,
    YahooFinanceCollector,
    RedditCollector
)
from database_manager import DatabaseManager

logger = logging.getLogger("RetailXAI.UnifiedDataCollector")


class UnifiedDataCollector:
    """Unified collector that integrates all new data sources."""

    def __init__(self, config_path: str = "config/config.yaml", shutdown_event: Optional[threading.Event] = None):
        """Initialize unified data collector.
        
        Args:
            config_path: Path to configuration file
            shutdown_event: Event for graceful shutdown
        """
        self.shutdown_event = shutdown_event or threading.Event()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize database
        self.db_manager = self._setup_database()
        
        # Initialize collectors
        self.collectors = self._initialize_collectors()
        
        # Statistics
        self.stats = {
            'total_items': 0,
            'items_by_source': {},
            'errors': 0,
            'start_time': datetime.now()
        }

    def _setup_database(self) -> DatabaseManager:
        """Setup database connection."""
        db_config = {
            'host': 'localhost',
            'name': 'retailxai',
            'user': 'retailxbt_user',
            'password': os.getenv('DATABASE_PASSWORD', 'Seattle2311'),
            'min_connections': 1,
            'max_connections': 5,
            'connect_timeout': 10
        }
        return DatabaseManager(db_config)

    def _initialize_collectors(self) -> Dict:
        """Initialize all data collectors based on configuration."""
        collectors = {}
        
        # SEC EDGAR Collector
        if self.config.get('sources', {}).get('sec_edgar', {}).get('enabled', False):
            cik_map = self.config['sources']['sec_edgar']['cik_map']
            collectors['sec_edgar'] = SECEDGARCollector(cik_map, self.shutdown_event)
        
        # IR RSS Collector
        if self.config.get('sources', {}).get('ir_rss', {}).get('enabled', False):
            feeds = self.config['sources']['ir_rss']['feeds']
            collectors['ir_rss'] = IRRSSCollector(feeds, self.shutdown_event)
        
        # Trade Media Collector
        if self.config.get('sources', {}).get('trade_media', {}).get('enabled', False):
            feeds = self.config['sources']['trade_media']['feeds']
            collectors['trade_media'] = TradeMediaCollector(feeds, self.shutdown_event)
        
        # Google News Collector
        if self.config.get('sources', {}).get('google_news', {}).get('enabled', False):
            queries = self.config['sources']['google_news']['queries']
            collectors['google_news'] = GoogleNewsCollector(queries, self.shutdown_event)
        
        # Transcript Collector
        if self.config.get('sources', {}).get('transcripts', {}).get('enabled', False):
            sources = self.config['sources']['transcripts']['sources']
            collectors['transcripts'] = TranscriptCollector(sources, self.shutdown_event)
        
        # Yahoo Finance Collector
        if self.config.get('sources', {}).get('yahoo_finance', {}).get('enabled', False):
            symbols = self.config['sources']['yahoo_finance']['symbols']
            collectors['yahoo_finance'] = YahooFinanceCollector(symbols, self.shutdown_event)
        
        # Reddit Collector
        if self.config.get('sources', {}).get('reddit', {}).get('enabled', False):
            subreddit_queries = self.config['sources']['reddit']['subreddit_queries']
            collectors['reddit'] = RedditCollector(subreddit_queries, self.shutdown_event)
        
        logger.info(f"Initialized {len(collectors)} data collectors")
        return collectors

    def _store_item(self, item: Dict) -> bool:
        """Store collected item in database.
        
        Args:
            item: Item data to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Map to existing database schema
            if item['source'] in ['sec_edgar', 'yahoo_finance']:
                # Store as company data or metadata
                # For now, store as transcript with special source type
                transcript_id = self.db_manager.insert_transcript(
                    1,  # company_id - Default company ID
                    item['metadata'].get('ticker', item['metadata'].get('symbol', 'unknown')),  # source_id
                    item['title'],  # title
                    item['summary'],  # content
                    item['published_at']  # published_at
                )
                return transcript_id is not None
                
            else:
                # Store as transcript
                company_id = self._get_company_id_from_item(item)
                transcript_id = self.db_manager.insert_transcript(
                    company_id,  # company_id
                    item['url'].split('/')[-1] if item['url'] else 'unknown',  # source_id
                    item['title'],  # title
                    item['summary'],  # content
                    item['published_at']  # published_at
                )
                return transcript_id is not None
                
        except Exception as e:
            logger.error(f"Error storing item: {e}")
            return False

    def _get_company_id_from_item(self, item: Dict) -> int:
        """Get company ID from item metadata.
        
        Args:
            item: Item data
            
        Returns:
            Company ID (defaults to 1 for Walmart)
        """
        # Try to extract company from metadata
        mentioned_companies = item.get('metadata', {}).get('mentioned_companies', [])
        if mentioned_companies:
            # Map company names to IDs (simplified)
            company_map = {
                'Walmart': 1,
                'Target': 2,
                'Costco': 3,
                'Kroger': 4,
                'Amazon': 5
            }
            for company in mentioned_companies:
                if company in company_map:
                    return company_map[company]
        
        # Default to Walmart
        return 1

    def collect_from_source(self, source_name: str) -> List[Dict]:
        """Collect data from a specific source.
        
        Args:
            source_name: Name of the source to collect from
            
        Returns:
            List of collected items
        """
        if source_name not in self.collectors:
            logger.warning(f"Collector not found: {source_name}")
            return []
        
        collector = self.collectors[source_name]
        items = []
        
        try:
            if source_name == 'sec_edgar':
                items = collector.collect_all_companies()
            elif source_name == 'ir_rss':
                items = collector.collect_all_feeds()
            elif source_name == 'trade_media':
                items = collector.collect_all_feeds()
            elif source_name == 'google_news':
                items = collector.collect_all_queries()
            elif source_name == 'transcripts':
                items = collector.collect_all_transcripts()
            elif source_name == 'yahoo_finance':
                items = collector.collect_all_symbols()
            elif source_name == 'reddit':
                items = collector.collect_all_subreddits()
            
            logger.info(f"Collected {len(items)} items from {source_name}")
            return items
            
        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {e}")
            self.stats['errors'] += 1
            return []

    def collect_all_sources(self) -> Dict:
        """Collect data from all enabled sources.
        
        Returns:
            Dictionary with collection results
        """
        logger.info("Starting unified data collection...")
        
        all_items = []
        source_results = {}
        
        for source_name, collector in self.collectors.items():
            if self.shutdown_event.is_set():
                break
                
            logger.info(f"Collecting from {source_name}...")
            items = self.collect_from_source(source_name)
            
            # Store items in database
            stored_count = 0
            for item in items:
                if self._store_item(item):
                    stored_count += 1
            
            source_results[source_name] = {
                'collected': len(items),
                'stored': stored_count
            }
            
            all_items.extend(items)
            self.stats['items_by_source'][source_name] = len(items)
            
            # Rate limiting between sources
            rate_limit = self.config.get('sources', {}).get(source_name, {}).get('rate_limit', 1.0)
            time.sleep(rate_limit)
        
        self.stats['total_items'] = len(all_items)
        
        logger.info(f"Collection completed: {len(all_items)} total items")
        return {
            'total_items': len(all_items),
            'source_results': source_results,
            'stats': self.stats
        }

    def run_collection_cycle(self) -> Dict:
        """Run a complete collection cycle.
        
        Returns:
            Collection results
        """
        start_time = datetime.now()
        
        try:
            results = self.collect_all_sources()
            
            # Update statistics
            duration = datetime.now() - start_time
            results['duration'] = str(duration)
            results['timestamp'] = start_time.isoformat()
            
            logger.info(f"Collection cycle completed in {duration}")
            return results
            
        except Exception as e:
            logger.error(f"Error in collection cycle: {e}")
            return {
                'error': str(e),
                'timestamp': start_time.isoformat()
            }


def main():
    """Main function for testing the unified collector."""
    logging.basicConfig(level=logging.INFO)
    
    collector = UnifiedDataCollector()
    results = collector.run_collection_cycle()
    
    print("Collection Results:")
    print(f"Total items: {results.get('total_items', 0)}")
    print(f"Source results: {results.get('source_results', {})}")
    print(f"Duration: {results.get('duration', 'Unknown')}")


if __name__ == "__main__":
    main()

