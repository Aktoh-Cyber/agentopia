#!/bin/bash

# {{ cookiecutter.project_name }} Deployment Script
# JavaScript Workflow Supervisor for Cloudflare Workers

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deploying {{ cookiecutter.project_name }}${NC}"
echo -e "${BLUE}========================================${NC}"

# Check for required environment variables
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}Error: CLOUDFLARE_API_TOKEN is not set${NC}"
    echo "Please set your Cloudflare API token:"
    echo "  export CLOUDFLARE_API_TOKEN=your_token_here"
    exit 1
fi

# Display workflow configuration
echo -e "${YELLOW}Workflow Configuration:${NC}"
echo -e "  Strategy: {{ cookiecutter.supervisor_strategy }}"
echo -e "  Error Handling: {{ cookiecutter.error_handling }}"
echo -e "  Max Retries: {{ cookiecutter.max_retries }}"
echo -e "  Timeout: {{ cookiecutter.timeout_ms }}ms"
echo -e "  Specialist Agents: $(echo '{{ cookiecutter.specialist_agents_json }}' | jq length) agents"
echo -e "  Workflow Steps: $(echo '{{ cookiecutter.workflow_steps_json }}' | jq length) steps"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Optional: Set account ID if provided
{% if cookiecutter.cloudflare_account_id %}
export CLOUDFLARE_ACCOUNT_ID={{ cookiecutter.cloudflare_account_id }}
{% endif %}

# Deploy the Worker
echo -e "${YELLOW}Deploying Workflow Supervisor...${NC}"
npx wrangler deploy

# Deployment successful
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\nYour workflow supervisor is available at:"
echo -e "  ${BLUE}https://{{ cookiecutter.project_slug }}.workers.dev${NC}"
{% if cookiecutter.domain %}
echo -e "  ${BLUE}https://{{ cookiecutter.domain }}${NC}"
{% endif %}

echo -e "\n${YELLOW}API Endpoints:${NC}"
echo -e "  GET  / - Web interface with workflow visualization"
echo -e "  POST / - Process workflow requests"
echo -e "  GET  /health - Health check with agent status"
echo -e "  POST /mcp - MCP protocol endpoint"
echo -e "  GET  /workflow/status - Current workflow status"
echo -e "  POST /workflow/cancel - Cancel running workflow"
echo -e "  GET  /workflow/history - Workflow execution history"
echo -e "  POST /workflow/retry - Retry failed workflow"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Test the workflow with: curl -X POST https://{{ cookiecutter.project_slug }}.workers.dev \\"
echo -e "   -H 'Content-Type: application/json' \\"
echo -e "   -d '{\"question\": \"Your complex task here\"}'"
echo -e "2. Monitor workflows at: https://{{ cookiecutter.project_slug }}.workers.dev"
echo -e "3. Configure specialist agents in wrangler.toml"
echo -e "4. Enable KV namespace for workflow state persistence"