# RetailXAI Dashboard Security Guide

## Overview

This guide covers the comprehensive security measures implemented in the RetailXAI Secure Dashboard to protect against common web application vulnerabilities and ensure production-ready security.

## Security Features Implemented

### 1. Authentication & Authorization

#### JWT-Based Authentication
- **Access Tokens**: Short-lived (15 minutes) for API access
- **Refresh Tokens**: Long-lived (7 days) for token renewal
- **Secure Token Storage**: Tokens stored in localStorage with automatic cleanup
- **Token Validation**: Server-side validation on every request

#### User Management
- **Password Hashing**: bcrypt with salt for secure password storage
- **Role-Based Access Control**: Admin, Editor, and Viewer roles
- **Account Lockout**: Automatic lockout after 5 failed login attempts
- **Session Management**: Automatic session timeout and refresh

#### Multi-Factor Security
- **API Key Authentication**: Required for sensitive admin endpoints
- **Rate Limiting**: Prevents brute force attacks
- **Input Validation**: Comprehensive validation on all inputs

### 2. Network Security

#### CORS Configuration
```python
# Restrictive CORS policy
allow_origins=["http://localhost:3000", "https://retailxai.github.io"]
allow_credentials=True
allow_methods=["GET", "POST", "PUT", "DELETE"]
```

#### Security Headers
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-XSS-Protection**: Enables XSS filtering
- **Strict-Transport-Security**: Enforces HTTPS
- **Content-Security-Policy**: Restricts resource loading

#### Trusted Host Middleware
- Validates incoming requests against allowed hosts
- Prevents Host header injection attacks

### 3. Input Validation & Sanitization

#### Pydantic Models
```python
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v.lower()
```

#### Content Validation
- **Title**: 1-200 characters, required
- **Summary**: Max 500 characters
- **Body**: Max 10,000 characters
- **Tags**: Max 10 tags, alphanumeric with hyphens/underscores only

### 4. Rate Limiting & DDoS Protection

#### Endpoint-Specific Limits
- **Login**: 5 attempts per minute
- **Token Refresh**: 10 attempts per minute
- **API Calls**: 30 calls per minute
- **Admin Operations**: 10 calls per minute

#### Implementation
```python
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    # Login logic
```

### 5. Security Logging & Monitoring

#### Security Events Logged
- **Authentication Events**: Login attempts, successes, failures
- **Authorization Events**: Access denied, role violations
- **Data Events**: Draft creation, updates, publishing
- **System Events**: Token refresh, logout, account lockouts

#### Log Format
```json
{
    "timestamp": "2025-01-15T10:30:00Z",
    "event_type": "FAILED_LOGIN",
    "user": "admin",
    "ip": "192.168.1.100",
    "details": {"username": "admin"}
}
```

### 6. API Security

#### API Key Protection
- Required for sensitive admin endpoints
- Configurable via environment variables
- Header-based authentication

#### Request Signing
- All API requests require valid JWT tokens
- Automatic token refresh mechanism
- Secure token storage and transmission

## Deployment Security

### 1. Environment Configuration

#### Required Environment Variables
```bash
# Security Keys (Generate new ones!)
SECRET_KEY=your-super-secure-secret-key-at-least-32-characters-long
REFRESH_SECRET_KEY=your-super-secure-refresh-secret-key-at-least-32-characters-long

# Security Settings
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Host Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com
```

### 2. SSL/TLS Configuration

#### HTTPS Enforcement
```python
# Enable HTTPS in production
uvicorn.run(
    app, 
    host="0.0.0.0", 
    port=443,
    ssl_keyfile="/path/to/private.key",
    ssl_certfile="/path/to/certificate.crt"
)
```

#### Security Headers
- **Strict-Transport-Security**: Enforces HTTPS
- **Secure Cookies**: HttpOnly and Secure flags
- **SameSite**: CSRF protection

### 3. Database Security

#### Connection Security
- Use encrypted connections (SSL/TLS)
- Implement connection pooling
- Regular security updates

#### Data Protection
- Encrypt sensitive data at rest
- Use parameterized queries
- Implement data retention policies

## Security Best Practices

### 1. Password Security
- **Minimum Length**: 8 characters
- **Complexity**: Mix of letters, numbers, symbols
- **Hashing**: bcrypt with salt
- **Rotation**: Regular password changes

### 2. Session Management
- **Short Sessions**: 15-minute access tokens
- **Automatic Refresh**: Seamless user experience
- **Secure Logout**: Complete token invalidation
- **Concurrent Sessions**: Monitor and limit

### 3. Error Handling
- **Generic Messages**: Don't reveal system details
- **Logging**: Detailed logs for debugging
- **Rate Limiting**: Prevent information disclosure

### 4. Monitoring & Alerting
- **Failed Logins**: Alert on suspicious activity
- **Rate Limiting**: Monitor for DDoS attempts
- **Token Usage**: Track authentication patterns
- **System Health**: Monitor security metrics

## Security Checklist

### Pre-Deployment
- [ ] Generate strong SECRET_KEY and REFRESH_SECRET_KEY
- [ ] Configure ALLOWED_HOSTS and ALLOWED_ORIGINS
- [ ] Set up SSL/TLS certificates
- [ ] Configure API keys for admin access
- [ ] Set strong admin password
- [ ] Enable security logging
- [ ] Configure rate limiting
- [ ] Test authentication flows
- [ ] Verify CORS configuration
- [ ] Test input validation

### Post-Deployment
- [ ] Monitor security logs
- [ ] Set up alerting for failed logins
- [ ] Regular security updates
- [ ] Monitor rate limiting effectiveness
- [ ] Review access patterns
- [ ] Test backup and recovery
- [ ] Regular security audits
- [ ] Update dependencies
- [ ] Monitor SSL certificate expiration

## Common Security Issues & Solutions

### 1. Brute Force Attacks
**Problem**: Automated login attempts
**Solution**: Rate limiting + account lockout

### 2. Session Hijacking
**Problem**: Stolen session tokens
**Solution**: Short-lived tokens + secure storage

### 3. CSRF Attacks
**Problem**: Cross-site request forgery
**Solution**: SameSite cookies + CSRF tokens

### 4. XSS Attacks
**Problem**: Cross-site scripting
**Solution**: Input validation + CSP headers

### 5. SQL Injection
**Problem**: Malicious SQL queries
**Solution**: Parameterized queries + input validation

## Incident Response

### 1. Security Breach Detection
- Monitor failed login attempts
- Watch for unusual access patterns
- Check for suspicious API usage
- Review security logs regularly

### 2. Immediate Response
- Lock compromised accounts
- Revoke all active tokens
- Check for data exfiltration
- Document the incident

### 3. Recovery Steps
- Reset all passwords
- Generate new API keys
- Update security configurations
- Review and strengthen controls

## Contact & Support

For security-related issues or questions:
- **Email**: security@retailxai.com
- **Documentation**: This guide
- **Logs**: Check `logs/security.log`

## Updates

This security guide is regularly updated. Last updated: January 15, 2025

---

**Remember**: Security is an ongoing process, not a one-time setup. Regular reviews and updates are essential for maintaining a secure system.

