#!/bin/bash

# RetailXAI Dashboard Deployment Script
# This script deploys the dashboard to the production server

echo "🚀 Deploying RetailXAI Dashboard..."

# Check if we're on the production server
if [ ! -f "/home/retailxai/precipice/main.py" ]; then
    echo "❌ Error: This script must be run on the production server"
    exit 1
fi

# Navigate to the project directory
cd /home/retailxai/precipice

# Install web server dependencies
echo "📦 Installing web server dependencies..."
/home/retailxai/precipice/venv_new/bin/pip install flask flask-cors tweepy python-dotenv requests gunicorn

# Create systemd service for the web server
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/retailxai-dashboard.service > /dev/null << EOF
[Unit]
Description=RetailXAI Dashboard Web Server
After=network.target retailxai.service
Wants=retailxai.service

[Service]
Type=simple
User=retailxai
Group=retailxai
WorkingDirectory=/home/retailxai/precipice
Environment=PYTHONPATH=/home/retailxai/precipice
ExecStart=/home/retailxai/precipice/venv_new/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 web_server:app
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=retailxai-dashboard

# Resource limits
LimitNOFILE=65536
LimitNPROC=32768

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=false
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the service
echo "🔄 Starting dashboard service..."
sudo systemctl daemon-reload
sudo systemctl enable retailxai-dashboard.service
sudo systemctl start retailxai-dashboard.service

# Check service status
echo "📊 Checking service status..."
sudo systemctl status retailxai-dashboard.service --no-pager

# Create nginx configuration (if nginx is installed)
if command -v nginx &> /dev/null; then
    echo "🌐 Creating nginx configuration..."
    sudo tee /etc/nginx/sites-available/retailxai-dashboard > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/retailxai-dashboard /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    echo "✅ Nginx configuration created and reloaded"
fi

echo "🎉 Dashboard deployment complete!"
echo "📱 Dashboard should be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo "📊 Check status with: sudo systemctl status retailxai-dashboard"
echo "📝 View logs with: journalctl -u retailxai-dashboard -f"
