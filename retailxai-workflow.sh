#!/bin/bash
# RetailXAI Full-Stack Workflow - Elon Style
# Local → Git → GitHub Actions → Production Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 RetailXAI Full-Stack Workflow - Elon Style${NC}"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Run this from the RetailXAI project root directory${NC}"
    exit 1
fi

# Function to show project status
show_status() {
    echo -e "${BLUE}📊 RetailXAI Project Status${NC}"
    echo "=========================="
    
    # Backend status
    if [ -d "backend" ]; then
        echo -e "${GREEN}✅ Backend: $(find backend -name "*.py" | wc -l) Python files${NC}"
    else
        echo -e "${RED}❌ Backend: Not found${NC}"
    fi
    
    # Frontend status
    if [ -d "frontend" ]; then
        echo -e "${GREEN}✅ Frontend: $(find frontend -name "*.tsx" -o -name "*.ts" | wc -l) TypeScript files${NC}"
    else
        echo -e "${RED}❌ Frontend: Not found${NC}"
    fi
    
    # Content status
    if [ -d "articles" ] && [ "$(ls -A articles 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ Articles: $(ls articles/ | wc -l) files${NC}"
    else
        echo -e "${YELLOW}ℹ️  Articles: No files${NC}"
    fi
    
    if [ -d "transcripts" ] && [ "$(ls -A transcripts 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ Transcripts: $(ls transcripts/ | wc -l) files${NC}"
    else
        echo -e "${YELLOW}ℹ️  Transcripts: No files${NC}"
    fi
    
    # Git status
    echo -e "${CYAN}📝 Git Status:${NC}"
    git status --porcelain | head -10
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${GREEN}✅ Working directory clean${NC}"
    else
        echo -e "${YELLOW}⚠️  Uncommitted changes${NC}"
    fi
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}🧪 Running Tests${NC}"
    echo "==============="
    
    # Backend tests
    if [ -d "backend" ]; then
        echo -e "${YELLOW}Testing backend...${NC}"
        cd backend
        python -m pytest -v || echo -e "${RED}Backend tests failed${NC}"
        cd ..
    fi
    
    # Frontend tests
    if [ -d "frontend" ]; then
        echo -e "${YELLOW}Testing frontend...${NC}"
        cd frontend
        npm test -- --passWithNoTests || echo -e "${RED}Frontend tests failed${NC}"
        cd ..
    fi
    
    echo -e "${GREEN}✅ Tests completed${NC}"
}

# Function to build project
build_project() {
    echo -e "${BLUE}🔨 Building Project${NC}"
    echo "=================="
    
    # Build backend
    if [ -d "backend" ]; then
        echo -e "${YELLOW}Building backend...${NC}"
        cd backend
        pip install -r requirements.txt
        cd ..
    fi
    
    # Build frontend
    if [ -d "frontend" ]; then
        echo -e "${YELLOW}Building frontend...${NC}"
        cd frontend
        npm ci
        npm run build
        npm run export
        cd ..
    fi
    
    echo -e "${GREEN}✅ Build completed${NC}"
}

# Function to deploy to production
deploy_production() {
    echo -e "${BLUE}🚀 Deploying to Production${NC}"
    echo "=========================="
    
    # Check for changes
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}ℹ️  No changes to commit${NC}"
        return 0
    fi
    
    # Add all changes
    echo -e "${YELLOW}📝 Adding changes...${NC}"
    git add .
    
    # Commit with timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    commit_msg="🤖 RetailXAI: Full-stack update at $timestamp"
    
    echo -e "${YELLOW}💾 Committing: $commit_msg${NC}"
    git commit -m "$commit_msg"
    
    # Push to main
    echo -e "${YELLOW}🚀 Pushing to GitHub...${NC}"
    git push origin main
    
    echo -e "${GREEN}✅ Deploy initiated!${NC}"
    echo -e "${BLUE}🔄 GitHub Actions will now deploy to production server${NC}"
    echo -e "${CYAN}📊 Check Actions tab: https://github.com/retailxai/Precipice/actions${NC}"
}

