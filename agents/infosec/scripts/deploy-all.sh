#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Scout - Network Discovery & Reconnaissance Expert Deployment${NC}"
echo "================================================"

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}ERROR: CLOUDFLARE_API_TOKEN environment variable is required${NC}"
    exit 1
fi

ACCOUNT_ID="82d842d586a0298981ab28617ec8ac66"
SCRIPT_NAME="{{domain.split('.')[0]}}"
ZONE_ID="4f8b8a0bd742d7872f75b8144b3851f8"

# Step 1: Create DNS record
echo -e "\n${YELLOW}Step 1: Creating DNS record for scout.mindhive.tech...${NC}"

DNS_DATA=$(cat <<EOF
{
  "type": "CNAME",
  "name": "{{domain.split('.')[0]}}",
  "content": "{{domain.split('.').slice(1).join('.')}}",
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
fi

# Step 2: Deploy Worker
echo -e "\n${YELLOW}Step 2: Deploying Worker to Cloudflare...${NC}"

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
echo -e "\n${YELLOW}Step 3: Creating route for scout.mindhive.tech...${NC}"

ROUTE_DATA=$(cat <<EOF
{
  "pattern": "scout.mindhive.tech/*",
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
elif echo "$ROUTE_RESPONSE" | grep -q "already exists"; then
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
echo "Your agent is now available at:"
echo -e "${YELLOW}https://scout.mindhive.tech${NC}"