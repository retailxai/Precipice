#!/usr/bin/env python3
"""
Daily Article Generator
Generates retail analysis articles on a schedule.
"""

import sys
import os
import logging
from datetime import datetime

# Add the precipice directory to the path
sys.path.append('/home/retailxai/precipice')

from simple_article_generator import SimpleArticleGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/retailxai/precipice/logs/article_generator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("RetailXAI.ArticleGenerator")

def generate_daily_article():
    """Generate a daily retail analysis article."""
    try:
        logger.info("Starting daily article generation")
        
        # Create article generator
        generator = SimpleArticleGenerator()
        
        # Generate article with current date
        current_date = datetime.now().strftime('%B %Y')
        title = f"Retail Market Analysis - {current_date}"
        
        filepath = generator.generate_article(title)
        
        logger.info(f"Daily article generated successfully: {filepath}")
        
        # Also generate a weekly summary if it's Monday
        if datetime.now().weekday() == 0:  # Monday
            weekly_title = f"Weekly Retail Roundup - {current_date}"
            weekly_filepath = generator.generate_article(weekly_title)
            logger.info(f"Weekly summary generated: {weekly_filepath}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating daily article: {e}")
        return False

if __name__ == "__main__":
    success = generate_daily_article()
    if success:
        print("Article generation completed successfully")
        sys.exit(0)
    else:
        print("Article generation failed")
        sys.exit(1)

