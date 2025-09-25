#!/usr/bin/env python3
"""
Test email configuration for Substack drafts.
"""

import os
import yaml
from content_manager import ContentManager
from database_manager import DatabaseManager
from entities import Article

def main():
    """Test email configuration."""
    print("📧 Testing email configuration...")
    
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check if email credentials are set
    substack_config = config['publishing']['substack']
    
    print(f"📧 Email User: {substack_config.get('email_user', 'NOT SET')}")
    print(f"📧 Email Recipient: {substack_config.get('email_recipient', 'NOT SET')}")
    print(f"📧 SMTP Server: {substack_config.get('smtp_server', 'NOT SET')}")
    print(f"📧 SMTP Port: {substack_config.get('smtp_port', 'NOT SET')}")
    
    # Check if credentials are environment variables
    if substack_config.get('email_user', '').startswith('${'):
        print("⚠️  Email credentials are using environment variables")
        print("   Make sure to set SUBSTACK_EMAIL_USER, SUBSTACK_EMAIL_PASSWORD, SUBSTACK_EMAIL_RECIPIENT")
    else:
        print("✅ Email credentials are set directly in config")
    
    # Test with a sample article
    try:
        # Initialize database
        db_manager = DatabaseManager(config['global']['database'])
        
        # Create sample article
        article = Article(
            headline="Test Email - RetailXAI Analysis",
            summary="This is a test email to verify Substack integration",
            body="This is a test article to verify that email sending works correctly.",
            key_insights=["Test insight 1", "Test insight 2"]
        )
        
        # Initialize content manager
        twitter_config = {
            'consumer_key': 'dummy',
            'consumer_secret': 'dummy', 
            'access_token': 'dummy',
            'access_token_secret': 'dummy',
            'draft_directory': 'drafts/twitter'
        }
        
        content_manager = ContentManager(
            db_manager.pool,
            substack_config,
            twitter_config,
            None
        )
        
        print("📝 Generating test Substack draft...")
        result = content_manager.publish_to_substack(article)
        print(f"✅ Draft generated: {result}")
        
        if "emailed-to" in result:
            print("📧 Email sent successfully!")
        else:
            print("📁 Draft saved to file (email not sent)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



