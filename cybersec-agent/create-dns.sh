#!/bin/bash

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "CLOUDFLARE_API_TOKEN environment variable is required"
    exit 1
fi

ZONE_ID="4f8b8a0bd742d7872f75b8144b3851f8"

# Create a CNAME record pointing to the root domain
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

echo "Creating DNS record for cybersec.mindhive.tech..."

curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DNS_DATA"

echo ""
echo "DNS record created!"