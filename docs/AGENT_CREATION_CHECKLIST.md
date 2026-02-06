# Cloudflare Agent Creation Checklist

This checklist covers all steps needed to create a Cloudflare Workers agent using the Agentopia framework, push it to GitHub, and deploy it to a custom domain.

**Example**: Creating an InfoSec agent at `infosec.aktohcyber.com`

## Prerequisites ✓

- [ ] Cloudflare account with Workers enabled
- [ ] Custom domain registered and added to Cloudflare
- [ ] Cloudflare API token with Workers permissions (see below)
- [ ] GitHub account and `gh` CLI installed
- [ ] Node.js 18+ and npm installed
- [ ] Wrangler CLI installed (`npm install -g wrangler`)
- [ ] Access to Agentopia framework repository

### Creating a Cloudflare API Token

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use "Custom token" template with these permissions:
   - **Account** → `Cloudflare Workers Scripts:Edit`
   - **Account** → `Workers KV Storage:Edit` (if using caching)
   - **Account** → `Account Settings:Read`
   - **Zone** → `Zone:Read`
   - **Zone** → `DNS:Edit` (for custom domain setup)
   - **Zone** → `Workers Routes:Edit` (for custom domain routing)
4. Set the correct Account and Zone resources
5. Create token and save it securely

**Important**: The API token must be for the account that owns the domain. If you get authentication errors, verify:
- The token is for the correct account
- The account ID in wrangler.toml matches the token's account
- The zone ID corresponds to a domain in that account

## Phase 1: Configuration Planning

### 1.1 Choose Agent Type
- [ ] **Specialist Agent** - Single-purpose, domain expert (recommended for most cases)
- [ ] **Router Agent** - Routes requests to multiple specialist agents
- [ ] **Supervisor Agent** - LangGraph multi-agent orchestration
- [ ] **Network/Committee/Hierarchical** - Advanced multi-agent patterns

**Example**: InfoSec agent = Specialist Agent

### 1.2 Gather Configuration Details
- [ ] Agent name: `{agent-name}` (example: `infosec`)
- [ ] Description: `{description}` (example: "Information security and cybersecurity expert")
- [ ] Custom domain: `{subdomain}.{domain}.com` (example: `infosec.aktohcyber.com`)
- [ ] GitHub repository: `{agent-name}-agent` (example: `infosec-agent`)
- [ ] Cloudflare Account ID: `{account-id}`
- [ ] Cloudflare Zone ID: `{zone-id}`
- [ ] AI model: `@cf/meta/llama-3.1-8b-instruct` (recommended)

### 1.3 Prepare System Prompt
Create a detailed system prompt that defines the agent's expertise, behavior, and capabilities.

**InfoSec Example**:
```
You are an information security expert specializing in cybersecurity, threat analysis, 
vulnerability assessment, security best practices, compliance frameworks (SOC2, ISO27001, 
NIST), and incident response. Provide practical, actionable security guidance while 
explaining complex concepts clearly. Focus on defensive security measures and ethical 
security practices.
```

## Phase 2: Agent Generation

### 2.1 Create Configuration File
```bash
cd generators/javascript
```

Create `configs/{agent-name}.json`:
```json
{
  "name": "{agent-name}",
  "description": "{description}",
  "type": "specialist",
  "domain": "{subdomain}.{domain}.com",
  "accountId": "{cloudflare-account-id}",
  "zoneId": "{cloudflare-zone-id}",
  "model": "@cf/meta/llama-3.1-8b-instruct",
  "systemPrompt": "{your detailed system prompt}",
  "keywords": ["keyword1", "keyword2", "..."],
  "patterns": ["pattern1", "pattern2", "..."],
  "mcpToolName": "{agent-name}-tool",
  "expertise": "{domain expertise description}"
}
```

**InfoSec Example** (`configs/infosec.json`):
```json
{
  "name": "infosec",
  "description": "Information security and cybersecurity expert",
  "type": "specialist",
  "domain": "infosec.aktohcyber.com",
  "accountId": "YOUR_ACCOUNT_ID",
  "zoneId": "YOUR_ZONE_ID", 
  "model": "@cf/meta/llama-3.1-8b-instruct",
  "systemPrompt": "You are an information security expert specializing in cybersecurity, threat analysis, vulnerability assessment, security best practices, compliance frameworks (SOC2, ISO27001, NIST), and incident response. Provide practical, actionable security guidance while explaining complex concepts clearly. Focus on defensive security measures and ethical security practices.",
  "keywords": [
    "security", "vulnerability", "threat", "exploit", "breach", 
    "compliance", "encryption", "authentication", "firewall", 
    "malware", "phishing", "pentesting", "SOC2", "ISO27001", 
    "NIST", "zero trust", "incident response", "SIEM", "IDS", "IPS"
  ],
  "patterns": [
    "CVE-\\d{4}-\\d+", 
    "security.*assessment", 
    "threat.*analysis", 
    "incident.*response",
    "penetration.*test",
    "vulnerability.*scan"
  ],
  "mcpToolName": "infosec-tool",
  "expertise": "Cybersecurity, threat analysis, compliance frameworks, security architecture, and incident response"
}
```

