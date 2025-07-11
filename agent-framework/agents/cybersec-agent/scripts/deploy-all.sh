#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Cloudflare Cybersecurity AI Assistant Deployment${NC}"
echo "================================================"

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}ERROR: CLOUDFLARE_API_TOKEN environment variable is required${NC}"
    echo ""
    echo "Please create a token at: https://dash.cloudflare.com/profile/api-tokens"
    echo "The token needs these permissions:"
    echo "  - Account: Cloudflare Workers Scripts:Edit"
    echo "  - Zone: Workers Routes:Edit (for mindhive.tech)"
    echo "  - Zone: DNS:Edit (for mindhive.tech)"
    echo ""
    echo "Then run:"
    echo "  export CLOUDFLARE_API_TOKEN=\"your-token-here\""
    echo "  ./deploy-all.sh"
    exit 1
fi

ACCOUNT_ID="82d842d586a0298981ab28617ec8ac66"
SCRIPT_NAME="cybersec-agent"
ZONE_ID="4f8b8a0bd742d7872f75b8144b3851f8"

# Step 1: Create DNS record
echo -e "\n${YELLOW}Step 1: Creating DNS record for cybersec.mindhive.tech...${NC}"

DNS_DATA=$(cat <<EOF
{
  "type": "CNAME",
  "name": "cybersec",
  "content": "mindhive.tech",
  "ttl": 1,
  "proxied": true
}
EOF
)

DNS_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DNS_DATA")

if echo "$DNS_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ DNS record created successfully${NC}"
elif echo "$DNS_RESPONSE" | grep -q "already exists"; then
    echo -e "${GREEN}✓ DNS record already exists${NC}"
else
    echo -e "${RED}✗ Failed to create DNS record${NC}"
    echo "$DNS_RESPONSE"
    # Don't exit on DNS error if record already exists
    if ! echo "$DNS_RESPONSE" | grep -q "already exists"; then
        exit 1
    fi
fi

# Step 2: Deploy Worker
echo -e "\n${YELLOW}Step 2: Deploying Worker to Cloudflare...${NC}"

# Create metadata
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
      "type": "kv_namespace",
      "name": "CACHE",
      "namespace_id": "94f2859d6efd4fc8830887d5d797324a"
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
    },
    {
      "type": "plain_text",
      "name": "JUDGE_URL",
      "text": "https://judge.mindhive.tech"
    }
  ]
}
EOF
)

WORKER_RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$SCRIPT_NAME" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -F "metadata=$METADATA;type=application/json" \
  -F "index.js=@src/index.js;type=application/javascript+module")

if echo "$WORKER_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ Worker deployed successfully${NC}"
else
    echo -e "${RED}✗ Failed to deploy Worker${NC}"
    echo "$WORKER_RESPONSE"
    exit 1
fi

# Step 3: Create route
echo -e "\n${YELLOW}Step 3: Creating route for cybersec.mindhive.tech...${NC}"

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
elif echo "$ROUTE_RESPONSE" | grep -q "Route pattern already exists"; then
    echo -e "${GREEN}✓ Route already exists${NC}"
else
    echo -e "${RED}✗ Failed to create route${NC}"
    echo "$ROUTE_RESPONSE"
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
echo "  • Response caching for improved performance"
echo "  • Clean web interface with example questions"
echo ""
echo "API Endpoint:"
echo "  POST https://cybersec.mindhive.tech/api/ask"
echo "  Body: {\"question\": \"your cybersecurity question\"}"
echo ""
echo -e "${YELLOW}Note: DNS propagation may take a few minutes.${NC}"