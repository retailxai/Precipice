#!/bin/bash

# Stop All RetailXAI Dashboard Services
# This script stops all running dashboard instances

echo "🛑 Stopping All RetailXAI Dashboard Services"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Function to kill processes by port
kill_by_port() {
    local port=$1
    local service_name=$2
    
    print_status "Checking port $port for $service_name..."
    
    # Find processes using the port
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        print_warning "Found processes on port $port: $pids"
        for pid in $pids; do
            print_status "Killing process $pid..."
            kill -TERM $pid 2>/dev/null
            sleep 2
            
            # Check if process is still running
            if kill -0 $pid 2>/dev/null; then
                print_warning "Process $pid still running, force killing..."
                kill -KILL $pid 2>/dev/null
            fi
        done
        print_success "$service_name stopped on port $port"
    else
        print_status "No processes found on port $port"
    fi
}

# Function to kill processes by name
kill_by_name() {
    local process_name=$1
    local service_name=$2
    
    print_status "Checking for $service_name processes..."
    
    # Find processes by name
    local pids=$(pgrep -f "$process_name" 2>/dev/null)
    
    if [ -n "$pids" ]; then
        print_warning "Found $service_name processes: $pids"
        for pid in $pids; do
            print_status "Killing process $pid..."
            kill -TERM $pid 2>/dev/null
            sleep 2
            
            # Check if process is still running
            if kill -0 $pid 2>/dev/null; then
                print_warning "Process $pid still running, force killing..."
                kill -KILL $pid 2>/dev/null
            fi
        done
        print_success "$service_name processes stopped"
    else
        print_status "No $service_name processes found"
    fi
}

# Stop services by port
kill_by_port 8001 "Enhanced Dashboard"
kill_by_port 8003 "Production Dashboard"
kill_by_port 8004 "Secure Dashboard"
kill_by_port 5000 "Web Server"

# Stop services by process name
kill_by_name "enhanced_dashboard.py" "Enhanced Dashboard"
kill_by_name "production_dashboard_secure.py" "Production Dashboard"
kill_by_name "secure_dashboard.py" "Secure Dashboard"
kill_by_name "web_server.py" "Web Server"
kill_by_name "simple_dashboard.py" "Simple Dashboard"

# Stop any uvicorn processes
kill_by_name "uvicorn" "Uvicorn Server"

# Stop any Flask processes
kill_by_name "flask" "Flask Server"

# Check for any remaining Python web processes
print_status "Checking for remaining Python web processes..."
remaining_pids=$(pgrep -f "python.*dashboard\|python.*server\|uvicorn\|flask" 2>/dev/null)

if [ -n "$remaining_pids" ]; then
    print_warning "Found remaining web processes: $remaining_pids"
    for pid in $remaining_pids; do
        print_status "Killing remaining process $pid..."
        kill -TERM $pid 2>/dev/null
        sleep 2
        
        if kill -0 $pid 2>/dev/null; then
            print_warning "Process $pid still running, force killing..."
            kill -KILL $pid 2>/dev/null
        fi
    done
else
    print_success "No remaining web processes found"
fi

# Verify all ports are free
print_status "Verifying all dashboard ports are free..."
ports=(8001 8003 8004 5000)
all_free=true

for port in "${ports[@]}"; do
    if lsof -ti:$port >/dev/null 2>&1; then
        print_error "Port $port is still in use"
        all_free=false
    else
        print_success "Port $port is free"
    fi
done

if [ "$all_free" = true ]; then
    print_success "All dashboard services have been stopped successfully!"
else
    print_warning "Some ports may still be in use. Check manually if needed."
fi

echo ""
echo "🔒 Dashboard Status: OFFLINE"
echo "============================="
echo "All RetailXAI dashboard services have been stopped."
echo "The site is now inaccessible for security updates."
echo ""
echo "To restart services after security updates:"
echo "  ./start_secure_dashboard.sh"
echo ""
echo "To enable maintenance mode:"
echo "  ./enable_maintenance.sh"

