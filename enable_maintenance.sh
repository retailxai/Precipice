#!/bin/bash

# Enable Maintenance Mode for RetailXAI Dashboard
# This script puts the dashboard into maintenance mode

echo "🔧 Enabling Maintenance Mode for RetailXAI Dashboard"
echo "=================================================="

# Set maintenance mode environment variable
export MAINTENANCE_MODE=true

# Create .env file with maintenance mode enabled
cat > .env << EOF
# RetailXAI Dashboard Environment Configuration
MAINTENANCE_MODE=true
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
EOF

echo "✅ Maintenance mode enabled"
echo "✅ Environment configuration updated"
echo ""
echo "The dashboard will now show a maintenance page instead of the normal interface."
echo "To disable maintenance mode, run: ./disable_maintenance.sh"
echo ""
echo "Current status: MAINTENANCE_MODE=true"

