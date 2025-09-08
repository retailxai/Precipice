#!/bin/bash
# Production start script for RetailXAI

set -e

echo "🚀 Starting RetailXAI Production System..."

# Check if running as correct user
if [ "$USER" != "retailxai" ]; then
    echo "❌ Must run as retailxai user"
    exit 1
fi

# Check environment
if [ ! -f "config/.env" ]; then
    echo "❌ Environment file not found"
    exit 1
fi

# Load environment
source config/.env

# Validate environment
python3 environment_validator.py

# Start the service
echo "✅ Starting RetailXAI scheduler..."
python3 main.py
