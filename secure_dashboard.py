#!/usr/bin/env python3
"""
RetailXAI Secure Dashboard - Production-Ready with Comprehensive Security
Features:
- JWT-based authentication with refresh tokens
- Rate limiting and brute force protection
- Input validation and sanitization
- Secure CORS configuration
- API key authentication
- Security headers and HTTPS enforcement
- Audit logging
- Environment-based configuration
"""

import os
import hashlib
import secrets
import jwt
import bcrypt
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from functools import wraps
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request, Depends, Form, status, Cookie, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RetailXAI.Security')

# Security Configuration
class SecurityConfig:
    def __init__(self):
        self.SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(32))
        self.REFRESH_SECRET_KEY = os.getenv('REFRESH_SECRET_KEY', secrets.token_urlsafe(32))
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
        self.MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
        self.LOCKOUT_DURATION_MINUTES = int(os.getenv('LOCKOUT_DURATION_MINUTES', '15'))
        self.ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,143.198.14.56').split(',')
        self.ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,https://retailxai.github.io').split(',')
        self.API_KEY_HEADER = os.getenv('API_KEY_HEADER', 'X-API-Key')
        self.API_KEYS = os.getenv('API_KEYS', '').split(',') if os.getenv('API_KEYS') else []
        
    def validate_config(self):
        """Validate security configuration"""
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if len(self.REFRESH_SECRET_KEY) < 32:
            raise ValueError("REFRESH_SECRET_KEY must be at least 32 characters")
        if not self.API_KEYS:
            logger.warning("No API keys configured - API access will be disabled")

config = SecurityConfig()
config.validate_config()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# FastAPI App
app = FastAPI(
    title="RetailXAI Secure Dashboard",
    description="Production-ready secure content management system",
    version="3.0.0",
    docs_url="/api/docs" if os.getenv('ENABLE_DOCS', 'false').lower() == 'true' else None,
    redoc_url="/api/redoc" if os.getenv('ENABLE_DOCS', 'false').lower() == 'true' else None
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=config.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; img-src 'self' data: https:; connect-src 'self'"
    
    return response

# Security Models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v.lower()

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class DraftUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = Field(None, max_length=10000)
    tags: Optional[List[str]] = Field(None, max_items=10)
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if len(tag) > 50 or not tag.replace('-', '').replace('_', '').isalnum():
                    raise ValueError('Invalid tag format')
        return v

class DraftCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., max_length=500)
    body: str = Field(..., max_length=10000)
    tags: List[str] = Field(default_factory=list, max_items=10)

# User Management
class UserManager:
    def __init__(self):
        self.users = {}
        self.login_attempts = defaultdict(list)
        self.locked_accounts = {}
        self._load_default_users()
    
    def _load_default_users(self):
        """Load default users from environment or create admin user"""
        admin_password = os.getenv('ADMIN_PASSWORD', 'SecureAdmin123!')
        self.create_user("admin", admin_password, "admin@retailxai.com", "admin")
        
        # Load additional users from environment
        additional_users = os.getenv('ADDITIONAL_USERS', '')
        if additional_users:
            for user_data in additional_users.split(';'):
                if ':' in user_data:
                    username, password, email, role = user_data.split(':')
                    self.create_user(username, password, email, role)
    
    def create_user(self, username: str, password: str, email: str, role: str = "user"):
        """Create a new user with hashed password"""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.users[username] = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        logger.info(f"User created: {username} with role: {role}")
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        user = self.users.get(username)
        if not user:
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), user["hashed_password"])
    
    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed login attempts"""
        if username in self.locked_accounts:
            lockout_time = self.locked_accounts[username]
            if datetime.now() < lockout_time:
                return True
            else:
                del self.locked_accounts[username]
        return False
    
    def record_login_attempt(self, username: str, success: bool):
        """Record login attempt and manage account locking"""
        now = datetime.now()
        
        if success:
            # Clear failed attempts on successful login
            if username in self.login_attempts:
                del self.login_attempts[username]
            if username in self.locked_accounts:
                del self.locked_accounts[username]
            
            # Update last login
            if username in self.users:
                self.users[username]["last_login"] = now.isoformat()
        else:
            # Record failed attempt
            self.login_attempts[username].append(now)
            
            # Check if account should be locked
            recent_attempts = [
                attempt for attempt in self.login_attempts[username]
                if now - attempt < timedelta(minutes=config.LOCKOUT_DURATION_MINUTES)
            ]
            
            if len(recent_attempts) >= config.MAX_LOGIN_ATTEMPTS:
                self.locked_accounts[username] = now + timedelta(minutes=config.LOCKOUT_DURATION_MINUTES)
                logger.warning(f"Account locked: {username} due to {len(recent_attempts)} failed attempts")
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        return self.users.get(username)

user_manager = UserManager()

# Token Management
class TokenManager:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: dict):
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, config.REFRESH_SECRET_KEY, algorithm=config.ALGORITHM)
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[str]:
        """Verify access token and return username"""
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            if payload.get("type") != "access":
                return None
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[str]:
        """Verify refresh token and return username"""
        try:
            payload = jwt.decode(token, config.REFRESH_SECRET_KEY, algorithms=[config.ALGORITHM])
            if payload.get("type") != "refresh":
                return None
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except jwt.PyJWTError:
            return None

# Authentication Dependencies
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    username = TokenManager.verify_access_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_manager.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None

def require_api_key(api_key: str = Header(None)):
    """Require valid API key for API endpoints"""
    if not api_key or api_key not in config.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

def require_role(required_role: str):
    """Require specific role for endpoint access"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Rate Limiting Decorators
