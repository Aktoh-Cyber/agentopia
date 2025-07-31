#!/bin/bash

# Aktoh Cyber InfoSec Deployment Script
# This script deploys all InfoSec agents to Cloudflare using Pulumi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Aktoh Cyber InfoSec Deployment${NC}"
echo "================================================"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check if Pulumi is installed
if ! command -v pulumi &> /dev/null; then
    echo -e "${RED}❌ Pulumi is not installed. Please install it first:${NC}"
    echo "curl -fsSL https://get.pulumi.com | sh"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install it first.${NC}"
    exit 1
fi

# Check environment variables
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}❌ CLOUDFLARE_API_TOKEN environment variable is required${NC}"
    echo "Please set it with: export CLOUDFLARE_API_TOKEN='your-token-here'"
    exit 1
fi

if [ -z "$CLOUDFLARE_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ CLOUDFLARE_ACCOUNT_ID environment variable is required${NC}"
    echo "Please set it with: export CLOUDFLARE_ACCOUNT_ID='your-account-id'"
    exit 1
fi

if [ -z "$CLOUDFLARE_ZONE_ID" ]; then
    echo -e "${RED}❌ CLOUDFLARE_ZONE_ID environment variable is required${NC}"
    echo "Please set it with: export CLOUDFLARE_ZONE_ID='your-zone-id'"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Navigate to pulumi directory
cd "$(dirname "$0")/pulumi"

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
npm install

# Initialize Pulumi stack if it doesn't exist
if ! pulumi stack ls | grep -q "dev"; then
    echo -e "\n${YELLOW}Creating Pulumi stack...${NC}"
    pulumi stack init dev
fi

# Set configuration
echo -e "\n${YELLOW}Setting Pulumi configuration...${NC}"
pulumi config set cloudflare:apiToken "$CLOUDFLARE_API_TOKEN" --secret
pulumi config set accountId "$CLOUDFLARE_ACCOUNT_ID" --secret
pulumi config set zoneId "$CLOUDFLARE_ZONE_ID" --secret

# Preview the deployment
echo -e "\n${YELLOW}Previewing deployment...${NC}"
pulumi preview

# Ask for confirmation
echo -e "\n${YELLOW}Do you want to proceed with the deployment? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "\n${YELLOW}Deploying infrastructure...${NC}"
    pulumi up --yes
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}🎉 Deployment successful!${NC}"
        echo -e "\n${GREEN}Your Aktoh Cyber InfoSec agents are now live:${NC}"
        echo -e "${GREEN}• InfoSec Supervisor: https://infosec.a.aktohcyber.com${NC}"
        echo -e "${GREEN}• Judge (Vulnerability & Compliance): https://judge.a.aktohcyber.com${NC}"
        echo -e "${GREEN}• Lancer (Red Team & Penetration Testing): https://lancer.a.aktohcyber.com${NC}"
        echo -e "${GREEN}• Scout (Discovery & Reconnaissance): https://scout.a.aktohcyber.com${NC}"
        echo -e "${GREEN}• Shield (Blue Team & Incident Response): https://shield.a.aktohcyber.com${NC}"
        
        echo -e "\n${BLUE}📋 Next Steps:${NC}"
        echo "1. Test each agent endpoint"
        echo "2. Configure any additional security settings"
        echo "3. Set up monitoring and alerting"
        echo "4. Update your documentation with the new URLs"
    else
        echo -e "\n${RED}❌ Deployment failed. Check the logs above for details.${NC}"
        exit 1
    fi
else
    echo -e "\n${YELLOW}Deployment cancelled.${NC}"
fi