### 2.2 Generate Agent Code
```bash
node build-agent.js configs/{agent-name}.json ../../{agent-name}-agent
```

**InfoSec Example**:
```bash
node build-agent.js configs/infosec.json ../../infosec-agent
```

### 2.3 Verify Generated Files
Navigate to the generated directory and verify:
```bash
cd ../../{agent-name}-agent
ls -la
```

Check for:
- [ ] `src/index.js` - Main agent code with LangChain.js integration
- [ ] `wrangler.toml` - Cloudflare Workers configuration
- [ ] `package.json` - Dependencies including LangChain.js
- [ ] `scripts/deploy.sh` - Deployment automation script
- [ ] `README.md` - Agent-specific documentation

### 2.4 Fix Known Issues (Temporary)
Until the template is updated, manually fix these issues:

1. **Copy framework files**:
```bash
mkdir -p src/agent-framework
cp ../generators/javascript/base-agent.js src/agent-framework/
cp ../generators/javascript/tool-registry.js src/agent-framework/
```

2. **Fix import path in src/index.js**:
Change: `import { BaseAgent } from '../agent-framework/base-agent.js';`
To: `import { BaseAgent } from './agent-framework/base-agent.js';`

3. **Fix wrangler.toml name**:
Replace any template variables like `{{domain.split('.')[0]}}` with actual worker name

4. **Add .dev.vars to .gitignore**:
```bash
echo ".dev.vars" >> .gitignore
```

## Phase 3: Local Development and Testing

### 3.1 Install Dependencies
```bash
cd ../../{agent-name}-agent
npm install
```

### 3.2 Configure Environment
Create `.dev.vars` file for local development:
```bash
CLOUDFLARE_API_TOKEN=your-api-token-here
```

### 3.3 Test Locally
```bash
# Start local development server
npx wrangler dev

# In another terminal, test the endpoints:
# Main endpoint
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the OWASP Top 10 vulnerabilities?"}'

# Health check
curl http://localhost:8787/health

# MCP endpoint
curl -X POST http://localhost:8787/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

**InfoSec Test Examples**:
```bash
# Security analysis query
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"question": "How can I implement zero trust architecture?"}'

# Vulnerability assessment
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"question": "Analyze security risks in serverless applications"}'
```

## Phase 4: GitHub Repository Creation

### 4.1 Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit: {agent-name} agent"
```

### 4.2 Create GitHub Repository
```bash
# Create private repository in Aktoh-Cyber organization
gh repo create Aktoh-Cyber/{agent-name}-agent --private \
  --description "{agent description}"

# Add remote and push
git branch -M main
git remote add origin https://github.com/Aktoh-Cyber/{agent-name}-agent.git
git push -u origin main
```

**InfoSec Example**:
```bash
gh repo create Aktoh-Cyber/infosec-agent --private \
  --description "Information security and cybersecurity expert agent"

git branch -M main
git remote add origin https://github.com/Aktoh-Cyber/infosec-agent.git
git push -u origin main
```

### 4.3 Set Up GitHub Secrets (Optional - for CI/CD)
```bash
# Add Cloudflare API token for automated deployments
gh secret set CLOUDFLARE_API_TOKEN --body "$CLOUDFLARE_API_TOKEN"

# Add account ID if not hardcoded in wrangler.toml
gh secret set CLOUDFLARE_ACCOUNT_ID --body "your-account-id"
```

## Phase 5: Cloudflare Deployment Preparation

### 5.1 Create KV Namespace for Caching
```bash
# Create KV namespace
npx wrangler kv:namespace create "{agent-name}-cache"

# Note the ID that is returned, you'll need it for wrangler.toml
```

**InfoSec Example**:
```bash
npx wrangler kv:namespace create "infosec-cache"
# Returns: { binding = "CACHE", id = "abcd1234..." }
```

### 5.2 Update wrangler.toml with KV Namespace
Edit `wrangler.toml` to add the KV namespace ID:
```toml
[[kv_namespaces]]
binding = "CACHE"
id = "{namespace-id-from-above}"
```

