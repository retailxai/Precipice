#!/usr/bin/env python3
"""
Test script for RetailXAI agents.

This script demonstrates how to use the new agent framework and provides
examples of running individual agents and the full pipeline.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent_manager import AgentManager
from agents.base_agent import AgentConfig
from entities import Company, Transcript
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RetailXAI.AgentTest")


async def test_individual_agents():
    """Test individual agents with sample data."""
    logger.info("=== Testing Individual Agents ===")
    
    # Create some sample companies
    sample_companies = [
        Company(
            name="Walmart",
            youtube_channels=["WalmartInc"],
            rss_feed="https://corporate.walmart.com/news/rss.xml",
            keywords=["retail", "earnings", "growth"]
        ),
        Company(
            name="Target",
            youtube_channels=["Target"],
            rss_feed="https://corporate.target.com/news/rss.xml",
            keywords=["retail", "digital", "expansion"]
        )
    ]
    
    # Create sample transcripts
    sample_transcripts = [
        Transcript(
            content="Q4 earnings call transcript: Walmart reported strong growth in e-commerce sales, up 23% year-over-year. The company is investing heavily in AI and automation to improve customer experience and operational efficiency.",
            company="Walmart",
            source_id="walmart_q4_2024",
            title="Walmart Q4 2024 Earnings Call",
            published_at=datetime.now(),
            source_type="earnings_call"
        ),
        Transcript(
            content="Target announced a new sustainability initiative focused on reducing carbon emissions by 30% by 2030. The company is also expanding its same-day delivery services to compete with Amazon.",
            company="Target",
            source_id="target_sustainability_2024",
            title="Target Sustainability Announcement",
            published_at=datetime.now(),
            source_type="news_api"
        )
    ]
    
    # Test Sentiment Agent
    logger.info("Testing Sentiment Agent...")
    from agents.processing import SentimentAgent
    
    sentiment_config = AgentConfig(
        name="test_sentiment",
        enabled=True,
        config={'transcripts': sample_transcripts}
    )
    
    sentiment_agent = SentimentAgent(sentiment_config)
    sentiment_result = await sentiment_agent.run_with_retry()
    
    if sentiment_result.success:
        logger.info(f"Sentiment analysis completed: {len(sentiment_result.data)} results")
        for result in sentiment_result.data[:1]:  # Show first result
            logger.info(f"  Company: {result['company']}")
            logger.info(f"  Sentiment: {result['sentiment_label']} (confidence: {result['confidence']:.2f})")
    else:
        logger.error(f"Sentiment analysis failed: {sentiment_result.error}")
    
    # Test Trend Agent
    logger.info("Testing Trend Agent...")
    from agents.processing import TrendAgent
    
    trend_config = AgentConfig(
        name="test_trend",
        enabled=True,
        config={'transcripts': sample_transcripts}
    )
    
    trend_agent = TrendAgent(trend_config)
    trend_result = await trend_agent.run_with_retry()
    
    if trend_result.success:
        logger.info("Trend analysis completed")
        aggregated = trend_result.data['aggregated_trends']
        logger.info(f"  Top trends: {list(aggregated['top_trends'].keys())}")
    else:
        logger.error(f"Trend analysis failed: {trend_result.error}")
    
    # Test Earnings Collector
    logger.info("Testing Earnings Collector...")
    from agents.data_collection import EarningsAgent
    
    earnings_config = AgentConfig(
        name="test_earnings",
        enabled=True,
        config={}
    )
    
    earnings_agent = EarningsAgent(earnings_config, sample_companies)
    earnings_result = await earnings_agent.run_with_retry()
    
    if earnings_result.success:
        logger.info(f"Earnings collection completed: {len(earnings_result.data)} documents")
    else:
        logger.error(f"Earnings collection failed: {earnings_result.error}")


async def test_agent_manager():
    """Test the agent manager and pipeline execution."""
    logger.info("=== Testing Agent Manager ===")
    
    # Initialize agent manager
    try:
        agent_manager = AgentManager("config/agents.yaml")
        logger.info("Agent manager initialized successfully")
    except Exception as e:
        logger.warning(f"Using default configuration due to error: {e}")
        agent_manager = AgentManager("nonexistent.yaml")  # Will use defaults
    
    # Get agent status
    status = agent_manager.get_agent_status()
    logger.info("Agent Status:")
    for agent_name, agent_status in status.items():
        enabled = agent_status.get('enabled', False)
        logger.info(f"  {agent_name}: {'✓' if enabled else '✗'} {'Enabled' if enabled else 'Disabled'}")
    
    # Test individual agent execution
    logger.info("Testing individual agent execution...")
    result = await agent_manager.execute_agent('earnings_collector')
    if result.success:
        logger.info(f"✓ Earnings collector executed: {len(result.data or [])} items collected")
    else:
        logger.warning(f"✗ Earnings collector failed: {result.error}")
    
    # Test data collection pipeline
    logger.info("Testing data collection pipeline...")
    collection_results = await agent_manager.execute_data_collection_pipeline()
    
    total_transcripts = 0
    for agent_name, result in collection_results.items():
        if result.success and result.data:
            count = len(result.data)
            total_transcripts += count
            logger.info(f"  ✓ {agent_name}: {count} items")
        else:
            logger.info(f"  ✗ {agent_name}: {result.error}")
    
    logger.info(f"Total transcripts collected: {total_transcripts}")
    
    # Test full pipeline if we have data
    if total_transcripts > 0:
        logger.info("Testing full pipeline...")
        pipeline_result = await agent_manager.execute_full_pipeline()
        
        summary = pipeline_result['summary']
        logger.info(f"Pipeline completed in {summary['execution_time']:.2f} seconds")
        logger.info(f"  Transcripts processed: {summary['total_transcripts']}")
        
        # Show results summary
        for stage, results in pipeline_result.items():
            if stage != 'summary' and isinstance(results, dict):
                logger.info(f"  {stage}: {len(results)} agents executed")
    else:
        logger.info("Skipping full pipeline test (no transcripts collected)")


async def test_publishing_agents():
    """Test publishing agents with sample data."""
    logger.info("=== Testing Publishing Agents ===")
    
    # Test Slack Agent (only if webhook configured)
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    if slack_webhook:
        logger.info("Testing Slack notifications...")
        from agents.publishing import SlackAgent
        
        slack_config = AgentConfig(
            name="test_slack",
            enabled=True,
            config={
                'webhook_url': slack_webhook,
                'channel': '#test',
                'notification_type': 'daily_summary',
                'notification_data': {
                    'stats': {
                        'transcripts_collected': 5,
                        'companies_analyzed': 3,
                        'sources': ['earnings_call', 'news_api']
                    },
                    'top_trends': ['AI adoption', 'Supply chain optimization'],
                    'articles_generated': 2
                },
                'notification_types': ['daily_summary', 'error_alerts', 'trend_alerts']
            }
        )
        
        slack_agent = SlackAgent(slack_config)
        slack_result = await slack_agent.run_with_retry()
        
        if slack_result.success:
            logger.info("✓ Slack notification sent successfully")
        else:
            logger.error(f"✗ Slack notification failed: {slack_result.error}")
    else:
        logger.info("Skipping Slack test (no webhook URL configured)")
    
    # Test LinkedIn Publisher (draft mode)
    logger.info("Testing LinkedIn publisher (draft mode)...")
    from agents.publishing import LinkedInPublisher
    from entities import Article
    
    sample_article = Article(
        headline="RetailXAI Test: AI Trends in Retail",
        summary="This is a test article generated by RetailXAI to demonstrate LinkedIn publishing capabilities.",
        body="The retail industry is experiencing significant transformation driven by AI and automation technologies. Companies are investing in these capabilities to improve customer experience and operational efficiency.",
        key_insights=["AI adoption accelerating", "Customer experience focus", "Operational efficiency gains"]
    )
    
    linkedin_config = AgentConfig(
        name="test_linkedin",
        enabled=True,
        config={
            'access_token': 'dummy_token',  # Won't actually publish
            'company_id': 'dummy_id',
            'draft_mode': True,
            'draft_directory': 'test_drafts/linkedin',
            'articles': [sample_article]
        }
    )
    
    linkedin_agent = LinkedInPublisher(linkedin_config)
    linkedin_result = await linkedin_agent.run_with_retry()
    
    if linkedin_result.success:
        logger.info("✓ LinkedIn draft created successfully")
        if linkedin_result.data:
            for post in linkedin_result.data:
                if post.get('file_path'):
                    logger.info(f"  Draft saved to: {post['file_path']}")
    else:
        logger.error(f"✗ LinkedIn publishing failed: {linkedin_result.error}")


async def main():
    """Main test function."""
    logger.info("Starting RetailXAI Agent Tests")
    logger.info("=" * 50)
    
    try:
        # Test individual agents
        await test_individual_agents()
        
        # Test agent manager
        await test_agent_manager()
        
        # Test publishing agents
        await test_publishing_agents()
        
        logger.info("=" * 50)
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("config/.env")
    
    # Run tests
    asyncio.run(main())