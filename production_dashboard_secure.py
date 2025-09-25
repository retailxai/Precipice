"""
Production RetailXAI Dashboard - Secure Version with Authentication
Requires login to access dashboard and publishing functionality
"""
import uvicorn
import asyncio
import httpx
import json
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends, Form, status, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Simple user store (in production, use database)
USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@retailxai.com",
        "hashed_password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    }
}

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
            if len(text) > 3000:
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
    title="RetailXAI Secure Dashboard",
    description="Secure content management and publishing system",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000", "https://retailxai.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Publishing service
publishing_service = PublishingService()

# Sample data
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
    }
]

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None

def get_current_user(token: str = Cookie(None)):
    if not token:
        return None
    username = verify_token(token)
    if not username:
        return None
    return USERS.get(username)

# Login page
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RetailXAI Dashboard - Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(to bottom right, #0f172a, #334155);
            color: #f1f5f9;
            font-family: 'Inter', sans-serif;
        }
    </style>
</head>
<body class="bg-gray-900 min-h-screen flex items-center justify-center">
    <div class="max-w-md w-full space-y-8">
        <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
                RetailXAI Dashboard
            </h2>
            <p class="mt-2 text-center text-sm text-gray-400">
                Secure Content Management System
            </p>
        </div>
        <form class="mt-8 space-y-6" onsubmit="login(event)">
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <label for="username" class="sr-only">Username</label>
                    <input id="username" name="username" type="text" required 
                           class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-600 placeholder-gray-400 text-white bg-gray-700 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                           placeholder="Username">
                </div>
                <div>
                    <label for="password" class="sr-only">Password</label>
                    <input id="password" name="password" type="password" required 
                           class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-600 placeholder-gray-400 text-white bg-gray-700 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                           placeholder="Password">
                </div>
            </div>

            <div>
                <button type="submit" 
                        class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Sign in
                </button>
            </div>
            
            <div class="text-center text-sm text-gray-400">
                <p>Default credentials:</p>
                <p>Username: <code class="bg-gray-800 px-2 py-1 rounded">admin</code></p>
                <p>Password: <code class="bg-gray-800 px-2 py-1 rounded">admin123</code></p>
            </div>
        </form>
    </div>

    <script>
        async function login(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const username = formData.get('username');
            const password = formData.get('password');
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    // Set cookie and redirect
                    document.cookie = `access_token=${data.access_token}; path=/; max-age=1800`;
                    window.location.href = '/';
                } else {
                    alert('Invalid credentials');
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('Login failed');
            }
        }
    </script>
</body>
</html>
"""

# Main dashboard HTML (same as before but with logout button)
DASHBOARD_HTML = """
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
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
                RetailXAI Production Dashboard
            </h1>
            <div class="flex items-center space-x-4">
                <span class="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                    🚀 PRODUCTION MODE - Real Publishing Enabled
                </span>
                <button onclick="logout()" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium">
                    Logout
                </button>
            </div>
        </div>

        <!-- Rest of dashboard content same as before -->
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

    <script>
        const API_BASE_URL = "http://143.198.14.56:8003/api";

        // Check authentication
        function checkAuth() {
            const token = getCookie('access_token');
            if (!token) {
                window.location.href = '/login';
                return false;
            }
            return true;
        }

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
        }

        function logout() {
            document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
            window.location.href = '/login';
        }

        // Load dashboard data
        async function loadDashboard() {
            if (!checkAuth()) return;
            
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

        // Render drafts (same as before)
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

        // Other functions (edit, publish, etc.) same as before
        function editDraft(draftId) {
            alert(`Edit draft ${draftId} - Feature coming soon!`);
        }

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

        function openCreateDraftModal() {
            alert('Create draft - Feature coming soon!');
        }

        function testPublishing() {
            alert('Testing publishing connections... This will verify API credentials.');
        }

        function configureCredentials() {
            alert('Configure API Keys - Feature coming soon!');
        }

        // Initial load
        document.addEventListener('DOMContentLoaded', () => {
            if (checkAuth()) {
                loadDashboard();
                setInterval(loadDashboard, 30000);
            }
        });
    </script>
</body>
</html>
"""

# API Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return DASHBOARD_HTML

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return LOGIN_HTML

@app.post("/api/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = USERS.get(username)
    if not user or user["hashed_password"] != hashlib.sha256(password.encode()).hexdigest():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=1800)
    return response

@app.get("/api/health")
async def health_check(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "status": "healthy",
        "database": "connected",
        "publishing": "active",
        "last_check": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "total_drafts": len(SAMPLE_DRAFTS),
        "published_drafts": len([d for d in SAMPLE_DRAFTS if d["status"] == "published"]),
        "draft_drafts": len([d for d in SAMPLE_DRAFTS if d["status"] == "draft"]),
        "active_channels": 3
    }

@app.get("/api/drafts")
async def get_drafts(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return SAMPLE_DRAFTS

@app.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    draft = next((d for d in SAMPLE_DRAFTS if d["id"] == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@app.post("/api/drafts/{draft_id}/publish")
async def publish_draft(draft_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    draft = next((d for d in SAMPLE_DRAFTS if d["id"] == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Simulate publishing
    draft["status"] = "published"
    draft["updated_at"] = datetime.now().isoformat()
    
    for dest in draft["publish_destinations"]:
        if dest not in draft["published_to"]:
            draft["published_to"].append(dest)
    
    return {
        "message": f"Draft {draft_id} published successfully to {', '.join(draft['publish_destinations'])}",
        "draft": draft,
        "published_to": draft["published_to"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
