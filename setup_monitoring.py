#!/usr/bin/env python3
"""
Setup Production Monitoring and Alerting
This script helps configure monitoring alerts for the production system.
"""

import os
import json
import yaml
from pathlib import Path

def setup_monitoring_config():
    """Set up monitoring configuration with user input."""
    print("🔧 Setting up Production Monitoring and Alerting")
    print("=" * 50)
    
    # Email configuration
    print("\n📧 Email Alert Configuration:")
    email_config = {
        'smtp_server': input("SMTP Server (default: smtp.gmail.com): ") or "smtp.gmail.com",
        'smtp_port': int(input("SMTP Port (default: 587): ") or "587"),
        'username': input("Email Username: "),
        'password': input("Email Password/App Password: "),
        'from': input("From Email: "),
        'to': [input("Alert Recipient Email: ")]
    }
    
    # Slack configuration
    print("\n💬 Slack Alert Configuration:")
    slack_webhook = input("Slack Webhook URL (optional): ")
    
    # Create monitoring configuration
    monitoring_config = {
        'alerts': {
            'email': {
                'enabled': bool(email_config['username']),
                **email_config
            },
            'slack': {
                'enabled': bool(slack_webhook),
                'webhook_url': slack_webhook,
                'channel': '#retailxai-alerts'
            }
        },
        'metrics': {
            'retention_days': 30,
            'collection_interval': 60,
            'export_interval': 300
        },
        'sla_targets': {
            'uptime': 99.9,
            'response_time_ms': 2000,
            'error_rate_percent': 1.0,
            'data_freshness_minutes': 60
        }
    }
    
    # Save configuration
    with open('config/monitoring.yaml', 'w') as f:
        yaml.dump(monitoring_config, f, default_flow_style=False)
    
    print(f"\n✅ Monitoring configuration saved to config/monitoring.yaml")
    
    # Create environment variables template
    env_template = f"""# Production Environment Variables for RetailXAI
# Copy this to .env and fill in your actual values

# Database Configuration
DATABASE_URL=postgresql://retailxbt_user@localhost:5432/retailxai
DATABASE_PASSWORD=Seattle2311!

# Required API Keys
CLAUDE_API_KEY=sk-ant-your-claude-key-here
YOUTUBE_API_KEY=your-youtube-api-key-here

# Optional API Keys (for enhanced features)
NEWS_API_KEY=your-news-api-key
LINKEDIN_API_KEY=your-linkedin-api-key
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
SLACK_WEBHOOK_URL={slack_webhook or 'your-slack-webhook-url'}
TWITTER_CONSUMER_KEY=your-twitter-consumer-key
TWITTER_CONSUMER_SECRET=your-twitter-consumer-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret

# Monitoring and Alerting
ALERT_EMAIL_SMTP={email_config['smtp_server']}
ALERT_EMAIL_PORT={email_config['smtp_port']}
ALERT_EMAIL_USER={email_config['username'] or 'your-email@gmail.com'}
ALERT_EMAIL_PASS={email_config['password'] or 'your-app-password'}
ALERT_EMAIL_FROM={email_config['from'] or 'your-email@gmail.com'}
ALERT_EMAIL_TO={email_config['to'][0] or 'alerts@yourcompany.com'}

# Slack Configuration
SLACK_BOT_TOKEN=your-slack-bot-token
"""
    
    with open('config/.env.template', 'w') as f:
        f.write(env_template)
    
    print(f"✅ Environment template saved to config/.env.template")
    
    return monitoring_config

def test_monitoring_setup():
    """Test the monitoring setup."""
    print("\n🧪 Testing Monitoring Setup...")
    
    try:
        from production_monitor import ProductionMonitor
        
        # Load monitoring config
        with open('config/monitoring.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Create monitor instance
        monitor = ProductionMonitor(config)
        
        # Run health check
        health_status = monitor.check_system_health()
        
        print(f"✅ Health check completed: {health_status['overall_status']}")
        
        # Test alert creation
        monitor._create_alert('LOW', 'test', 'This is a test alert')
        print("✅ Alert system working")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 RetailXAI Production Monitoring Setup")
    print("=" * 50)
    
    # Create config directory if it doesn't exist
    os.makedirs('config', exist_ok=True)
    
    # Set up monitoring
    config = setup_monitoring_config()
    
    # Test setup
    if test_monitoring_setup():
        print("\n🎉 Monitoring setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Copy config/.env.template to config/.env")
        print("2. Fill in your actual API keys and credentials")
        print("3. Deploy to production server")
        print("4. Monitor alerts and SLA metrics")
    else:
        print("\n❌ Monitoring setup failed. Please check the configuration.")

if __name__ == "__main__":
    main()
