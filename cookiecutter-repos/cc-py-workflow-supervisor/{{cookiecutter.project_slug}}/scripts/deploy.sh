#!/bin/bash

# {{ cookiecutter.project_name }} Deployment Script
# Deploys the Python workflow supervisor to Cloudflare Workers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="{{ cookiecutter.project_slug }}"
DOMAIN="{{ cookiecutter.domain }}"
ACCOUNT_ID="{{ cookiecutter.cloudflare_account_id }}"
ZONE_ID="{{ cookiecutter.cloudflare_zone_id }}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists wrangler; then
        print_error "Wrangler CLI is not installed"
        print_status "Install with: npm install -g wrangler"
        exit 1
    fi
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check for API token
    if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
        print_error "CLOUDFLARE_API_TOKEN environment variable is not set"
        print_status "Set your token with: export CLOUDFLARE_API_TOKEN='your-token-here'"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Validate configuration
validate_config() {
    print_status "Validating configuration..."
    
    # Check if wrangler.toml exists
    if [ ! -f "wrangler.toml" ]; then
        print_error "wrangler.toml not found"
        exit 1
    fi
    
    # Validate Python entry point
    if [ ! -f "src/entry.py" ]; then
        print_error "src/entry.py not found"
        exit 1
    fi
    
    # Check required Python modules
    for module in "base_agent.py" "workflow_engine.py" "state_manager.py"; do
        if [ ! -f "src/$module" ]; then
            print_error "Required module src/$module not found"
            exit 1
        fi
    done
    
    print_success "Configuration validation passed"
}

# Validate Python syntax
validate_python() {
    print_status "Validating Python syntax..."
    
    for py_file in src/*.py; do
        if [ -f "$py_file" ]; then
            if ! python3 -m py_compile "$py_file"; then
                print_error "Syntax error in $py_file"
                exit 1
            fi
        fi
    done
    
    print_success "Python syntax validation passed"
}

# Deploy to specific environment
deploy_to_env() {
    local env=$1
    local env_name="${PROJECT_NAME}"
    
    if [ "$env" != "production" ]; then
        env_name="${PROJECT_NAME}-${env}"
    fi
    
    print_status "Deploying to $env environment ($env_name)..."
    
    # Deploy with wrangler
    if [ "$env" = "production" ]; then
        wrangler deploy --env production
    else
        wrangler deploy --env "$env"
    fi
    
    print_success "Successfully deployed to $env"
    
    # Show deployment URL
    if [ "$env" = "production" ] && [ -n "$DOMAIN" ]; then
        print_success "🌐 Production URL: https://$DOMAIN"
    else
        print_success "🌐 Worker URL: https://$env_name.workers.dev"
    fi
}

# Test deployment
test_deployment() {
    local url=$1
    print_status "Testing deployment at $url..."
    
    # Test status endpoint
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url/api/status" || echo "000")
    
    if [ "$status_code" = "200" ]; then
        print_success "✅ Status endpoint is healthy"
    else
        print_warning "⚠️  Status endpoint returned $status_code"
    fi
    
    # Test basic chat endpoint
    local chat_response
    chat_response=$(curl -s -X POST "$url/api/chat" \
        -H "Content-Type: application/json" \
        -d '{"question":"test"}' \
        -w "%{http_code}" || echo "error")
    
    if echo "$chat_response" | grep -q "200$"; then
        print_success "✅ Chat endpoint is working"
    else
        print_warning "⚠️  Chat endpoint test failed"
    fi
}

# Setup KV namespace
setup_kv() {
    print_status "Setting up KV namespace for workflow state..."
    
    # Check if KV namespace exists
    local kv_id
    kv_id=$(wrangler kv:namespace list | grep "\"${PROJECT_NAME}-workflows\"" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ -z "$kv_id" ]; then
        print_status "Creating KV namespace..."
        kv_id=$(wrangler kv:namespace create "${PROJECT_NAME}-workflows" --preview=false | grep -o 'id = "[^"]*"' | cut -d'"' -f2)
        
        if [ -n "$kv_id" ]; then
            print_success "Created KV namespace with ID: $kv_id"
            print_warning "Please update your wrangler.toml with this KV namespace ID:"
            print_warning "  id = \"$kv_id\""
        else
            print_error "Failed to create KV namespace"
        fi
    else
        print_success "KV namespace already exists with ID: $kv_id"
    fi
}

# Main deployment function
main() {
    print_status "🚀 Starting deployment of {{ cookiecutter.project_name }}..."
    echo
    
    # Parse command line arguments
    local target_env="production"
    local skip_tests=false
    local setup_kv_flag=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                target_env="$2"
                shift 2
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --setup-kv)
                setup_kv_flag=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --env ENV        Target environment (production, staging, development)"
                echo "  --skip-tests     Skip post-deployment tests"
                echo "  --setup-kv       Setup KV namespace for workflow state"
                echo "  -h, --help       Show this help message"
                echo
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run deployment steps
    check_prerequisites
    validate_config
    validate_python
    
    if [ "$setup_kv_flag" = true ]; then
        setup_kv
    fi
    
    # Deploy to target environment
    deploy_to_env "$target_env"
    
    # Test deployment unless skipped
    if [ "$skip_tests" = false ]; then
        if [ "$target_env" = "production" ] && [ -n "$DOMAIN" ]; then
            test_deployment "https://$DOMAIN"
        else
            local worker_name="${PROJECT_NAME}"
            if [ "$target_env" != "production" ]; then
                worker_name="${PROJECT_NAME}-${target_env}"
            fi
            test_deployment "https://$worker_name.workers.dev"
        fi
    fi
    
    echo
    print_success "🎉 Deployment completed successfully!"
    print_status "Monitor your deployment at: https://dash.cloudflare.com/"
    
    # Print workflow information
    echo
    print_status "📋 Workflow Configuration:"
    print_status "  Strategy: {{ cookiecutter.supervisor_strategy }}"
    print_status "  Error Handling: {{ cookiecutter.error_handling }}"
    print_status "  Max Retries: {{ cookiecutter.max_retries }}"
    print_status "  Timeout: {{ cookiecutter.timeout_ms }}ms"
    
    echo
    print_status "🔧 Next Steps:"
    print_status "  1. Test your workflow supervisor"
    print_status "  2. Configure specialist agent endpoints"
    print_status "  3. Monitor workflow execution logs"
    print_status "  4. Set up alerting for failed workflows"
}

# Run main function
main "$@"