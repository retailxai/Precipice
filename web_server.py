#!/usr/bin/env python3
"""
RetailXAI Web Server
Serves the dashboard and provides API endpoints for publishing
"""

import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
import os
import sys

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from publish_api import PublishingAPI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('RetailXAI.WebServer')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize publishing API
publish_api = PublishingAPI()

@app.route('/')
def dashboard():
    """Serve the main dashboard."""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/drafts')
def get_drafts():
    """Get all available drafts."""
    try:
        drafts = publish_api.get_drafts()
        return jsonify({
            'success': True,
            'drafts': drafts,
            'count': len(drafts)
        })
    except Exception as e:
        logger.error(f"Error getting drafts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/drafts/<int:draft_id>')
def get_draft(draft_id):
    """Get a specific draft by ID."""
    try:
        drafts = publish_api.get_drafts()
        draft = next((d for d in drafts if d['id'] == draft_id), None)
        
        if not draft:
            return jsonify({
                'success': False,
                'error': 'Draft not found'
            }), 404
        
        return jsonify({
            'success': True,
            'draft': draft
        })
    except Exception as e:
        logger.error(f"Error getting draft {draft_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/publish', methods=['POST'])
def publish_draft():
    """Publish a draft to a specific channel."""
    try:
        data = request.get_json()
        draft_id = data.get('draftId')
        channel = data.get('channel')
        
        if not draft_id or not channel:
            return jsonify({
                'success': False,
                'error': 'Missing draftId or channel'
            }), 400
        
        result = publish_api.publish_draft(draft_id, channel)
        
        if result['success']:
            logger.info(f"Successfully published draft {draft_id} to {channel}")
        else:
            logger.error(f"Failed to publish draft {draft_id} to {channel}: {result.get('error')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error publishing draft: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    try:
        drafts = publish_api.get_drafts()
        
        # Calculate stats
        total_drafts = len(drafts)
        published_today = len([d for d in drafts if d.get('status') == 'published' and 
                              datetime.fromisoformat(d.get('created_at', '1970-01-01').replace('Z', '+00:00')).date() == datetime.now().date()])
        
        # Count unique channels
        channels = set()
        for draft in drafts:
            if 'channels' in draft:
                channels.update(draft['channels'])
            elif 'type' in draft:
                channels.add(draft['type'])
        
        return jsonify({
            'success': True,
            'stats': {
                'totalDrafts': total_drafts,
                'publishedToday': published_today,
                'activeChannels': len(channels),
                'lastUpdate': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system-status')
def get_system_status():
    """Get system status information."""
    try:
        # This would typically check actual system status
        # For now, we'll return mock data
        status = {
            'database': 'Connected',
            'apiKeys': 'Valid',
            'lastCollection': '2025-09-11T22:11:42Z',
            'nextScheduled': '2025-09-12T07:00:00Z',
            'agentsRunning': 4,
            'totalAgents': 9,
            'uptime': '2 hours 15 minutes'
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Trigger a data refresh."""
    try:
        # This would typically trigger the data collection pipeline
        # For now, we'll just return success
        logger.info("Data refresh requested")
        
        return jsonify({
            'success': True,
            'message': 'Data refresh initiated'
        })
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('drafts/substack', exist_ok=True)
    os.makedirs('drafts/twitter', exist_ok=True)
    os.makedirs('test_drafts/linkedin', exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
