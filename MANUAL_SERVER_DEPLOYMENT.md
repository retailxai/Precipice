# 🚀 Manual Server Deployment Guide

**Server:** `root@143.198.14.56`  
**Directory:** `/home/retailxai/precipice`  
**Database User:** `retailxbt_user`

## 📋 **QUICK DEPLOYMENT (Automated)**

```bash
# Run the automated deployment script
./deploy_to_server.sh
```

## 🔧 **MANUAL DEPLOYMENT (Step by Step)**

### **Step 1: Prepare Local Environment**

```bash
# 1. Commit and push your changes
git add .
git commit -m "Production deployment ready"
git push origin main

# 2. Test locally first
python3 environment_validator.py
python3 health_monitor.py
```

### **Step 2: Connect to Server**

```bash
# SSH into your server
ssh root@143.198.14.56

# Navigate to working directory
cd /home/retailxai/precipice
```

### **Step 3: Clone/Update Repository**

```bash
# If first time, clone the repository
git clone https://github.com/your-username/Precipice-1.git .

# If already exists, update it
git pull origin main
```

### **Step 4: Install Dependencies**

```bash
# Update system packages
apt update -y

# Install Python and PostgreSQL client
apt install -y python3 python3-pip python3-venv postgresql-client

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### **Step 5: Configure Environment**

```bash
# Create config directory
mkdir -p config

# Create .env file
nano config/.env
```

**Add this content to `config/.env`:**
```bash
# Database Configuration
DATABASE_URL=postgresql://retailxbt_user@localhost:5432/retailxai

# Required API Keys (REPLACE WITH YOUR ACTUAL KEYS)
CLAUDE_API_KEY=sk-ant-your-claude-key-here
YOUTUBE_API_KEY=your-youtube-api-key-here

# Optional API Keys
NEWS_API_KEY=your-news-api-key
LINKEDIN_API_KEY=your-linkedin-api-key
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
SLACK_WEBHOOK_URL=your-slack-webhook-url
TWITTER_CONSUMER_KEY=your-twitter-consumer-key
TWITTER_CONSUMER_SECRET=your-twitter-consumer-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret

# System Configuration
LOG_LEVEL=INFO
MAX_WORKERS=4
DATABASE_POOL_SIZE=5
API_TIMEOUT=30
```

### **Step 6: Test Database Connection**

```bash
# Test database connection
python3 -c "
from database_manager import DatabaseManager

db_config = {
    'host': 'localhost',
    'name': 'retailxai',
    'user': 'retailxbt_user',
    'password': '',  # Add password if needed
    'min_connections': 1,
    'max_connections': 5,
    'connect_timeout': 10
}

try:
    db = DatabaseManager(db_config)
    is_healthy = db.is_healthy()
    if is_healthy:
        print('✅ Database connection successful!')
    else:
        print('❌ Database connection failed')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

### **Step 7: Test Environment and Health**

```bash
# Test environment validation
python3 environment_validator.py

# Test health monitoring
python3 health_monitor.py

# Test circuit breakers
python3 -c "
from circuit_breaker import get_circuit_breaker
youtube_cb = get_circuit_breaker('youtube')
print(f'YouTube Circuit Breaker: {youtube_cb.state}')
"
```

### **Step 8: Create Systemd Service**

```bash
# Create service file
cat > /etc/systemd/system/retailxai.service << 'EOF'
[Unit]
Description=RetailXAI Data Collection and Processing System
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=retailxai
Group=retailxai
WorkingDirectory=/home/retailxai/precipice
Environment=PATH=/home/retailxai/precipice/venv/bin
ExecStart=/home/retailxai/precipice/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/retailxai/precipice

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
systemctl daemon-reload
systemctl enable retailxai
systemctl start retailxai
```

### **Step 9: Verify Deployment**

```bash
# Check service status
systemctl status retailxai

# Check if process is running
ps aux | grep python | grep main.py

# View recent logs
journalctl -u retailxai -n 20

# Follow logs in real-time
journalctl -u retailxai -f
```

## 🔍 **TROUBLESHOOTING**

### **Database Connection Issues**

```bash
# Check if PostgreSQL is running
systemctl status postgresql

# Check database exists
sudo -u postgres psql -c "\l" | grep retailxai

# Test connection manually
psql -h localhost -U retailxbt_user -d retailxai
```

### **Service Issues**

```bash
# Check service status
systemctl status retailxai

# Restart service
systemctl restart retailxai

# Check logs for errors
journalctl -u retailxai -n 50

# Check if port is in use
netstat -tlnp | grep :5432
```

### **Permission Issues**

```bash
# Fix ownership
chown -R retailxai:retailxai /home/retailxai/precipice

# Fix permissions
chmod 600 config/.env
chmod +x main.py
```

## 📊 **MONITORING COMMANDS**

```bash
# Service status
systemctl status retailxai

# Real-time logs
journalctl -u retailxai -f

# Health check
cd /home/retailxai/precipice && source venv/bin/activate && python3 health_monitor.py

# Environment validation
cd /home/retailxai/precipice && source venv/bin/activate && python3 environment_validator.py

# Check database health
cd /home/retailxai/precipice && source venv/bin/activate && python3 -c "
from database_manager import DatabaseManager
import os
db = DatabaseManager({'host': 'localhost', 'name': 'retailxai', 'user': 'retailxbt_user', 'password': '', 'min_connections': 1, 'max_connections': 5, 'connect_timeout': 10})
print('Database healthy:', db.is_healthy())
"
```

## 🎯 **SUCCESS INDICATORS**

Your deployment is successful when:
- ✅ `systemctl status retailxai` shows "active (running)"
- ✅ `journalctl -u retailxai` shows "RetailXAI Scheduler started"
- ✅ `python3 health_monitor.py` shows all checks passing
- ✅ `python3 environment_validator.py` shows no critical errors
- ✅ Database connection test succeeds

## 🚀 **NEXT STEPS**

1. **Add your API keys** to `config/.env`
2. **Monitor the logs** for the first few hours
3. **Set up log rotation** for long-term operation
4. **Configure backup** for your database
5. **Set up monitoring alerts** for health check failures

---

**Your RetailXAI system will be running on your server!** 🎉