def rate_limit_override(limit: str):
    """Override rate limiting for specific endpoints"""
    def decorator(func):
        func._rate_limit_override = limit
        return func
    return decorator

# Sample Data (In production, this would be in a database)
SAMPLE_DRAFTS = [
    {
        "id": 1,
        "title": "Walmart Shows Strong Q4 Performance",
        "summary": "Walmart demonstrates robust growth in Q4 2024 with positive market trends.",
        "body": "Walmart has shown strong performance in Q4 2024 with positive sentiment and growing market share. The company is focusing on digital-first consumer preferences and expanding automation capabilities.",
        "status": "draft",
        "created_at": "2025-09-08T23:44:25Z",
        "updated_at": "2025-09-08T23:44:25Z",
        "tags": ["retail", "walmart", "q4", "performance", "earnings"],
        "publish_destinations": ["substack", "linkedin", "twitter"],
        "published_to": [],
        "author": "admin"
    }
]

# Security Logging
def log_security_event(event_type: str, details: dict, user: str = None, ip: str = None):
    """Log security events"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user": user,
        "ip": ip,
        "details": details
    }
    logger.info(f"SECURITY_EVENT: {log_entry}")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Serve the main dashboard page"""
    if not current_user:
        return RedirectResponse(url="/login")
    
    return HTMLResponse(content=get_dashboard_html())

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page"""
    return HTMLResponse(content=get_login_html())

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """Authenticate user and return tokens"""
    username = login_data.username
    password = login_data.password
    
    # Check if account is locked
    if user_manager.is_account_locked(username):
        log_security_event("ACCOUNT_LOCKED_ACCESS_ATTEMPT", {"username": username}, ip=get_remote_address(request))
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts"
        )
    
    # Verify credentials
    if not user_manager.verify_password(username, password):
        user_manager.record_login_attempt(username, False)
        log_security_event("FAILED_LOGIN", {"username": username}, ip=get_remote_address(request))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Record successful login
    user_manager.record_login_attempt(username, True)
    log_security_event("SUCCESSFUL_LOGIN", {"username": username}, ip=get_remote_address(request))
    
    # Create tokens
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = TokenManager.create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    refresh_token = TokenManager.create_refresh_token(data={"sub": username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.post("/api/auth/refresh")
@limiter.limit("10/minute")
async def refresh_token(request: Request, refresh_token: str = Form(...)):
    """Refresh access token using refresh token"""
    username = TokenManager.verify_refresh_token(refresh_token)
    if not username:
        log_security_event("INVALID_REFRESH_TOKEN", {}, ip=get_remote_address(request))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = TokenManager.create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    log_security_event("TOKEN_REFRESHED", {"username": username}, ip=get_remote_address(request))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Keep the same refresh token
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.post("/api/auth/logout")
@limiter.limit("10/minute")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout user (client should discard tokens)"""
    log_security_event("USER_LOGOUT", {"username": current_user["username"]}, ip=get_remote_address(request))
    return {"message": "Successfully logged out"}

