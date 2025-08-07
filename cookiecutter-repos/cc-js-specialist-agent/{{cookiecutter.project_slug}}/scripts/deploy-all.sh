#!/bin/bash

# {{cookiecutter.project_name}} Deployment Script
# Generated on {% now 'utc', '%Y-%m-%d' %}

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying {{cookiecutter.project_name}}...${NC}"

# Check for required environment variables
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}Error: CLOUDFLARE_API_TOKEN is not set${NC}"
    echo "Please set your Cloudflare API token:"
    echo "  export CLOUDFLARE_API_TOKEN=your_token_here"
    exit 1
fi

# Optional: Set account ID if provided
{% if cookiecutter.cloudflare_account_id %}
export CLOUDFLARE_ACCOUNT_ID={{cookiecutter.cloudflare_account_id}}
{% endif %}

# Deploy the Worker
echo -e "${YELLOW}Deploying Worker...${NC}"
npx wrangler deploy

# If using custom domain
{% if cookiecutter.domain %}
echo -e "${YELLOW}Setting up custom domain: {{cookiecutter.domain}}${NC}"
# Note: Custom domain setup requires manual configuration in Cloudflare dashboard
# or additional wrangler commands based on your setup
{% endif %}

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Your agent is available at:"
echo -e "  https://{{cookiecutter.project_slug}}.workers.dev"
{% if cookiecutter.domain %}
echo -e "  https://{{cookiecutter.domain}}"
{% endif %}