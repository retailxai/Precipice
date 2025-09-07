# 🚀 Git Commit & Server Deployment Guide

This guide will walk you through committing your production fixes to git and deploying to your server.

## 📝 **STEP 1: Commit to Git**

### **1.1 Check Current Status**
```bash
# Check what files have changed
git status

# See the differences
git diff
```

### **1.2 Add All Production Fixes**
```bash
# Add all the new production files
git add environment_validator.py
git add circuit_breaker.py
git add health_monitor.py
git add deploy_production.py
git add PRODUCTION_FIXES.md
git add DEPLOYMENT_GUIDE.md

# Add modified files
git add database_manager.py
git add main.py
git add scheduler.py
git add agent_manager.py
git add claude_processor.py
git add youtube_collector.py
git add config/schedule.yaml

# Add all changes at once (alternative)
git add .
```

### **1.3 Commit with Descriptive Message**
```bash
git commit -m "🚀 Add production-ready fixes and monitoring

- Fix database connection management with retry logic
- Add environment variable validation at startup
- Implement global exception handling
- Add circuit breaker pattern for API calls
- Add comprehensive health monitoring
- Fix memory leaks and add cleanup
- Add state persistence and crash recovery
- Add production deployment tools

Critical fixes:
- Prevents API timeout hangs (30s → milliseconds)
- Prevents database connection leaks
- Prevents memory growth without bounds
- Adds crash recovery and state persistence
- Adds real-time health monitoring"
```

### **1.4 Push to Remote Repository**
```bash
# Push to main branch
git push origin main

# Or if you're on a different branch
git push origin your-branch-name
```

## 🖥️ **STEP 2: Deploy to Server**

### **Option A: Direct Server Deployment (Recommended)**

#### **2.1 Connect to Your Server**
```bash
# SSH into your server
ssh username@your-server-ip

# Or if using a specific key
ssh -i /path/to/your/key.pem username@your-server-ip
```

#### **2.2 Clone/Update Repository on Server**
```bash
# If first time on server
git clone https://github.com/your-username/Precipice-1.git
cd Precipice-1

# If already exists, update it
git pull origin main
```

#### **2.3 Set Up Environment**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install psutil
```

#### **2.4 Configure Environment Variables**
```bash
# Create .env file
mkdir -p config
nano config/.env
```

**Add your environment variables:**
```bash
# Required
CLAUDE_API_KEY=sk-ant-your-key-here
YOUTUBE_API_KEY=your-youtube-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/retailxai

# Optional (for full functionality)
NEWS_API_KEY=your-news-api-key
LINKEDIN_API_KEY=your-linkedin-key
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-secret
SLACK_WEBHOOK_URL=your-slack-webhook
TWITTER_CONSUMER_KEY=your-twitter-key
TWITTER_CONSUMER_SECRET=your-twitter-secret
TWITTER_ACCESS_TOKEN=your-twitter-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-token-secret

# System settings
LOG_LEVEL=INFO
MAX_WORKERS=4
DATABASE_POOL_SIZE=5
API_TIMEOUT=30
```

#### **2.5 Set Up Database**
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE retailxai;
CREATE USER retailxai WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE retailxai TO retailxai;
\q
```

#### **2.6 Run Production Deployment Script**
```bash
# Make deployment script executable
chmod +x deploy_production.py

# Run production deployment
python deploy_production.py
```

#### **2.7 Set Up Systemd Service (Recommended)**
```bash
# Copy service file
sudo cp retailxai.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable retailxai
sudo systemctl start retailxai

# Check status
sudo systemctl status retailxai

# View logs
sudo journalctl -u retailxai -f
```

### **Option B: Docker Deployment**

#### **2.1 Set Up Docker on Server**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### **2.2 Deploy with Docker**
```bash
# Create .env file for Docker
cp config/.env.example .env
nano .env  # Add your environment variables

# Run deployment script to generate Docker files
python deploy_production.py

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f retailxai
```

## 🔧 **STEP 3: Verify Deployment**

### **3.1 Check System Health**
```bash
# Run health checks
python health_monitor.py

# Check environment validation
python environment_validator.py

# Check system status
python -c "from agent_manager import AgentManager; am = AgentManager(); print(am.get_system_status())"
```

### **3.2 Monitor Logs**
```bash
# View application logs
tail -f logs/retailxai.log

# View systemd logs (if using systemd)
sudo journalctl -u retailxai -f

# View Docker logs (if using Docker)
docker-compose logs -f retailxai
```

### **3.3 Test Functionality**
```bash
# Test the main application
python main.py

# In another terminal, check if it's running
ps aux | grep python
```

## 🛠️ **STEP 4: Production Maintenance**

### **4.1 Regular Monitoring**
```bash
# Check health status
curl http://localhost:8000/health  # If you add a health endpoint

# Check system resources
htop
df -h
free -h
```

### **4.2 Log Rotation**
```bash
# Set up log rotation
sudo nano /etc/logrotate.d/retailxai
```

**Add this content:**
```
/path/to/Precipice-1/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 retailxai retailxai
    postrotate
        systemctl reload retailxai
    endscript
}
```

### **4.3 Backup Strategy**
```bash
# Create backup script
nano backup_retailxai.sh
```

**Add this content:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/retailxai"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump retailxai > $BACKUP_DIR/database_$DATE.sql

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Make executable and schedule
chmod +x backup_retailxai.sh
crontab -e

# Add this line for daily backups at 3 AM
0 3 * * * /path/to/backup_retailxai.sh
```

## 🚨 **TROUBLESHOOTING**

### **Common Issues:**

#### **1. Environment Variables Not Found**
```bash
# Check if .env file exists and has correct values
cat config/.env
python environment_validator.py
```

#### **2. Database Connection Failed**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U retailxai -d retailxai
```

#### **3. Permission Denied**
```bash
# Fix file permissions
chmod +x main.py
chmod +x deploy_production.py
chmod 600 config/.env
```

#### **4. Service Won't Start**
```bash
# Check service status
sudo systemctl status retailxai

# Check logs
sudo journalctl -u retailxai -n 50

# Restart service
sudo systemctl restart retailxai
```

## 📊 **MONITORING COMMANDS**

```bash
# Check system health
python health_monitor.py

# Check circuit breaker status
python -c "from circuit_breaker import circuit_breaker_manager; print(circuit_breaker_manager.get_all_states())"

# Check memory usage
python -c "from agent_manager import AgentManager; am = AgentManager(); print(am.get_memory_usage())"

# Check database health
python -c "from database_manager import DatabaseManager; db = DatabaseManager({'host': 'localhost', 'name': 'retailxai', 'user': 'retailxai', 'password': 'your-password', 'min_connections': 1, 'max_connections': 5, 'connect_timeout': 10}); print(db.is_healthy())"
```

## 🎯 **SUCCESS INDICATORS**

Your deployment is successful when:
- ✅ `python environment_validator.py` shows no errors
- ✅ `python health_monitor.py` shows all checks passing
- ✅ Service starts without errors
- ✅ Logs show "RetailXAI Scheduler started"
- ✅ Health checks run daily at midnight
- ✅ Memory cleanup runs daily at 2 AM

---

**Your RetailXAI system is now production-ready and deployed!** 🚀

**Next Steps:**
1. Monitor the logs for the first few days
2. Set up alerting for health check failures
3. Configure backup strategies
4. Scale as needed based on usage
