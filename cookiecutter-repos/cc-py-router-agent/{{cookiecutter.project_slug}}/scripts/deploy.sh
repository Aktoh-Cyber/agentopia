#!/bin/bash

# {{cookiecutter.project_name}} Deployment Script
# Python Router Agent for Cloudflare Workers

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying {{cookiecutter.project_name}} (Python)...${NC}"

# Check for required environment variables
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}Error: CLOUDFLARE_API_TOKEN is not set${NC}"
    echo "Please set your Cloudflare API token:"
    echo "  export CLOUDFLARE_API_TOKEN=your_token_here"
    exit 1
fi

# Note about Python Workers
echo -e "${YELLOW}Note: This is a Python Worker using Pyodide runtime${NC}"
echo -e "${YELLOW}Production deployment uses standard library only${NC}"

# Optional: Set account ID if provided
{% if cookiecutter.cloudflare_account_id %}
export CLOUDFLARE_ACCOUNT_ID={{cookiecutter.cloudflare_account_id}}
{% endif %}

# Deploy the Worker
echo -e "${YELLOW}Deploying Python Worker...${NC}"
npx wrangler deploy

# If using custom domain
{% if cookiecutter.domain %}
echo -e "${YELLOW}Setting up custom domain: {{cookiecutter.domain}}${NC}"
# Note: Custom domain setup requires manual configuration in Cloudflare dashboard
# or additional wrangler commands based on your setup
{% endif %}

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Your Python router agent is available at:"
echo -e "  https://{{cookiecutter.project_slug}}.workers.dev"
{% if cookiecutter.domain %}
echo -e "  https://{{cookiecutter.domain}}"
{% endif %}

echo -e "\n${YELLOW}Python Worker Notes:${NC}"
echo -e "- Uses Pyodide runtime for Python execution"
echo -e "- Standard library only in production"
echo -e "- FFI imports available (from js import ...)"
echo -e "- Full async/await support"