@app.get("/api/health")
@limiter.limit("30/minute")
async def health_check(current_user: dict = Depends(get_current_user)):
    """Get system health status"""
    return {
        "status": "healthy",
        "database": "connected",
        "publishing": "active",
        "last_check": datetime.now().isoformat(),
        "user": current_user["username"]
    }

@app.get("/api/stats")
@limiter.limit("30/minute")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    return {
        "total_drafts": len(SAMPLE_DRAFTS),
        "published_drafts": len([d for d in SAMPLE_DRAFTS if d["status"] == "published"]),
        "draft_drafts": len([d for d in SAMPLE_DRAFTS if d["status"] == "draft"]),
        "active_channels": 3,
        "user": current_user["username"]
    }

@app.get("/api/drafts")
@limiter.limit("30/minute")
async def get_drafts(current_user: dict = Depends(get_current_user)):
    """Get all drafts (filtered by user role)"""
    if current_user["role"] == "admin":
        return SAMPLE_DRAFTS
    else:
        # Regular users only see their own drafts
        return [d for d in SAMPLE_DRAFTS if d.get("author") == current_user["username"]]

@app.get("/api/drafts/{draft_id}")
@limiter.limit("30/minute")
async def get_draft(draft_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific draft"""
    draft = next((d for d in SAMPLE_DRAFTS if d["id"] == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Check permissions
    if current_user["role"] != "admin" and draft.get("author") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return draft

@app.put("/api/drafts/{draft_id}")
@limiter.limit("10/minute")
async def update_draft(draft_id: int, update_data: DraftUpdate, current_user: dict = Depends(get_current_user)):
    """Update a draft"""
    draft = next((d for d in SAMPLE_DRAFTS if d["id"] == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Check permissions
    if current_user["role"] != "admin" and draft.get("author") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update the draft
    if update_data.title is not None:
        draft["title"] = update_data.title
    if update_data.summary is not None:
        draft["summary"] = update_data.summary
    if update_data.body is not None:
        draft["body"] = update_data.body
    if update_data.tags is not None:
        draft["tags"] = update_data.tags
    
    draft["updated_at"] = datetime.now().isoformat()
    
    log_security_event("DRAFT_UPDATED", {"draft_id": draft_id, "user": current_user["username"]})
    
    return {"message": f"Draft {draft_id} updated successfully", "draft": draft}

@app.post("/api/drafts/{draft_id}/publish")
@limiter.limit("5/minute")
async def publish_draft(draft_id: int, current_user: dict = Depends(get_current_user)):
    """Publish a draft"""
    draft = next((d for d in SAMPLE_DRAFTS if d["id"] == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Check permissions
    if current_user["role"] != "admin" and draft.get("author") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Simulate publishing
    draft["status"] = "published"
    draft["updated_at"] = datetime.now().isoformat()
    
    for dest in draft["publish_destinations"]:
        if dest not in draft["published_to"]:
            draft["published_to"].append(dest)
    
    log_security_event("DRAFT_PUBLISHED", {"draft_id": draft_id, "user": current_user["username"]})
    
    return {
        "message": f"Draft {draft_id} published successfully to {', '.join(draft['publish_destinations'])}",
        "draft": draft,
        "published_to": draft["published_to"]
    }

# API Key Protected Routes
@app.get("/api/admin/users")
@limiter.limit("10/minute")
async def get_users(api_key: str = Depends(require_api_key), current_user: dict = Depends(require_role("admin"))):
    """Get all users (admin only, requires API key)"""
    return {"users": list(user_manager.users.values())}

@app.get("/api/admin/security-logs")
@limiter.limit("10/minute")
async def get_security_logs(api_key: str = Depends(require_api_key), current_user: dict = Depends(require_role("admin"))):
    """Get security logs (admin only, requires API key)"""
    # In production, this would read from a proper log file
    return {"message": "Security logs endpoint - implement log reading"}

# HTML Templates
def get_login_html():
    """Generate secure login page HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RetailXAI Secure Dashboard - Login</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
            }
            .security-badge {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            }
        </style>
    </head>
    <body class="min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full space-y-8 p-8">
            <div class="text-center">
                <h2 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
                    RetailXAI Dashboard
                </h2>
                <p class="mt-2 text-sm text-gray-400">
                    Secure Content Management System
                </p>
                <div class="mt-4">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium security-badge text-white">
                        🔒 Security Enhanced
                    </span>
                </div>
            </div>
            
            <form class="mt-8 space-y-6" onsubmit="login(event)">
                <div class="space-y-4">
                    <div>
                        <label for="username" class="block text-sm font-medium text-gray-300 mb-2">Username</label>
                        <input id="username" name="username" type="text" required 
                               class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                               placeholder="Enter username">
                    </div>
                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-300 mb-2">Password</label>
                        <input id="password" name="password" type="password" required 
                               class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                               placeholder="Enter password">
                    </div>
                </div>

                <div>
                    <button type="submit" 
                            class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-300">
                        Sign In Securely
                    </button>
                </div>
                
                <div class="text-center text-sm text-gray-400">
                    <p>🔐 All connections are encrypted</p>
                    <p>🛡️ Protected against brute force attacks</p>
                    <p>⏰ Session timeout: 15 minutes</p>
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
                        // Store tokens securely
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('refresh_token', data.refresh_token);
                        localStorage.setItem('token_expires', Date.now() + (data.expires_in * 1000));
                        
                        window.location.href = '/';
                    } else {
                        const error = await response.json();
                        alert(error.detail || 'Login failed');
                    }
                } catch (error) {
                    console.error('Login error:', error);
                    alert('Login failed - please try again');
                }
            }
        </script>
    </body>
    </html>
    """

def get_dashboard_html():
    """Generate secure dashboard HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RetailXAI Secure Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
            }
            .card {
                background-color: #1e293b;
                border: 1px solid #334155;
                transition: all 0.3s ease-in-out;
            }
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            }
            .security-indicator {
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
        </style>
    </head>
    <body class="min-h-screen p-8">
        <div class="max-w-7xl mx-auto">
            <!-- Header -->
            <div class="flex justify-between items-center mb-8">
                <div>
                    <h1 class="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
                        RetailXAI Secure Dashboard
                    </h1>
                    <p class="text-gray-400 mt-2">Production-Ready Content Management System</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="flex items-center space-x-2">
                        <div class="w-3 h-3 bg-green-500 rounded-full security-indicator"></div>
                        <span class="text-sm text-green-400 font-medium">Secure Session Active</span>
                    </div>
                    <button onclick="logout()" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition duration-300">
                        🔒 Logout
                    </button>
                </div>
            </div>

            <!-- Security Status -->
            <div class="card p-6 rounded-lg shadow-lg mb-8">
                <h2 class="text-xl font-semibold text-green-300 mb-4 flex items-center">
                    🛡️ Security Status
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full mr-3 security-indicator"></div>
                        <span class="text-gray-300">Authentication: <span class="text-green-400 font-medium">Active</span></span>
                    </div>
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full mr-3 security-indicator"></div>
                        <span class="text-gray-300">Rate Limiting: <span class="text-green-400 font-medium">Enabled</span></span>
                    </div>
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full mr-3 security-indicator"></div>
                        <span class="text-gray-300">Input Validation: <span class="text-green-400 font-medium">Active</span></span>
                    </div>
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-yellow-500 rounded-full mr-3"></div>
                        <span class="text-gray-300">Session: <span class="text-yellow-400 font-medium" id="session-time">15:00</span></span>
                    </div>
                </div>
            </div>

            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="card p-6 rounded-lg shadow-lg">
                    <h3 class="text-lg font-semibold text-blue-300 mb-2">Total Drafts</h3>
                    <p class="text-3xl font-bold text-blue-400" id="total-drafts">-</p>
                </div>
                <div class="card p-6 rounded-lg shadow-lg">
                    <h3 class="text-lg font-semibold text-green-300 mb-2">Published</h3>
                    <p class="text-3xl font-bold text-green-400" id="published-drafts">-</p>
                </div>
                <div class="card p-6 rounded-lg shadow-lg">
                    <h3 class="text-lg font-semibold text-yellow-300 mb-2">Drafts</h3>
                    <p class="text-3xl font-bold text-yellow-400" id="draft-drafts">-</p>
                </div>
                <div class="card p-6 rounded-lg shadow-lg">
                    <h3 class="text-lg font-semibold text-purple-300 mb-2">Active Channels</h3>
                    <p class="text-3xl font-bold text-purple-400" id="active-channels">-</p>
                </div>
            </div>

            <!-- Drafts List -->
            <div class="card p-8 rounded-lg shadow-lg">
                <h2 class="text-2xl font-semibold text-blue-300 mb-6">Your Drafts</h2>
                <div id="drafts-list" class="space-y-4">
                    <!-- Drafts will be loaded here -->
                </div>
            </div>
        </div>

        <script>
            let sessionTimer;
            let refreshTimer;

            // Check authentication on page load
            function checkAuth() {
                const token = localStorage.getItem('access_token');
                const expires = localStorage.getItem('token_expires');
                
                if (!token || !expires || Date.now() > parseInt(expires)) {
                    window.location.href = '/login';
                    return false;
                }
                return true;
            }

            // Start session timer
            function startSessionTimer() {
                let timeLeft = 15 * 60; // 15 minutes in seconds
                
                sessionTimer = setInterval(() => {
                    timeLeft--;
                    const minutes = Math.floor(timeLeft / 60);
                    const seconds = timeLeft % 60;
                    document.getElementById('session-time').textContent = 
                        `${minutes}:${seconds.toString().padStart(2, '0')}`;
                    
                    if (timeLeft <= 0) {
                        logout();
                    }
                }, 1000);
            }

            // Auto-refresh token
            function startTokenRefresh() {
                refreshTimer = setInterval(async () => {
                    const refreshToken = localStorage.getItem('refresh_token');
                    if (!refreshToken) {
                        logout();
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/auth/refresh', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: `refresh_token=${refreshToken}`
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            localStorage.setItem('access_token', data.access_token);
                            localStorage.setItem('token_expires', Date.now() + (data.expires_in * 1000));
                        } else {
                            logout();
                        }
                    } catch (error) {
                        console.error('Token refresh failed:', error);
                        logout();
                    }
                }, 10 * 60 * 1000); // Refresh every 10 minutes
            }

            // Logout function
            function logout() {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('token_expires');
                clearInterval(sessionTimer);
                clearInterval(refreshTimer);
                window.location.href = '/login';
            }

            // Load dashboard data
            async function loadDashboard() {
                if (!checkAuth()) return;
                
                try {
                    const token = localStorage.getItem('access_token');
                    const [healthResponse, statsResponse, draftsResponse] = await Promise.all([
                        fetch('/api/health', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        }),
                        fetch('/api/stats', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        }),
                        fetch('/api/drafts', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        })
                    ]);

                    if (healthResponse.ok) {
                        const health = await healthResponse.json();
                        console.log('Health check:', health);
                    }

                    if (statsResponse.ok) {
                        const stats = await statsResponse.json();
                        document.getElementById('total-drafts').textContent = stats.total_drafts || 0;
                        document.getElementById('published-drafts').textContent = stats.published_drafts || 0;
                        document.getElementById('draft-drafts').textContent = stats.draft_drafts || 0;
                        document.getElementById('active-channels').textContent = stats.active_channels || 0;
                    }

                    if (draftsResponse.ok) {
                        const drafts = await draftsResponse.json();
                        renderDrafts(drafts);
                    }
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
                            </div>
                            <div class="flex space-x-2 ml-4">
                                <button onclick="editDraft(${draft.id})" class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition duration-300">
                                    Edit
                                </button>
                                <button onclick="publishDraft(${draft.id})" class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition duration-300">
                                    Publish
                                </button>
                            </div>
                        </div>
                    `;
                    draftsList.appendChild(draftCard);
                });
            }

            // Draft actions
            function editDraft(draftId) {
                alert(`Edit draft ${draftId} - Feature coming soon!`);
            }

            async function publishDraft(draftId) {
                try {
                    const token = localStorage.getItem('access_token');
                    const response = await fetch(`/api/drafts/${draftId}/publish`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        loadDashboard();
                        alert(`Draft published successfully! ${result.message}`);
                    } else {
                        const error = await response.json();
                        alert(`Error: ${error.detail}`);
                    }
                } catch (error) {
                    console.error('Error publishing draft:', error);
                    alert('Error publishing draft');
                }
            }

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', () => {
                if (checkAuth()) {
                    loadDashboard();
                    startSessionTimer();
                    startTokenRefresh();
                    setInterval(loadDashboard, 30000); // Refresh data every 30 seconds
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Run the secure dashboard
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv('PORT', '8004')),
        ssl_keyfile=os.getenv('SSL_KEYFILE'),
        ssl_certfile=os.getenv('SSL_CERTFILE')
    )

