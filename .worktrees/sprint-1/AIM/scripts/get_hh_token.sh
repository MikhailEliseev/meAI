#!/bin/bash
# Get HH API access token after application approval

set -e

echo "🔑 HH API Token Generator"
echo "========================="
echo ""

# Check if credentials are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./get_hh_token.sh CLIENT_ID CLIENT_SECRET"
    echo ""
    echo "Get your credentials from https://dev.hh.ru/admin"
    echo "After your application is approved."
    exit 1
fi

CLIENT_ID="$1"
CLIENT_SECRET="$2"

echo "📡 Requesting token from HH API..."
echo ""

# Request token
RESPONSE=$(curl -s -X POST https://api.hh.ru/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET")

# Check if request was successful
if echo "$RESPONSE" | grep -q "access_token"; then
    ACCESS_TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

    echo "✅ Token received successfully!"
    echo ""
    echo "Your access token:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$ACCESS_TOKEN"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Save to .env
    if [ -f .env ]; then
        # Update existing .env
        if grep -q "HH_ACCESS_TOKEN=" .env; then
            sed -i.bak "s|HH_ACCESS_TOKEN=.*|HH_ACCESS_TOKEN=$ACCESS_TOKEN|" .env
            rm .env.bak
            echo "✅ Updated .env file"
        else
            echo "HH_ACCESS_TOKEN=$ACCESS_TOKEN" >> .env
            echo "✅ Added token to .env file"
        fi
    else
        # Create new .env from example
        cp .env.example .env
        sed -i.bak "s|HH_ACCESS_TOKEN=.*|HH_ACCESS_TOKEN=$ACCESS_TOKEN|" .env
        sed -i.bak "s|HH_CLIENT_ID=.*|HH_CLIENT_ID=$CLIENT_ID|" .env
        sed -i.bak "s|HH_CLIENT_SECRET=.*|HH_CLIENT_SECRET=$CLIENT_SECRET|" .env
        rm .env.bak
        echo "✅ Created .env file with your credentials"
    fi

    echo ""
    echo "🎉 All set! You can now run:"
    echo "   python scripts/test_hh_agent.py"

else
    echo "❌ Error getting token:"
    echo "$RESPONSE"
    exit 1
fi