# Function to run YouTube CLI
run_youtube_cli() {
    local video_url="$1"
    local company="${2:-Unknown}"
    local theme="${3:-Retail Analysis}"
    local publish="${4:-}"
    
    echo -e "${PURPLE}🎥 YouTube CLI Processing${NC}"
    echo "======================="
    echo -e "${YELLOW}🎥 Video: $video_url${NC}"
    echo -e "${YELLOW}🏢 Company: $company${NC}"
    echo -e "${YELLOW}📝 Theme: $theme${NC}"
    
    if [ -n "$publish" ]; then
        echo -e "${YELLOW}📤 Publishing to: $publish${NC}"
        youtube-ai "$video_url" --company "$company" --theme "$theme" --publish "$publish" --verbose
    else
        youtube-ai "$video_url" --company "$company" --theme "$theme" --verbose
    fi
}

# Function to run data pipeline
run_pipeline() {
    echo -e "${BLUE}🔄 Running Data Pipeline${NC}"
    echo "======================="
    
    # Run the main pipeline
    if [ -f "run_production_pipeline.py" ]; then
        echo -e "${YELLOW}Running production pipeline...${NC}"
        python run_production_pipeline.py
    else
        echo -e "${RED}❌ Production pipeline not found${NC}"
    fi
    
    echo -e "${GREEN}✅ Pipeline completed${NC}"
}

# Function to start local development
start_dev() {
    echo -e "${BLUE}🛠️  Starting Local Development${NC}"
    echo "============================="
    
    # Start backend
    if [ -d "backend" ]; then
        echo -e "${YELLOW}Starting backend...${NC}"
        cd backend
        python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        cd ..
    fi
    
    # Start frontend
    if [ -d "frontend" ]; then
        echo -e "${YELLOW}Starting frontend...${NC}"
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..
    fi
    
    echo -e "${GREEN}✅ Development servers started${NC}"
    echo -e "${CYAN}🌐 Backend: http://localhost:8000${NC}"
    echo -e "${CYAN}🌐 Frontend: http://localhost:3000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    
    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
}

# Main workflow
case "${1:-help}" in
    "status")
        show_status
        ;;
    "test")
        run_tests
        ;;
    "build")
        build_project
        ;;
    "deploy")
        deploy_production
        ;;
    "youtube")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Usage: $0 youtube <video_url> [company] [theme] [publish]${NC}"
            exit 1
        fi
        run_youtube_cli "$2" "$3" "$4" "$5"
        ;;
    "pipeline")
        run_pipeline
        ;;
    "dev")
        start_dev
        ;;
    "full")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Usage: $0 full <video_url> [company] [theme] [publish]${NC}"
            exit 1
        fi
        run_youtube_cli "$2" "$3" "$4" "$5"
        deploy_production
        ;;
    "help"|*)
        echo -e "${BLUE}RetailXAI Full-Stack Workflow - Elon Style${NC}"
        echo "=============================================="
        echo ""
        echo "Usage:"
        echo "  $0 status                                    - Show project status"
        echo "  $0 test                                      - Run all tests"
        echo "  $0 build                                     - Build project"
        echo "  $0 deploy                                    - Deploy to production"
        echo "  $0 youtube <video_url> [company] [theme] [publish] - Process YouTube video"
        echo "  $0 pipeline                                  - Run data pipeline"
        echo "  $0 dev                                       - Start local development"
        echo "  $0 full <video_url> [company] [theme] [publish] - Process video + deploy"
        echo "  $0 help                                      - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 test"
        echo "  $0 deploy"
        echo "  $0 youtube 'https://youtube.com/watch?v=abc123' 'Tesla' 'Q3 Earnings'"
        echo "  $0 full 'https://youtube.com/watch?v=abc123' 'Tesla' 'Q3 Earnings' substack"
        echo "  $0 dev"
        ;;
esac
