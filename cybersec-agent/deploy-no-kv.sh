#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Cloudflare Cybersecurity AI Assistant Deployment (No KV)${NC}"
echo "========================================================"

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}ERROR: CLOUDFLARE_API_TOKEN environment variable is required${NC}"
    exit 1
fi

ACCOUNT_ID="82d842d586a0298981ab28617ec8ac66"
SCRIPT_NAME="cybersec-agent"
ZONE_ID="4f8b8a0bd742d7872f75b8144b3851f8"

# Step 1: Deploy Worker without KV
echo -e "\n${YELLOW}Deploying Worker to Cloudflare (without KV caching)...${NC}"

# Create metadata without KV binding
METADATA=$(cat <<EOF
{
  "main_module": "index.js",
  "compatibility_date": "2024-01-01",
  "bindings": [
    {
      "type": "ai",
      "name": "AI"
    },
    {
      "type": "plain_text",
      "name": "MAX_TOKENS",
      "text": "512"
    },
    {
      "type": "plain_text",
      "name": "TEMPERATURE",
      "text": "0.3"
    }
  ]
}
EOF
)

WORKER_RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$SCRIPT_NAME" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -F "metadata=$METADATA;type=application/json" \
  -F "index.js=@src/index-no-kv.js;type=application/javascript+module")

if echo "$WORKER_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ Worker deployed successfully${NC}"
else
    echo -e "${RED}✗ Failed to deploy Worker${NC}"
    echo "$WORKER_RESPONSE"
    exit 1
fi

# Step 2: Create route
echo -e "\n${YELLOW}Creating route for cybersec.mindhive.tech...${NC}"

# First, check if route already exists
ROUTES_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN")

if echo "$ROUTES_RESPONSE" | grep -q "cybersec.mindhive.tech"; then
    echo -e "${GREEN}✓ Route already exists${NC}"
else
    ROUTE_DATA=$(cat <<EOF
{
  "pattern": "cybersec.mindhive.tech/*",
  "script": "$SCRIPT_NAME"
}
EOF
)

    ROUTE_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$ROUTE_DATA")

    if echo "$ROUTE_RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✓ Route created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create route${NC}"
        echo "$ROUTE_RESPONSE"
    fi
fi

# Final message
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Your cybersecurity AI assistant is now available at:"
echo -e "${YELLOW}https://cybersec.mindhive.tech${NC}"
echo ""
echo "Features:"
echo "  • AI-powered Q&A using Llama 3.1 8B"
echo "  • Specialized in cybersecurity topics"
echo "  • Clean web interface with example questions"
echo ""
echo -e "${YELLOW}Note: Caching is disabled in this version due to KV permissions.${NC}"
echo -e "${YELLOW}To enable caching, update your API token with KV permissions.${NC}"