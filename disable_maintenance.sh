#!/bin/bash

# Disable Maintenance Mode for RetailXAI Dashboard
# This script removes maintenance mode and restores normal operation

echo "🔓 Disabling Maintenance Mode for RetailXAI Dashboard"
echo "==================================================="

# Set maintenance mode environment variable to false
export MAINTENANCE_MODE=false

# Update .env file with maintenance mode disabled
if [ -f ".env" ]; then
    # Update existing .env file
    sed -i.bak 's/MAINTENANCE_MODE=true/MAINTENANCE_MODE=false/' .env
    echo "✅ Updated existing .env file"
else
    # Create new .env file
    cat > .env << EOF
# RetailXAI Dashboard Environment Configuration
MAINTENANCE_MODE=false
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
EOF
    echo "✅ Created new .env file"
fi

echo "✅ Maintenance mode disabled"
echo "✅ Environment configuration updated"
echo ""
echo "The dashboard will now show the normal interface."
echo "To re-enable maintenance mode, run: ./enable_maintenance.sh"
echo ""
echo "Current status: MAINTENANCE_MODE=false"

