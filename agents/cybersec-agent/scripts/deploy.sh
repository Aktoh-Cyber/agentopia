#!/bin/bash

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "CLOUDFLARE_API_TOKEN environment variable is required"
    echo "Please create a token at: https://dash.cloudflare.com/profile/api-tokens"
    echo "The token needs these permissions:"
    echo "  - Account: Cloudflare Workers Scripts:Edit"
    echo "  - Zone: Workers Routes:Edit (for mindhive.tech)"
    exit 1
fi

ACCOUNT_ID="82d842d586a0298981ab28617ec8ac66"
SCRIPT_NAME="cybersec-agent"
ZONE_ID="4f8b8a0bd742d7872f75b8144b3851f8"

# Read the worker code
WORKER_CODE=$(cat src/index.js)

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
    }
  ]
}
EOF
)

echo "Deploying Worker to Cloudflare..."

# Upload the worker
curl -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$SCRIPT_NAME" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -F "metadata=$METADATA;type=application/json" \
  -F "index.js=@src/index.js;type=application/javascript+module"

echo ""
echo "Creating route for cybersec.mindhive.tech..."

# Create the route
ROUTE_DATA=$(cat <<EOF
{
  "pattern": "cybersec.mindhive.tech/*",
  "script": "$SCRIPT_NAME"
}
EOF
)

curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$ROUTE_DATA"

echo ""
echo "Deployment complete!"
echo ""
echo "Your cybersecurity AI assistant is now available at:"
echo "https://cybersec.mindhive.tech"