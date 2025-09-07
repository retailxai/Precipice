#!/usr/bin/env python3
"""
Generate static site for GitHub Pages deployment.
This script fetches data from the production server and generates static HTML files.
"""

import os
import json
import requests
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# Production server configuration
PRODUCTION_SERVER = "http://143.198.14.56:5000"
OUTPUT_DIR = "docs"

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

def fetch_data_from_server(endpoint):
    """Fetch data from production server."""
    try:
        response = requests.get(f"{PRODUCTION_SERVER}{endpoint}", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Warning: Could not fetch {endpoint}: {e}")
        return []

def generate_index_html():
    """Generate the main index.html file."""
    # Fetch data from production server
    stats = fetch_data_from_server("/api/stats")
    companies = fetch_data_from_server("/api/companies")
    transcripts = fetch_data_from_server("/api/transcripts")
    analyses = fetch_data_from_server("/api/analyses")
    articles = fetch_data_from_server("/api/articles")
    health = fetch_data_from_server("/api/health")
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RetailXAI Staging Dashboard</title>
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
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
        }}
        
        .content-section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .section-title {{
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .content-item {{
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background: #f9f9f9;
        }}
        
        .content-item h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .content-item p {{
            color: #666;
            line-height: 1.5;
        }}
        
        .timestamp {{
            font-size: 0.8rem;
            color: #999;
            margin-top: 10px;
        }}
        
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }}
        
        .status-online {{
            background: #4CAF50;
        }}
        
        .status-offline {{
            background: #f44336;
        }}
        
        .last-updated {{
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9rem;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RetailXAI Staging Dashboard</h1>
            <p>Real-time content generation and system monitoring</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('companies', 0)}</div>
                <div class="stat-label">Companies Tracked</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('transcripts', 0)}</div>
                <div class="stat-label">Transcripts Collected</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('analyses', 0)}</div>
                <div class="stat-label">AI Analyses Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('articles', 0)}</div>
                <div class="stat-label">Articles Created</div>
            </div>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">📊 Recent Transcripts</h2>
            <div id="transcriptsList">
                {generate_transcripts_html(transcripts)}
            </div>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">🤖 AI Analyses</h2>
            <div id="analysesList">
                {generate_analyses_html(analyses)}
            </div>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">📝 Generated Articles</h2>
            <div id="articlesList">
                {generate_articles_html(articles)}
            </div>
        </div>
        
        <div class="content-section">
            <h2 class="section-title">⚡ System Health</h2>
            <div id="healthStatus">
                {generate_health_html(health)}
            </div>
        </div>
        
        <div class="last-updated">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
    </div>
</body>
</html>"""
    
    return html_content

def generate_transcripts_html(transcripts):
    """Generate HTML for transcripts section."""
    if not transcripts:
        return '<p>No transcripts available yet. The system will start collecting data at 7:00 AM UTC.</p>'
    
    html = ""
    for transcript in transcripts[:10]:  # Show only first 10
        company_name = transcript.get('company_name', 'Unknown Company')
        title = transcript.get('title', 'N/A')
        content = transcript.get('content', '')
        created_at = transcript.get('created_at', '')
        
        # Format date
        try:
            if created_at:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            else:
                formatted_date = 'Unknown'
        except:
            formatted_date = 'Unknown'
        
        html += f"""
        <div class="content-item">
            <h3>{company_name}</h3>
            <p><strong>Title:</strong> {title}</p>
            <p><strong>Content:</strong> {content[:200]}{'...' if len(content) > 200 else ''}</p>
            <div class="timestamp">Created: {formatted_date}</div>
        </div>
        """
    
    return html

def generate_analyses_html(analyses):
    """Generate HTML for analyses section."""
    if not analyses:
        return '<p>No analyses available yet. AI analysis will begin once transcripts are collected.</p>'
    
    html = ""
    for analysis in analyses[:10]:  # Show only first 10
        company_name = analysis.get('company_name', 'Unknown Company')
        analysis_type = analysis.get('analysis_type', 'N/A')
        summary = analysis.get('summary', '')
        created_at = analysis.get('created_at', '')
        
        # Format date
        try:
            if created_at:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            else:
                formatted_date = 'Unknown'
        except:
            formatted_date = 'Unknown'
        
        html += f"""
        <div class="content-item">
            <h3>{company_name}</h3>
            <p><strong>Type:</strong> {analysis_type}</p>
            <p><strong>Summary:</strong> {summary[:200]}{'...' if len(summary) > 200 else ''}</p>
            <div class="timestamp">Created: {formatted_date}</div>
        </div>
        """
    
    return html

def generate_articles_html(articles):
    """Generate HTML for articles section."""
    if not articles:
        return '<p>No articles available yet. Articles will be generated once analyses are complete.</p>'
    
    html = ""
    for article in articles[:10]:  # Show only first 10
        title = article.get('title', 'Untitled')
        company_name = article.get('company_name', 'N/A')
        content = article.get('content', '')
        created_at = article.get('created_at', '')
        
        # Format date
        try:
            if created_at:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            else:
                formatted_date = 'Unknown'
        except:
            formatted_date = 'Unknown'
        
        html += f"""
        <div class="content-item">
            <h3>{title}</h3>
            <p><strong>Company:</strong> {company_name}</p>
            <p><strong>Content:</strong> {content[:200]}{'...' if len(content) > 200 else ''}</p>
            <div class="timestamp">Created: {formatted_date}</div>
        </div>
        """
    
    return html

def generate_health_html(health):
    """Generate HTML for health section."""
    if not health:
        return '<p>Health status unavailable.</p>'
    
    is_healthy = health.get('database_connected', False)
    status_class = 'status-online' if is_healthy else 'status-offline'
    status_text = 'Online' if is_healthy else 'Offline'
    
    health_checks = health.get('health_checks', [])
    agent_states = health.get('agent_states', [])
    
    last_check = 'Never'
    if health_checks:
        try:
            last_check_date = datetime.fromisoformat(health_checks[0]['created_at'].replace('Z', '+00:00'))
            last_check = last_check_date.strftime('%Y-%m-%d %H:%M')
        except:
            pass
    
    active_agents = len([agent for agent in agent_states if agent.get('is_running', False)])
    
    return f"""
    <div class="content-item">
        <h3><span class="status-indicator {status_class}"></span>System Status: {status_text}</h3>
        <p><strong>Database:</strong> {'Connected' if is_healthy else 'Disconnected'}</p>
        <p><strong>Last Health Check:</strong> {last_check}</p>
        <p><strong>Active Agents:</strong> {active_agents}</p>
    </div>
    """

def main():
    """Main function to generate static site."""
    print("🚀 Generating static site for GitHub Pages...")
    
    ensure_output_dir()
    
    # Generate index.html
    print("📄 Generating index.html...")
    index_content = generate_index_html()
    
    with open(f"{OUTPUT_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"✅ Static site generated in {OUTPUT_DIR}/ directory")
    print(f"📊 Data fetched from production server: {PRODUCTION_SERVER}")

if __name__ == "__main__":
    main()
