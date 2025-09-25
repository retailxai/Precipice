#!/bin/bash
# YouTube CLI Workflow - Elon Style
# Local → Git → Server pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 YouTube CLI Workflow - Elon Style${NC}"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "youtube_cli.py" ]; then
    echo -e "${RED}❌ Error: Run this from the project root directory${NC}"
    exit 1
fi

# Function to run YouTube CLI
run_youtube_cli() {
    local video_url="$1"
    local company="${2:-Unknown}"
    local theme="${3:-Retail Analysis}"
    local publish="${4:-}"
    
    echo -e "${YELLOW}🎥 Processing: $video_url${NC}"
    echo -e "${YELLOW}🏢 Company: $company${NC}"
    echo -e "${YELLOW}📝 Theme: $theme${NC}"
    
    if [ -n "$publish" ]; then
        echo -e "${YELLOW}📤 Publishing to: $publish${NC}"
        youtube-ai "$video_url" --company "$company" --theme "$theme" --publish "$publish" --verbose
    else
        youtube-ai "$video_url" --company "$company" --theme "$theme" --verbose
    fi
}

# Function to commit and push changes
git_deploy() {
    echo -e "${BLUE}📦 Git Deploy${NC}"
    echo "============="
    
    # Check for changes
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}ℹ️  No changes to commit${NC}"
        return 0
    fi
    
    # Add all changes
    echo -e "${YELLOW}📝 Adding changes...${NC}"
    git add articles/ transcripts/ analyses/ youtube_cli.py youtube-ai
    
    # Commit with timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    commit_msg="🤖 YouTube CLI: Generated content at $timestamp"
    
    echo -e "${YELLOW}💾 Committing: $commit_msg${NC}"
    git commit -m "$commit_msg"
    
    # Push to main
    echo -e "${YELLOW}🚀 Pushing to GitHub...${NC}"
    git push origin main
    
    echo -e "${GREEN}✅ Git deploy complete!${NC}"
    echo -e "${BLUE}🔄 GitHub Actions will now deploy to production server${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Current Status${NC}"
    echo "==============="
    
    if [ -d "articles" ] && [ "$(ls -A articles 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ Articles: $(ls articles/ | wc -l) files${NC}"
        ls articles/ | head -5
    else
        echo -e "${YELLOW}ℹ️  No articles found${NC}"
    fi
    
    if [ -d "transcripts" ] && [ "$(ls -A transcripts 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ Transcripts: $(ls transcripts/ | wc -l) files${NC}"
    else
        echo -e "${YELLOW}ℹ️  No transcripts found${NC}"
    fi
    
    if [ -d "analyses" ] && [ "$(ls -A analyses 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ Analyses: $(ls analyses/ | wc -l) files${NC}"
    else
        echo -e "${YELLOW}ℹ️  No analyses found${NC}"
    fi
}

# Main workflow
case "${1:-help}" in
    "process")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Usage: $0 process <video_url> [company] [theme] [publish]${NC}"
            exit 1
        fi
        run_youtube_cli "$2" "$3" "$4" "$5"
        ;;
    "deploy")
        git_deploy
        ;;
    "full")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Usage: $0 full <video_url> [company] [theme] [publish]${NC}"
            exit 1
        fi
        run_youtube_cli "$2" "$3" "$4" "$5"
        git_deploy
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        echo -e "${BLUE}YouTube CLI Workflow - Elon Style${NC}"
        echo "=================================="
        echo ""
        echo "Usage:"
        echo "  $0 process <video_url> [company] [theme] [publish]  - Process video only"
        echo "  $0 deploy                                          - Deploy to production"
        echo "  $0 full <video_url> [company] [theme] [publish]    - Process + Deploy"
        echo "  $0 status                                          - Show current status"
        echo "  $0 help                                            - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 process 'https://youtube.com/watch?v=abc123' 'Tesla' 'Q3 Earnings'"
        echo "  $0 full 'https://youtube.com/watch?v=abc123' 'Tesla' 'Q3 Earnings' substack"
        echo "  $0 deploy"
        echo "  $0 status"
        ;;
esac
