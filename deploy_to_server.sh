#!/bin/bash
# Deploy RetailXAI to production server
# Server: root@143.198.14.56
# Working directory: /home/retailxai/precipice

set -e  # Exit on any error

# Server configuration
SERVER="root@143.198.14.56"
REMOTE_DIR="/home/retailxai/precipice"
DB_USER="retailxbt_user"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "🚀 RetailXAI Production Deployment"
echo "=================================="
echo "Server: $SERVER"
echo "Directory: $REMOTE_DIR"
echo "Database User: $DB_USER"
echo ""

# Step 1: Commit and push changes
print_info "Step 1: Committing and pushing changes to git..."

if [ -z "$(git status --porcelain)" ]; then
    print_warning "No changes to commit. All files are already committed."
else
    git add .
    git commit -m "🚀 Production deployment - server ready

- All production fixes implemented
- Database connection with retry logic
- Health monitoring and circuit breakers
- Environment validation and error handling
- Memory leak prevention and state persistence
- Production deployment scripts

Ready for server deployment at 143.198.14.56"
    print_status "Changes committed to git"
fi

# Push to remote
git push origin main
print_status "Changes pushed to remote repository"

# Step 2: Connect to server and deploy
print_info "Step 2: Deploying to server..."

# Create deployment script for server
cat > server_deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🖥️  Server-side deployment starting..."

# Update system packages
echo "📦 Updating system packages..."
apt update -y

# Install Python and pip if not present
echo "🐍 Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv postgresql-client

# Navigate to working directory
cd /home/retailxai/precipice

# Clone or update repository
if [ -d ".git" ]; then
    echo "📥 Updating existing repository..."
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone https://github.com/your-username/Precipice-1.git .
fi

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config directory
mkdir -p config

# Create .env file with database configuration
echo "⚙️  Creating environment configuration..."
cat > config/.env << 'ENVEOF'
# Database Configuration
DATABASE_URL=postgresql://retailxbt_user@localhost:5432/retailxai

# Required API Keys (you'll need to add these)
CLAUDE_API_KEY=your-claude-api-key-here
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
ENVEOF

# Set proper permissions
chmod 600 config/.env
chown -R retailxai:retailxai /home/retailxai/precipice

echo "✅ Server setup completed!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit config/.env with your actual API keys"
echo "2. Test database connection: python3 -c \"from database_manager import DatabaseManager; print('DB OK')\""
echo "3. Run environment validation: python3 environment_validator.py"
echo "4. Start the application: python3 main.py"
EOF

# Copy deployment script to server
scp server_deploy.sh $SERVER:/tmp/

# Execute deployment on server
print_info "Executing deployment on server..."
ssh $SERVER "chmod +x /tmp/server_deploy.sh && /tmp/server_deploy.sh"

# Clean up local deployment script
rm server_deploy.sh

print_status "Server deployment completed!"

# Step 3: Test deployment
print_info "Step 3: Testing deployment..."

# Test database connection
print_info "Testing database connection..."
ssh $SERVER "cd $REMOTE_DIR && source venv/bin/activate && python3 -c \"
from database_manager import DatabaseManager
import os

# Test database connection
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
\""

# Test environment validation
print_info "Testing environment validation..."
ssh $SERVER "cd $REMOTE_DIR && source venv/bin/activate && python3 environment_validator.py"

# Test health monitoring
print_info "Testing health monitoring..."
ssh $SERVER "cd $REMOTE_DIR && source venv/bin/activate && python3 health_monitor.py"

print_status "Deployment testing completed!"

# Step 4: Create systemd service
print_info "Step 4: Creating systemd service..."

# Create systemd service file
cat > retailxai.service << 'EOF'
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

# Copy service file to server
scp retailxai.service $SERVER:/etc/systemd/system/

# Enable and start service
print_info "Setting up systemd service..."
ssh $SERVER "
systemctl daemon-reload
systemctl enable retailxai
systemctl start retailxai
systemctl status retailxai --no-pager
"

# Clean up local service file
rm retailxai.service

print_status "Systemd service configured and started!"

# Step 5: Final verification
print_info "Step 5: Final verification..."

# Check service status
ssh $SERVER "systemctl status retailxai --no-pager"

# Check logs
print_info "Recent logs:"
ssh $SERVER "journalctl -u retailxai -n 20 --no-pager"

# Check if process is running
ssh $SERVER "ps aux | grep python | grep main.py"

print_status "Deployment completed successfully!"

echo ""
echo "🎉 RETAILXAI IS NOW RUNNING ON YOUR SERVER!"
echo "============================================="
echo ""
echo "📊 Monitoring Commands:"
echo "  - Check status: ssh $SERVER 'systemctl status retailxai'"
echo "  - View logs: ssh $SERVER 'journalctl -u retailxai -f'"
echo "  - Check health: ssh $SERVER 'cd $REMOTE_DIR && source venv/bin/activate && python3 health_monitor.py'"
echo ""
echo "🔧 Configuration:"
echo "  - Edit config: ssh $SERVER 'nano $REMOTE_DIR/config/.env'"
echo "  - Restart service: ssh $SERVER 'systemctl restart retailxai'"
echo ""
echo "📁 Files:"
echo "  - Working directory: $REMOTE_DIR"
echo "  - Logs: /var/log/journal/ (systemd logs)"
echo "  - Application logs: $REMOTE_DIR/logs/"
echo ""
print_warning "Don't forget to add your actual API keys to config/.env!"
