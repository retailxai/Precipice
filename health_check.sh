#!/bin/bash
# Health check script for RetailXAI

echo "🏥 Checking RetailXAI Health..."

# Check if service is running
if ! systemctl is-active --quiet retailxai; then
    echo "❌ RetailXAI service is not running"
    exit 1
fi

# Check API endpoints
if ! curl -f -s http://localhost:5000/api/health > /dev/null; then
    echo "❌ Health endpoint not responding"
    exit 1
fi

# Check database connectivity
if ! python3 -c "from database_manager import DatabaseManager; print('DB OK')" 2>/dev/null; then
    echo "❌ Database connection failed"
    exit 1
fi

echo "✅ All health checks passed"
exit 0