### 5.3 Set Cloudflare Secrets
```bash
# Set the Cloudflare API token as a secret
npx wrangler secret put CLOUDFLARE_API_TOKEN
# Enter your token when prompted
```

## Phase 6: Deploy to Cloudflare Workers

### 6.1 Deploy Using Wrangler
```bash
# Deploy to production
npx wrangler deploy

# Or use the provided deployment script
./scripts/deploy.sh
```

### 6.2 Verify Deployment
After deployment, you'll see:
```
Published {agent-name}-agent
  https://{agent-name}-agent.{subdomain}.workers.dev
```

Test the worker URL:
```bash
# Test worker domain
curl https://{agent-name}-agent.{subdomain}.workers.dev/health
```

## Phase 7: Custom Domain Configuration

### 7.1 Add DNS Record
In Cloudflare Dashboard:
1. Navigate to your domain (aktohcyber.com)
2. Go to DNS → Records
3. Add a new CNAME record:
   - Type: `CNAME`
   - Name: `{subdomain}` (example: `infosec`)
   - Target: `{agent-name}-agent.{account-subdomain}.workers.dev`
   - Proxy status: `Proxied` (orange cloud ON)
   - TTL: `Auto`

**InfoSec Example**:
- Name: `infosec`
- Target: `infosec-agent.aktoh-cyber.workers.dev`

### 7.2 Configure Worker Route
Option A: Via Cloudflare Dashboard
1. Go to Workers & Pages → Overview
2. Click on your worker ({agent-name}-agent)
3. Go to Settings → Triggers → Custom Domains
4. Click "Add Custom Domain"
5. Enter: `{subdomain}.{domain}.com` (example: `infosec.aktohcyber.com`)
6. Click "Add Custom Domain"

Option B: Via wrangler.toml (then redeploy)
Add to `wrangler.toml`:
```toml
routes = [
  { pattern = "{subdomain}.{domain}.com/*", zone_id = "{your-zone-id}" }
]
```

Then redeploy:
```bash
npx wrangler deploy
```

## Phase 8: Verification and Testing

### 8.1 Test Custom Domain
Wait 2-5 minutes for DNS propagation, then test:

```bash
# Health check
curl https://{subdomain}.{domain}.com/health

# Main query endpoint
curl -X POST https://{subdomain}.{domain}.com \
  -H "Content-Type: application/json" \
  -d '{"question": "Your test question here"}'

# MCP endpoint
curl -X POST https://{subdomain}.{domain}.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

**InfoSec Example Tests**:
```bash
# Basic health check
curl https://infosec.aktohcyber.com/health

# Security analysis
curl -X POST https://infosec.aktohcyber.com \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the security implications of using JWT tokens?"}'

# Vulnerability assessment
curl -X POST https://infosec.aktohcyber.com \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain SQL injection vulnerabilities and prevention methods"}'

# MCP tool discovery
curl -X POST https://infosec.aktohcyber.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'

# MCP tool call
curl -X POST https://infosec.aktohcyber.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "infosec-tool",
      "arguments": {
        "question": "Analyze security best practices for API development"
      }
    }
  }'
```

### 8.2 Monitor Logs
```bash
# Tail real-time logs
npx wrangler tail

# Or view in Cloudflare Dashboard:
# Workers & Pages → your-worker → Logs
```

### 8.3 Verify Caching
Check if responses are being cached:
```bash
# Make the same request twice and check response times
time curl https://{subdomain}.{domain}.com/health
time curl https://{subdomain}.{domain}.com/health
# Second request should be faster if caching works
```

## Phase 9: Post-Deployment Tasks

### 9.1 Update Documentation
- [ ] Update agent README.md with:
  - Production URL
  - API endpoints documentation
  - Example requests and responses
  - Integration instructions

### 9.2 Performance Optimization
- [ ] Enable Cloudflare Analytics in dashboard
- [ ] Monitor request patterns and optimize caching
- [ ] Review and adjust cache TTL if needed
- [ ] Check cold start performance

### 9.3 Integration with Other Agents (Optional)
If you have a router agent, add this specialist to the registry:
```json
{
  "tool": "{agent-name}",
  "url": "https://{subdomain}.{domain}.com",
  "keywords": [...],
  "patterns": [...],
  "priority": 1
}
```

### 9.4 Continuous Deployment Setup (Optional)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Cloudflare Workers
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. DNS Not Resolving
- **Symptom**: Browser shows "DNS_PROBE_FINISHED_NXDOMAIN"
- **Solutions**:
  - Wait up to 24 hours for full DNS propagation
  - Verify CNAME record exists and is proxied (orange cloud)
  - Check DNS with: `dig {subdomain}.{domain}.com`
  - Clear local DNS cache

#### 2. 522 Connection Timeout
- **Symptom**: Cloudflare error page with 522 error
- **Solutions**:
  - Verify worker is deployed: `npx wrangler deployments list`
  - Check worker route/custom domain configuration
  - Ensure zone ID in wrangler.toml matches your domain

#### 3. 1101 Worker Not Found
- **Symptom**: "Worker not found" error
- **Solutions**:
  - Verify deployment succeeded
  - Check worker name consistency across configs
  - Ensure custom domain is properly linked to worker

#### 4. Authentication/Token Errors
- **Symptom**: Deployment fails with auth errors
- **Solutions**:
  - Regenerate Cloudflare API token with correct permissions
  - Verify token includes Workers permissions
  - Check account ID matches your Cloudflare account

#### 5. CORS Errors
- **Symptom**: Browser console shows CORS errors
- **Solutions**:
  - Agent framework includes CORS headers by default
  - Check if requests are from allowed origins
  - Verify response headers include proper CORS settings

### Useful Debugging Commands
```bash
# List all workers
npx wrangler deployments list

