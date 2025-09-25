#!/usr/bin/env python3
"""
RetailXAI Maintenance Server
Serves a maintenance page while security updates are being applied
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from datetime import datetime

app = FastAPI(
    title="RetailXAI Maintenance",
    description="Maintenance mode for security updates",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response

def get_maintenance_html():
    """Generate maintenance page HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RetailXAI Dashboard - Maintenance</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
            }
            .maintenance-icon {
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            .security-badge {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            }
        </style>
    </head>
    <body class="min-h-screen flex items-center justify-center">
        <div class="max-w-2xl w-full space-y-8 p-8 text-center">
            <div>
                <div class="maintenance-icon text-8xl mb-4">🔧</div>
                <h1 class="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-600 mb-4">
                    Maintenance Mode
                </h1>
                <p class="text-xl text-gray-300 mb-2">
                    The RetailXAI Dashboard is currently undergoing security updates
                </p>
                <p class="text-lg text-gray-400">
                    We're implementing enhanced security measures to better protect your data
                </p>
            </div>
            
            <div class="bg-yellow-500/20 border border-yellow-500/30 rounded-xl p-8">
                <h2 class="text-2xl font-semibold text-yellow-300 mb-4 flex items-center justify-center">
                    🛡️ Security Updates in Progress
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                    <div class="space-y-2">
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                            JWT Authentication System
                        </div>
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                            Rate Limiting Protection
                        </div>
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                            Input Validation & Sanitization
                        </div>
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                            Security Headers Implementation
                        </div>
                    </div>
                    <div class="space-y-2">
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                            CORS Policy Updates
                        </div>
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                            API Key Authentication
                        </div>
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                            Security Logging & Monitoring
                        </div>
                        <div class="flex items-center text-gray-300">
                            <span class="w-2 h-2 bg-yellow-500 rounded-full mr-3"></span>
                            Session Management (In Progress)
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="bg-blue-500/20 border border-blue-500/30 rounded-xl p-6">
                <h3 class="text-xl font-semibold text-blue-300 mb-3">🔒 Enhanced Security Features</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div class="text-center">
                        <div class="text-2xl mb-2">🛡️</div>
                        <div class="text-gray-300">Brute Force Protection</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl mb-2">🔐</div>
                        <div class="text-gray-300">Secure Token Management</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl mb-2">📊</div>
                        <div class="text-gray-300">Security Monitoring</div>
                    </div>
                </div>
            </div>
            
            <div class="text-sm text-gray-400 space-y-2">
                <p><strong>Expected completion:</strong> Within 24 hours</p>
                <p><strong>For urgent access:</strong> admin@retailxai.com</p>
                <p><strong>Last updated:</strong> """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + """</p>
            </div>
            
            <div class="flex justify-center space-x-4">
                <button onclick="location.reload()" class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition duration-300">
                    🔄 Check Again
                </button>
                <button onclick="window.open('mailto:admin@retailxai.com?subject=Urgent Dashboard Access Request', '_blank')" class="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition duration-300">
                    📧 Contact Admin
                </button>
            </div>
            
            <div class="mt-8 pt-6 border-t border-gray-600">
                <div class="flex items-center justify-center space-x-2 text-xs text-gray-500">
                    <span class="security-badge px-3 py-1 rounded-full text-white font-medium">
                        🔒 Security Enhanced
                    </span>
                    <span>•</span>
                    <span>RetailXAI Dashboard v3.0</span>
                    <span>•</span>
                    <span>Maintenance Mode Active</span>
                </div>
            </div>
        </div>
        
        <script>
            // Auto-refresh every 30 seconds
            setTimeout(() => {
                location.reload();
            }, 30000);
            
            // Show last update time
            document.addEventListener('DOMContentLoaded', function() {
                const now = new Date();
                const timeString = now.toLocaleString();
                console.log('Page loaded at:', timeString);
            });
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def maintenance_page():
    """Serve the maintenance page"""
    return HTMLResponse(content=get_maintenance_html(), status_code=503)

@app.get("/maintenance", response_class=HTMLResponse)
async def maintenance_page_alt():
    """Alternative maintenance page route"""
    return HTMLResponse(content=get_maintenance_html(), status_code=503)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "maintenance",
        "message": "Dashboard is in maintenance mode for security updates",
        "timestamp": datetime.now().isoformat(),
        "expected_completion": "Within 24 hours"
    }

@app.get("/api/status")
async def status_check():
    """Status check endpoint"""
    return {
        "maintenance_mode": True,
        "security_updates": "in_progress",
        "services": {
            "dashboard": "offline",
            "api": "maintenance_mode",
            "authentication": "updating"
        },
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🔧 Starting RetailXAI Maintenance Server")
    print("======================================")
    print("Maintenance mode is active")
    print("Dashboard is offline for security updates")
    print("")
    print("Access URLs:")
    print("  Maintenance Page: http://localhost:8001")
    print("  Health Check: http://localhost:8001/api/health")
    print("  Status Check: http://localhost:8001/api/status")
    print("")
    print("To stop maintenance mode:")
    print("  ./disable_maintenance.sh")
    print("")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info"
    )

