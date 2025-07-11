#!/bin/bash

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "CLOUDFLARE_API_TOKEN environment variable is required"
    exit 1
fi

ZONE_ID="4f8b8a0bd742d7872f75b8144b3851f8"
SCRIPT_NAME="cybersec-agent"

echo "Creating route for cybersec.mindhive.tech..."

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

echo "$ROUTE_RESPONSE" | jq .

if echo "$ROUTE_RESPONSE" | grep -q '"success":true'; then
    echo "✓ Route created successfully!"
    echo ""
    echo "Your cybersecurity AI assistant is now available at:"
    echo "https://cybersec.mindhive.tech"
else
    echo "✗ Failed to create route"
fi