#!/usr/bin/env python3
"""
Enhanced Static Site Generator
Generates static site for GitHub Pages with new data sources.
"""

import os
import sys
import json
import requests
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_data_from_server():
    """Fetch data from production server."""
    base_url = "http://143.198.14.56:5000"
    
    data = {
        'transcripts': [],
        'analyses': [],
        'articles': [],
        'companies': [],
        'stats': {},
        'health': {}
    }
    
    try:
        # Fetch transcripts
        response = requests.get(f"{base_url}/api/transcripts", timeout=30)
        if response.status_code == 200:
            data['transcripts'] = response.json()
        else:
            logger.warning(f"Failed to fetch transcripts: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching transcripts: {e}")
    
    try:
        # Fetch analyses
        response = requests.get(f"{base_url}/api/analyses", timeout=30)
        if response.status_code == 200:
            data['analyses'] = response.json()
        else:
            logger.warning(f"Failed to fetch analyses: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching analyses: {e}")
    
    try:
        # Fetch articles
        response = requests.get(f"{base_url}/api/articles", timeout=30)
        if response.status_code == 200:
            data['articles'] = response.json()
        else:
            logger.warning(f"Failed to fetch articles: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching articles: {e}")
    
    try:
        # Fetch companies
        response = requests.get(f"{base_url}/api/companies", timeout=30)
        if response.status_code == 200:
            data['companies'] = response.json()
        else:
            logger.warning(f"Failed to fetch companies: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching companies: {e}")
    
    try:
        # Fetch stats
        response = requests.get(f"{base_url}/api/stats", timeout=30)
        if response.status_code == 200:
            data['stats'] = response.json()
        else:
            logger.warning(f"Failed to fetch stats: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching stats: {e}")
    
    try:
        # Fetch health
        response = requests.get(f"{base_url}/api/health", timeout=30)
        if response.status_code == 200:
            data['health'] = response.json()
        else:
            logger.warning(f"Failed to fetch health: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching health: {e}")
    
    return data

