#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}pipeline-demo Deployment${NC}"
echo "================================================"

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}ERROR: CLOUDFLARE_API_TOKEN environment variable is required${NC}"
    exit 1
fi

ACCOUNT_ID="your-account-id"
SCRIPT_NAME="pipeline-demo"
ZONE_ID="your-zone-id"

echo -e "\n${YELLOW}Deploying Python Worker to Cloudflare...${NC}"

if command -v wrangler &> /dev/null; then
    npx wrangler@latest deploy

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Python Worker deployed successfully${NC}"
        echo ""
        echo "Your Python agent is now available at:"
        echo -e "${YELLOW}https://pipeline-demo.example.com${NC}"
        echo ""
        echo "🐍 Python Workers Features:"
        echo "• Standard library support in production"
        echo "• Cloudflare AI and KV bindings"
        echo "• MCP server interface"
        echo "• Fast cold starts with Pyodide"
    else
        echo -e "${RED}✗ Failed to deploy Worker${NC}"
        exit 1
    fi
else
    echo -e "${RED}Wrangler not found. Please install: npm install -g wrangler${NC}"
    exit 1
fi
