#!/bin/bash
# Quick deployment script for RetailXAI production fixes

set -e  # Exit on any error

echo "🚀 RetailXAI Production Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository. Please run this from the project root."
    exit 1
fi

echo "📝 Step 1: Committing production fixes to git..."

# Check git status
if [ -z "$(git status --porcelain)" ]; then
    print_warning "No changes to commit. All files are already committed."
else
    # Add all files
    git add .
    
    # Commit with descriptive message
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
    
    print_status "Changes committed to git"
fi

# Ask if user wants to push to remote
read -p "📤 Push to remote repository? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    print_status "Changes pushed to remote repository"
else
    print_warning "Skipping push to remote repository"
fi

echo ""
echo "🖥️  Step 2: Server deployment options"
echo "====================================="

echo "Choose your deployment method:"
echo "1) Direct server deployment (SSH)"
echo "2) Docker deployment"
echo "3) Manual deployment instructions"
echo "4) Skip deployment"

read -p "Enter your choice (1-4): " -n 1 -r
echo

case $REPLY in
    1)
        echo ""
        echo "🔧 Direct Server Deployment"
        echo "=========================="
        echo ""
        echo "1. SSH into your server:"
        echo "   ssh username@your-server-ip"
        echo ""
        echo "2. Clone/update the repository:"
        echo "   git clone https://github.com/your-username/Precipice-1.git"
        echo "   # OR if already exists:"
        echo "   cd Precipice-1 && git pull origin main"
        echo ""
        echo "3. Set up the environment:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r requirements.txt"
        echo "   pip install psutil"
        echo ""
        echo "4. Configure environment variables:"
        echo "   mkdir -p config"
        echo "   nano config/.env"
        echo "   # Add your API keys and database URL"
        echo ""
        echo "5. Run production deployment:"
        echo "   python deploy_production.py"
        echo ""
        echo "6. Set up systemd service:"
        echo "   sudo cp retailxai.service /etc/systemd/system/"
        echo "   sudo systemctl daemon-reload"
        echo "   sudo systemctl enable retailxai"
        echo "   sudo systemctl start retailxai"
        echo ""
        echo "7. Monitor the service:"
        echo "   sudo systemctl status retailxai"
        echo "   sudo journalctl -u retailxai -f"
        ;;
    2)
        echo ""
        echo "🐳 Docker Deployment"
        echo "==================="
        echo ""
        echo "1. SSH into your server:"
        echo "   ssh username@your-server-ip"
        echo ""
        echo "2. Clone/update the repository:"
        echo "   git clone https://github.com/your-username/Precipice-1.git"
        echo "   cd Precipice-1"
        echo ""
        echo "3. Install Docker and Docker Compose:"
        echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "   sudo sh get-docker.sh"
        echo "   sudo curl -L 'https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose"
        echo "   sudo chmod +x /usr/local/bin/docker-compose"
        echo ""
        echo "4. Configure environment:"
        echo "   cp config/.env.example .env"
        echo "   nano .env  # Add your environment variables"
        echo ""
        echo "5. Generate Docker files:"
        echo "   python deploy_production.py"
        echo ""
        echo "6. Start services:"
        echo "   docker-compose up -d"
        echo ""
        echo "7. Monitor services:"
        echo "   docker-compose ps"
        echo "   docker-compose logs -f retailxai"
        ;;
    3)
        echo ""
        echo "📖 Manual Deployment Instructions"
        echo "================================"
        echo ""
        echo "See DEPLOYMENT_GUIDE.md for detailed instructions"
        echo ""
        echo "Quick commands:"
        echo "  python environment_validator.py  # Validate environment"
        echo "  python health_monitor.py         # Check system health"
        echo "  python deploy_production.py      # Run production setup"
        echo "  python main.py                   # Start the application"
        ;;
    4)
        print_warning "Skipping deployment"
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set up your environment variables in config/.env"
echo "2. Ensure your database is running and accessible"
echo "3. Run: python environment_validator.py"
echo "4. Run: python health_monitor.py"
echo "5. Start your application: python main.py"
echo ""
echo "📊 Monitoring:"
echo "- Check logs: tail -f logs/retailxai.log"
echo "- Health checks: python health_monitor.py"
echo "- System status: Check the generated service files"
echo ""
print_status "Production fixes are ready for deployment! 🚀"
