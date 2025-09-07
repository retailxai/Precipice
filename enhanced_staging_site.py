#!/usr/bin/env python3
"""
Enhanced Staging Site
Flask application for the enhanced staging dashboard with new data sources.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RetailXAI.EnhancedStaging")

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'name': 'retailxai',
    'user': 'retailxbt_user',
    'password': os.getenv('DATABASE_PASSWORD', 'Seattle2311'),
    'min_connections': 1,
    'max_connections': 5,
    'connect_timeout': 10
}

# Initialize connection pool
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        DB_CONFIG['min_connections'],
        DB_CONFIG['max_connections'],
        host=DB_CONFIG['host'],
        database=DB_CONFIG['name'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        connect_timeout=DB_CONFIG['connect_timeout']
    )
    logger.info("Database connection pool initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database connection pool: {e}")
    connection_pool = None

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('enhanced_index.html')

@app.route('/api/transcripts')
def get_transcripts():
    """Get recent transcripts."""
    if not connection_pool:
        return jsonify([])
    
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.id, t.title, t.content, t.published_at, c.name as company_name
                FROM transcripts t
                JOIN companies c ON t.company_id = c.id
                ORDER BY t.published_at DESC
                LIMIT 50
            """)
            transcripts = []
            for row in cur.fetchall():
                transcripts.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:500] + '...' if len(row[2]) > 500 else row[2],
                    'published_at': row[3].isoformat() if row[3] else None,
                    'company_name': row[4]
                })
            return jsonify(transcripts)
    except Exception as e:
        logger.error(f"Error fetching transcripts: {e}")
        return jsonify([])
    finally:
        connection_pool.putconn(conn)

@app.route('/api/analyses')
def get_analyses():
    """Get recent analyses."""
    if not connection_pool:
        return jsonify([])
    
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.metrics, a.strategy, a.trends, a.consumer_insights, 
                       a.tech_observations, a.operations, a.outlook, t.title, c.name as company_name
                FROM analyses a
                JOIN transcripts t ON a.transcript_id = t.id
                JOIN companies c ON t.company_id = c.id
                ORDER BY a.id DESC
                LIMIT 50
            """)
            analyses = []
            for row in cur.fetchall():
                try:
                    analyses.append({
                        'id': row[0],
                        'metrics': json.loads(row[1]) if row[1] else {},
                        'strategy': json.loads(row[2]) if row[2] else {},
                        'trends': json.loads(row[3]) if row[3] else {},
                        'consumer_insights': json.loads(row[4]) if row[4] else {},
                        'tech_observations': json.loads(row[5]) if row[5] else {},
                        'operations': json.loads(row[6]) if row[6] else {},
                        'outlook': json.loads(row[7]) if row[7] else {},
                        'transcript_title': row[8],
                        'company_name': row[9]
                    })
                except json.JSONDecodeError:
                    continue
            return jsonify(analyses)
    except Exception as e:
        logger.error(f"Error fetching analyses: {e}")
        return jsonify([])
    finally:
        connection_pool.putconn(conn)

@app.route('/api/articles')
def get_articles():
    """Get recent articles."""
    if not connection_pool:
        return jsonify([])
    
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, content, published_at, company_id
                FROM articles
                ORDER BY published_at DESC
                LIMIT 50
            """)
            articles = []
            for row in cur.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:500] + '...' if len(row[2]) > 500 else row[2],
                    'published_at': row[3].isoformat() if row[3] else None,
                    'company_id': row[4]
                })
            return jsonify(articles)
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return jsonify([])
    finally:
        connection_pool.putconn(conn)

@app.route('/api/companies')
def get_companies():
    """Get all companies."""
    if not connection_pool:
        return jsonify([])
    
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM companies ORDER BY name")
            companies = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
            return jsonify(companies)
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        return jsonify([])
    finally:
        connection_pool.putconn(conn)

@app.route('/api/stats')
def get_stats():
    """Get system statistics."""
    if not connection_pool:
        return jsonify({})
    
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            # Get counts
            cur.execute("SELECT COUNT(*) FROM companies")
            company_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM transcripts")
            transcript_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM analyses")
            analysis_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM articles")
            article_count = cur.fetchone()[0]
            
            # Get recent activity
            cur.execute("""
                SELECT COUNT(*) FROM transcripts 
                WHERE published_at >= NOW() - INTERVAL '7 days'
            """)
            recent_transcripts = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM analyses 
                WHERE id IN (
                    SELECT a.id FROM analyses a
                    JOIN transcripts t ON a.transcript_id = t.id
                    WHERE t.published_at >= NOW() - INTERVAL '7 days'
                )
            """)
            recent_analyses = cur.fetchone()[0]
            
            return jsonify({
                'companies': company_count,
                'transcripts': transcript_count,
                'analyses': analysis_count,
                'articles': article_count,
                'recent_transcripts': recent_transcripts,
                'recent_analyses': recent_analyses,
                'last_updated': datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({})
    finally:
        connection_pool.putconn(conn)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    if not connection_pool:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected'})
    
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
    finally:
        connection_pool.putconn(conn)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
