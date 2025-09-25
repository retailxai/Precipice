#!/bin/bash

# RetailXAI Secure Dashboard Deployment Script
# This script deploys the secure dashboard with proper security configurations

set -e  # Exit on any error

echo "🔒 RetailXAI Secure Dashboard Deployment"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi
print_success "Python version check passed: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install/update dependencies
print_status "Installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn slowapi bcrypt pyjwt httpx python-multipart python-dotenv
print_success "Dependencies installed"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p drafts
mkdir -p ssl
print_success "Directories created"

# Check if environment file exists
if [ ! -f ".env" ]; then
    print_warning "Environment file not found. Creating from template..."
    if [ -f "secure_dashboard.env" ]; then
        cp secure_dashboard.env .env
        print_warning "Please edit .env file with your production values before continuing"
        print_warning "Especially update SECRET_KEY, REFRESH_SECRET_KEY, and ADMIN_PASSWORD"
        read -p "Press Enter after updating .env file..."
    else
        print_error "secure_dashboard.env template not found"
        exit 1
    fi
fi

# Generate secure keys if not set
print_status "Checking security configuration..."
if grep -q "your-super-secure-secret-key" .env; then
    print_warning "Default security keys detected. Generating new ones..."
    
    # Generate new secret keys
    new_secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    new_refresh_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env file
    sed -i.bak "s/your-super-secure-secret-key-at-least-32-characters-long/$new_secret_key/" .env
    sed -i.bak "s/your-super-secure-refresh-secret-key-at-least-32-characters-long/$new_refresh_key/" .env
    
    print_success "New security keys generated and updated"
fi

# Check SSL configuration
print_status "Checking SSL configuration..."
if [ ! -f "ssl/private.key" ] || [ ! -f "ssl/certificate.crt" ]; then
    print_warning "SSL certificates not found. Generating self-signed certificates for development..."
    
    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:4096 -keyout ssl/private.key -out ssl/certificate.crt -days 365 -nodes \
        -subj "/C=US/ST=State/L=City/O=RetailXAI/CN=localhost"
    
    # Update .env file with SSL paths
    if ! grep -q "SSL_KEYFILE" .env; then
        echo "SSL_KEYFILE=ssl/private.key" >> .env
        echo "SSL_CERTFILE=ssl/certificate.crt" >> .env
    fi
    
    print_warning "Self-signed certificates generated. For production, use proper SSL certificates"
else
    print_success "SSL certificates found"
fi

# Set proper permissions
print_status "Setting secure file permissions..."
chmod 600 .env
chmod 600 ssl/private.key
chmod 644 ssl/certificate.crt
chmod 755 logs
print_success "File permissions set"

# Create systemd service file
print_status "Creating systemd service..."
cat > retailxai-secure.service << EOF
[Unit]
Description=RetailXAI Secure Dashboard
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python secure_dashboard.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$(pwd)/logs $(pwd)/drafts

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service file created"

# Create startup script
print_status "Creating startup script..."
cat > start_secure_dashboard.sh << 'EOF'
#!/bin/bash
# RetailXAI Secure Dashboard Startup Script

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Start the secure dashboard
python secure_dashboard.py
EOF

chmod +x start_secure_dashboard.sh
print_success "Startup script created"

# Create health check script
print_status "Creating health check script..."
cat > health_check_secure.sh << 'EOF'
#!/bin/bash
# Health check for RetailXAI Secure Dashboard

DASHBOARD_URL="http://localhost:8004"
LOGIN_URL="$DASHBOARD_URL/login"

# Check if dashboard is running
if curl -s -f "$DASHBOARD_URL" > /dev/null; then
    echo "✅ Dashboard is running"
    exit 0
else
    echo "❌ Dashboard is not responding"
    exit 1
fi
EOF

chmod +x health_check_secure.sh
print_success "Health check script created"

# Test the installation
print_status "Testing installation..."
if python3 -c "import fastapi, uvicorn, slowapi, bcrypt, jwt" 2>/dev/null; then
    print_success "All required packages are installed"
else
    print_error "Some packages are missing. Please check the installation"
    exit 1
fi

# Display deployment summary
echo ""
echo "🎉 Secure Dashboard Deployment Complete!"
echo "======================================"
echo ""
print_success "Dashboard files created:"
echo "  - secure_dashboard.py (main application)"
echo "  - .env (environment configuration)"
echo "  - retailxai-secure.service (systemd service)"
echo "  - start_secure_dashboard.sh (startup script)"
echo "  - health_check_secure.sh (health check)"
echo ""

print_status "Next steps:"
echo "1. Review and update .env file with your production values"
echo "2. For production, replace self-signed SSL certificates with real ones"
echo "3. Configure firewall to allow port 8004 (or your chosen port)"
echo "4. Set up monitoring and log rotation"
echo "5. Test the deployment:"
echo "   ./start_secure_dashboard.sh"
echo ""

print_status "Default credentials:"
echo "  Username: admin"
echo "  Password: SecureAdmin123! (change this in .env)"
echo ""

print_status "Access URLs:"
echo "  Dashboard: http://localhost:8004"
echo "  Login: http://localhost:8004/login"
echo ""

print_warning "Security reminders:"
echo "  - Change default admin password immediately"
echo "  - Use strong, unique API keys"
echo "  - Enable HTTPS in production"
echo "  - Monitor security logs regularly"
echo "  - Keep dependencies updated"
echo ""

print_success "Deployment completed successfully! 🔒"

