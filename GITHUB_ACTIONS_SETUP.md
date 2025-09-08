# 🚀 GitHub Actions Setup Guide

This guide will help you set up automated deployment with GitHub Actions.

## 📋 Required Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

### **Server Connection Secrets**
- `SERVER_HOST`: `143.198.14.56`
- `SERVER_USER`: `root`
- `SERVER_SSH_KEY`: Your private SSH key for server access

### **API Keys (Optional)**
- `CLAUDE_API_KEY`: Your Anthropic Claude API key
- `YOUTUBE_API_KEY`: Your YouTube Data API key
- `NEWS_API_KEY`: Your News API key (optional)
- `LINKEDIN_API_KEY`: Your LinkedIn API key (optional)
- `REDDIT_CLIENT_ID`: Your Reddit API client ID (optional)
- `REDDIT_CLIENT_SECRET`: Your Reddit API client secret (optional)
- `SLACK_WEBHOOK_URL`: Your Slack webhook URL (optional)
- `TWITTER_CONSUMER_KEY`: Your Twitter API consumer key (optional)
- `TWITTER_CONSUMER_SECRET`: Your Twitter API consumer secret (optional)
- `TWITTER_ACCESS_TOKEN`: Your Twitter API access token (optional)
- `TWITTER_ACCESS_TOKEN_SECRET`: Your Twitter API access token secret (optional)

### **Monitoring Secrets**
- `ALERT_EMAIL_USER`: Email for alerts (optional)
- `ALERT_EMAIL_PASS`: Email password/app password (optional)
- `ALERT_EMAIL_FROM`: From email address (optional)
- `ALERT_EMAIL_TO`: Alert recipient email (optional)

## 🔑 How to Get SSH Key

1. **Generate SSH key pair** (if you don't have one):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
   ```

2. **Copy the private key**:
   ```bash
   cat ~/.ssh/id_rsa
   ```

3. **Add the public key to your server**:
   ```bash
   ssh-copy-id root@143.198.14.56
   ```

4. **Add the private key to GitHub Secrets** as `SERVER_SSH_KEY`

## 🚀 Deployment Process

Once secrets are configured:

1. **Push to master branch** - triggers automatic deployment
2. **GitHub Actions will**:
   - Run tests
   - Deploy to production server
   - Restart services
   - Verify deployment

## 📊 Monitoring

After deployment, monitor your system:

- **Health endpoint**: `http://143.198.14.56:5000/api/health`
- **Detailed health**: `http://143.198.14.56:5000/api/health/detailed`
- **SLA metrics**: `http://143.198.14.56:5000/api/health/sla`

## 🔧 Manual Deployment

If you need to deploy manually:

```bash
# Connect to server
ssh root@143.198.14.56

# Navigate to project
cd /home/retailxai/precipice

# Pull latest changes
git pull origin master

# Install dependencies
source venv_new/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart retailxai
sudo systemctl restart staging_site

# Check status
sudo systemctl status retailxai
```

## 🚨 Troubleshooting

### Service Not Starting
```bash
# Check logs
journalctl -u retailxai.service -f

# Check configuration
python3 environment_validator.py

# Test manually
python3 main.py
```

### API Quota Issues
```bash
# Check quota usage
python3 -c "from production_monitor import ProductionMonitor; m = ProductionMonitor({}); print(m._check_api_quotas())"
```

### Database Issues
```bash
# Check database connection
python3 -c "from database_manager import DatabaseManager; db = DatabaseManager({'host': 'localhost', 'name': 'retailxai', 'user': 'retailxbt_user', 'password': 'Seattle2311!', 'min_connections': 1, 'max_connections': 5, 'connect_timeout': 10}); print('DB OK' if db.is_healthy() else 'DB FAILED')"
```

## 📈 Performance Monitoring

Monitor these key metrics:

- **Uptime**: Should be > 99.9%
- **Response Time**: Should be < 2 seconds
- **Error Rate**: Should be < 1%
- **Memory Usage**: Should be < 80%
- **Disk Space**: Should be > 15% free

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ All health checks pass
- ✅ API endpoints respond correctly
- ✅ Database connections are healthy
- ✅ Monitoring alerts are configured
- ✅ GitHub Actions deployment works
- ✅ Static site updates automatically

## 📞 Support

If you encounter issues:

1. Check the logs: `journalctl -u retailxai.service -f`
2. Verify configuration: `python3 environment_validator.py`
3. Test endpoints: `curl http://143.198.14.56:5000/api/health`
4. Check GitHub Actions logs in your repository

---

**🎉 Congratulations! Your RetailXAI system is now production-ready with automated deployment!**
