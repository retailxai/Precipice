#!/usr/bin/env python3
"""
RetailXAI Staging Site - Fixed for Production Database Schema
A simple web interface to view generated content and system status.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'retailxai',
    'user': 'retailxbt_user',
    'password': os.getenv('DATABASE_PASSWORD', 'Seattle2311')
}

def get_db_connection():
    """Get database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('index.html')

@app.route('/api/companies')
def get_companies():
    """Get all companies being tracked."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM companies ORDER BY name")
            companies = cur.fetchall()
            return jsonify([dict(company) for company in companies])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/transcripts')
def get_transcripts():
    """Get recent transcripts."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT t.*, c.name as company_name 
                FROM transcripts t 
                LEFT JOIN companies c ON t.company_id = c.id 
                ORDER BY t.published_at DESC 
                LIMIT 50
            """)
            transcripts = cur.fetchall()
            return jsonify([dict(transcript) for transcript in transcripts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/analyses')
def get_analyses():
    """Get recent analyses."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, c.name as company_name, t.title as transcript_title
                FROM analyses a 
                LEFT JOIN transcripts t ON a.transcript_id = t.id
                LEFT JOIN companies c ON t.company_id = c.id 
                ORDER BY a.created_at DESC 
                LIMIT 50
            """)
            analyses = cur.fetchall()
            return jsonify([dict(analysis) for analysis in analyses])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/articles')
def get_articles():
    """Get recent articles."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, 'Unknown Company' as company_name
                FROM articles a 
                ORDER BY a.created_at DESC 
                LIMIT 50
            """)
            articles = cur.fetchall()
            return jsonify([dict(article) for article in articles])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/health')
def get_health():
    """Get system health status."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get recent health checks
            cur.execute("""
                SELECT * FROM health_checks 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            health_checks = cur.fetchall()
            
            # Get agent states
            cur.execute("SELECT * FROM agent_states ORDER BY last_execution DESC")
            agent_states = cur.fetchall()
            
            return jsonify({
                'health_checks': [dict(hc) for hc in health_checks],
                'agent_states': [dict(as_state) for as_state in agent_states],
                'database_connected': True
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/stats')
def get_stats():
    """Get system statistics."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            stats = {}
            
            # Count records
            cur.execute("SELECT COUNT(*) as count FROM companies")
            stats['companies'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM transcripts")
            stats['transcripts'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM analyses")
            stats['analyses'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM articles")
            stats['articles'] = cur.fetchone()['count']
            
            # Recent activity (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            cur.execute("SELECT COUNT(*) as count FROM transcripts WHERE published_at > %s", (yesterday,))
            stats['transcripts_24h'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM analyses WHERE created_at > %s", (yesterday,))
            stats['analyses_24h'] = cur.fetchone()['count']
            
            return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