# Show worker configuration
npx wrangler deployments view

# List KV namespaces
npx wrangler kv:namespace list

# Test worker directly (bypass domain)
curl https://{worker-name}.{account-subdomain}.workers.dev/health

# Check DNS resolution
dig {subdomain}.{domain}.com
nslookup {subdomain}.{domain}.com

# View detailed logs
npx wrangler tail --format pretty
```

## Complete Example Script

Save as `create-infosec-agent.sh`:
```bash
#!/bin/bash
set -e

# Configuration
AGENT_NAME="infosec"
AGENT_DESC="Information security and cybersecurity expert"
DOMAIN="infosec.aktohcyber.com"
ACCOUNT_ID="YOUR_ACCOUNT_ID"
ZONE_ID="YOUR_ZONE_ID"

echo "Creating InfoSec Agent..."

# 1. Generate agent
cd generators/javascript
cat > configs/infosec.json << EOF
{
  "name": "infosec",
  "description": "Information security and cybersecurity expert",
  "type": "specialist",
  "domain": "infosec.aktohcyber.com",
  "accountId": "$ACCOUNT_ID",
  "zoneId": "$ZONE_ID",
  "model": "@cf/meta/llama-3.1-8b-instruct",
  "systemPrompt": "You are an information security expert...",
  "keywords": ["security", "vulnerability", "threat"],
  "patterns": ["CVE-\\\\d{4}-\\\\d+"],
  "mcpToolName": "infosec-tool",
  "expertise": "Cybersecurity and threat analysis"
}
EOF

node build-agent.js configs/infosec.json ../../infosec-agent

# 2. Setup and test
cd ../../infosec-agent
npm install
echo "CLOUDFLARE_API_TOKEN=$CLOUDFLARE_API_TOKEN" > .dev.vars

# 3. Git setup
git init
git add .
git commit -m "Initial commit: InfoSec agent"

# 4. Create GitHub repo and push
gh repo create Aktoh-Cyber/infosec-agent --private -d "$AGENT_DESC"
git branch -M main
git remote add origin https://github.com/Aktoh-Cyber/infosec-agent.git
git push -u origin main

# 5. Deploy
npx wrangler deploy
npx wrangler secret put CLOUDFLARE_API_TOKEN

echo "InfoSec agent deployed! Test at: https://infosec.aktohcyber.com"
```

## Success Checklist

- [ ] Agent responds at `https://{subdomain}.{domain}.com/`
- [ ] Health endpoint returns `{"status":"healthy"}`
- [ ] Query endpoint processes questions correctly
- [ ] MCP endpoint returns tool list
- [ ] Response times are under 1 second
- [ ] Caching reduces response time for repeated queries
- [ ] Logs show successful request handling
- [ ] No errors in Cloudflare dashboard
- [ ] GitHub repository contains all code
- [ ] Documentation is complete and accurate

## Next Steps

1. **Enhance Agent Capabilities**
   - Add more keywords and patterns
   - Refine system prompt based on usage
   - Add specialized knowledge areas

2. **Multi-Agent Integration**
   - Add to router agent registry
   - Create agent-to-agent communication
   - Build hierarchical agent networks

3. **Monitoring and Analytics**
   - Set up Cloudflare Analytics dashboards
   - Monitor usage patterns
   - Track performance metrics
   - Set up alerting for errors

4. **Continuous Improvement**
   - Collect user feedback
   - Iterate on prompts and responses
   - Add new capabilities based on needs
   - Update documentation regularly