def generate_html(data):
    """Generate HTML content."""
    stats = data.get('stats', {})
    transcripts = data.get('transcripts', [])
    analyses = data.get('analyses', [])
    articles = data.get('articles', [])
    companies = data.get('companies', [])
    health = data.get('health', {})
    
    # Generate company list
    company_list = ""
    for company in companies:
        company_list += f"<li>{company.get('name', 'Unknown')}</li>"
    
    # Generate recent transcripts
    transcript_list = ""
    for transcript in transcripts[:10]:  # Show last 10
        title = transcript.get('title', 'Untitled')
        company = transcript.get('company_name', 'Unknown Company')
        published = transcript.get('published_at', 'Unknown Date')
        content = transcript.get('content', 'No content available')[:200] + "..."
        
        transcript_list += f"""
        <div class="item">
            <div class="item-title">{title}</div>
            <div class="item-meta">{company} • {published}</div>
            <div class="item-content">{content}</div>
        </div>
        """
    
    # Generate recent analyses
    analysis_list = ""
    for analysis in analyses[:10]:  # Show last 10
        title = analysis.get('transcript_title', 'Analysis')
        company = analysis.get('company_name', 'Unknown Company')
        sentiment = analysis.get('metrics', {}).get('sentiment', 'N/A')
        confidence = analysis.get('metrics', {}).get('confidence', 'N/A')
        strategy = analysis.get('strategy', {})
        trends = analysis.get('trends', {})
        consumer_insights = analysis.get('consumer_insights', {})
        tech_observations = analysis.get('tech_observations', {})
        operations = analysis.get('operations', {})
        outlook = analysis.get('outlook', {})
        
        # Format sentiment with color coding
        sentiment_color = "#27ae60" if isinstance(sentiment, (int, float)) and sentiment > 0 else "#e74c3c" if isinstance(sentiment, (int, float)) and sentiment < 0 else "#f39c12"
        sentiment_display = f"{sentiment:.2f}" if isinstance(sentiment, (int, float)) else str(sentiment)
        
        # Format outlook with emoji
        outlook_emoji = "📈" if outlook.get('forecast') == 'bullish' else "📉" if outlook.get('forecast') == 'bearish' else "➡️"
        
        analysis_list += f"""
        <div class="item">
            <div class="item-title">{title}</div>
            <div class="item-meta">{company} • Analysis ID: {analysis.get('id', 'N/A')}</div>
            <div class="item-content">
                <div style="margin-bottom: 10px;">
                    <strong>Sentiment:</strong> <span style="color: {sentiment_color}; font-weight: bold;">{sentiment_display}</span> 
                    (Confidence: {confidence})
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Strategy:</strong> {', '.join([f"{k}: {v}" for k, v in strategy.items()]) if strategy else 'N/A'}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Trends:</strong> {', '.join([f"{k}: {v}" for k, v in trends.items()]) if trends else 'N/A'}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Consumer Insights:</strong> {', '.join([f"{k}: {v}" for k, v in consumer_insights.items()]) if consumer_insights else 'N/A'}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Tech Observations:</strong> {', '.join([f"{k}: {v}" for k, v in tech_observations.items()]) if tech_observations else 'N/A'}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Operations:</strong> {', '.join([f"{k}: {v}" for k, v in operations.items()]) if operations else 'N/A'}
                </div>
                <div>
                    <strong>Outlook:</strong> {outlook_emoji} {', '.join([f"{k}: {v}" for k, v in outlook.items()]) if outlook else 'N/A'}
                </div>
            </div>
        </div>
        """
    
    # Generate recent articles
    article_list = ""
    for article in articles[:10]:  # Show last 10
        title = article.get('title', 'Untitled')
        published = article.get('published_at', 'Unknown Date')
        content = article.get('content', 'No content available')[:200] + "..."
        
        article_list += f"""
        <div class="item">
            <div class="item-title">{title}</div>
            <div class="item-meta">{published}</div>
            <div class="item-content">{content}</div>
        </div>
        """
    
    # Health status - determine from health checks
    health_checks = health.get('health_checks', [])
    all_healthy = all(check.get('status', False) for check in health_checks) if health_checks else False
    database_connected = health.get('database_connected', False)
    
    # System is healthy if all checks pass and database is connected
    is_healthy = all_healthy and database_connected
    
    health_class = 'status-healthy' if is_healthy else 'status-unhealthy'
    health_text = 'Healthy' if is_healthy else 'Unhealthy'
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RetailXAI Enhanced Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }}

        .header h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .stat-label {{
            font-size: 1.1rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .content-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        .content-card {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .card-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            font-size: 1.3rem;
            font-weight: bold;
        }}

        .card-content {{
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }}

        .item {{
            padding: 15px;
            border-bottom: 1px solid #eee;
            transition: background-color 0.3s ease;
        }}

        .item:hover {{
            background-color: #f8f9fa;
        }}

        .item:last-child {{
            border-bottom: none;
        }}

        .item-title {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}

        .item-meta {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 8px;
        }}

        .item-content {{
            font-size: 0.95rem;
            color: #555;
            line-height: 1.4;
        }}

        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}

        .status-healthy {{
            background-color: #27ae60;
        }}

        .status-unhealthy {{
            background-color: #e74c3c;
        }}

        .last-updated {{
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }}

        @media (max-width: 768px) {{
            .content-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RetailXAI Enhanced Dashboard</h1>
            <p>Advanced Retail Intelligence with 7 New Data Sources</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('companies', 0)}</div>
                <div class="stat-label">Companies</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('transcripts', 0)}</div>
                <div class="stat-label">Transcripts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('analyses', 0)}</div>
                <div class="stat-label">Analyses</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('articles', 0)}</div>
                <div class="stat-label">Articles</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('recent_transcripts', 0)}</div>
                <div class="stat-label">Recent (7d)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('recent_analyses', 0)}</div>
                <div class="stat-label">Recent (7d)</div>
            </div>
        </div>

        <div class="content-grid">
            <div class="content-card">
                <div class="card-header">📊 Recent Transcripts</div>
                <div class="card-content">
                    {transcript_list if transcript_list else '<div class="item">No transcripts available</div>'}
                </div>
            </div>

            <div class="content-card">
                <div class="card-header">📰 Recent Articles</div>
                <div class="card-content">
                    {article_list if article_list else '<div class="item">No articles available</div>'}
                </div>
            </div>
        </div>

        <div class="content-card" style="margin-bottom: 40px;">
            <div class="card-header">🤖 AI Analysis Results</div>
            <div class="card-content" style="max-height: 600px;">
                {analysis_list if analysis_list else '<div class="item">No analyses available</div>'}
            </div>
        </div>

        <div class="content-grid">
            <div class="content-card">
                <div class="card-header">🏥 System Health</div>
                <div class="card-content">
                    <div class="item">
                        <div class="item-title">
                            <span class="status-indicator {health_class}"></span>
                            System Status: {health_text}
                        </div>
                        <div class="item-meta">Database: {'Connected' if database_connected else 'Disconnected'}</div>
                        <div class="item-content">
                            Last Updated: {health.get('timestamp', 'Unknown')}
                        </div>
                    </div>
                </div>
            </div>

            <div class="content-card">
                <div class="card-header">📈 Analysis Summary</div>
                <div class="card-content">
                    <div class="item">
                        <div class="item-title">Sentiment Distribution</div>
                        <div class="item-content">
                            <div style="margin-bottom: 10px;">
                                <strong>Positive:</strong> {len([a for a in analyses if isinstance(a.get('metrics', {}).get('sentiment'), (int, float)) and a.get('metrics', {}).get('sentiment', 0) > 0])} analyses
                            </div>
                            <div style="margin-bottom: 10px;">
                                <strong>Neutral:</strong> {len([a for a in analyses if isinstance(a.get('metrics', {}).get('sentiment'), (int, float)) and a.get('metrics', {}).get('sentiment', 0) == 0])} analyses
                            </div>
                            <div style="margin-bottom: 10px;">
                                <strong>Negative:</strong> {len([a for a in analyses if isinstance(a.get('metrics', {}).get('sentiment'), (int, float)) and a.get('metrics', {}).get('sentiment', 0) < 0])} analyses
                            </div>
                        </div>
                    </div>
                    <div class="item">
                        <div class="item-title">Outlook Distribution</div>
                        <div class="item-content">
                            <div style="margin-bottom: 10px;">
                                <strong>📈 Bullish:</strong> {len([a for a in analyses if a.get('outlook', {}).get('forecast') == 'bullish'])} analyses
                            </div>
                            <div style="margin-bottom: 10px;">
                                <strong>📉 Bearish:</strong> {len([a for a in analyses if a.get('outlook', {}).get('forecast') == 'bearish'])} analyses
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="last-updated">
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    """Generate static site."""
    logger.info("🚀 Generating enhanced static site...")
    
    # Create docs directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)
    
    # Fetch data from production server
    logger.info("📡 Fetching data from production server...")
    data = fetch_data_from_server()
    
    # Generate HTML
    logger.info("🎨 Generating HTML...")
    html_content = generate_html(data)
    
    # Write to file
    output_file = 'docs/index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"✅ Static site generated: {output_file}")
    
    # Print summary
    stats = data.get('stats', {})
    logger.info(f"📊 Data Summary:")
    logger.info(f"   Companies: {stats.get('companies', 0)}")
    logger.info(f"   Transcripts: {stats.get('transcripts', 0)}")
    logger.info(f"   Analyses: {stats.get('analyses', 0)}")
    logger.info(f"   Articles: {stats.get('articles', 0)}")

if __name__ == "__main__":
    main()
