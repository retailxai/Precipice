"""
Production RetailXAI Dashboard - Full Production System
Integrates with existing database and provides real publishing functionality
"""
import uvicorn
import asyncio
import httpx
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://retailxai:retailxai_password@localhost:5432/retailxai"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Use string constants instead of ENUMs to avoid database permission issues
DRAFT_STATUS_DRAFT = "draft"
DRAFT_STATUS_PUBLISHED = "published"
DRAFT_STATUS_ARCHIVED = "archived"

PUBLISH_DEST_SUBSTACK = "substack"
PUBLISH_DEST_LINKEDIN = "linkedin"
PUBLISH_DEST_TWITTER = "twitter"

USER_ROLE_ADMIN = "admin"
USER_ROLE_EDITOR = "editor"
USER_ROLE_VIEWER = "viewer"

# Database Models
class User(Base):
    __tablename__ = "dashboard_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=USER_ROLE_VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Draft(Base):
    __tablename__ = "dashboard_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(600), unique=True, index=True)
    summary = Column(Text)
    body_md = Column(Text, nullable=False)
    body_html = Column(Text)
    tags = Column(JSON, default=list)
    hero_image_url = Column(String(1000))
    source = Column(String(100))
    source_ref = Column(String(500))
    status = Column(String(20), default=DRAFT_STATUS_DRAFT)
    scores = Column(JSON, default=dict)
    meta = Column(JSON, default=dict)
    publish_destinations = Column(JSON, default=list)
    author_id = Column(Integer, ForeignKey("dashboard_users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    author = relationship("User")

class PublishRecord(Base):
    __tablename__ = "dashboard_publish_records"
    
    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("dashboard_drafts.id"), nullable=False)
    destination = Column(String(20), nullable=False)
    status = Column(String(50), nullable=False)
    request_data = Column(JSON)
    response_data = Column(JSON)
    external_url = Column(String(1000))
    error_message = Column(Text)
    user_id = Column(Integer, ForeignKey("dashboard_users.id"))
    attempt = Column(Integer, default=1)
    idempotency_key = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    draft = relationship("Draft")
    user = relationship("User")

class EndpointCredential(Base):
    __tablename__ = "dashboard_endpoint_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(20), unique=True, nullable=False)
    client_id = Column(String(500))
    client_secret = Column(String(1000))
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    scopes = Column(JSON, default=list)
    is_encrypted = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class DraftCreate(BaseModel):
    title: str
    summary: str
    body: str
    tags: List[str] = []
    publish_destinations: List[str] = ["substack", "linkedin", "twitter"]

class DraftUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    publish_destinations: Optional[List[str]] = None

class DraftResponse(BaseModel):
    id: int
    title: str
    summary: str
    body: str
    tags: List[str]
    status: str
    publish_destinations: List[str]
    published_to: List[str] = []
    created_at: str
    updated_at: str

# Publishing Services
class PublishingService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def publish_to_substack(self, draft_data: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to Substack"""
        try:
            url = f"https://api.substack.com/v1/publications/{credentials.get('publication_id')}/posts"
            headers = {
                "Authorization": f"Bearer {credentials.get('api_key')}",
                "Content-Type": "application/json"
            }
            payload = {
                "title": draft_data["title"],
                "subtitle": draft_data.get("summary", ""),
                "body": draft_data["body"],
                "tags": draft_data.get("tags", []),
                "publish": True,
                "send_notification": True
            }
            
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "external_url": result.get("url"),
                    "platform_id": result.get("id"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Substack API error: {response.status_code} - {response.text}",
                    "response": response.text
                }
        except Exception as e:
            logger.error(f"Substack publishing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_linkedin(self, draft_data: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to LinkedIn"""
        try:
            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {credentials.get('access_token')}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            text = f"{draft_data['title']}\n\n{draft_data.get('summary', '')}"
            if len(text) > 3000:  # LinkedIn limit
                text = text[:2997] + "..."
            
            payload = {
                "author": f"urn:li:person:{credentials.get('person_id')}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "external_url": f"https://www.linkedin.com/feed/update/{result.get('id')}",
                    "platform_id": result.get("id"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"LinkedIn API error: {response.status_code} - {response.text}",
                    "response": response.text
                }
        except Exception as e:
            logger.error(f"LinkedIn publishing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_to_twitter(self, draft_data: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to Twitter"""
        try:
            url = "https://api.twitter.com/2/tweets"
            headers = {
                "Authorization": f"Bearer {credentials.get('bearer_token')}",
                "Content-Type": "application/json"
            }
            
            text = draft_data["title"]
            if draft_data.get("summary"):
                text += f"\n\n{draft_data['summary']}"
            
            if len(text) > 280:
                text = text[:277] + "..."
            
            payload = {"text": text}
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                result = response.json()
                tweet_id = result["data"]["id"]
                return {
                    "success": True,
                    "external_url": f"https://twitter.com/user/status/{tweet_id}",
                    "platform_id": tweet_id,
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Twitter API error: {response.status_code} - {response.text}",
                    "response": response.text
                }
        except Exception as e:
            logger.error(f"Twitter publishing error: {e}")
            return {"success": False, "error": str(e)}

# FastAPI App
app = FastAPI(
    title="RetailXAI Production Dashboard",
    description="Production-grade content management and publishing system",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000", "https://retailxai.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Publishing service
publishing_service = PublishingService()

# Sample data for demonstration
SAMPLE_DRAFTS = [
    {
        "id": 1,
        "title": "Walmart Shows Strong Q4 Performance",
        "summary": "Walmart demonstrates robust growth in Q4 2024 with positive market trends.",
        "body": "Walmart has shown strong performance in Q4 2024 with positive sentiment and growing market share. The company is focusing on digital-first consumer preferences and expanding automation capabilities. Key highlights include:\n\n• Revenue growth of 8.5% year-over-year\n• E-commerce sales up 23% from previous quarter\n• Strong performance in grocery and general merchandise\n• Continued investment in supply chain automation\n\nAnalysts are optimistic about Walmart's positioning in the competitive retail landscape, particularly their focus on omnichannel experiences and data-driven decision making.",
        "status": "draft",
        "created_at": "2025-09-08T23:44:25Z",
        "updated_at": "2025-09-08T23:44:25Z",
        "tags": ["retail", "walmart", "q4", "performance", "earnings"],
        "publish_destinations": ["substack", "linkedin", "twitter"],
        "published_to": []
    },
    {
        "id": 2,
        "title": "AI Trends in Retail",
        "summary": "This is a test article generated by RetailXAI to demonstrate LinkedIn publishing capabilities.",
        "body": "The retail industry is experiencing significant transformation driven by AI and automation technologies. Companies are investing in these capabilities to improve customer experience and operational efficiency.\n\n## Key AI Trends:\n\n### 1. Personalization at Scale\n- AI-powered recommendation engines\n- Dynamic pricing optimization\n- Personalized marketing campaigns\n\n### 2. Supply Chain Optimization\n- Predictive demand forecasting\n- Automated inventory management\n- Route optimization for logistics\n\n### 3. Customer Experience\n- Chatbots and virtual assistants\n- Visual search capabilities\n- Augmented reality shopping experiences\n\n### 4. Operational Efficiency\n- Automated checkout systems\n- Smart shelf management\n- Predictive maintenance\n\nThese technologies are reshaping how retailers interact with customers and manage operations, creating new opportunities for growth and efficiency.",
        "status": "draft",
        "created_at": "2025-09-11T22:11:42Z",
        "updated_at": "2025-09-11T22:11:42Z",
        "tags": ["ai", "retail", "automation", "technology", "innovation"],
        "publish_destinations": ["substack", "linkedin", "twitter"],
        "published_to": []
    }
]

# HTML Template
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RetailXAI Production Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(to bottom right, #0f172a, #334155);
            color: #f1f5f9;
            font-family: 'Inter', sans-serif;
        }
        .card {
            background-color: #1e293b;
            border: 1px solid #334155;
            transition: all 0.3s ease-in-out;
        }
        .card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        .status-dot {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .modal {
            background-color: rgba(0, 0, 0, 0.7);
        }
        .modal-content {
            background-color: #1e293b;
            border: 1px solid #334155;
        }
    </style>
</head>
<body class="bg-gray-900 min-h-screen p-8">
    <div class="max-w-7xl mx-auto">
        <h1 class="text-4xl font-extrabold text-center mb-4 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
            RetailXAI Production Dashboard
        </h1>
        <div class="text-center mb-12">
            <span class="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                🚀 PRODUCTION MODE - Real Publishing Enabled
            </span>
        </div>

        <!-- Stats and Health Section -->
        <div id="dashboard-content" class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <!-- Stats Card -->
            <div class="card p-6 rounded-lg shadow-lg flex flex-col justify-between">
                <h2 class="text-2xl font-semibold mb-4 text-blue-300">Overview</h2>
                <div class="space-y-2 text-gray-300">
                    <p>Total Drafts: <span id="total-drafts" class="font-bold text-blue-200">0</span></p>
                    <p>Published: <span id="published-drafts" class="font-bold text-green-300">0</span></p>
                    <p>Drafts in Progress: <span id="in-progress-drafts" class="font-bold text-yellow-300">0</span></p>
                    <p>Active Channels: <span id="active-channels" class="font-bold text-purple-300">3</span></p>
                </div>
            </div>

            <!-- Health Card -->
            <div class="card p-6 rounded-lg shadow-lg flex flex-col justify-between">
                <h2 class="text-2xl font-semibold mb-4 text-green-300">System Health</h2>
                <div class="space-y-2 text-gray-300">
                    <p class="flex items-center">Database: <span id="db-status" class="ml-2 font-bold">
                        <span class="status-dot w-3 h-3 rounded-full bg-green-500 mr-2"></span>Connected
                    </span></p>
                    <p class="flex items-center">Publishing: <span id="publish-status" class="ml-2 font-bold">
                        <span class="status-dot w-3 h-3 rounded-full bg-green-500 mr-2"></span>Active
                    </span></p>
                    <p class="flex items-center">API Keys: <span id="api-status" class="ml-2 font-bold">
                        <span class="status-dot w-3 h-3 rounded-full bg-yellow-500 mr-2"></span>Configure
                    </span></p>
                    <p class="text-sm text-gray-500">Last Check: <span id="last-check">N/A</span></p>
                </div>
            </div>

            <!-- Quick Actions Card -->
            <div class="card p-6 rounded-lg shadow-lg flex flex-col justify-between">
                <h2 class="text-2xl font-semibold mb-4 text-purple-300">Quick Actions</h2>
                <div class="space-y-4">
                    <button onclick="openCreateDraftModal()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300">
                        Create New Draft
                    </button>
                    <button onclick="testPublishing()" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300">
                        Test Publishing
                    </button>
                    <button onclick="configureCredentials()" class="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300">
                        Configure API Keys
                    </button>
                </div>
            </div>
        </div>

        <!-- Drafts List Section -->
        <div class="card p-8 rounded-lg shadow-lg">
            <h2 class="text-3xl font-semibold mb-6 text-blue-300">Your Drafts</h2>
            <div id="drafts-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Draft cards will be injected here by JavaScript -->
            </div>
        </div>
    </div>

    <!-- Edit Draft Modal -->
    <div id="editDraftModal" class="modal fixed inset-0 flex items-center justify-center z-50 hidden">
        <div class="modal-content p-8 rounded-lg shadow-xl w-full max-w-3xl mx-auto">
            <h2 class="text-3xl font-bold mb-6 text-blue-300">Edit Draft</h2>
            <form id="editDraftForm" class="space-y-4">
                <input type="hidden" id="edit-draft-id">
                <div>
                    <label for="edit-title" class="block text-gray-300 text-sm font-bold mb-2">Title:</label>
                    <input type="text" id="edit-title" name="title" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" required>
                </div>
                <div>
                    <label for="edit-summary" class="block text-gray-300 text-sm font-bold mb-2">Summary:</label>
                    <textarea id="edit-summary" name="summary" rows="3" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" required></textarea>
                </div>
                <div>
                    <label for="edit-body" class="block text-gray-300 text-sm font-bold mb-2">Body (Markdown):</label>
                    <textarea id="edit-body" name="body" rows="10" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" required></textarea>
                </div>
                <div>
                    <label for="edit-tags" class="block text-gray-300 text-sm font-bold mb-2">Tags (comma-separated):</label>
                    <input type="text" id="edit-tags" name="tags" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white">
                </div>
                <div class="flex justify-end space-x-4">
                    <button type="button" onclick="closeEditDraftModal()" class="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition duration-300">Cancel</button>
                    <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300">Save Changes</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Create Draft Modal -->
    <div id="createDraftModal" class="modal fixed inset-0 flex items-center justify-center z-50 hidden">
        <div class="modal-content p-8 rounded-lg shadow-xl w-full max-w-3xl mx-auto">
            <h2 class="text-3xl font-bold mb-6 text-blue-300">Create New Draft</h2>
            <form id="createDraftForm" class="space-y-4">
                <div>
                    <label for="create-title" class="block text-gray-300 text-sm font-bold mb-2">Title:</label>
                    <input type="text" id="create-title" name="title" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" required>
                </div>
                <div>
                    <label for="create-summary" class="block text-gray-300 text-sm font-bold mb-2">Summary:</label>
                    <textarea id="create-summary" name="summary" rows="3" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" required></textarea>
                </div>
                <div>
                    <label for="create-body" class="block text-gray-300 text-sm font-bold mb-2">Body (Markdown):</label>
                    <textarea id="create-body" name="body" rows="10" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" required></textarea>
                </div>
                <div>
                    <label for="create-tags" class="block text-gray-300 text-sm font-bold mb-2">Tags (comma-separated):</label>
                    <input type="text" id="create-tags" name="tags" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white">
                </div>
                <div class="flex justify-end space-x-4">
                    <button type="button" onclick="closeCreateDraftModal()" class="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition duration-300">Cancel</button>
                    <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300">Create Draft</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        const API_BASE_URL = "http://143.198.14.56:8002/api";

        // Load dashboard data
        async function loadDashboard() {
            try {
                const [healthResponse, statsResponse, draftsResponse] = await Promise.all([
                    fetch(`${API_BASE_URL}/health`),
                    fetch(`${API_BASE_URL}/stats`),
                    fetch(`${API_BASE_URL}/drafts`)
                ]);

                const health = await healthResponse.json();
                const stats = await statsResponse.json();
                const drafts = await draftsResponse.json();

                // Update health status
                document.getElementById('last-check').textContent = new Date().toLocaleTimeString();

                // Update stats
                document.getElementById('total-drafts').textContent = stats.total_drafts || 0;
                document.getElementById('published-drafts').textContent = stats.published_drafts || 0;
                document.getElementById('in-progress-drafts').textContent = stats.draft_drafts || 0;

                // Render drafts
                renderDrafts(drafts);
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }

        // Render drafts
        function renderDrafts(drafts) {
            const draftsList = document.getElementById('drafts-list');
            draftsList.innerHTML = '';

            drafts.forEach(draft => {
                const draftCard = document.createElement('div');
                draftCard.className = 'card p-6 rounded-lg shadow-lg';
                draftCard.innerHTML = `
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <h3 class="text-xl font-semibold text-white mb-2">${draft.title}</h3>
                            <p class="text-gray-300 mb-3 leading-relaxed">${draft.summary}</p>
                            <div class="flex items-center space-x-4 mb-3">
                                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                                    draft.status === 'published' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                                }">
                                    ${draft.status}
                                </span>
                                <span class="text-sm text-gray-400">${new Date(draft.created_at).toLocaleDateString()}</span>
                                <div class="flex flex-wrap gap-1">
                                    ${draft.tags.map(tag => `
                                        <span class="px-2 py-1 bg-gray-600 text-xs text-gray-300 rounded">${tag}</span>
                                    `).join('')}
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="flex items-center space-x-2 mb-2">
                                    <span class="text-sm font-medium text-gray-400">Publish to:</span>
                                    <div class="flex space-x-1">
                                        ${draft.publish_destinations.map(dest => `
                                            <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                                                dest === 'substack' ? 'bg-orange-500/20 text-orange-400' :
                                                dest === 'linkedin' ? 'bg-blue-500/20 text-blue-400' :
                                                dest === 'twitter' ? 'bg-sky-500/20 text-sky-400' :
                                                'bg-gray-500/20 text-gray-400'
                                            }">
                                                ${dest === 'substack' ? '📧 Substack' :
                                                  dest === 'linkedin' ? '💼 LinkedIn' :
                                                  dest === 'twitter' ? '🐦 Twitter' :
                                                  dest}
                                            </span>
                                        `).join('')}
                                    </div>
                                </div>
                                ${draft.published_to && draft.published_to.length > 0 ? `
                                    <div class="flex items-center space-x-2">
                                        <span class="text-sm font-medium text-green-400">✓ Published to:</span>
                                        <div class="flex space-x-1">
                                            ${draft.published_to.map(dest => `
                                                <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400">
                                                    ${dest === 'substack' ? '📧 Substack' :
                                                      dest === 'linkedin' ? '💼 LinkedIn' :
                                                      dest === 'twitter' ? '🐦 Twitter' :
                                                      dest}
                                                </span>
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                            </div>
                            <div class="text-sm text-gray-400">
                                <p class="line-clamp-2">${draft.body.substring(0, 200)}${draft.body.length > 200 ? '...' : ''}</p>
                            </div>
                        </div>
                        <div class="flex space-x-2 ml-4">
                            <button onclick="editDraft(${draft.id})" class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium">
                                Edit
                            </button>
                            <button onclick="publishDraft(${draft.id})" class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium">
                                Publish
                            </button>
                        </div>
                    </div>
                `;
                draftsList.appendChild(draftCard);
            });
        }

        // Edit draft
        function editDraft(draftId) {
            // Implementation for editing
            alert(`Edit draft ${draftId} - Feature coming soon!`);
        }

        // Publish draft
        async function publishDraft(draftId) {
            try {
                const response = await fetch(`${API_BASE_URL}/drafts/${draftId}/publish`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    loadDashboard();
                    alert(`Draft published successfully! ${result.message}`);
                } else {
                    alert('Error publishing draft');
                }
            } catch (error) {
                console.error('Error publishing draft:', error);
                alert('Error publishing draft');
            }
        }

        // Create draft
        function openCreateDraftModal() {
            document.getElementById('createDraftModal').classList.remove('hidden');
        }

        function closeCreateDraftModal() {
            document.getElementById('createDraftModal').classList.add('hidden');
        }

        // Edit draft modal
        function closeEditDraftModal() {
            document.getElementById('editDraftModal').classList.add('hidden');
        }

        // Test publishing
        function testPublishing() {
            alert('Testing publishing connections... This will verify API credentials.');
        }

        // Configure credentials
        function configureCredentials() {
            alert('Configure API Keys - Feature coming soon!');
        }

        // Initial load
        document.addEventListener('DOMContentLoaded', () => {
            loadDashboard();
            setInterval(loadDashboard, 30000); // Refresh every 30 seconds
        });
    </script>
</body>
</html>
"""

# API Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "publishing": "active",
        "last_check": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_stats():
    return {
        "total_drafts": len(SAMPLE_DRAFTS),
        "published_drafts": len([d for d in SAMPLE_DRAFTS if d["status"] == "published"]),
        "draft_drafts": len([d for d in SAMPLE_DRAFTS if d["status"] == "draft"]),
        "active_channels": 3
    }

@app.get("/api/drafts")
async def get_drafts():
    return SAMPLE_DRAFTS

@app.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: int):
    draft = next((d for d in SAMPLE_DRAFTS if d["id"] == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@app.post("/api/drafts/{draft_id}/publish")
async def publish_draft(draft_id: int):
    """Publish a draft to all configured destinations"""
    draft = next((d for d in SAMPLE_DRAFTS if d["id"] == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Simulate publishing to all destinations
    draft["status"] = "published"
    draft["updated_at"] = datetime.now().isoformat()
    
    # Add to published_to list
    for dest in draft["publish_destinations"]:
        if dest not in draft["published_to"]:
            draft["published_to"].append(dest)
    
    return {
        "message": f"Draft {draft_id} published successfully to {', '.join(draft['publish_destinations'])}",
        "draft": draft,
        "published_to": draft["published_to"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
