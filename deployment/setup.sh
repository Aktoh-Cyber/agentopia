#!/bin/bash

# Aktoh Cyber InfoSec Setup Script
# This script helps you gather the required information for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Aktoh Cyber InfoSec Setup${NC}"
echo "================================================"

echo -e "\n${YELLOW}This script will help you gather the required information for deployment.${NC}"

# Function to get Cloudflare info
get_cloudflare_info() {
    echo -e "\n${YELLOW}Step 1: Cloudflare API Token${NC}"
    echo "1. Go to https://dash.cloudflare.com/profile/api-tokens"
    echo "2. Click 'Create Token'"
    echo "3. Use 'Custom token' with these permissions:"
    echo "   - Zone:Zone:Read"
    echo "   - Zone:DNS:Edit" 
    echo "   - Account:Cloudflare Workers:Edit"
    echo "4. Include all zones for your account"
    
    echo -e "\n${BLUE}Enter your Cloudflare API Token:${NC}"
    read -s api_token
    export CLOUDFLARE_API_TOKEN="$api_token"
    
    # Test the token
    echo -e "\n${YELLOW}Testing API token...${NC}"
    response=$(curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ API token is valid${NC}"
    else
        echo -e "${RED}❌ API token is invalid. Please check and try again.${NC}"
        exit 1
    fi
}

# Function to get zone information
get_zone_info() {
    echo -e "\n${YELLOW}Step 2: Getting Zone Information${NC}"
    echo "Fetching information for aktohcyber.com..."
    
    zone_info=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" | \
        jq -r '.result[] | select(.name=="aktohcyber.com") | {name, id, account_id: .account.id}')
    
    if [ -z "$zone_info" ] || [ "$zone_info" = "null" ]; then
        echo -e "${RED}❌ Could not find aktohcyber.com in your Cloudflare account.${NC}"
        echo "Please ensure:"
        echo "1. The domain is added to your Cloudflare account"
        echo "2. Your API token has the correct permissions"
        exit 1
    fi
    
    zone_id=$(echo "$zone_info" | jq -r '.id')
    account_id=$(echo "$zone_info" | jq -r '.account_id')
    
    echo -e "${GREEN}✅ Found aktohcyber.com${NC}"
    echo "Zone ID: $zone_id"
    echo "Account ID: $account_id"
    
    export CLOUDFLARE_ZONE_ID="$zone_id"
    export CLOUDFLARE_ACCOUNT_ID="$account_id"
}

# Function to create environment file
create_env_file() {
    echo -e "\n${YELLOW}Step 3: Creating Environment File${NC}"
    
    env_file="$(dirname "$0")/.env"
    cat > "$env_file" << EOF
# Cloudflare Configuration for Aktoh Cyber InfoSec Deployment
# Generated on $(date)

export CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN"
export CLOUDFLARE_ACCOUNT_ID="$CLOUDFLARE_ACCOUNT_ID"
export CLOUDFLARE_ZONE_ID="$CLOUDFLARE_ZONE_ID"

# Usage: source deployment/.env
EOF
    
    echo -e "${GREEN}✅ Environment file created at: $env_file${NC}"
    echo -e "${BLUE}You can now source this file with: source deployment/.env${NC}"
}

# Function to show next steps
show_next_steps() {
    echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
    echo "================================================"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Source the environment file:"
    echo "   ${BLUE}source deployment/.env${NC}"
    echo ""
    echo "2. Run the deployment:"
    echo "   ${BLUE}./deployment/deploy.sh${NC}"
    echo ""
    echo "3. Your agents will be deployed at:"
    echo "   • InfoSec Supervisor: https://infosec.a.aktohcyber.com"
    echo "   • Judge: https://judge.a.aktohcyber.com"
    echo "   • Lancer: https://lancer.a.aktohcyber.com"
    echo "   • Scout: https://scout.a.aktohcyber.com"
    echo "   • Shield: https://shield.a.aktohcyber.com"
}

# Main execution
main() {
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq is required but not installed.${NC}"
        echo "Please install jq first:"
        echo "  macOS: brew install jq"
        echo "  Ubuntu: sudo apt-get install jq"
        echo "  CentOS: sudo yum install jq"
        exit 1
    fi
    
    get_cloudflare_info
    get_zone_info
    create_env_file
    show_next_steps
}

# Run main function
main