#!/bin/bash

# Test runner script for RetailXAI Dashboard
# Runs all tests: backend, frontend, and E2E

set -e

echo "🧪 Running RetailXAI Dashboard Tests"
echo "=================================="

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

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Parse command line arguments
RUN_BACKEND=true
RUN_FRONTEND=true
RUN_E2E=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            RUN_FRONTEND=false
            RUN_E2E=false
            shift
            ;;
        --frontend-only)
            RUN_BACKEND=false
            RUN_E2E=false
            shift
            ;;
        --e2e-only)
            RUN_BACKEND=false
            RUN_FRONTEND=false
            RUN_E2E=true
            shift
            ;;
        --include-e2e)
            RUN_E2E=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --backend-only    Run only backend tests"
            echo "  --frontend-only   Run only frontend tests"
            echo "  --e2e-only        Run only E2E tests"
            echo "  --include-e2e     Include E2E tests (default: false)"
            echo "  --verbose         Verbose output"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Backend tests
if [ "$RUN_BACKEND" = true ]; then
    echo ""
    echo "🔧 Running Backend Tests"
    echo "========================"
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing backend dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Run tests
    if [ "$VERBOSE" = true ]; then
        pytest -v --cov=app --cov-report=term-missing
    else
        pytest --cov=app --cov-report=term-missing
    fi
    
    if [ $? -eq 0 ]; then
        print_status "Backend tests passed!"
    else
        print_error "Backend tests failed!"
        exit 1
    fi
    
    deactivate
    cd ..
fi

# Frontend tests
if [ "$RUN_FRONTEND" = true ]; then
    echo ""
    echo "🎨 Running Frontend Tests"
    echo "========================"
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "Node modules not found. Installing dependencies..."
        npm install
    fi
    
    # Run tests
    if [ "$VERBOSE" = true ]; then
        npm test -- --verbose
    else
        npm test
    fi
    
    if [ $? -eq 0 ]; then
        print_status "Frontend tests passed!"
    else
        print_error "Frontend tests failed!"
        exit 1
    fi
    
    cd ..
fi

# E2E tests
if [ "$RUN_E2E" = true ]; then
    echo ""
    echo "🌐 Running E2E Tests"
    echo "==================="
    
    # Check if Playwright is installed
    if ! command -v npx playwright &> /dev/null; then
        print_warning "Playwright not found. Installing..."
        cd e2e
        npm install
        npx playwright install
        cd ..
    fi
    
    # Run E2E tests
    cd e2e
    
    if [ "$VERBOSE" = true ]; then
        npx playwright test --reporter=list
    else
        npx playwright test
    fi
    
    if [ $? -eq 0 ]; then
        print_status "E2E tests passed!"
    else
        print_error "E2E tests failed!"
        exit 1
    fi
    
    cd ..
fi

echo ""
echo "🎉 All tests completed successfully!"
echo "=================================="
